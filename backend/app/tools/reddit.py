"""Reddit search using Google (no PRAW needed)."""
from typing import Optional
from app.services.serpapi import serpapi_client


async def search_reddit(
    query: str,
    subreddits: Optional[list[str]] = None,
    limit: int = 20,
) -> list[dict]:
    """
    Search Reddit for discussions using Google search.
    
    Args:
        query: Search query
        subreddits: Optional list of specific subreddits to search
        limit: Number of posts to return (default: 20)
    
    Returns:
        List of Reddit posts with title, url, snippet
    """
    # Build Reddit-specific search query
    if subreddits:
        subreddit_queries = " OR ".join([f"site:reddit.com/r/{sub}" for sub in subreddits])
        search_query = f"({subreddit_queries}) {query}"
    else:
        # Search career/education subreddits
        default_subs = [
            "careerguidance", "ITCareerQuestions", "cscareerquestions",
            "learnprogramming", "jobs", "GetEmployed", "OnlineEducation"
        ]
        subreddit_queries = " OR ".join([f"site:reddit.com/r/{sub}" for sub in default_subs])
        search_query = f"({subreddit_queries}) {query}"
    
    # Search using Google
    results = await serpapi_client.search(
        query=search_query,
        num_results=limit,
    )
    
    # Format results
    reddit_posts = []
    for result in results:
        url = result.get("url", "")
        
        # Extract subreddit from URL
        subreddit = "unknown"
        if "/r/" in url:
            try:
                subreddit = url.split("/r/")[1].split("/")[0]
            except:
                pass
        
        reddit_posts.append({
            "title": result.get("title", ""),
            "url": url,
            "snippet": result.get("snippet", ""),
            "subreddit": subreddit,
            "source": "reddit",
        })
    
    return reddit_posts
