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
    
    if next_node == "tool_executor" and state.get("current_tool_call"):
        return "tool_executor"
    elif next_node == "response":
        return "response"
    else:
        # Default to response if unclear
        return "response"


def route_after_reflection(state: AgentState) -> str:
    """Route after reflection - simple routing based on data and limits."""
    reflection = state.get("reflection_result")
    research_data = state.get("research_data", {})
    retry_count = state.get("retry_count", 0)
    tool_call_count = state.get("tool_call_count", 0)
    
    # Count data we have
    courses = research_data.get("courses", [])
    podcasts = research_data.get("podcasts", [])
    competitors = research_data.get("competitors", [])
    total_items = len(courses) + len(podcasts) + len(competitors)
    
    print(f"📊 Data: {len(courses)} courses, {len(podcasts)} podcasts, total={total_items}, calls={tool_call_count}")
    
    # 1. SAFETY LIMITS - Always respond if we hit these
    if tool_call_count >= 4:
        print(f"✅ Max tool calls ({tool_call_count}) - generating response")
        return "response"
    
    if retry_count >= 3:
        print(f"✅ Max retries ({retry_count}) - generating response")
        return "response"
    
    # 2. ENOUGH DATA - Respond if we have good data
    if len(courses) >= 10:
        print(f"✅ Have {len(courses)} courses - generating response")
        return "response"
    
    if total_items >= 15:
        print(f"✅ Have {total_items} total items - generating response")
        return "response"
    
    # 3. REFLECTION SAYS SUFFICIENT - Respect it if we have any data
    if reflection and reflection.get("is_sufficient") and total_items >= 3:
        print(f"✅ Reflection says sufficient - generating response")
        return "response"
    
    # 4. Continue researching
    print(f"🔄 Need more data (have {total_items} items) - continuing")
    return "reasoning"


def route_after_response(state: AgentState) -> str:
    """Route after response - either end or continue conversation."""
    # For now, always end after response
    # In future, could check if user asked follow-up
    return "end"


def create_research_graph():
    """
    Create the LangGraph for research agent.
    
    Flow:
    1. reasoning_node: Decides what tool to call
    2. tool_executor_node: Executes the tool
    3. reflection_node: Validates result, decides if more needed
    4. response_node: Generates final response
    
    The loop between reasoning -> tool -> reflection continues
    until reflection says we have enough data.
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

