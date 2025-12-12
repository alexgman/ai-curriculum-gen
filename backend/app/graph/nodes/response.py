"""Response node - generates user-facing response grounded in research data."""
import json
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langchain_anthropic import ChatAnthropic
from app.graph.state import AgentState
from app.config import settings
from app.prompts.response import RESPONSE_SYSTEM_PROMPT, RESPONSE_USER_PROMPT
from app.utils.truncation import truncate_text, truncate_research_data
from app.graph.nodes.reflection import _session_research_data


async def response_node(state: AgentState) -> dict:
    """
    Generate a response to the user based on collected research data.
    
    CRITICAL: This response is GROUNDED in actual tool results.
    The system prompt explicitly forbids making up data.
    All claims must have sources from the research_data.
    """
    
    # Get session ID
    session_id = state.get("session_id", "default")
    
    # DEBUG: Print what's in cache
    print(f"🔍 Response: Looking for session {session_id}")
    print(f"🔍 Cache keys: {list(_session_research_data.keys())}")
    
    # Get research data from session cache (PRIMARY) or state (fallback)
    research_data_full = _session_research_data.get(session_id)
    if research_data_full is None:
        print(f"⚠️ Session not in cache, using state")
        research_data_full = state.get("research_data", {})
    else:
        print(f"✅ Found session in cache")
    
    # DEBUG: Print what we have
    courses = research_data_full.get("courses", [])
    competitors = research_data_full.get("competitors", [])
    print(f"📝 Response node has: {len(courses)} courses, {len(competitors)} competitors")
    if courses:
        print(f"📝 First course: {courses[0].get('name', 'Unknown')}")
    
    research_data = truncate_research_data(research_data_full, max_items_per_category=10)
    
    # Build conversation history for context
    conversation_history = []
    for msg in list(state["messages"])[-10:]:  # Last 10 messages
        if isinstance(msg, HumanMessage):
            conversation_history.append(f"User: {msg.content}")
        elif isinstance(msg, AIMessage) and not msg.content.startswith(("Reasoning:", "Reflection:", "Executing:")):
            # Only include actual responses
            conversation_history.append(f"Assistant: {msg.content[:300]}...")
    
    conversation_context = "\n\n".join(conversation_history) if conversation_history else ""
    
    # Get the last user message
    last_user_message = ""
    for msg in reversed(state["messages"]):
        if isinstance(msg, HumanMessage):
            last_user_message = msg.content
            break
    
    # Build context from research data (already truncated)
    research_context = _build_research_context(research_data)
    
    # DEBUG: Print the context being sent to LLM
    print(f"📋 Research context preview (first 500 chars):")
    print(research_context[:500] if research_context else "EMPTY CONTEXT")
    
    # Check if we have enough data for a meaningful response
    has_data = bool(
        research_data.get("courses") or  # Primary: course data
        research_data.get("competitors") or
        research_data.get("curricula") or
        research_data.get("reddit_posts") or
        research_data.get("podcasts") or
        research_data.get("blogs")
    )
    
    llm = ChatAnthropic(
        model=settings.anthropic_model,
        api_key=settings.anthropic_api_key,
        temperature=0.3,
        max_tokens=4000,  # Reduced from 4096 to leave room for input
    )
    
    # Truncate context to stay well under limit
    research_context_truncated = truncate_text(research_context, max_tokens=15000)  # Max 15K tokens for context
    
    user_prompt = RESPONSE_USER_PROMPT.format(
        conversation_history=truncate_text(conversation_context, max_tokens=2000) if conversation_context else "This is the first message",
        user_query=truncate_text(last_user_message, max_tokens=200),
        industry=state.get("industry", "Not specified"),
        research_context=research_context_truncated,
        has_data="Yes" if has_data else "No",
    )
    
    messages = [
        SystemMessage(content=RESPONSE_SYSTEM_PROMPT),
        HumanMessage(content=user_prompt),
    ]
    
    response = await llm.ainvoke(messages)
    
    # Add the response to messages
    return {
        "messages": [AIMessage(content=response.content)],
        "next_node": "end",
    }


