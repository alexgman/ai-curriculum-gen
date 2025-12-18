"""Course discovery and ranking tool - comprehensive competitor research."""
from app.services.serpapi import serpapi_client
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
    print(f"[Progress] {message}")


async def discover_courses_with_rankings(
    industry: str = None,
    query: str = None,
    min_results: int = 25,
    selected_competitors: list = None,
    selected_certifications: list = None,
) -> dict:
    """
    Comprehensive course discovery for curriculum research.
    Finds 25-35 courses with full curriculum breakdowns.
    
    Args:
        industry: Industry, job title, or topic to research
        query: Alias for industry parameter
        min_results: Minimum number of courses to find
        selected_competitors: Optional list of specific competitors to search for
        selected_certifications: Optional list of certifications to prioritize
    
    Returns:
        Comprehensive course data with curricula, prices, rankings
    """
    print(f"COURSE DISCOVERY STARTED: industry={industry}, query={query}, min_results={min_results}")
    print(f"  Selected competitors: {selected_competitors[:5] if selected_competitors else 'None'}...")
    print(f"  Selected certs: {selected_certifications[:3] if selected_certifications else 'None'}...")
    industry = industry or query
    if not industry:
        return {"error": "Please provide an industry or query", "courses": []}
    
    all_results = []
    
    await _report_progress(f"Searching for '{industry}' courses across diverse platforms")
    
    # STEP 1: Search across DIVERSE sources (not just MOOCs!)
    # The key is to balance between:
    # - MOOCs (Coursera, Udemy, edX) - general courses
    # - Industry-specific providers - specialized training
    # - Certification bodies - official certifications
    # - Trade schools / bootcamps - practical training
    
    search_tasks = [
        # ==== INDUSTRY-SPECIFIC PROVIDERS (PRIORITY) ====
        # These are the most valuable for competitive research
        _search_platform(f"{industry} training provider certification program", "Industry Provider", 15),
        _search_platform(f"{industry} professional training school accredited", "Trade School", 12),
        _search_platform(f"{industry} certification body official training", "Certification Body", 10),
        _search_platform(f"{industry} vocational training apprenticeship", "Vocational", 8),
        
        # ==== MOOCS (SECONDARY - limit exposure) ====
        _search_platform(f"site:coursera.org {industry} professional certificate", "Coursera", 6),
        _search_platform(f"site:udemy.com {industry} course bestseller", "Udemy", 6),
        _search_platform(f"site:edx.org {industry} certificate", "edX", 5),
        _search_platform(f"site:linkedin.com/learning {industry}", "LinkedIn Learning", 5),
        
        # ==== BOOTCAMPS & SPECIALIZED ====
        _search_platform(f"{industry} bootcamp intensive training program", "Bootcamp", 8),
        _search_platform(f"{industry} online academy complete training", "Academy", 8),
        
        # ==== RANKING & COMPARISON ARTICLES ====
        _search_platform(f"best {industry} training programs 2024 review compare", "Rankings", 10),
        _search_platform(f"top {industry} certification courses accredited ranked", "Rankings", 8),
        _search_platform(f"{industry} training school comparison guide", "Rankings", 6),
    ]
    
    await _report_progress("Searching industry providers, certification bodies, trade schools, MOOCs, bootcamps")
    
    # If we have specific competitors from the research plan, search for them directly
    if selected_competitors:
        for comp in selected_competitors[:8]:  # Top 8 selected competitors
            search_tasks.append(
                _search_platform(f'"{comp}" {industry} courses training', f"Competitor: {comp}", 5)
            )
    
    # If we have specific certifications, search for them
    if selected_certifications:
        for cert in selected_certifications[:5]:  # Top 5 certifications
            search_tasks.append(
                _search_platform(f'{cert} certification training course {industry}', f"Cert: {cert}", 4)
            )
    results = await asyncio.gather(*search_tasks, return_exceptions=True)
    
    for result in results:
        if isinstance(result, list):
            all_results.extend(result)
    
    await _report_progress(f"Found {len(all_results)} results across all platforms")
    
    # STEP 2: Deduplicate and filter
    await _report_progress("Removing duplicates and filtering course pages")
    unique_results = _deduplicate_results(all_results)
    await _report_progress(f"{len(unique_results)} unique courses identified")
    
    # STEP 3: Extract comprehensive course data with Claude
    await _report_progress("Analyzing courses with AI - extracting curriculum details")
    await _report_progress("Extracting pricing, duration, ratings, and full curriculum")
    courses = await _extract_comprehensive_data(unique_results, industry)
    await _report_progress(f"Extracted details for {len(courses)} courses")
    
    # STEP 4: Organize by price tier
    await _report_progress("Organizing courses by price tier")
    tiered_courses = _organize_by_price(courses)
    premium = len(tiered_courses.get("premium", []))
    mid = len(tiered_courses.get("mid", []))
    budget = len(tiered_courses.get("budget", []))
    await _report_progress(f"{premium} Premium, {mid} Mid-range, {budget} Budget courses")
    
    # STEP 5: Build module inventory
    await _report_progress("Building comprehensive module inventory")
    module_inventory = _build_module_inventory(courses)
    await _report_progress(f"Identified {len(module_inventory)} unique modules across all courses")
    
    await _report_progress(f"Research complete: {len(courses)} courses with full curriculum data")
    
    return {
        "courses": courses,
        "tiered_courses": tiered_courses,
        "module_inventory": module_inventory,
        "industry": industry,
        "total_found": len(courses),
    }


