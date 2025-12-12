"""Reflection node - validates tool results to prevent hallucination."""
import json
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langchain_anthropic import ChatAnthropic
from app.graph.state import AgentState, ReflectionResult, ResearchData
from app.config import settings
from app.prompts.reflection import REFLECTION_SYSTEM_PROMPT, REFLECTION_USER_PROMPT
from app.utils.truncation import truncate_text, format_research_summary, truncate_research_data

# Session-based research data store (persists across nodes)
_session_research_data: dict[str, ResearchData] = {}


async def reflection_node(state: AgentState) -> dict:
    """
    Reflection node that validates tool results.
    
    This is the KEY anti-hallucination safeguard:
    1. Checks if tool result is valid (not empty, not error)
    2. Checks if result is relevant to user's query
    3. Checks if we have enough data or need more tools
    4. Decides next action based on actual data, not assumptions
    """
    
    tool_result = state.get("current_tool_result")
    
    if not tool_result:
        return {
            "reflection_result": ReflectionResult(
                is_valid=False,
                is_relevant=False,
                is_sufficient=False,
                next_action="call_more_tools",
                reasoning="No tool result to reflect on",
                missing_data=["tool_result"],
            ),
            "next_node": "reasoning",
        }
    
    # If tool failed, we need to try something else
    if not tool_result["success"]:
        return {
            "reflection_result": ReflectionResult(
                is_valid=False,
                is_relevant=False,
                is_sufficient=False,
                next_action="call_more_tools",
                reasoning=f"Tool failed: {tool_result.get('error', 'Unknown error')}",
                missing_data=[f"retry_{tool_result['tool_name']}"],
            ),
            "next_node": "reasoning",
            "retry_count": state.get("retry_count", 0) + 1,
        }
    
    # Use Claude to analyze the result with LIMITED max_tokens
    llm = ChatAnthropic(
        model=settings.anthropic_model,
        api_key=settings.anthropic_api_key,
        temperature=0,
        max_tokens=512,  # Reflection is just validation, very short
    )
    
    # Get the last user message for context
    last_user_message = ""
    for msg in reversed(state["messages"]):
        if isinstance(msg, HumanMessage):
            last_user_message = msg.content
            break
    
    # Build the prompt (HEAVILY TRUNCATED to prevent context overflow)
    # Best practice: Only send what's needed for validation
    tool_data_preview = str(tool_result["data"])[:1000] + "..." if tool_result.get("data") else "None"
    
    user_prompt = REFLECTION_USER_PROMPT.format(
        user_query=truncate_text(last_user_message, max_tokens=200),
        industry=state.get("industry", "Not specified"),
        tool_name=tool_result["tool_name"],
        tool_result=tool_data_preview,  # Only first 1000 chars
        current_research=format_research_summary(truncate_research_data(state["research_data"], max_items_per_category=5)),
    )
    
    messages = [
        SystemMessage(content=REFLECTION_SYSTEM_PROMPT),
        HumanMessage(content=user_prompt),
    ]
    
    response = await llm.ainvoke(messages)
    
    # Parse reflection result
    reflection = _parse_reflection_response(response.content)
    
    # Get session ID for storing data
    session_id = state.get("session_id", "default")
    
    # Get existing data for this session or use current state
    existing_research = _session_research_data.get(session_id, state["research_data"])
    
    # Update research data based on tool result
    updated_research = _update_research_data(
        existing_research,
        tool_result["tool_name"],
        tool_result["data"],
    )
    
    # Store in session-based cache (CRITICAL for persistence)
    _session_research_data[session_id] = updated_research
    
    # Debug: Log what we stored
    courses_count = len(updated_research.get("courses", []))
    print(f"📊 Research data updated: {courses_count} courses stored for session {session_id[:8]}")
    
    # Increment tool call count
    tool_call_count = state.get("tool_call_count", 0) + 1
    
    # Determine next node
    if reflection["is_sufficient"]:
        next_node = "response"
    else:
        next_node = "reasoning"
    
    # Build detailed reflection message
    reflection_msg = reflection['reasoning']
    if not reflection["is_sufficient"] and reflection.get("missing_data"):
        reflection_msg += f" | Missing: {', '.join(reflection['missing_data'][:3])}"
    
    return {
        "reflection_result": reflection,
        "research_data": updated_research,
        "next_node": next_node,
        "tool_call_count": tool_call_count,  # Track number of tool calls
        "messages": [AIMessage(content=f"Reflection: {reflection_msg}")],
        "reflection_explanation": reflection['reasoning'],  # Store for frontend
    }


