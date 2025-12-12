"""Forum and course review search tool."""
from app.services.serpapi import serpapi_client
from app.services.firecrawl import firecrawl_client
from app.services.anthropic import claude_client


async def search_all_forums(
    query: str,
    limit: int = 30,
) -> dict:
    """
    Search multiple forums and course review sites for discussions, rankings, and prices.
    
    Args:
        query: Search query (e.g., "data center technician course")
        limit: Total number of results to return
    
    Returns:
        Organized results from multiple sources
    """
    results = {
        "reddit": [],
        "quora": [],
        "course_reviews": [],
        "education_forums": [],
        "course_rankings": [],
    }
    
    # Reddit discussions
    reddit_query = f"site:reddit.com {query} course OR certification OR training"
    reddit_results = await serpapi_client.search(reddit_query, num_results=10)
    results["reddit"] = _format_results(reddit_results, "reddit")
    
    # Quora Q&A
    quora_query = f"site:quora.com {query} best course OR certification"
    quora_results = await serpapi_client.search(quora_query, num_results=10)
    results["quora"] = _format_results(quora_results, "quora")
    
    # Course review sites (Coursera, Udemy, CourseReport, SwitchUp)
    review_sites = [
        "coursereport.com",
        "switchup.org", 
        "coursecompare.ca",
        "classcentral.com",
    ]
    
    for site in review_sites:
        site_query = f"site:{site} {query} rating OR review OR price"
        site_results = await serpapi_client.search(site_query, num_results=5)
        results["course_reviews"].extend(_format_results(site_results, site))
    
    # Education forums
    forum_sites = [
        "stackoverflow.com",
        "hackernews.com",
        "producthunt.com",
    ]
    
    for site in forum_sites:
        forum_query = f"site:{site} {query} course recommendation"
        forum_results = await serpapi_client.search(forum_query, num_results=3)
        results["education_forums"].extend(_format_results(forum_results, site))
    
    # Course ranking sites
    ranking_query = f"{query} best courses 2024 OR 2025 ranking OR comparison"
    ranking_results = await serpapi_client.search(ranking_query, num_results=10)
    results["course_rankings"] = _format_results(ranking_results, "rankings")
    
    return results


async def extract_course_prices(search_results: list[dict]) -> dict:
    """
    Extract course prices from search results using Claude.
    
    Args:
        search_results: List of search results
    
    Returns:
        Courses with extracted prices
    """
    if not search_results:
        return {"courses": [], "price_ranges": {}}
    
    # Build content for Claude
    content = "\n\n".join([
        f"Title: {r.get('title')}\nSnippet: {r.get('snippet')}\nURL: {r.get('url')}"
        for r in search_results[:20]
    ])
    
    prompt = f"""Analyze these search results and extract course pricing information.

SEARCH RESULTS:
{content}

Extract and return JSON with:
{{
    "courses": [
        {{
            "name": "Course name",
            "provider": "Provider/platform",
            "price": "Price (e.g., $199, $49/month, Free)",
            "price_numeric": 199,  # Numeric value for sorting
            "url": "Course URL",
            "rating": "Rating if mentioned",
            "students": "Number of students if mentioned"
        }}
    ],
    "price_ranges": {{
        "free": ["list of free courses"],
        "budget": ["$0-$100"],
        "mid": ["$100-$500"],
        "premium": ["$500+"]
    }}
}}

Return only valid JSON."""

    try:
        result = await claude_client.complete(
            prompt=prompt,
            system="You extract pricing and ranking data from search results. Return only JSON.",
            temperature=0,
        )
        
        import json
        # Clean JSON
        result = result.strip()
        if result.startswith("```json"):
            result = result[7:]
        if result.startswith("```"):
            result = result[3:]
        if result.endswith("```"):
            result = result[:-3]
        
        return json.loads(result.strip())
    
    except Exception as e:
        return {
            "courses": [],
            "price_ranges": {},
            "error": str(e),
        }


async def search_course_rankings(
    industry: str,
    limit: int = 20,
) -> list[dict]:
    """
    Find course rankings and comparisons for an industry.
    
    Args:
        industry: Industry or topic (e.g., "data center technician")
        limit: Number of results
    
    Returns:
        Course rankings with prices and ratings
    """
    # Search for ranking/comparison articles
    queries = [
        f"best {industry} courses 2024 2025",
        f"{industry} certification comparison ranking",
        f"{industry} online course review price",
        f"top {industry} training programs cost",
    ]
    
    all_results = []
    for query in queries:
        results = await serpapi_client.search(query, num_results=limit // len(queries))
        all_results.extend(results)
    
    # Extract pricing from these results
    pricing_data = await extract_course_prices(all_results)
    
    return {
        "ranking_sources": all_results,
        "courses_with_prices": pricing_data.get("courses", []),
        "price_tiers": pricing_data.get("price_ranges", {}),
    }


def _format_results(results: list[dict], source: str) -> list[dict]:
    """Format search results with source information."""
    formatted = []
    for result in results:
        formatted.append({
            **result,
            "source": source,
        })
    return formatted