def _deduplicate_results(results: list) -> list:
    """Remove duplicates and filter to course-related pages only."""
    seen = set()
    unique = []
    
    for r in results:
        url = r.get("url", "")
        if not url or not url.startswith("http"):
            continue
        
        # Clean URL
        base = url.split("?")[0].rstrip("/").lower()
        
        # Skip non-course pages
        skip = ["/blog/", "/help/", "/about/", "/support/", "/careers/",
                "/terms/", "/privacy/", "/search", "/browse/", "/category/",
                "/topics/", "/tags/", "/author/"]
        if any(p in base for p in skip):
            continue
        
        if base not in seen:
            seen.add(base)
            r["url"] = url.split("?")[0]
            unique.append(r)
    
    return unique[:80]  # Max 80 results for processing


async def _extract_comprehensive_data(results: list, industry: str) -> list:
    """Extract comprehensive course data including full curriculum."""
    
    # Build context from search results - limit to 30 for manageable output
    context_lines = []
    for i, r in enumerate(results[:30], 1):
        context_lines.append(
            f"{i}. **{r.get('title', 'N/A')}**\n"
            f"   URL: {r.get('url', '')}\n"
            f"   Platform: {r.get('platform', 'Unknown')}\n"
            f"   Info: {r.get('snippet', '')[:300]}"  # Shorter snippet
        )
    
    context = "\n\n".join(context_lines)
    
    prompt = f"""Analyze these {industry} course search results and extract COMPREHENSIVE data for competitive research.

SEARCH RESULTS:
{context}

Extract detailed information for EACH unique course (target: 20-25 courses).

For EACH course provide:
1. **name**: Full course title
2. **provider**: Platform name
3. **url**: Direct course URL
4. **price**: Extract or estimate:
   - Coursera: "$49/month" (subscription) or "$200-500" (specialization)
   - Udemy: "$20-150" (sale) / "$100-200" (full price)
   - edX: "Free (audit)" / "$150-300" (verified cert)
   - LinkedIn Learning: "$29.99/month"
   - Bootcamps: "$2,000-15,000"
5. **price_tier**: "premium" (>$500), "mid" ($100-500), or "budget" (<$100)
6. **duration**: Hours, weeks, or months
7. **certification**: Certificate type ("Professional Certificate", "Nanodegree", "Completion Certificate", etc.)
8. **rating**: Star rating (e.g., "4.6/5")
9. **students**: Enrollment count if available
10. **curriculum**: List 8-15 modules/topics that this course likely covers. For well-known courses, include the actual curriculum. For others, estimate based on the topic and platform.

Each curriculum item should be a dict with:
- "name": Module/topic name
- "description": 1-2 sentence description of what's taught

Return ONLY this JSON (no other text):
{{
  "courses": [
    {{
      "name": "Google Data Analytics Professional Certificate",
      "provider": "Coursera",
      "url": "https://...",
      "price": "$49/month",
      "price_tier": "mid",
      "duration": "6 months",
      "certification": "Google Professional Certificate",
      "rating": "4.8/5",
      "students": "1.5M+ enrolled",
      "curriculum": [
        {{"name": "Foundations: Data, Data, Everywhere", "description": "Introduction to data analytics, analytical thinking, and the data ecosystem"}},
        {{"name": "Ask Questions to Make Data-Driven Decisions", "description": "Effective questioning, structured thinking, and stakeholder management"}},
        {{"name": "Prepare Data for Exploration", "description": "Data types, data structures, and data integrity"}},
        {{"name": "Process Data from Dirty to Clean", "description": "Data cleaning, SQL queries, and data verification"}},
        {{"name": "Analyze Data to Answer Questions", "description": "Data analysis with spreadsheets and SQL, calculations and formatting"}},
        {{"name": "Share Data Through Visualization", "description": "Data visualization with Tableau, presenting findings"}},
        {{"name": "Data Analysis with R Programming", "description": "R programming fundamentals and data analysis in R"}},
        {{"name": "Capstone: Complete a Case Study", "description": "End-to-end data analysis project demonstrating skills"}}
      ]
    }}
  ]
}}

IMPORTANT:
- Extract 20-25 courses
- Include 5-8 curriculum modules per course (keep descriptions brief - 1 sentence max)
- Group similar courses together (don't duplicate)
- Use realistic pricing based on platform
- ENSURE valid JSON - close all brackets properly
"""

    try:
        print(f"📤 Sending request to Claude for course extraction ({len(results)} results)")
        await _report_progress("Calling AI to extract curriculum details")
        
        result = await claude_client.complete(
            prompt=prompt,
            system=f"You are a curriculum researcher. Extract comprehensive {industry} course data with FULL curriculum breakdowns. Be thorough - this is for competitive intelligence.",
            temperature=0,
            max_tokens=16000,  # Increased to handle full curriculum data
        )
        
        print(f"📥 Claude response received: {len(result)} chars")
        await _report_progress("AI analysis complete")
        
        # Parse JSON - handle truncated responses
        result = result.strip()
        if "```json" in result:
            result = result.split("```json")[1].split("```")[0]
        elif "```" in result:
            result = result.split("```")[1].split("```")[0]
        
        result = result.strip()
        
        # Try to fix truncated JSON
        try:
            data = json.loads(result)
        except json.JSONDecodeError:
            # Try to fix truncated JSON by finding the last complete course entry
            print("⚠️ JSON parsing failed, attempting to fix truncated response")
            
            # Find the start of the courses array
            if '"courses"' in result and '[' in result:
                courses_start = result.find('[', result.find('"courses"'))
                # Find all complete course objects
                import re
                course_pattern = r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}'
                courses_text = result[courses_start:]
                
                # Try progressively shorter versions until valid JSON
                for end_pos in range(len(courses_text), 0, -100):
                    try:
                        test_json = '{"courses": ' + courses_text[:end_pos] + ']}'
                        data = json.loads(test_json)
                        print(f"Fixed truncated JSON, found {len(data.get('courses', []))} courses")
                        break
                    except:
                        continue
                else:
                    # Give up and use fallback
                    raise ValueError("Could not fix truncated JSON")
            else:
                raise ValueError("No courses array found")
        
        courses = data.get("courses", [])
        print(f"Extracted {len(courses)} courses from Claude response")
        return courses
        
    except Exception as e:
        print(f"❌ Course extraction error: {e}")
        import traceback
        traceback.print_exc()
        await _report_progress("⚠️ AI extraction failed, using fallback")
        return _fallback_extraction(results, industry)


