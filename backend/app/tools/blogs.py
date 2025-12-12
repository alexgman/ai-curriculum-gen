"""Blog discovery tool."""
from app.services.serpapi import serpapi_client


async def find_blogs(industry: str, limit: int = 10) -> list[dict]:
    """
    Find popular blogs in an industry.
    
    Args:
        industry: The industry to search for
        limit: Number of blogs to return
    
    Returns:
        List of blogs with name, url, description
    """
    # Search for industry blogs
    search_queries = [
        f"best {industry} blogs 2024",
        f"top {industry} industry blogs",
        f"{industry} news and insights blog",
    ]
    
    all_results = []
    for query in search_queries:
        results = await serpapi_client.search(
            query=query,
            num_results=limit,
        )
        all_results.extend(results)
    
    # Deduplicate and format
    blogs = []
    seen_urls = set()
    
    for result in all_results:
        url = result.get("url", "")
        # Get base domain
        base_url = _get_base_url(url)
        
        if base_url and base_url not in seen_urls:
            seen_urls.add(base_url)
            blogs.append({
                "name": result.get("title", ""),
                "url": url,
                "description": result.get("snippet", ""),
                "source": "google_search",
            })
    
    return blogs[:limit]


def _get_base_url(url: str) -> str:
    """Extract base URL (domain) from full URL."""
    import re
    match = re.search(r"https?://(?:www\.)?([^/]+)", url)
    return match.group(0) if match else url

