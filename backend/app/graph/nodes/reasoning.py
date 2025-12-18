"""Reasoning node - decides what tool to call based on user query and state."""
import json
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_anthropic import ChatAnthropic
from app.graph.state import AgentState, ToolCall
from app.config import settings
from app.prompts.reasoning import REASONING_SYSTEM_PROMPT, REASONING_USER_PROMPT
from app.tools import get_tool_descriptions
from app.utils.truncation import truncate_text, format_research_summary, truncate_research_data


async def reasoning_node(state: AgentState) -> dict:
    """
    Reasoning node that decides what action to take.
    
    Analyzes:
    - User's query
    - Current research state
    - Previous tool results
    
    Decides:
    - Which tool to call next, OR
    - Ready to respond to user
    """
    
    # Initialize Claude with LIMITED max_tokens
    llm = ChatAnthropic(
        model=settings.anthropic_model,
        api_key=settings.anthropic_api_key,
        temperature=0,
        max_tokens=1024,  # Reasoning decisions are short, don't need much
    )
    
    # Build context about current state (TRUNCATED to prevent context overflow)
    research_data_truncated = truncate_research_data(state["research_data"], max_items_per_category=5)
    research_summary = format_research_summary(research_data_truncated)
    tool_descriptions = get_tool_descriptions()
    
    # Build conversation history (last 5 messages for context)
    conversation_history = []
    for msg in list(state["messages"])[-10:]:  # Last 10 messages
        if isinstance(msg, HumanMessage):
            conversation_history.append(f"User: {msg.content}")
        elif isinstance(msg, AIMessage) and not msg.content.startswith("Reasoning:"):
            # Only include actual responses, not internal reasoning
            conversation_history.append(f"Assistant: {msg.content[:200]}...")
    
    conversation_context = "\n".join(conversation_history) if conversation_history else "No previous conversation"
    
    # Get the current/last user message
    last_user_message = ""
    for msg in reversed(state["messages"]):
        if isinstance(msg, HumanMessage):
            last_user_message = msg.content
            break
    
    # Build the prompt (with truncation)
    system_prompt = REASONING_SYSTEM_PROMPT.format(
        tool_descriptions=tool_descriptions
    )
    
    # Truncate tool result to prevent overflow
    tool_result_str = "None"
    if state.get("current_tool_result"):
        tool_result = state["current_tool_result"]
        tool_result_limited = {
            "tool_name": tool_result.get("tool_name"),
            "success": tool_result.get("success"),
            "data_summary": str(tool_result.get("data", ""))[:500] + "..." if tool_result.get("data") else None,
        }
        tool_result_str = json.dumps(tool_result_limited, indent=2)
    
    # Get research plan if available
    research_plan_str = "No research plan yet - do general research."
    research_plan = state.get("research_plan")
    if research_plan and research_plan.get("is_confirmed"):
        # Format the confirmed research plan
        plan_parts = [
            f"**Industry:** {research_plan.get('industry', 'Not specified')}",
            f"\n**Selected Competitors to Research:**"
        ]
        for comp in research_plan.get("competitors", [])[:10]:
            if comp["name"] in research_plan.get("selected_competitors", []):
                plan_parts.append(f"  - {comp['name']} ({comp.get('type', 'unknown')})")
        
        plan_parts.append(f"\n**Certifications to Cover:**")
        for cert in research_plan.get("certifications", [])[:6]:
            if cert["name"] in research_plan.get("selected_certifications", []):
                plan_parts.append(f"  - {cert['name']}")
        
        plan_parts.append(f"\n**Target Audience:** {research_plan.get('selected_audience', 'All levels')}")
        research_plan_str = "\n".join(plan_parts)
    
    user_prompt = REASONING_USER_PROMPT.format(
        conversation_history=truncate_text(conversation_context, max_tokens=1000),
        user_query=truncate_text(last_user_message, max_tokens=200),
        industry=state.get("industry", "Not specified yet"),
        research_plan=research_plan_str,
        research_summary=research_summary,
        last_tool_result=tool_result_str,
        reflection_feedback=truncate_text(
            state.get("reflection_result", {}).get("reasoning", "None") if state.get("reflection_result") else "None",
            max_tokens=300
        ),
    )
    
    # Call Claude
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_prompt),
    ]
    
    import sys
    print(f"🧠 REASONING: Calling Claude for query: {last_user_message[:50]}...", file=sys.stderr, flush=True)
    
    response = await llm.ainvoke(messages)
    
    print(f"🧠 REASONING RESPONSE: {response.content[:300]}...", file=sys.stderr, flush=True)
    
    # Parse the response
    try:
        result = _parse_reasoning_response(response.content)
        print(f"🧠 PARSED RESULT: action={result.get('action')}, tool={result.get('tool_name', 'N/A')}", file=sys.stderr, flush=True)
    except Exception as e:
        # If parsing fails, try to respond to user
        return {
            "next_node": "response",
            "error": f"Failed to parse reasoning response: {str(e)}",
        }
    
    # Update state based on decision
    if result["action"] == "ask_question":
        # AI is asking a clarifying question - respond directly with the question
        question = result.get("question", "Could you please provide more details?")
        options = result.get("options", [])
        
        # Format the question with options if provided
        if options:
            options_text = "\n".join([f"- {opt}" for opt in options])
            question_text = f"{question}\n\n{options_text}"
        else:
            question_text = question
        
        return {
            "next_node": "response",  # Go directly to response to show the question
            "messages": [AIMessage(content=question_text)],
            "is_clarifying_question": True,  # Flag for frontend
        }
    elif result["action"] == "call_tool":
        # Include the full reasoning explanation
        reasoning_text = result.get("thinking", "Planning next step")
        return {
            "current_tool_call": ToolCall(
                name=result["tool_name"],
                arguments=result["tool_arguments"],
            ),
            "next_node": "tool_executor",
            "industry": result.get("industry") or state.get("industry"),
            "messages": [AIMessage(content=f"Reasoning: {reasoning_text}")],
            "reasoning_explanation": reasoning_text,  # Store for frontend
        }
    else:
        # Ready to respond
        return {
            "next_node": "response",
            "messages": [AIMessage(content=result.get("thinking", ""))],
        }


