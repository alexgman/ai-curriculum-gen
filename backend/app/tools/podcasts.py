"""Podcast discovery tool with Listen Notes API + Serper fallback."""
from app.services.listennotes import listennotes_client
from app.services.serpapi import serpapi_client


async def find_podcasts(industry: str, limit: int = 15) -> list[dict]:
    """
    Find popular podcasts in an industry.
    
    Uses Listen Notes API as primary source, falls back to Serper/Google search
    if Listen Notes fails or returns insufficient results.
    
    Args:
        industry: The industry to search for (e.g., "data science", "real estate")
        limit: Number of podcasts to return
    
    Returns:
        List of podcasts with name, description, url, publisher
    """
    all_podcasts = []
    seen_names = set()
    listen_notes_worked = False
    
    # 1. Try Listen Notes API (PRIMARY)
    try:
        ln_podcasts = await listennotes_client.search_podcasts(
            query=f"{industry} education learning",
            type="podcast",
            limit=limit,
        )
        
        if ln_podcasts and len(ln_podcasts) > 0:
            listen_notes_worked = True
            for podcast in ln_podcasts:
                name = podcast.get("name", "").lower()
                if name and name not in seen_names:
                    seen_names.add(name)
                    all_podcasts.append(podcast)
            
            # Also search for episodes
            ln_episodes = await listennotes_client.search_podcasts(
                query=f"{industry} courses training",
                type="episode",
                limit=8,
            )
            
            for ep in ln_episodes:
                name = ep.get("name", "").lower()
                if name and name not in seen_names:
                    seen_names.add(name)
                    all_podcasts.append({
                        "name": ep.get("name", ""),
                        "description": ep.get("description", ""),
                        "url": ep.get("url", ""),
                        "publisher": ep.get("podcast_name", ""),
                        "source": "listennotes_episode",
                    })
    except Exception as e:
        print(f"⚠️ Listen Notes error: {e}")
        listen_notes_worked = False
    
    # 2. FALLBACK: Use Serper/Google search if Listen Notes failed or returned too few
    if not listen_notes_worked or len(all_podcasts) < limit // 2:
        print("📻 Using Serper fallback for podcasts...")
        
        try:
            # Search for best podcasts
            search_queries = [
                f"best {industry} podcasts 2024 2025",
                f"top {industry} educational podcasts",
                f"site:spotify.com {industry} podcast",
                f"site:podcasts.apple.com {industry}",
            ]
            
            for query in search_queries:
                results = await serpapi_client.search(
                    query=query,
                    num_results=8,
                )
                
                for result in results:
                    title = result.get("title", "")
                    # Clean up title
                    title = title.replace(" | Spotify", "").replace(" on Apple Podcasts", "")
                    title = title.replace(" - Podcast", "").replace(" Podcast", "").strip()
                    
                    if title and title.lower() not in seen_names and len(title) > 5:
                        seen_names.add(title.lower())
                        all_podcasts.append({
                            "name": title,
                            "url": result.get("url", ""),
                            "description": result.get("snippet", "")[:200],
                            "publisher": _extract_publisher(result.get("url", "")),
                            "source": "serper_search",
                        })
                
                # Stop if we have enough
                if len(all_podcasts) >= limit:
                    break
        
        except Exception as e:
            print(f"⚠️ Serper fallback error: {e}")
    
    total = len(all_podcasts)
    source = "Listen Notes" if listen_notes_worked else "Serper"
    print(f"📻 Found {total} podcasts for '{industry}' (primary source: {source})")
    
    return all_podcasts[:limit]


def _extract_publisher(url: str) -> str:
    """Extract publisher name from URL."""
    if "spotify.com" in url:
        return "Spotify"
    elif "apple.com" in url:
        return "Apple Podcasts"
    elif "youtube.com" in url:
        return "YouTube"
    elif "stitcher.com" in url:
        return "Stitcher"
    return "Podcast"


async def find_educational_podcasts(industry: str) -> list[dict]:
    """
    Find educational podcasts specifically about learning/courses in an industry.
    
    Uses Listen Notes with Serper fallback.
    
    Args:
        industry: The industry/topic
    
    Returns:
        List of educational podcasts
    """
    all_podcasts = []
    seen = set()
    
    # Try Listen Notes first
    try:
        queries = [
            f"{industry} learning podcast",
            f"{industry} tutorial education",
            f"learn {industry}",
        ]
        
        for query in queries:
            podcasts = await listennotes_client.search_podcasts(
                query=query,
                type="podcast",
                limit=5,
            )
            
            for p in podcasts:
                name = p.get("name", "").lower()
                if name and name not in seen:
                    seen.add(name)
                    all_podcasts.append(p)
        
        if all_podcasts:
            return all_podcasts[:15]
    except Exception as e:
        print(f"⚠️ Listen Notes educational search error: {e}")
    
    # Fallback to Serper
    print("📻 Using Serper fallback for educational podcasts...")
    try:
        results = await serpapi_client.search(
            query=f"best {industry} learning podcasts educational",
            num_results=15,
        )
        
        for result in results:
            title = result.get("title", "")
            title = title.replace(" | Spotify", "").replace(" on Apple Podcasts", "").strip()
            
            if title and title.lower() not in seen:
                seen.add(title.lower())
                all_podcasts.append({
                    "name": title,
                    "url": result.get("url", ""),
                    "description": result.get("snippet", "")[:200],
                    "source": "serper_search",
                })
    except Exception as e:
        print(f"⚠️ Serper educational fallback error: {e}")
    
    return all_podcasts[:15]

