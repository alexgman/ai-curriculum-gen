"""Content analysis tool using Claude."""
import json
from app.services.anthropic import claude_client


async def analyze_content(
    content: str,
    analysis_type: str = "trends",
) -> dict:
    """
    Analyze content to extract insights, trends, and sentiment.
    
    Args:
        content: The content to analyze
        analysis_type: Type of analysis:
            - "sentiment": Analyze sentiment and opinions
            - "trends": Identify trending topics
            - "topics": Extract main topics/themes
            - "curriculum": Extract curriculum structure
    
    Returns:
        Analysis results based on type
    """
    if analysis_type == "sentiment":
        return await _analyze_sentiment(content)
    elif analysis_type == "trends":
        return await _analyze_trends(content)
    elif analysis_type == "topics":
        return await _analyze_topics(content)
    elif analysis_type == "curriculum":
        return await _analyze_curriculum(content)
    else:
        return {"error": f"Unknown analysis type: {analysis_type}"}


async def _analyze_sentiment(content: str) -> dict:
    """Analyze sentiment from content (e.g., Reddit posts)."""
    prompt = f"""Analyze the sentiment in the following content from online discussions.

Content:
{content[:6000]}

Provide a JSON response with:
{{
    "overall_sentiment": "positive" | "negative" | "neutral" | "mixed",
    "sentiment_score": 0.0 to 1.0 (0 = very negative, 1 = very positive),
    "key_positive_points": ["list of positive things mentioned"],
    "key_negative_points": ["list of complaints or concerns"],
    "common_questions": ["frequently asked questions"],
    "recommendations_mentioned": ["courses, books, resources people recommend"]
}}

Return only valid JSON."""

    result = await claude_client.complete(
        prompt=prompt,
        system="You are a sentiment analysis expert. Analyze online discussions objectively.",
        temperature=0,
    )
    
    return _parse_json_response(result)


async def _analyze_trends(content: str) -> dict:
    """Identify trending topics from content."""
    prompt = f"""Analyze the following content to identify trending topics and themes.

Content:
{content[:6000]}

Provide a JSON response with:
{{
    "trending_topics": [
        {{
            "topic": "Topic name",
            "mentions": "How often it appears",
            "sentiment": "positive/negative/neutral",
            "relevance": "high/medium/low"
        }}
    ],
    "emerging_trends": ["New topics gaining attention"],
    "declining_topics": ["Topics losing interest"],
    "technology_changes": ["Tech changes mentioned"],
    "industry_shifts": ["Industry changes noted"],
    "time_period": "Last 12-18 months focus"
}}

Return only valid JSON."""

    result = await claude_client.complete(
        prompt=prompt,
        system="You analyze content to identify industry trends and changes.",
        temperature=0,
    )
    
    return _parse_json_response(result)


async def _analyze_topics(content: str) -> dict:
    """Extract main topics from content."""
    prompt = f"""Extract the main topics and themes from the following content.

Content:
{content[:6000]}

Provide a JSON response with:
{{
    "main_topics": [
        {{
            "name": "Topic name",
            "description": "Brief description",
            "subtopics": ["Related subtopics"],
            "frequency": "high/medium/low"
        }}
    ],
    "keywords": ["Important keywords"],
    "categories": ["Broad categories these fall into"]
}}

Return only valid JSON."""

    result = await claude_client.complete(
        prompt=prompt,
        system="You extract and categorize topics from content.",
        temperature=0,
    )
    
    return _parse_json_response(result)


async def _analyze_curriculum(content: str) -> dict:
    """Extract curriculum structure from content."""
    prompt = f"""Analyze this content and extract any curriculum or course structure.

Content:
{content[:6000]}

Provide a JSON response with:
{{
    "course_name": "Name if found",
    "modules": [
        {{
            "title": "Module title",
            "topics": ["Topics covered"],
            "skills": ["Skills taught"]
        }}
    ],
    "total_topics": 0,
    "skill_level": "beginner/intermediate/advanced",
    "estimated_duration": "Duration if mentioned"
}}

Return only valid JSON."""

    result = await claude_client.complete(
        prompt=prompt,
        system="You extract curriculum structure from educational content.",
        temperature=0,
    )
    
    return _parse_json_response(result)


def _parse_json_response(response: str) -> dict:
    """Parse JSON from Claude's response."""
    try:
        # Clean up response
        response = response.strip()
        if response.startswith("```json"):
            response = response[7:]
        if response.startswith("```"):
            response = response[3:]
        if response.endswith("```"):
            response = response[:-3]
        
        return json.loads(response.strip())
    except json.JSONDecodeError as e:
        return {"error": f"Failed to parse response: {e}", "raw": response[:500]}

