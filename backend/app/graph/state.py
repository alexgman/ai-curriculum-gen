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


class ResearchPlan(TypedDict):
    """Research plan discovered from preliminary research."""
    industry: str
    competitors: list[dict]  # Discovered competitors with type and description
    certifications: list[dict]  # Discovered certifications
    target_audiences: list[dict]  # Identified audience segments
    # User selections (updated through feedback)
    selected_competitors: list[str]  # Names of competitors to focus on
    selected_certifications: list[str]  # Certifications to cover
    selected_audience: str  # Target audience
    # Plan status
    is_confirmed: bool  # User has confirmed the plan


class ClarificationState(TypedDict):
    """State for human-in-the-loop planning and confirmation."""
    stage: str  # "discovery" | "presenting_plan" | "refining" | "confirmed"
    iteration: int  # How many refinement iterations
    user_feedback: list[str]  # History of user feedback
    is_complete: bool  # Whether planning is done


# ===== STEP 2: CURRICULUM DRAFTING TYPES =====

class ExpertCourse(TypedDict):
    """User-added course that research didn't find."""
    source: str  # Provider name (e.g., "HVACREdu", "ESCO Institute")
    modules: list[str]  # List of module names
    notes: Optional[str]  # Any additional notes from user


class CurriculumModule(TypedDict):
    """A single module in the curriculum."""
    id: str  # e.g., "1.1", "2.3"
    name: str
    description: Optional[str]
    duration_minutes: Optional[int]
    source: str  # "research" | "expert"
    prerequisites: list[str]  # List of module IDs


class CurriculumSection(TypedDict):
    """A section containing multiple modules."""
    name: str
    description: Optional[str]
    duration_hours: Optional[float]
    modules: list[CurriculumModule]


class CurriculumProposal(TypedDict):
    """The proposed curriculum structure."""
    title: str
    summary: str
    target_audience: str
    certification_focus: list[str]
    duration_hours: float
    total_modules: int
    sections: list[CurriculumSection]


class CurriculumDraft(TypedDict):
    """State for curriculum drafting (Step 2)."""
    stage: str  # "collecting" | "proposing" | "refining" | "generating" | "complete"
    
    # Knowledge base
    expert_courses: list[ExpertCourse]  # User-added courses/modules
    
    # Current proposal
    proposal: Optional[CurriculumProposal]
    
    # Tracking
    iteration: int  # v1, v2, v3...
    user_feedback: list[str]  # History of refinements
    is_approved: bool  # User approved the proposal


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
    
    # ===== Human-in-the-Loop Planning =====
    research_plan: Optional[ResearchPlan]  # Discovered and refined research plan
    clarification: Optional[ClarificationState]
    awaiting_clarification: bool  # True when waiting for user response
    
    # ===== Step 2: Curriculum Drafting =====
    curriculum_draft: Optional[CurriculumDraft]  # Curriculum drafting state
    awaiting_curriculum_input: bool  # True when waiting for user input on curriculum
    curriculum_intent: bool  # Pre-computed by Claude: True if user wants to create curriculum
    
    # ===== Accumulated Research Data =====
    research_data: ResearchData
    
    # ===== Control Flow =====
    # Determines which node to go to next
    next_node: str  # "reasoning" | "clarification" | "tool_executor" | "reflection" | "response" | "end"
    
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
        research_plan=None,
        clarification=None,
        awaiting_clarification=False,
        curriculum_draft=None,
        awaiting_curriculum_input=False,
        curriculum_intent=False,
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

