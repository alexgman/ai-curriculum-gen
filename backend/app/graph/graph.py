"""LangGraph definition for the Research Agent."""
from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage
from app.graph.state import AgentState, create_initial_state
from app.graph.nodes import (
    reasoning_node,
    tool_executor_node,
    reflection_node,
    response_node,
    clarification_node,
    curriculum_draft_node,
)


async def detect_curriculum_intent(message: str, has_research_data: bool) -> bool:
    """
    Use Claude to detect if the user wants to start curriculum drafting.
    
    This is called BEFORE graph execution to pre-compute intent.
    Only called when research is complete (has_research_data=True).
    
    Args:
        message: User's message
        has_research_data: Whether Step 1 research is complete
        
    Returns:
        True if user wants to create/draft curriculum, False otherwise
    """
    # Only check for curriculum intent if research is complete
    if not has_research_data:
        return False
    
    # Quick check for obvious non-curriculum messages (save API calls)
    msg_lower = message.lower().strip()
    
    # Obvious NOT curriculum triggers - simple confirmations or questions
    non_triggers = ["proceed", "yes", "no", "ok", "okay", "help", "what", "how", "why", "?"]
    if msg_lower in non_triggers or len(message) < 5:
        return False
    
    # Use Claude to understand intent
    from app.services.anthropic import claude_client
    
    try:
        prompt = f"""Analyze this user message and determine if they want to CREATE or DRAFT a CURRICULUM/COURSE/TRAINING PROGRAM.

User message: "{message}"

Context: The user has just completed research on training courses. They can now either:
1. Start curriculum drafting (create a structured course/curriculum based on research)
2. Add expert courses/modules they found
3. Ask questions or make other requests

Does this message indicate the user wants to CREATE/DRAFT a curriculum or training program?

Consider messages like:
- "Create a curriculum for beginners" → YES
- "Let's build a course structure" → YES  
- "Draft a training program" → YES
- "I also found these courses: X, Y, Z" → YES (adding expert input for curriculum)
- "Can you make a lesson plan?" → YES
- "Structure this into modules" → YES
- "What did you find?" → NO
- "Tell me more about X" → NO
- "Thanks" → NO

Answer with ONLY "YES" or "NO":"""

        response = await claude_client.complete(
            prompt=prompt,
            system="You are an intent classifier. Respond with only YES or NO.",
            max_tokens=10,
            temperature=0,
        )
        
        result = response.strip().upper()
        is_curriculum = result.startswith("YES")
        
        print(f"🎯 Curriculum intent detection: '{message[:50]}...' → {is_curriculum}")
        return is_curriculum
        
    except Exception as e:
        print(f"⚠️ Intent detection error: {e}, falling back to pattern matching")
        # Fallback to simple pattern matching if Claude fails
        return _fallback_curriculum_check(message)


def _fallback_curriculum_check(message: str) -> bool:
    """Fallback pattern-based check if Claude intent detection fails."""
    import re
    msg_lower = message.lower().strip()
    
    patterns = [
        r"create\s+(?:a\s+)?curriculum",
        r"draft\s+(?:a\s+)?curriculum", 
        r"build\s+(?:a\s+)?(?:course|curriculum|training)",
        r"make\s+(?:a\s+)?(?:course|curriculum)",
        r"i\s+(?:also\s+)?found\s+(?:these|some)",
        r"add\s+(?:these|my)\s+(?:courses|modules)",
        r"structure\s+(?:this|the)\s+(?:into|as)",
    ]
    
    return any(re.search(pattern, msg_lower) for pattern in patterns)


