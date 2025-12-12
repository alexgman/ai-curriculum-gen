"""Serper.dev client for Google search."""
import httpx
from typing import Optional
from app.config import settings


class SerpAPIClient:
    """Client for Serper.dev (Google Search API)."""
    
    BASE_URL = "https://google.serper.dev/search"
    
    def __init__(self):
        self.api_key = settings.search_api_key
    
    async def search(
        self,
        query: str,
        num_results: int = 10,
        search_type: str = "search",
    ) -> list[dict]:
        """
        Search Google via Serper.dev.
        
        Args:
            query: Search query
            num_results: Number of results to return
            search_type: Type of search (search, news, images, etc.)
        
        Returns:
            List of search results
        """
        if not self.api_key:
            print("⚠️ No Serper API key - using mock data")
            return self._mock_search(query, num_results)
        
        headers = {
            "X-API-KEY": self.api_key,
            "Content-Type": "application/json",
        }
        
        payload = {
            "q": query,
            "num": num_results,
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.BASE_URL,
                    headers=headers,
                    json=payload,
                    timeout=30.0,
                )
                response.raise_for_status()
                data = response.json()
            
            # Extract organic results
            results = []
            for item in data.get("organic", [])[:num_results]:
                results.append({
                    "title": item.get("title", ""),
                    "url": item.get("link", ""),
                    "snippet": item.get("snippet", ""),
                    "position": item.get("position", 0),
                })
            
            print(f"✅ Serper API: Found {len(results)} results for '{query}'")
            return results
            
        except Exception as e:
            print(f"❌ Serper API error: {e}")
            # Return mock data on error
            return self._mock_search(query, num_results)
    
    def _mock_search(self, query: str, num_results: int) -> list[dict]:
        """Return mock data for testing without API key."""
        return [
            {
                "title": f"Mock Result 1 for: {query}",
                "url": "https://example.com/course1",
                "snippet": "This is a mock search result for testing purposes.",
                "position": 1,
            },
            {
                "title": f"Mock Result 2 for: {query}",
                "url": "https://example.com/course2", 
                "snippet": "Another mock result with course information.",
                "position": 2,
            },
        ][:num_results]


# Singleton instance
serpapi_client = SerpAPIClient()

