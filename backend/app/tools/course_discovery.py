"""Course discovery and ranking tool - finds courses with prices and rankings."""
from app.services.serpapi import serpapi_client
from app.services.firecrawl import firecrawl_client
from app.services.anthropic import claude_client
import json
import asyncio

# Progress callback for real-time status updates
_progress_callback = None

def set_progress_callback(callback):
    """Set a callback function for progress updates."""
    global _progress_callback
    _progress_callback = callback

async def _report_progress(message: str):
    """Report progress if callback is set."""
    global _progress_callback
    if _progress_callback:
        await _progress_callback(message)
    print(f"📊 {message}")


async def discover_courses_with_rankings(
    industry: str,
    min_results: int = 25,
) -> dict:
    """
    Comprehensive course discovery - finds 20-25 courses with detailed data.
    
    Args:
        industry: Industry, job title, or topic to research
        min_results: Minimum number of courses to find (default 25)
    
    Returns:
        Course data with rankings, prices, certifications, and ratings
    """
    all_courses = []
    
    await _report_progress(f"Searching courses for '{industry}'...")
    
    # Comprehensive parallel searches to get 20-25+ courses
    search_tasks = [
        # Platform-specific searches
        _search_with_context(f"site:coursera.org {industry} course certificate", "Coursera", "course", 10),
        _search_with_context(f"site:udemy.com {industry} course bestseller", "Udemy", "course", 10),
        _search_with_context(f"site:edx.org {industry} course certification", "edX", "course", 8),
        _search_with_context(f"site:linkedin.com/learning {industry}", "LinkedIn Learning", "course", 6),
        # Ranking/review searches
        _search_with_context(f"best {industry} courses 2024 2025 price rating", "Rankings", "ranking", 10),
        _search_with_context(f"top {industry} online certification programs cost", "Rankings", "ranking", 10),
        _search_with_context(f"{industry} bootcamp course review comparison", "Reviews", "ranking", 8),
    ]
    
    await _report_progress("Running 7 parallel searches...")
    
    # Execute ALL searches in parallel
    results = await asyncio.gather(*search_tasks, return_exceptions=True)
    
    # Collect results
    for result in results:
        if isinstance(result, list):
            all_courses.extend(result)
    
    await _report_progress(f"Found {len(all_courses)} results, extracting detailed data...")
    
    # Extract comprehensive data using Claude
    courses_with_data = await _extract_course_data_comprehensive(all_courses, industry)
    
    num_courses = len(courses_with_data.get('courses', []))
    await _report_progress(f"Extracted {num_courses} unique courses with details")
    
    return courses_with_data


async def _extract_course_data_comprehensive(courses: list[dict], industry: str) -> dict:
    """Comprehensive extraction - gets 20-25 courses with full details."""
    
    # Use all results (up to 60)
    content = "\n".join([
        f"{i+1}. {c.get('title', 'N/A')} | {c.get('platform', 'N/A')} | {c.get('snippet', '')[:150]} | {c.get('url', '')[:80]}"
        for i, c in enumerate(courses[:60])
    ])
    
    prompt = f"""Extract ALL unique {industry} courses from these search results. I need 20-25 courses minimum.

SEARCH RESULTS:
{content}

For EACH unique course, extract:
- name: Full course name
- provider: Platform/school (Coursera, Udemy, edX, etc.)
- url: Course URL
- price: Exact price ($X, $X/month, Free, or estimate based on platform)
- certification: What certificate/credential you get (e.g., "Professional Certificate", "Nanodegree", "Verified Certificate", "None")
- rating: Rating if mentioned (X/5)
- duration: Course length if mentioned
- modules: List of module/lesson names mentioned in the description (if any)

IMPORTANT:
- Extract AT LEAST 20 unique courses
- Include certification info (most Coursera courses offer certificates, Udemy offers completion certificates)
- Estimate prices based on platform if not explicit (Coursera ~$49/month, Udemy ~$20-200, edX ~Free or $150-300 for cert)
- Extract any module/lesson names mentioned (e.g., "Introduction to X", "Fundamentals of Y", etc.)

Return JSON:
{{"courses": [
  {{"name": "Course Name", "provider": "Platform", "url": "URL", "price": "$X", "certification": "Certificate Type", "rating": "X/5", "duration": "X weeks", "modules": ["Module 1 Name", "Module 2 Name"]}}
], "total": N}}"""

    try:
        result = await claude_client.complete(
            prompt=prompt,
            system="Extract comprehensive course data. Return JSON with 20-25 courses. Include certification details for each.",
            temperature=0,
            max_tokens=4000,
        )
        
        # Parse JSON
        result = result.strip()
        if "```" in result:
            result = result.split("```")[1].replace("json", "").strip()
        
        data = json.loads(result)
        data["industry"] = industry
        data["raw_results"] = len(courses)
        return data
    
    except Exception as e:
        # Fallback: return raw data
        return {
            "courses": [
                {
                    "name": c.get("title", "Unknown"),
                    "url": c.get("url", ""),
                    "provider": c.get("platform", "Unknown"),
                    "price": "See website",
                    "certification": "Available",
                }
                for c in courses[:25]
            ],
            "error": str(e),
            "industry": industry,
        }


