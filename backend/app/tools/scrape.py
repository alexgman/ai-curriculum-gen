"""Web scraping tool using Firecrawl."""
import re
from app.services.firecrawl import firecrawl_client
from app.services.anthropic import claude_client


async def scrape_webpage(url: str) -> dict:
    """
    Scrape a webpage and extract curriculum/course structure.
    
    Args:
        url: The URL to scrape
    
    Returns:
        Extracted content including curriculum if found
    """
    # Scrape the page
    page_data = await firecrawl_client.scrape(url)
    
    # Try to extract curriculum structure using Claude
    markdown_content = page_data.get("markdown", "")
    
    if markdown_content:
        # Use Claude to extract structured curriculum
        curriculum = await _extract_curriculum(
            content=markdown_content,
            url=url,
            title=page_data.get("title", ""),
        )
        page_data["curriculum"] = curriculum
    
    return page_data


async def _extract_curriculum(content: str, url: str, title: str) -> dict:
    """Extract curriculum structure from page content using Claude."""
    
    # Limit content to avoid token limits
    content_truncated = content[:8000]
    
    prompt = f"""Analyze this course page content and extract the curriculum structure.

URL: {url}
Title: {title}

Content:
{content_truncated}

Extract and return a JSON object with:
{{
    "course_name": "Name of the course",
    "provider": "Course provider/platform",
    "price": "Price if found",
    "modules": [
        {{
            "title": "Module title",
            "lessons": ["Lesson 1", "Lesson 2"],
            "description": "Brief description if available"
        }}
    ],
    "certifications": ["Any certifications mentioned"],
    "duration": "Course duration if mentioned",
    "level": "Beginner/Intermediate/Advanced if mentioned"
}}

If you can't find curriculum information, return an empty modules array.
Return ONLY the JSON object, no other text."""

    try:
        result = await claude_client.complete(
            prompt=prompt,
            system="You extract structured curriculum data from course pages. Return only valid JSON.",
            temperature=0,
        )
        
        # Try to parse the JSON
        import json
        # Clean up the response
        result = result.strip()
        if result.startswith("```json"):
            result = result[7:]
        if result.startswith("```"):
            result = result[3:]
        if result.endswith("```"):
            result = result[:-3]
        
        return json.loads(result.strip())
    
    except Exception as e:
        # Return basic structure if extraction fails
        return {
            "course_name": title,
            "provider": _extract_domain(url),
            "price": None,
            "modules": [],
            "certifications": [],
            "duration": None,
            "level": None,
            "extraction_error": str(e),
        }


def _extract_domain(url: str) -> str:
    """Extract domain name from URL."""
    match = re.search(r"https?://(?:www\.)?([^/]+)", url)
    return match.group(1) if match else url

