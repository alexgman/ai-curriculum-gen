"""Quora search tool (via Google search since Quora has no public API)."""
from app.services.serpapi import serpapi_client


async def search_quora(query: str, limit: int = 10) -> list[dict]:
    """
    Search Quora for Q&A about a topic (via Google search).
    
    Args:
        query: Search query
        limit: Number of results to return
    
    Returns:
        List of Quora questions and answers
    """
    # Search Google for Quora results
    search_query = f"site:quora.com {query}"
    
    results = await serpapi_client.search(
        query=search_query,
        num_results=limit,
    )
    
    # Format results as Quora Q&A
    quora_results = []
    for result in results:
        quora_results.append({
            "question": result.get("title", "").replace(" - Quora", ""),
            "url": result.get("url", ""),
            "snippet": result.get("snippet", ""),
            "source": "quora",
        })
    
    return quora_results