def _fallback_extraction(results: list, industry: str) -> list:
    """Fallback when Claude extraction fails."""
    courses = []
    
    platform_info = {
        "Coursera": {"price": "$49/month", "price_tier": "mid", "cert": "Professional Certificate"},
        "Udemy": {"price": "$20-150", "price_tier": "budget", "cert": "Completion Certificate"},
        "edX": {"price": "Free to $300", "price_tier": "mid", "cert": "Verified Certificate"},
        "LinkedIn Learning": {"price": "$29.99/month", "price_tier": "mid", "cert": "Certificate of Completion"},
        "Skillshare": {"price": "$14/month", "price_tier": "budget", "cert": "None"},
        "Udacity": {"price": "$400/month", "price_tier": "premium", "cert": "Nanodegree"},
        "Pluralsight": {"price": "$29/month", "price_tier": "mid", "cert": "Skill IQ"},
    }
    
    for r in results[:30]:
        platform = r.get("platform", "Unknown")
        if platform in ["Rankings", "Bootcamp", "Certification"]:
            continue
        
        info = platform_info.get(platform, {"price": "See website", "price_tier": "mid", "cert": "Available"})
        
        courses.append({
            "name": r.get("title", "Unknown Course"),
            "provider": platform,
            "url": r.get("url", ""),
            "price": info["price"],
            "price_tier": info["price_tier"],
            "duration": "[See website]",
            "certification": info["cert"],
            "rating": "[See website]",
            "students": "[See website]",
            "curriculum": [],
        })
    
    return courses