def _build_research_context(research_data: dict) -> str:
    """Build a detailed context from research data for the response."""
    sections = []
    
    # COURSES section (PRIMARY DATA) - with modules
    if research_data.get("courses"):
        courses = research_data["courses"]
        course_lines = ["## Courses Found"]
        all_modules = []  # Collect all modules for inventory
        
        for i, course in enumerate(courses[:25], 1):
            name = course.get("name", course.get("title", "Unknown"))
            provider = course.get("provider", course.get("platform", ""))
            url = course.get("url", "")
            price = course.get("price", "N/A")
            certification = course.get("certification", "")
            rating = course.get("rating", "")
            duration = course.get("duration", "")
            modules = course.get("modules", [])
            
            course_lines.append(f"{i}. **{name}**")
            if provider:
                course_lines.append(f"   - Provider: {provider}")
            if url:
                course_lines.append(f"   - URL: {url}")
            if price:
                course_lines.append(f"   - Price: {price}")
            if certification:
                course_lines.append(f"   - Certification: {certification}")
            if rating:
                course_lines.append(f"   - Rating: {rating}")
            if duration:
                course_lines.append(f"   - Duration: {duration}")
            
            # Include modules if available
            if modules:
                course_lines.append(f"   - Modules/Lessons:")
                for mod in modules[:8]:  # Limit to 8 modules per course
                    if isinstance(mod, str):
                        course_lines.append(f"     * {mod}")
                        all_modules.append({"title": mod, "source": f"{name} ({provider})"})
                    elif isinstance(mod, dict):
                        mod_title = mod.get("title", mod.get("name", str(mod)))
                        course_lines.append(f"     * {mod_title}")
                        all_modules.append({"title": mod_title, "source": f"{name} ({provider})"})
        
        sections.append("\n".join(course_lines))
        
        # Add module inventory section if we have modules
        if all_modules:
            mod_lines = ["\n## All Modules/Lessons Discovered (Module Inventory)"]
            mod_lines.append("These modules were found across all courses:\n")
            for j, mod in enumerate(all_modules[:50], 1):  # Limit to 50 modules
                mod_lines.append(f"{j}. **{mod['title']}** (from: {mod['source']})")
            sections.append("\n".join(mod_lines))
    
    # Competitors section (legacy)
    if research_data.get("competitors"):
        competitors = research_data["competitors"]
        comp_lines = ["## Additional Competitors"]
        for i, comp in enumerate(competitors[:10], 1):  # Limit to top 10
            name = comp.get("name", comp.get("title", "Unknown"))
            url = comp.get("url", comp.get("link", ""))
            price = comp.get("price", "N/A")
            comp_lines.append(f"{i}. **{name}**")
            if url:
                comp_lines.append(f"   - URL: {url}")
            if price and price != "N/A":
                comp_lines.append(f"   - Price: {price}")
        sections.append("\n".join(comp_lines))
    
    # Curricula section
    if research_data.get("curricula"):
        curricula = research_data["curricula"]
        curr_lines = ["## Extracted Curricula"]
        for curr in curricula[:10]:  # Limit
            if isinstance(curr, dict):
                name = curr.get("course_name", "Unknown Course")
                modules = curr.get("modules", curr.get("curriculum", []))
                curr_lines.append(f"\n### {name}")
                if isinstance(modules, list):
                    for mod in modules[:10]:
                        if isinstance(mod, str):
                            curr_lines.append(f"- {mod}")
                        elif isinstance(mod, dict):
                            curr_lines.append(f"- {mod.get('title', mod.get('name', str(mod)))}")
        sections.append("\n".join(curr_lines))
    
    # Reddit insights
    if research_data.get("reddit_posts"):
        posts = research_data["reddit_posts"]
        reddit_lines = ["## Reddit Discussions"]
        for post in posts[:10]:
            title = post.get("title", "")
            subreddit = post.get("subreddit", "")
            score = post.get("score", post.get("upvotes", 0))
            reddit_lines.append(f"- [{subreddit}] {title} (Score: {score})")
        sections.append("\n".join(reddit_lines))
    
    # Podcasts
    if research_data.get("podcasts"):
        podcasts = research_data["podcasts"]
        pod_lines = ["## Relevant Podcasts"]
        for pod in podcasts[:10]:
            name = pod.get("name", pod.get("title", "Unknown"))
            pod_lines.append(f"- {name}")
        sections.append("\n".join(pod_lines))
    
    # Blogs
    if research_data.get("blogs"):
        blogs = research_data["blogs"]
        blog_lines = ["## Relevant Blogs"]
        for blog in blogs[:10]:
            name = blog.get("name", blog.get("title", "Unknown"))
            url = blog.get("url", "")
            blog_lines.append(f"- {name}" + (f" ({url})" if url else ""))
        sections.append("\n".join(blog_lines))
    
    # Trending topics
    if research_data.get("trending_topics"):
        topics = research_data["trending_topics"]
        topic_lines = ["## Trending Topics (Last 12-18 months)"]
        for topic in topics[:15]:
            topic_lines.append(f"- {topic}")
        sections.append("\n".join(topic_lines))
    
    # Sentiment summary
    if research_data.get("sentiment_summary"):
        sections.append(f"## Sentiment Analysis\n{research_data['sentiment_summary']}")
    
    if not sections:
        return "No research data collected yet. I should gather more information."
    
    return "\n\n".join(sections)

