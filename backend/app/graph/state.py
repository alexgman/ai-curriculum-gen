"""Agent state schema for LangGraph."""
from typing import TypedDict, Annotated, Sequence, Optional, Any
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages


class ToolCall(TypedDict):
    """Tool call information."""
    name: str
    arguments: dict[str, Any]


class ToolResult(TypedDict):
    """Tool execution result."""
    tool_name: str
    success: bool
    data: Any
    error: Optional[str]


class ReflectionResult(TypedDict):
    """Result from reflection node."""
    is_valid: bool
    is_relevant: bool
    is_sufficient: bool
    next_action: str  # "call_more_tools" | "respond_to_user"
    reasoning: str
    missing_data: list[str]


class ResearchData(TypedDict):
    """Accumulated research data."""
    competitors: list[dict]  # Course providers/competitors
    curricula: list[dict]    # Curriculum/lesson data
    courses: list[dict]      # Detailed course info with pricing
    lesson_frequency: list[dict]  # Lessons ranked by frequency
    module_inventory: list[dict]  # All unique modules across courses
    tiered_courses: dict  # Courses organized by price tier
    reddit_posts: list[dict]
    quora_answers: list[dict]
    podcasts: list[dict]
    blogs: list[dict]
    sentiment_summary: Optional[str]
    trending_topics: list[str]
    price_analysis: Optional[dict]  # Price range analysis


class AgentState(TypedDict):
    """
    State schema for the Research Agent.
    
    The agent maintains this state throughout the conversation,
    accumulating research data and tracking the current step.
    """
    
    # ===== Conversation =====
    messages: Annotated[Sequence[BaseMessage], add_messages]
    
    # ===== Session Info =====
    session_id: str
    industry: Optional[str]
    
    # ===== Current Tool Execution =====
    current_tool_call: Optional[ToolCall]
    current_tool_result: Optional[ToolResult]
    reasoning_explanation: Optional[str]  # Why the agent chose this action
    
    # ===== Reflection State =====
    reflection_result: Optional[ReflectionResult]
    reflection_explanation: Optional[str]  # Why reflection made its decision
    
    # ===== Accumulated Research Data =====
    research_data: ResearchData
    
    # ===== Control Flow =====
    # Determines which node to go to next
    next_node: str  # "reasoning" | "tool_executor" | "reflection" | "response" | "end"
    
    # ===== Error Handling =====
    error: Optional[str]
    retry_count: int
    tool_call_count: int  # Track number of tool calls made


def create_initial_state(session_id: str) -> AgentState:
    """Create initial state for a new research session."""
    return AgentState(
        messages=[],
        session_id=session_id,
        industry=None,
        current_tool_call=None,
        current_tool_result=None,
        reasoning_explanation=None,
        reflection_result=None,
        reflection_explanation=None,
        research_data=ResearchData(
            competitors=[],
            curricula=[],
            courses=[],
            lesson_frequency=[],
            module_inventory=[],
            tiered_courses={},
            reddit_posts=[],
            quora_answers=[],
            podcasts=[],
            blogs=[],
            sentiment_summary=None,
            trending_topics=[],
            price_analysis=None,
        ),
        next_node="reasoning",
        error=None,
        retry_count=0,
        tool_call_count=0,
    )

