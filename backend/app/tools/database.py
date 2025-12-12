"""Database tools for saving and retrieving research data."""
from typing import Optional
import json


# In-memory storage for now (replace with actual DB operations)
_research_store: dict[str, dict] = {}


async def save_research(
    session_id: str,
    data_type: str,
    data: dict,
) -> dict:
    """
    Save research data to storage.
    
    Args:
        session_id: The research session ID
        data_type: Type of data (competitor, curriculum, sentiment, etc.)
        data: The data to save
    
    Returns:
        Success confirmation
    """
    if session_id not in _research_store:
        _research_store[session_id] = {
            "competitors": [],
            "curricula": [],
            "sentiment": [],
            "reddit_posts": [],
            "podcasts": [],
            "blogs": [],
            "reports": [],
        }
    
    store = _research_store[session_id]
    
    if data_type == "competitor":
        store["competitors"].append(data)
    elif data_type == "curriculum":
        store["curricula"].append(data)
    elif data_type == "sentiment":
        store["sentiment"].append(data)
    elif data_type == "reddit":
        store["reddit_posts"].extend(data if isinstance(data, list) else [data])
    elif data_type == "podcast":
        store["podcasts"].extend(data if isinstance(data, list) else [data])
    elif data_type == "blog":
        store["blogs"].extend(data if isinstance(data, list) else [data])
    elif data_type == "report":
        store["reports"].append(data)
    else:
        return {"success": False, "error": f"Unknown data type: {data_type}"}
    
    return {
        "success": True,
        "message": f"Saved {data_type} data for session {session_id}",
        "count": len(store.get(data_type + "s", store.get(data_type, []))),
    }


async def get_research(
    session_id: str,
    data_type: Optional[str] = None,
) -> dict:
    """
    Retrieve saved research data.
    
    Args:
        session_id: The research session ID
        data_type: Optional filter by type (competitor, curriculum, etc.)
    
    Returns:
        Saved research data
    """
    if session_id not in _research_store:
        return {
            "session_id": session_id,
            "data": {},
            "message": "No data found for this session",
        }
    
    store = _research_store[session_id]
    
    if data_type:
        # Return specific type
        type_key = data_type + "s" if not data_type.endswith("s") else data_type
        if type_key in store:
            return {
                "session_id": session_id,
                "data_type": data_type,
                "data": store[type_key],
                "count": len(store[type_key]),
            }
        else:
            return {
                "session_id": session_id,
                "data_type": data_type,
                "data": [],
                "message": f"No {data_type} data found",
            }
    
    # Return all data
    return {
        "session_id": session_id,
        "data": store,
        "summary": {
            "competitors": len(store.get("competitors", [])),
            "curricula": len(store.get("curricula", [])),
            "reddit_posts": len(store.get("reddit_posts", [])),
            "podcasts": len(store.get("podcasts", [])),
            "blogs": len(store.get("blogs", [])),
        },
    }

