"""LangGraph definition for the Research Agent."""
from langgraph.graph import StateGraph, END
from app.graph.state import AgentState, create_initial_state
from app.graph.nodes import (
    reasoning_node,
    tool_executor_node,
    reflection_node,
    response_node,
    clarification_node,
)


def route_entry(state: AgentState) -> str:
    """
    Route at entry point - decide if we need planning/clarification first.
    
    Flow:
    1. New research → planning (discovery + present plan)
    2. User responding to plan → planning (process feedback)
    3. Plan confirmed → reasoning (start research)
    4. Already researching → reasoning (continue)
    """
    research_data = state.get("research_data", {})
    courses = research_data.get("courses", [])
    research_plan = state.get("research_plan")
    clarification = state.get("clarification")
    awaiting = state.get("awaiting_clarification", False)
    tool_call_count = state.get("tool_call_count", 0)
    
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


def create_research_graph():
    """
    Create the LangGraph for research agent.
    
    Flow:
    1. entry → clarification (for new research) OR reasoning (continuing)
    2. clarification → end (wait for user) OR reasoning (user responded)
    3. reasoning_node: Decides what tool to call
    4. tool_executor_node: Executes the tool
    5. reflection_node: Validates result, decides if more needed
    6. response_node: Generates final response
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
    
    # Set entry point
    workflow.set_entry_point("entry")
    
    # Route from entry - clarification vs reasoning
    workflow.add_conditional_edges(
        "entry",
        route_entry,
        {
            "clarification": "clarification",
            "reasoning": "reasoning",
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
    
    # Compile the graph
    return workflow.compile()


# Create a singleton instance
research_graph = create_research_graph()