def _build_research_summary(research_data: dict) -> str:
    """Build a summary of current research data."""
    parts = []
    
    if research_data.get("competitors"):
        parts.append(f"- Found {len(research_data['competitors'])} competitors")
    
    if research_data.get("curricula"):
        parts.append(f"- Extracted {len(research_data['curricula'])} curricula")
    
    if research_data.get("reddit_posts"):
        parts.append(f"- Found {len(research_data['reddit_posts'])} Reddit posts")
    
    if research_data.get("quora_answers"):
        parts.append(f"- Found {len(research_data['quora_answers'])} Quora answers")
    
    if research_data.get("podcasts"):
        parts.append(f"- Found {len(research_data['podcasts'])} podcasts")
    
    if research_data.get("blogs"):
        parts.append(f"- Found {len(research_data['blogs'])} blogs")
    
    if research_data.get("trending_topics"):
        parts.append(f"- Identified {len(research_data['trending_topics'])} trending topics")
    
    if not parts:
        return "No research data collected yet."
    
    return "\n".join(parts)


def _parse_reasoning_response(content: str) -> dict:
    """Parse the reasoning response from Claude."""
    # Try to extract JSON from the response
    try:
        # Look for JSON block
        if "```json" in content:
            json_str = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            json_str = content.split("```")[1].split("```")[0].strip()
        else:
            # Try to parse the whole content as JSON
            json_str = content.strip()
        
        return json.loads(json_str)
    except json.JSONDecodeError:
        # If JSON parsing fails, try to extract key information
        if "respond" in content.lower() or "ready to respond" in content.lower():
            return {"action": "respond", "thinking": content}
        else:
            # Default to responding if we can't parse
            return {"action": "respond", "thinking": content}

