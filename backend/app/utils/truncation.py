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


def truncate_research_data(data: dict, max_items_per_category: int = 15) -> dict:
    """
    Truncate research data to prevent context overflow.
    Preserves the most important data for curriculum research.
    """
    truncated = {}
    
    # COURSES - Keep up to 30 with full curriculum
    if "courses" in data and data["courses"]:
        courses = data["courses"][:30]
        truncated["courses"] = [
            {
                "name": c.get("name", c.get("title", ""))[:200],
                "provider": c.get("provider", c.get("platform", ""))[:100],
                "url": c.get("url", "")[:250],
                "price": c.get("price", "[Not available]"),
                "price_tier": c.get("price_tier", "mid"),
                "certification": c.get("certification", "Available"),
                "rating": c.get("rating", ""),
                "students": c.get("students", ""),
                "duration": c.get("duration", ""),
                "curriculum": c.get("curriculum", c.get("modules", []))[:12],  # Keep 12 modules per course
            }
            for c in courses
        ]
        if len(data["courses"]) > 30:
            truncated["courses_total"] = len(data["courses"])
    
    # TIERED COURSES - Keep the structure
    if "tiered_courses" in data:
        truncated["tiered_courses"] = {}
        for tier, courses in data["tiered_courses"].items():
            truncated["tiered_courses"][tier] = [
                {
                    "name": c.get("name", "")[:200],
                    "provider": c.get("provider", "")[:100],
                    "url": c.get("url", "")[:250],
                    "price": c.get("price", ""),
                    "curriculum": c.get("curriculum", [])[:12],
                }
                for c in courses[:15]
            ]
    
    # MODULE INVENTORY - Keep all with truncated sources
    if "module_inventory" in data:
        truncated["module_inventory"] = [
            {
                "name": m.get("name", "")[:150],
                "description": m.get("description", "")[:200],
                "frequency": m.get("frequency", "Low"),
                "count": m.get("count", 1),
                "sources": m.get("sources", [])[:5],
            }
            for m in data["module_inventory"][:100]
        ]
    
    # Competitors - keep top 15
    if "competitors" in data and data["competitors"]:
        truncated["competitors"] = [
            {
                "name": c.get("name", c.get("title", ""))[:150],
                "url": c.get("url", "")[:250],
                "price": c.get("price", ""),
                "snippet": c.get("snippet", "")[:200],
            }
            for c in data["competitors"][:max_items_per_category]
        ]
    
    # Curricula
    if "curricula" in data:
        truncated["curricula"] = [
            {
                "course_name": c.get("course_name", "")[:150],
                "provider": c.get("provider", "")[:100],
                "modules": (c.get("modules", []) or [])[:10],
            }
            for c in data["curricula"][:10]
        ]
    
    # Forum posts
    for key in ["reddit_posts", "quora_answers", "podcasts", "blogs"]:
        if key in data:
            truncated[key] = [
                {
                    "title": item.get("title", item.get("name", ""))[:200],
                    "snippet": item.get("snippet", item.get("description", ""))[:250],
                    "url": item.get("url", "")[:250],
                }
                for item in data[key][:max_items_per_category]
            ]
    
    # Trending topics
    if "trending_topics" in data:
        truncated["trending_topics"] = data["trending_topics"][:20]
    
    # Sentiment summary
    if "sentiment_summary" in data and data["sentiment_summary"]:
        truncated["sentiment_summary"] = truncate_text(data["sentiment_summary"], max_tokens=600)
    
    return truncated


async def summarize_large_content(content: str, max_output_tokens: int = 1000) -> str:
    """
    Summarize large content using Claude before adding to context.
    """
    from app.services.anthropic import claude_client
    
    if estimate_tokens(content) < 1000:
        return content
    
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
        return truncate_text(content, max_tokens=max_output_tokens)


def format_research_summary(data: dict) -> str:
    """Format research data as a concise summary for reasoning node."""
    lines = []
    
    if data.get("courses"):
        count = len(data["courses"])
        total = data.get("courses_total", count)
        lines.append(f"- Courses: {count} loaded (total found: {total})")
        
        # Count by tier if available
        if data.get("tiered_courses"):
            for tier, courses in data["tiered_courses"].items():
                lines.append(f"  - {tier.title()}: {len(courses)} courses")
    
    if data.get("module_inventory"):
        count = len(data["module_inventory"])
        vital = sum(1 for m in data["module_inventory"] if m.get("frequency") == "Vital")
        lines.append(f"- Module Inventory: {count} unique topics ({vital} vital)")
    
    if data.get("competitors"):
        count = len(data["competitors"])
        lines.append(f"- Competitors: {count}")
    
    if data.get("curricula"):
        count = len(data["curricula"])
        lines.append(f"- Curricula: {count} extracted")
    
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