async def _search_with_context(query: str, platform: str, source: str, num_results: int) -> list:
    """Helper to search and add context to results."""
    try:
        results = await serpapi_client.search(query, num_results=num_results)
        return [
            {
                "title": r.get("title", ""),
                "url": r.get("url", ""),
                "snippet": r.get("snippet", ""),
                "platform": platform,
                "source": source,
            }
            for r in results
        ]
    except Exception as e:
        print(f"Search failed for {platform}: {e}")
        return []


# Keep legacy sequential code as fallback
async def _discover_courses_sequential(industry: str, min_results: int = 30) -> dict:
    """Legacy sequential discovery - slower but more thorough."""
    all_courses = []
    
    platforms = [
        ("coursera.org", "Coursera"),
        ("udemy.com", "Udemy"),
        ("edx.org", "edX"),
        ("pluralsight.com", "Pluralsight"),
        ("linkedin.com/learning", "LinkedIn Learning"),
        ("udacity.com", "Udacity"),
        ("skillshare.com", "Skillshare"),
        ("domestika.org", "Domestika"),
        ("masterclass.com", "MasterClass"),
        ("brilliant.org", "Brilliant"),
    ]
    
    for domain, platform_name in platforms:
        query = f"site:{domain} {industry} course curriculum syllabus lessons"
        results = await serpapi_client.search(query, num_results=5)
        
        for result in results:
            all_courses.append({
                "title": result.get("title", ""),
                "url": result.get("url", ""),
                "snippet": result.get("snippet", ""),
                "platform": platform_name,
                "source": "course_platform",
            })
    
    review_sites = [
        ("coursereport.com", "CourseReport"),
        ("switchup.org", "SwitchUp"),
        ("classcentral.com", "Class Central"),
        ("coursecompare.ca", "Course Compare"),
        ("trustpilot.com", "Trustpilot"),
        ("g2.com", "G2"),
    ]
    
    for domain, site_name in review_sites:
        query = f"site:{domain} {industry} course review rating"
        results = await serpapi_client.search(query, num_results=3)
        
        for result in results:
            all_courses.append({
                "title": result.get("title", ""),
                "url": result.get("url", ""),
                "snippet": result.get("snippet", ""),
                "platform": site_name,
                "source": "review_site",
            })
    
    ranking_queries = [
        f"best {industry} courses 2024 2025 ranking price",
        f"top {industry} certifications comparison cost",
        f"{industry} online training programs curriculum lessons",
        f"{industry} course reviews Google rating",
        f"most popular {industry} courses students enrolled",
    ]
    
    for query in ranking_queries:
        results = await serpapi_client.search(query, num_results=6)
        for result in results:
            all_courses.append({
                "title": result.get("title", ""),
                "url": result.get("url", ""),
                "snippet": result.get("snippet", ""),
                "platform": "Ranking Article",
                "source": "ranking_article",
            })
    
    # Extract comprehensive data using Claude
    return await _extract_comprehensive_course_data(all_courses, industry)


