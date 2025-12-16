"""LangGraph definition for the Research Agent."""
from langgraph.graph import StateGraph, END
from app.graph.state import AgentState, create_initial_state
from app.graph.nodes import (
    reasoning_node,
    tool_executor_node,
    reflection_node,
    response_node,
)


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
    1. reasoning_node: Decides what tool to call
    2. tool_executor_node: Executes the tool
    3. reflection_node: Validates result, decides if more needed
    4. response_node: Generates final response
    """
    
    # Create the graph
    workflow = StateGraph(AgentState)
    
    # Add nodes
    workflow.add_node("reasoning", reasoning_node)
    workflow.add_node("tool_executor", tool_executor_node)
    workflow.add_node("reflection", reflection_node)
    workflow.add_node("response", response_node)
    
    # Set entry point
    workflow.set_entry_point("reasoning")
    
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