def route_entry(state: AgentState) -> str:
    """
    Route at entry point - decide which node to go to.
    
    Flow:
    1. New research → clarification (discovery + present plan)
    2. User responding to plan → clarification (process feedback)
    3. Plan confirmed → reasoning (start research)
    4. Already researching → reasoning (continue)
    5. Research complete + curriculum input → curriculum_draft
    6. User responding to curriculum proposal → curriculum_draft
    """
    research_data = state.get("research_data", {})
    courses = research_data.get("courses", [])
    research_plan = state.get("research_plan")
    clarification = state.get("clarification")
    awaiting = state.get("awaiting_clarification", False)
    awaiting_curriculum = state.get("awaiting_curriculum_input", False)
    curriculum_draft = state.get("curriculum_draft")
    tool_call_count = state.get("tool_call_count", 0)
    
    # Get pre-computed curriculum intent (set by chat endpoint using Claude)
    curriculum_intent = state.get("curriculum_intent", False)
    
    # Get last user message
    last_user_message = ""
    for msg in reversed(state.get("messages", [])):
        if isinstance(msg, HumanMessage):
            last_user_message = msg.content
            break
    
    # ===== STEP 2: CURRICULUM DRAFTING =====
    # If user is responding to curriculum draft proposal
    if awaiting_curriculum and curriculum_draft:
        stage = curriculum_draft.get("stage", "")
        if stage in ["proposing", "refining"]:
            print(f"🔀 → CURRICULUM_DRAFT (user responded, stage={stage})")
            return "curriculum_draft"
    
    # If research is complete and Claude detected curriculum intent
    if len(courses) > 0 and curriculum_intent:
        print("🔀 → CURRICULUM_DRAFT (research complete, curriculum intent detected)")
        return "curriculum_draft"
    
    # ===== STEP 1: RESEARCH CLARIFICATION =====
    # If user is responding to planning questions
    if awaiting and clarification:
        stage = clarification.get("stage", "")
        if stage in ["presenting_plan", "refining", "discovery"]:
            print(f"🔀 → CLARIFICATION (user responded to plan, stage={stage})")
            return "clarification"
    
    # If we already have research data, continue to reasoning
    if len(courses) > 0:
        print("🔀 → REASONING (have research data)")
        return "reasoning"
    
    # If plan is confirmed, start reasoning
    if research_plan and research_plan.get("is_confirmed"):
        print("🔀 → REASONING (plan confirmed)")
        return "reasoning"
    
    # If clarification/planning is complete (confirmed stage), go to reasoning
    if clarification and clarification.get("stage") == "confirmed":
        print("🔀 → REASONING (planning stage=confirmed)")
        return "reasoning"
    
    # If we've already made tool calls, continue with reasoning
    if tool_call_count > 0:
        print("🔀 → REASONING (continuing research)")
        return "reasoning"
    
    # New research - do discovery and planning first
    if not research_plan:
        print("🔀 → CLARIFICATION (new research, start discovery)")
        return "clarification"
    
    # Has a plan but not confirmed - continue planning
    if research_plan and not research_plan.get("is_confirmed"):
        print("🔀 → CLARIFICATION (continue planning)")
        return "clarification"
    
    # Default to reasoning
    print("🔀 → REASONING (default)")
    return "reasoning"


def route_after_clarification(state: AgentState) -> str:
    """Route after clarification/planning node."""
    awaiting = state.get("awaiting_clarification", False)
    clarification = state.get("clarification")
    research_plan = state.get("research_plan")
    next_node = state.get("next_node")
    
    # Explicit next_node from clarification node
    if next_node == "reasoning":
        print("🔀 → REASONING (explicit from clarification)")
        return "reasoning"
    
    if awaiting:
        # Waiting for user response - end this execution
        print("🔀 → END (awaiting user response to plan)")
        return "end"
    
    # Plan is confirmed
    if research_plan and research_plan.get("is_confirmed"):
        print("🔀 → REASONING (plan confirmed)")
        return "reasoning"
    
    # Clarification complete
    if clarification and clarification.get("is_complete"):
        print("🔀 → REASONING (planning complete)")
        return "reasoning"
    
    # Default end
    print("🔀 → END (planning default)")
    return "end"


def route_after_reasoning(state: AgentState) -> str:
    """Route after reasoning node based on decision."""
    next_node = state.get("next_node", "response")
    tool_call = state.get("current_tool_call")
    
    print(f"🔀 ROUTING (after reasoning): next_node={next_node}, has_tool_call={bool(tool_call)}")
    
    if next_node == "tool_executor" and tool_call:
        print(f"✅ → TOOL_EXECUTOR (tool: {tool_call.get('name', 'unknown')})")
        return "tool_executor"
    elif next_node == "response":
        print(f"✅ → RESPONSE")
        return "response"
    else:
        # Default to response if unclear
        print(f"⚠️ → RESPONSE (default fallback)")
        return "response"


