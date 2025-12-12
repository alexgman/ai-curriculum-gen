"""Google search tool using SerpAPI."""
from app.services.serpapi import serpapi_client


async def search_google(
    query: str,
    num_results: int = 10,
) -> list[dict]:
    """
    Search Google for courses, competitors, certifications, or any topic.
    
    Args:
        query: The search query (e.g., "data center technician online course")
        num_results: Number of results to return (default: 10)
    
    Returns:
        List of search results with title, url, snippet
    """
    results = await serpapi_client.search(
        query=query,
        num_results=num_results,
    )
    
    return results

