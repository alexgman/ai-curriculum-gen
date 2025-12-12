"""Data truncation and summarization utilities to prevent context overflow."""
import json
from typing import Any


def estimate_tokens(text: str) -> int:
    """Rough estimate of tokens (1 token ≈ 4 characters)."""
    return len(text) // 4


def truncate_text(text: str, max_tokens: int = 2000) -> str:
    """Truncate text to stay within token limit."""
    max_chars = max_tokens * 4
    if len(text) <= max_chars:
        return text
    return text[:max_chars] + f"\n\n... (truncated, original length: {len(text)} chars)"


def truncate_research_data(data: dict, max_items_per_category: int = 10) -> dict:
    """
    Truncate research data to prevent context overflow.
    
    Best practice: Keep only the most relevant data, summarize the rest.
    """
    truncated = {}
    
    # COURSES - PRIMARY DATA (keep top 25)
    if "courses" in data and data["courses"]:
        courses = data["courses"][:25]  # Keep 25 courses
        truncated["courses"] = [
            {
                "name": c.get("name", c.get("title", ""))[:150],
                "provider": c.get("provider", c.get("platform", ""))[:100],
                "url": c.get("url", "")[:200],
                "price": c.get("price", "N/A"),
                "certification": c.get("certification", "Available"),
                "rating": c.get("rating", ""),
                "duration": c.get("duration", ""),
                "modules": c.get("modules", [])[:10],  # Include up to 10 modules per course
            }
            for c in courses
        ]
        if len(data["courses"]) > 25:
            truncated["courses_total"] = len(data["courses"])
    
    # Competitors - keep top 10
    if "competitors" in data and data["competitors"]:
        competitors = data["competitors"][:max_items_per_category]
        # Simplify each competitor
        truncated["competitors"] = [
            {
                "name": c.get("name", c.get("title", ""))[:100],
                "url": c.get("url", "")[:200],
                "price": c.get("price", ""),
                "snippet": c.get("snippet", "")[:200],
            }
            for c in competitors
        ]
        if len(data["competitors"]) > max_items_per_category:
            truncated["competitors_total"] = len(data["competitors"])
    
    # Curricula - keep top 5 with limited modules
    if "curricula" in data:
        curricula = data["curricula"][:5]
        truncated["curricula"] = [
            {
                "course_name": c.get("course_name", "")[:100],
                "provider": c.get("provider", "")[:50],
                "modules": (c.get("modules", []) or [])[:8],  # Only first 8 modules
            }
            for c in curricula
        ]
        if len(data["curricula"]) > 5:
            truncated["curricula_total"] = len(data["curricula"])
    
    # Reddit/forum posts - keep top 10 with truncated content
    for key in ["reddit_posts", "quora_answers", "podcasts", "blogs"]:
        if key in data:
            items = data[key][:max_items_per_category]
            truncated[key] = [
                {
                    "title": item.get("title", item.get("name", ""))[:150],
                    "snippet": item.get("snippet", item.get("description", ""))[:200],
                    "url": item.get("url", "")[:200],
                }
                for item in items
            ]
            if len(data[key]) > max_items_per_category:
                truncated[f"{key}_total"] = len(data[key])
    
    # Trending topics - keep top 15
    if "trending_topics" in data:
        truncated["trending_topics"] = data["trending_topics"][:15]
    
    # Sentiment summary - truncate if too long
    if "sentiment_summary" in data and data["sentiment_summary"]:
        truncated["sentiment_summary"] = truncate_text(data["sentiment_summary"], max_tokens=500)
    
    return truncated


async def summarize_large_content(content: str, max_output_tokens: int = 1000) -> str:
    """
    Summarize large content using Claude before adding to context.
    
    This is a KEY best practice for agentic systems:
    - Don't accumulate raw data
    - Summarize at each step
    - Keep context manageable
    """
    from app.services.anthropic import claude_client
    
    # If content is already small, return as-is
    if estimate_tokens(content) < 1000:
        return content
    
    # Otherwise, summarize
    prompt = f"""Summarize the key insights from this research data concisely:

{truncate_text(content, max_tokens=6000)}

Focus on:
- Main findings
- Important data points
- Key patterns
- Actionable insights

Keep it under {max_output_tokens} tokens."""

    try:
        summary = await claude_client.complete(
            prompt=prompt,
            system="You summarize research data concisely while preserving key insights.",
            max_tokens=max_output_tokens,
            temperature=0,
        )
        return summary
    except Exception as e:
        # If summarization fails, just truncate
        return truncate_text(content, max_tokens=max_output_tokens)


def format_research_summary(data: dict) -> str:
    """
    Format research data as a concise summary for reasoning node.
    
    Best practice: Give the reasoning node a SUMMARY, not raw data.
    """
    lines = []
    
    if data.get("competitors"):
        count = len(data["competitors"])
        total = data.get("competitors_total", count)
        lines.append(f"- Competitors: {count} loaded (total found: {total})")
    
    if data.get("curricula"):
        count = len(data["curricula"])
        total = data.get("curricula_total", count)
        lines.append(f"- Curricula: {count} extracted (total: {total})")
    
    if data.get("reddit_posts"):
        count = len(data["reddit_posts"])
        lines.append(f"- Reddit discussions: {count}")
    
    if data.get("podcasts"):
        count = len(data["podcasts"])
        lines.append(f"- Podcasts: {count}")
    
    if data.get("blogs"):
        count = len(data["blogs"])
        lines.append(f"- Blogs: {count}")
    
    if data.get("trending_topics"):
        count = len(data["trending_topics"])
        lines.append(f"- Trending topics: {count}")
    
    if not lines:
        return "No research data yet"
    
    return "\n".join(lines)