async def _extract_comprehensive_course_data(courses: list[dict], industry: str) -> dict:
    """Use Claude to extract comprehensive course data including lessons."""
    
    # Build context
    content = "\n\n".join([
        f"**{i+1}. {c.get('title')}**\n"
        f"Platform: {c.get('platform')}\n"
        f"URL: {c.get('url')}\n"
        f"Info: {c.get('snippet', '')[:300]}"
        for i, c in enumerate(courses[:50])
    ])
    
    prompt = f"""Analyze these {industry} courses and extract comprehensive structured data.

COURSES FOUND:
{content}

For each UNIQUE course, extract ALL available information:

Return JSON:
{{
    "courses": [
        {{
            "rank": 1,
            "name": "Full course name",
            "provider": "Platform name",
            "url": "Direct URL",
            "price": "Exact price (e.g., '$199', 'Free', '$49/month', 'Contact for price')",
            "duration": "Course length (e.g., '6 weeks', '40 hours', 'Self-paced')",
            "certification": "Certificate type or 'No certificate'",
            "rating": "Rating (e.g., '4.8/5')",
            "reviews_count": "Number of reviews (e.g., '12,500 reviews')",
            "students_enrolled": "Number (e.g., '150,000')",
            "lessons": [
                {{
                    "name": "Lesson/Module name",
                    "description": "2-3 sentence description of what student learns"
                }}
            ],
            "key_skills": ["skill1", "skill2"],
            "popularity_score": 1-100
        }}
    ],
    "lesson_frequency": [
        {{
            "lesson_topic": "Topic name",
            "frequency": 15,
            "courses_teaching_it": ["Course A", "Course B"]
        }}
    ],
    "price_analysis": {{
        "range": "$0 - $500",
        "average": "$199",
        "free_courses": 5,
        "budget_courses": 10,
        "premium_courses": 5
    }},
    "certification_types": ["Certificate A", "Certificate B"],
    "data_sources": ["List of websites/databases searched"]
}}

IMPORTANT:
- Rank courses by popularity (reviews, ratings, students enrolled)
- Extract ALL lessons mentioned for each course
- If exact price not found, estimate tier: Free / Budget ($0-50) / Mid ($50-200) / Premium ($200+)
- Track which lessons appear across multiple courses
- Don't make up data - mark as "[Not found]" if unavailable

Return ONLY valid JSON."""

    try:
        result = await claude_client.complete(
            prompt=prompt,
            system="You are a course data extraction expert. Extract comprehensive course information including all lessons. Return only valid JSON.",
            temperature=0,
            max_tokens=4000,
        )
        
        # Clean and parse JSON
        result = result.strip()
        if result.startswith("```json"):
            result = result[7:]
        if result.startswith("```"):
            result = result[3:]
        if result.endswith("```"):
            result = result[:-3]
        
        data = json.loads(result.strip())
        
        # Sort courses by popularity score
        if "courses" in data:
            data["courses"] = sorted(
                data["courses"],
                key=lambda x: x.get("popularity_score", 0),
                reverse=True
            )[:20]  # Top 20 courses
        
        # Sort lessons by frequency
        if "lesson_frequency" in data:
            data["lesson_frequency"] = sorted(
                data["lesson_frequency"],
                key=lambda x: x.get("frequency", 0),
                reverse=True
            )
        
        data["industry"] = industry
        data["total_courses_found"] = len(courses)
        
        return data
    
    except Exception as e:
        return {
            "courses": [
                {
                    "name": c.get("title"),
                    "provider": c.get("platform"),
                    "url": c.get("url"),
                    "price": "[Not found]",
                    "lessons": [],
                }
                for c in courses[:20]
            ],
            "lesson_frequency": [],
            "price_analysis": {},
            "error": str(e),
            "industry": industry,
        }


async def extract_course_lessons(url: str) -> dict:
    """
    Extract detailed lesson information from a specific course URL.
    
    Args:
        url: Course page URL to scrape
    
    Returns:
        Detailed lesson information with descriptions
    """
    try:
        # Try to scrape the course page
        content = await firecrawl_client.scrape(url)
        
        if not content:
            return {"error": "Could not scrape page", "url": url}
        
        # Extract lessons using Claude
        prompt = f"""Extract ALL lessons/modules from this course page:

{content[:8000]}

Return JSON:
{{
    "course_name": "Name",
    "provider": "Platform",
    "total_duration": "X hours/weeks",
    "lessons": [
        {{
            "number": 1,
            "name": "Lesson name",
            "duration": "X hours",
            "description": "2-3 sentences on what student learns",
            "topics_covered": ["topic1", "topic2"]
        }}
    ],
    "certification": "Certificate type",
    "price": "Price found"
}}

Return ONLY valid JSON."""

        result = await claude_client.complete(
            prompt=prompt,
            system="Extract course lessons and curriculum details. Return only JSON.",
            temperature=0,
        )
        
        # Parse JSON
        result = result.strip()
        if result.startswith("```"):
            result = result.split("```")[1]
            if result.startswith("json"):
                result = result[4:]
        
        return json.loads(result.strip())
    
    except Exception as e:
        return {"error": str(e), "url": url}

