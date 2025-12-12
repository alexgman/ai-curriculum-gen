"""Listen Notes API client for podcast search."""
import httpx
from app.config import settings


class ListenNotesClient:
    """Client for Listen Notes podcast API."""
    
    BASE_URL = "https://listen-api.listennotes.com/api/v2"
    
    def __init__(self):
        self.api_key = settings.listennotes_api_key
    
    async def search_podcasts(
        self,
        query: str,
        sort_by: str = "relevance",  # relevance, recent
        type: str = "podcast",  # podcast, episode
        limit: int = 10,
    ) -> list[dict]:
        """
        Search for podcasts on Listen Notes.
        
        Args:
            query: Search query
            sort_by: Sort order (relevance or recent)
            type: Search type (podcast or episode)
            limit: Number of results
        
        Returns:
            List of podcasts with details. Returns empty list on any error.
        """
        # Check API key
        if not self.api_key or self.api_key.strip() == "":
            print("⚠️ Listen Notes: API key not configured")
            return []
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.BASE_URL}/search",
                    headers={"X-ListenAPI-Key": self.api_key},
                    params={
                        "q": query,
                        "sort_by_date": 1 if sort_by == "recent" else 0,
                        "type": type,
                        "len_min": 10,  # Minimum 10 minutes
                        "page_size": limit,
                    },
                    timeout=15,  # Shorter timeout for faster fallback
                )
                
                if response.status_code == 200:
                    data = response.json()
                    results = data.get("results", [])
                    
                    if not results:
                        print(f"⚠️ Listen Notes: No results for '{query}'")
                        return []
                    
                    podcasts = []
                    for item in results:
                        try:
                            if type == "podcast":
                                podcasts.append({
                                    "name": item.get("title_original", "") or item.get("title", ""),
                                    "description": (item.get("description_original", "") or "")[:300],
                                    "url": item.get("listennotes_url", "") or item.get("website", ""),
                                    "publisher": item.get("publisher_original", "") or item.get("publisher", ""),
                                    "total_episodes": item.get("total_episodes", 0),
                                    "source": "listennotes",
                                })
                            else:  # episode
                                podcast_info = item.get("podcast") or {}
                                podcasts.append({
                                    "name": item.get("title_original", "") or item.get("title", ""),
                                    "description": (item.get("description_original", "") or "")[:300],
                                    "url": item.get("listennotes_url", ""),
                                    "podcast_name": podcast_info.get("title_original", "") if isinstance(podcast_info, dict) else "",
                                    "audio_length_sec": item.get("audio_length_sec", 0),
                                    "source": "listennotes",
                                })
                        except Exception as item_error:
                            print(f"⚠️ Listen Notes: Error parsing item: {item_error}")
                            continue
                    
                    if podcasts:
                        print(f"✅ Listen Notes: Found {len(podcasts)} {type}s for '{query}'")
                    return podcasts
                
                elif response.status_code == 401:
                    print(f"❌ Listen Notes: Invalid API key (401)")
                    return []
                elif response.status_code == 429:
                    print(f"❌ Listen Notes: Rate limited (429)")
                    return []
                else:
                    print(f"❌ Listen Notes: HTTP {response.status_code}")
                    return []
        
        except httpx.TimeoutException:
            print(f"⚠️ Listen Notes: Timeout searching for '{query}'")
            return []
        except httpx.ConnectError:
            print(f"⚠️ Listen Notes: Connection error")
            return []
        except Exception as e:
            print(f"❌ Listen Notes error: {type(e).__name__}: {e}")
            return []
    
    async def get_best_podcasts(
        self,
        genre_id: int = 0,  # 0 = all genres
        region: str = "us",
        limit: int = 10,
    ) -> list[dict]:
        """
        Get best/trending podcasts by genre.
        
        Common genre IDs:
        - 93: Business
        - 127: Technology
        - 88: Health & Fitness
        - 67: Education
        - 122: Society & Culture
        """
        if not self.api_key:
            return []
        
        try:
            async with httpx.AsyncClient() as client:
                url = f"{self.BASE_URL}/best_podcasts"
                if genre_id:
                    url = f"{url}?genre_id={genre_id}&region={region}&page=1"
                else:
                    url = f"{url}?region={region}&page=1"
                
                response = await client.get(
                    url,
                    headers={"X-ListenAPI-Key": self.api_key},
                    timeout=30,
                )
                
                if response.status_code == 200:
                    data = response.json()
                    podcasts = data.get("podcasts", [])[:limit]
                    
                    return [
                        {
                            "name": p.get("title", ""),
                            "description": p.get("description", "")[:300],
                            "url": p.get("listennotes_url", ""),
                            "publisher": p.get("publisher", ""),
                            "total_episodes": p.get("total_episodes", 0),
                            "listen_score": p.get("listen_score", 0),
                            "source": "listennotes_trending",
                        }
                        for p in podcasts
                    ]
                
                return []
        
        except Exception as e:
            print(f"❌ Listen Notes best_podcasts error: {e}")
            return []


# Singleton instance
listennotes_client = ListenNotesClient()