def _organize_by_price(courses: list) -> dict:
    """Organize courses into price tiers."""
    tiers = {
        "premium": [],
        "mid": [],
        "budget": [],
    }
    
    for course in courses:
        tier = course.get("price_tier", "mid")
        if tier in tiers:
            tiers[tier].append(course)
        else:
            tiers["mid"].append(course)
    
    return tiers


def _build_module_inventory(courses: list) -> list:
    """Build comprehensive module inventory from all courses."""
    module_data = {}
    
    for course in courses:
        course_name = course.get("name", "Unknown")
        curriculum = course.get("curriculum", [])
        
        for module in curriculum:
            if isinstance(module, dict):
                name = module.get("name", "")
                desc = module.get("description", "")
            else:
                name = str(module)
                desc = ""
            
            if not name:
                continue
            
            # Normalize for grouping
            key = name.lower().strip()
            
            if key not in module_data:
                module_data[key] = {
                    "name": name,
                    "description": desc,
                    "sources": [],
                    "count": 0
                }
            
            module_data[key]["count"] += 1
            if course_name not in module_data[key]["sources"]:
                module_data[key]["sources"].append(course_name)
            
            # Keep best description
            if desc and len(desc) > len(module_data[key].get("description", "")):
                module_data[key]["description"] = desc
    
    # Convert to list and sort by frequency
    inventory = []
    for key, data in module_data.items():
        count = data["count"]
        if count >= 5:
            frequency = "Vital"
        elif count >= 3:
            frequency = "High"
        elif count >= 2:
            frequency = "Medium"
        else:
            frequency = "Low"
        
        inventory.append({
            "name": data["name"],
            "description": data["description"],
            "frequency": frequency,
            "count": count,
            "sources": data["sources"][:5],
        })
    
    # Sort by count descending
    inventory.sort(key=lambda x: -x["count"])
    
    return inventory


async def _search_platform(query: str, platform: str, num_results: int) -> list:
    """Search and tag results with platform."""
    try:
        results = await serpapi_client.search(query, num_results=num_results)
        return [
            {
                "title": r.get("title", ""),
                "url": r.get("link", r.get("url", "")),
                "snippet": r.get("snippet", ""),
                "platform": platform,
            }
            for r in results
        ]
    except Exception as e:
        print(f"Search failed for {platform}: {e}")
        return []


async def extract_course_lessons(url: str) -> dict:
    """Extract detailed lessons from a specific course URL."""
    from app.services.firecrawl import firecrawl_client
    
    try:
        content = await firecrawl_client.scrape(url)
        if not content:
            return {"error": "Could not scrape page", "url": url}
        
        prompt = f"""Extract the COMPLETE curriculum from this course page:

{content[:10000]}

Return JSON with ALL modules and lessons:
{{
    "course_name": "Name",
    "provider": "Platform",
    "curriculum": [
        {{"name": "Module name", "description": "What student learns", "lessons": ["Lesson 1", "Lesson 2"]}}
    ],
    "price": "Price if found",
    "certification": "Certificate type"
}}"""

        result = await claude_client.complete(
            prompt=prompt,
            system="Extract complete course curriculum. Return only JSON.",
            temperature=0,
        )
        
        result = result.strip()
        if "```" in result:
            result = result.split("```")[1].replace("json", "").strip()
        
        return json.loads(result.strip())
    
    except Exception as e:
        return {"error": str(e), "url": url}
