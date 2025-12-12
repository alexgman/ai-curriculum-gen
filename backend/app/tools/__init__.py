"""Tool definitions and registry for the research agent."""
from typing import Any
from app.tools.search import search_google
from app.tools.scrape import scrape_webpage
from app.tools.reddit import search_reddit
from app.tools.quora import search_quora
from app.tools.podcasts import find_podcasts, find_educational_podcasts
from app.tools.blogs import find_blogs
from app.tools.forums import search_all_forums, search_course_rankings
from app.tools.course_discovery import discover_courses_with_rankings, extract_course_lessons
from app.tools.analyze import analyze_content
from app.tools.database import save_research, get_research
from app.tools.report import generate_report


# Tool registry
TOOLS = {
    "search_google": search_google,
    "scrape_webpage": scrape_webpage,
    "search_reddit": search_reddit,
    "search_quora": search_quora,
    "search_all_forums": search_all_forums,
    "search_course_rankings": search_course_rankings,
    "discover_courses_with_rankings": discover_courses_with_rankings,
    "extract_course_lessons": extract_course_lessons,
    "find_podcasts": find_podcasts,
    "find_educational_podcasts": find_educational_podcasts,
    "find_blogs": find_blogs,
    "analyze_content": analyze_content,
    "save_research": save_research,
    "get_research": get_research,
    "generate_report": generate_report,
}


def get_tool_descriptions() -> str:
    """Get formatted descriptions of all available tools."""
    descriptions = []
    
    descriptions.append("""
### search_google
Search Google for courses, competitors, certifications, or any topic.
Arguments:
- query (str): The search query, e.g., "data center technician online course"
- num_results (int, optional): Number of results to return (default: 10)
Returns: List of search results with title, url, snippet
""")
    
    descriptions.append("""
### discover_courses_with_rankings
**PRIMARY TOOL** - Comprehensive course discovery with rankings, prices, lessons, and reviews.
Searches: Coursera, Udemy, edX, Skillshare, MasterClass, review sites, rankings.
Captures: pricing, duration, certifications, ALL lessons with descriptions, popularity metrics.
Arguments:
- industry (str): Industry, job title, or topic to research
- min_results (int, optional): Minimum courses to find (default: 30)
Returns: Top 20 courses sorted by popularity + lesson frequency analysis + price summary
""")
    
    descriptions.append("""
### extract_course_lessons
Extract detailed lesson information from a specific course URL.
Use after discover_courses_with_rankings to get full curriculum for top courses.
Arguments:
- url (str): Course page URL to scrape
Returns: Full lesson list with descriptions, duration, topics covered
""")
    
    descriptions.append("""
### search_all_forums
Search multiple forums for course discussions and recommendations.
Searches: Reddit, Quora, StackOverflow, HackerNews, review sites.
Arguments:
- query (str): Search query
- limit (int, optional): Total results (default: 30)
Returns: Organized results from all forums with rankings and prices
""")
    
    descriptions.append("""
### search_course_rankings
Find course ranking and comparison articles with pricing.
Arguments:
- industry (str): Industry to research
- limit (int, optional): Number of results (default: 20)
Returns: Ranking sources and courses with prices sorted by popularity
""")
    
    descriptions.append("""
### scrape_webpage
Scrape a webpage and extract its content as structured data.
Arguments:
- url (str): The URL to scrape
Returns: Extracted content including curriculum if found
""")
    
    descriptions.append("""
### search_reddit
Search Reddit for discussions about a topic.
Arguments:
- query (str): Search query
- subreddits (list[str], optional): Specific subreddits to search
- limit (int, optional): Number of posts to return (default: 20)
Returns: List of posts with title, content, comments, upvotes
""")
    
    descriptions.append("""
### search_quora
Search Quora for Q&A about a topic.
Arguments:
- query (str): Search query
Returns: List of questions and top answers
""")
    
    descriptions.append("""
### find_podcasts
Find popular podcasts in an industry using Listen Notes API.
Searches: Listen Notes database, Spotify, Apple Podcasts.
Arguments:
- industry (str): The industry to search for
- limit (int, optional): Number of podcasts to return (default: 15)
Returns: List of podcasts with name, description, url, publisher, episodes, listen_score
""")
    
    descriptions.append("""
### find_blogs
Find popular blogs in an industry.
Arguments:
- industry (str): The industry to search for
- limit (int, optional): Number of blogs to return (default: 10)
Returns: List of blogs with name, url, description
""")
    
    descriptions.append("""
### analyze_content
Analyze content to extract insights, trends, and sentiment.
Arguments:
- content (str): The content to analyze
- analysis_type (str): Type of analysis - "sentiment", "trends", "topics", or "curriculum"
Returns: Analysis results based on type
""")
    
    descriptions.append("""
### save_research
Save research data to the database.
Arguments:
- session_id (str): The research session ID
- data_type (str): Type of data - "competitor", "curriculum", "sentiment"
- data (dict): The data to save
Returns: Success confirmation
""")
    
    descriptions.append("""
### get_research
Retrieve saved research data from the database.
Arguments:
- session_id (str): The research session ID
- data_type (str, optional): Filter by type
Returns: Saved research data
""")
    
    descriptions.append("""
### generate_report
Generate a comprehensive research report.
Arguments:
- session_id (str): The research session ID
- format (str, optional): Output format - "markdown" or "json" (default: markdown)
Returns: Formatted research report
""")
    
    return "\n".join(descriptions)


async def execute_tool(tool_name: str, arguments: dict[str, Any]) -> Any:
    """Execute a tool by name with given arguments."""
    if tool_name not in TOOLS:
        raise ValueError(f"Unknown tool: {tool_name}")
    
    tool_func = TOOLS[tool_name]
    return await tool_func(**arguments)