def route_after_reflection(state: AgentState) -> str:
    """
    Route after reflection - GO TO RESPONSE after first successful tool call with data.
    """
    research_data = state.get("research_data", {})
    tool_call_count = state.get("tool_call_count", 0)
    courses = research_data.get("courses", [])
    
    print(f"🔀 ROUTING: courses={len(courses)}, tool_calls={tool_call_count}")
    
    # SIMPLE RULE: If we have ANY courses, go to response
    # The discover_courses_with_rankings tool already gets 25-30 courses
    if len(courses) > 0:
        print(f"✅ → RESPONSE ({len(courses)} courses found)")
        return "response"
    
    # If we've made a tool call but got no courses, try once more
    if tool_call_count >= 2:
        print(f"✅ → RESPONSE (max attempts, {len(courses)} courses)")
        return "response"
    
    # Otherwise continue research
    print(f"🔄 → REASONING (no courses yet)")
    return "reasoning"


def route_after_response(state: AgentState) -> str:
    """Route after response - always end."""
    return "end"


def route_after_curriculum_draft(state: AgentState) -> str:
    """Route after curriculum draft node."""
    awaiting = state.get("awaiting_curriculum_input", False)
    curriculum_draft = state.get("curriculum_draft")
    
    if awaiting:
        # Waiting for user response
        print("🔀 → END (awaiting curriculum input)")
        return "end"
    
    # Curriculum complete
    if curriculum_draft and curriculum_draft.get("stage") == "complete":
        print("🔀 → END (curriculum complete)")
        return "end"
    
    # Default end
    print("🔀 → END (curriculum default)")
    return "end"


def create_research_graph():
    """
    Create the LangGraph for research agent.
    
    Flow:
    STEP 1 (Research):
    1. entry → clarification (for new research) OR reasoning (continuing)
    2. clarification → end (wait for user) OR reasoning (user responded)
    3. reasoning_node: Decides what tool to call
    4. tool_executor_node: Executes the tool
    5. reflection_node: Validates result, decides if more needed
    6. response_node: Generates final response
    
    STEP 2 (Curriculum Drafting):
    7. entry → curriculum_draft (when user adds expert courses after research)
    8. curriculum_draft → end (wait for user feedback or generate final)
    """
    
    # Create the graph
    workflow = StateGraph(AgentState)
    
    # Add nodes
    workflow.add_node("entry", lambda state: state)  # Pass-through entry node
    workflow.add_node("clarification", clarification_node)
    workflow.add_node("reasoning", reasoning_node)
    workflow.add_node("tool_executor", tool_executor_node)
    workflow.add_node("reflection", reflection_node)
    workflow.add_node("response", response_node)
    workflow.add_node("curriculum_draft", curriculum_draft_node)  # Step 2
    
    # Set entry point
    workflow.set_entry_point("entry")
    
    # Route from entry - clarification vs reasoning vs curriculum_draft
    workflow.add_conditional_edges(
        "entry",
        route_entry,
        {
            "clarification": "clarification",
            "reasoning": "reasoning",
            "curriculum_draft": "curriculum_draft",
        }
    )
    
    # Route from clarification
    workflow.add_conditional_edges(
        "clarification",
        route_after_clarification,
        {
            "reasoning": "reasoning",
            "end": END,
        }
    )
    
    # Add conditional edges from reasoning
    workflow.add_conditional_edges(
        "reasoning",
        route_after_reasoning,
        {
            "tool_executor": "tool_executor",
            "response": "response",
        }
    )
    
    # Tool executor always goes to reflection
    workflow.add_edge("tool_executor", "reflection")
    
    # Add conditional edges from reflection
    workflow.add_conditional_edges(
        "reflection",
        route_after_reflection,
        {
            "reasoning": "reasoning",
            "response": "response",
        }
    )
    
    # Add conditional edges from response
    workflow.add_conditional_edges(
        "response",
        route_after_response,
        {
            "end": END,
        }
    )
    
    # Route from curriculum_draft
    workflow.add_conditional_edges(
        "curriculum_draft",
        route_after_curriculum_draft,
        {
            "end": END,
        }
    )
    
    # Compile the graph
    return workflow.compile()


# Create a singleton instance
research_graph = create_research_graph()
