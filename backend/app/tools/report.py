"""Report generation tool."""
import json
from typing import Optional
from app.services.anthropic import claude_client
from app.tools.database import get_research


async def generate_report(
    session_id: str,
    format: str = "markdown",
) -> dict:
    """
    Generate a comprehensive research report.
    
    Args:
        session_id: The research session ID
        format: Output format - "markdown" or "json"
    
    Returns:
        Formatted research report
    """
    # Get all research data
    research = await get_research(session_id)
    data = research.get("data", {})
    
    if not data:
        return {
            "success": False,
            "error": "No research data found for this session",
        }
    
    # Build report using Claude
    report_content = await _generate_report_content(data)
    
    if format == "json":
        return {
            "success": True,
            "format": "json",
            "report": _structure_report_json(data, report_content),
        }
    else:
        return {
            "success": True,
            "format": "markdown",
            "report": report_content,
        }


async def _generate_report_content(data: dict) -> str:
    """Generate markdown report from research data."""
    
    # Prepare context
    context_parts = []
    
    # Competitors
    competitors = data.get("competitors", [])
    if competitors:
        comp_text = "## Competitors Found\n"
        for i, comp in enumerate(competitors[:20], 1):
            name = comp.get("name", comp.get("title", "Unknown"))
            url = comp.get("url", comp.get("link", ""))
            comp_text += f"{i}. **{name}**\n   - URL: {url}\n"
        context_parts.append(comp_text)
    
    # Curricula
    curricula = data.get("curricula", [])
    if curricula:
        curr_text = "## Extracted Curricula\n"
        for curr in curricula[:10]:
            if isinstance(curr, dict):
                name = curr.get("course_name", curr.get("title", "Unknown"))
                modules = curr.get("modules", curr.get("curriculum", []))
                curr_text += f"\n### {name}\n"
                if isinstance(modules, list):
                    for mod in modules[:8]:
                        if isinstance(mod, dict):
                            curr_text += f"- {mod.get('title', str(mod))}\n"
                        else:
                            curr_text += f"- {mod}\n"
        context_parts.append(curr_text)
    
    # Reddit posts
    reddit = data.get("reddit_posts", [])
    if reddit:
        reddit_text = "## Reddit Discussions\n"
        for post in reddit[:10]:
            title = post.get("title", "")
            score = post.get("score", 0)
            subreddit = post.get("subreddit", "")
            reddit_text += f"- [{subreddit}] {title} (Score: {score})\n"
        context_parts.append(reddit_text)
    
    # Podcasts
    podcasts = data.get("podcasts", [])
    if podcasts:
        pod_text = "## Industry Podcasts\n"
        for pod in podcasts[:10]:
            name = pod.get("name", pod.get("title", ""))
            pod_text += f"- {name}\n"
        context_parts.append(pod_text)
    
    # Blogs
    blogs = data.get("blogs", [])
    if blogs:
        blog_text = "## Industry Blogs\n"
        for blog in blogs[:10]:
            name = blog.get("name", blog.get("title", ""))
            url = blog.get("url", "")
            blog_text += f"- [{name}]({url})\n"
        context_parts.append(blog_text)
    
    context = "\n\n".join(context_parts)
    
    # Generate comprehensive report using Claude
    prompt = f"""Based on the following research data, generate a comprehensive research report.

RESEARCH DATA:
{context}

Generate a well-structured markdown report with these sections:

1. **Executive Summary** - Brief overview of findings
2. **Competitor Analysis** - Key competitors, their offerings, pricing tiers
3. **Curriculum Insights** - Common topics taught, unique offerings, gaps
4. **Industry Sentiment** - What students/professionals are saying
5. **Trending Topics** - What's hot in the last 12-18 months
6. **Recommendations** - Suggested topics for a new curriculum

Format the report professionally with markdown headers, bullet points, and tables where appropriate.
Only use information from the provided research data - do not make up details."""

    report = await claude_client.complete(
        prompt=prompt,
        system="You are a professional research analyst creating comprehensive reports.",
        max_tokens=4000,
        temperature=0.3,
    )
    
    return report


def _structure_report_json(data: dict, report_text: str) -> dict:
    """Structure report as JSON."""
    return {
        "summary": {
            "total_competitors": len(data.get("competitors", [])),
            "total_curricula": len(data.get("curricula", [])),
            "total_reddit_posts": len(data.get("reddit_posts", [])),
            "total_podcasts": len(data.get("podcasts", [])),
            "total_blogs": len(data.get("blogs", [])),
        },
        "competitors": data.get("competitors", [])[:20],
        "curricula": data.get("curricula", [])[:10],
        "reddit_highlights": data.get("reddit_posts", [])[:10],
        "podcasts": data.get("podcasts", [])[:10],
        "blogs": data.get("blogs", [])[:10],
        "full_report_markdown": report_text,
    }