def _summarize_research(research_data: ResearchData) -> str:
    """Summarize what research data we have so far."""
    parts = []
    
    if research_data.get("competitors"):
        competitors = research_data["competitors"]
        parts.append(f"Competitors ({len(competitors)}): {', '.join([c.get('name', 'Unknown')[:30] for c in competitors[:5]])}")
    
    if research_data.get("curricula"):
        parts.append(f"Curricula extracted: {len(research_data['curricula'])}")
    
    if research_data.get("reddit_posts"):
        parts.append(f"Reddit posts: {len(research_data['reddit_posts'])}")
    
    if research_data.get("podcasts"):
        parts.append(f"Podcasts found: {len(research_data['podcasts'])}")
    
    if research_data.get("blogs"):
        parts.append(f"Blogs found: {len(research_data['blogs'])}")
    
    if not parts:
        return "No research data collected yet."
    
    return "\n".join(parts)


def _parse_reflection_response(content: str) -> ReflectionResult:
    """Parse Claude's reflection response."""
    try:
        # Try to extract JSON
        if "```json" in content:
            json_str = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            json_str = content.split("```")[1].split("```")[0].strip()
        else:
            json_str = content.strip()
        
        data = json.loads(json_str)
        
        return ReflectionResult(
            is_valid=data.get("is_valid", False),
            is_relevant=data.get("is_relevant", False),
            is_sufficient=data.get("is_sufficient", False),
            next_action=data.get("next_action", "call_more_tools"),
            reasoning=data.get("reasoning", ""),
            missing_data=data.get("missing_data", []),
        )
    except (json.JSONDecodeError, KeyError):
        # Default to needing more data if we can't parse
        return ReflectionResult(
            is_valid=True,
            is_relevant=True,
            is_sufficient=False,
            next_action="call_more_tools",
            reasoning=content,
            missing_data=[],
        )


def _update_research_data(
    current: ResearchData,
    tool_name: str,
    tool_data: any,
) -> ResearchData:
    """Update research data based on tool result."""
    updated = dict(current)
    
    if tool_name == "search_google" and tool_data:
        # Add search results as potential competitors
        if isinstance(tool_data, list):
            for result in tool_data:
                if result not in updated["competitors"]:
                    updated["competitors"].append(result)
    
    elif tool_name == "discover_courses_with_rankings" and tool_data:
        # Add comprehensive course data
        if isinstance(tool_data, dict):
            # Add courses
            if "courses" in tool_data:
                courses_list = tool_data["courses"]
                print(f"📚 Adding {len(courses_list)} courses to research_data")
                updated["courses"].extend(courses_list)
            # Add lesson frequency data
            if "lesson_frequency" in tool_data:
                updated["lesson_frequency"].extend(tool_data["lesson_frequency"])
            # Add price analysis
            if "price_analysis" in tool_data:
                updated["price_analysis"] = tool_data["price_analysis"]
            # Add trending topics
            if "trending_topics" in tool_data:
                updated["trending_topics"].extend(tool_data.get("trending_topics", []))
    
    elif tool_name == "extract_course_lessons" and tool_data:
        # Add detailed lesson data to curricula
        if isinstance(tool_data, dict):
            updated["curricula"].append(tool_data)
    
    elif tool_name == "search_course_rankings" and tool_data:
        # Add course ranking data
        if isinstance(tool_data, dict) and "courses" in tool_data:
            for course in tool_data["courses"]:
                if course not in updated["courses"]:
                    updated["courses"].append(course)
    
    elif tool_name == "search_all_forums" and tool_data:
        # Add forum discussions
        if isinstance(tool_data, dict):
            if "reddit" in tool_data:
                updated["reddit_posts"].extend(tool_data.get("reddit", []))
            if "quora" in tool_data:
                updated["quora_answers"].extend(tool_data.get("quora", []))
    
    elif tool_name == "scrape_webpage" and tool_data:
        # Add scraped curriculum
        if isinstance(tool_data, dict):
            updated["curricula"].append(tool_data)
    
    elif tool_name == "search_reddit" and tool_data:
        # Add Reddit posts
        if isinstance(tool_data, list):
            updated["reddit_posts"].extend(tool_data)
    
    elif tool_name == "search_quora" and tool_data:
        # Add Quora answers
        if isinstance(tool_data, list):
            updated["quora_answers"].extend(tool_data)
    
    elif tool_name in ("find_podcasts", "find_educational_podcasts") and tool_data:
        # Add podcasts from Listen Notes
        if isinstance(tool_data, list):
            print(f"🎙️ Adding {len(tool_data)} podcasts to research data")
            updated["podcasts"].extend(tool_data)
    
    elif tool_name == "find_blogs" and tool_data:
        # Add blogs
        if isinstance(tool_data, list):
            updated["blogs"].extend(tool_data)
    
    elif tool_name == "analyze_content" and tool_data:
        # Update sentiment or trending topics
        if isinstance(tool_data, dict):
            if "sentiment" in tool_data:
                updated["sentiment_summary"] = tool_data["sentiment"]
            if "trending_topics" in tool_data:
                updated["trending_topics"].extend(tool_data["trending_topics"])
    
    return ResearchData(**updated)

