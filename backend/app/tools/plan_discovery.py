"""Plan Discovery Tool - Quick preliminary research to discover competitors, certifications, and audiences."""
import json
import asyncio
from app.services.serpapi import serpapi_client
from app.services.anthropic import claude_client


def _extract_clean_topic(user_input: str) -> str:
    """Extract the actual topic from user's natural language input."""
    import re
    
    cleaned = user_input.lower().strip()
    
    # First, remove time-based prefixes like "today", "now", etc.
    # Also remove "i", "let's" which often precede "want to"
    time_prefixes = r"^(?:today |now |right now |currently )?(?:i )?(?:let'?s |lets )?"
    cleaned = re.sub(time_prefixes, "", cleaned, flags=re.IGNORECASE).strip()
    
    # Remove common conversational prefixes (order matters - longer patterns first)
    prefixes_to_remove = [
        # Course creation patterns with "how to do/be/become"
        r"want to write (?:a |the )?course (?:about |on |for )?(?:how to (?:do |be good at |become good at |get better at |improve at |master )?(?:playing )?)?",
        r"want to create (?:a |the )?course (?:about |on |for )?(?:how to (?:do |be good at |become good at |get better at |improve at |master )?(?:playing )?)?",
        r"want to build (?:a |the )?course (?:about |on |for )?(?:how to (?:do |be good at |become good at |get better at |improve at |master )?(?:playing )?)?",
        r"write (?:a |the )?(?:course |curriculum )(?:about |on |for )?(?:how to (?:do )?)?",
        r"create (?:a |the )?(?:course |curriculum )(?:about |on |for )?(?:how to (?:do )?)?",
        r"build (?:a |the )?(?:course |curriculum )(?:about |on |for )?(?:how to (?:do )?)?",
        # Research patterns
        r"want to research (?:on |about )?",
        r"(?:can you |please )?research (?:on |about )?",
        r"research (?:on |about )?",
        # Learning patterns
        r"(?:want to |need to )?learn (?:about |how to (?:do )?)?",
        r"how to (?:do |be good at |become good at |get better at |improve at |master )?(?:playing )?",
        r"how to (?:learn |study |practice )?",
        # Course/training patterns
        r"need (?:courses?|training) (?:on |for |about )?",
        r"(?:courses?|training) (?:on |for |about )?",
        r"find (?:courses?|training) (?:on |for |about )?",
        r"looking for (?:courses?|training) (?:on |for |about )?",
        r"interested in (?:courses?|training|learning) (?:on |for |about )?",
        r"help me with ",
    ]
    
    for pattern in prefixes_to_remove:
        match = re.match(pattern, cleaned, re.IGNORECASE)
        if match:
            cleaned = cleaned[match.end():].strip()
            break
    
    # Remove trailing phrases that add noise
    suffixes_to_remove = [
        r" courses?$",
        r" training programs?$",
        r" programs?$",
        r" training$",
        r" game$",  # Keep "Counter Strike" not "Counter Strike game"
    ]
    
    for pattern in suffixes_to_remove:
        cleaned = re.sub(pattern, "", cleaned, flags=re.IGNORECASE).strip()
    
    # Remove filler words at the start
    filler_start = [r"^(?:playing |the |a |an |do )"]
    for pattern in filler_start:
        cleaned = re.sub(pattern, "", cleaned, flags=re.IGNORECASE).strip()
    
    # Capitalize properly - handle game names and common terms
    if cleaned:
        # Special case handling for known terms (exact match)
        special_cases = {
            "counter strike": "Counter-Strike",
            "counter-strike": "Counter-Strike",
            "cs go": "CS:GO",
            "csgo": "CS:GO",
            "cs2": "CS2",
            "hvac": "HVAC",
            "it": "IT",
            "ai": "AI",
        }
        
        cleaned_lower = cleaned.lower()
        if cleaned_lower in special_cases:
            return special_cases[cleaned_lower]
        
        # Handle terms that appear within the string (e.g., "hvac technician" -> "HVAC Technician")
        result = cleaned.title()
        term_replacements = {
            "Hvac": "HVAC",
            "Ai ": "AI ",
            "It ": "IT ",
            " Ai": " AI",
            " It": " IT",
        }
        for old, new in term_replacements.items():
            result = result.replace(old, new)
        
        return result
    
    return user_input.title()


async def discover_research_plan(industry: str) -> dict:
    """
    Quick preliminary research to discover:
    1. Main competitors/training providers in the space
    2. Relevant certifications
    3. Typical target audiences
    
    This is a FAST search (30-60 seconds) to inform the research plan.
    
    Args:
        industry: The industry/field to research (e.g., "HVAC technician training")
    
    Returns:
        Dictionary with discovered competitors, certifications, and audience types
    """
    # Extract clean topic from user input
    clean_topic = _extract_clean_topic(industry)
    print(f"🔍 PLAN DISCOVERY: Starting quick research for '{clean_topic}' (from: '{industry}')")
    
    # Run searches in parallel for speed (use clean topic for better results)
    search_tasks = [
        # Competitors/Providers
        _search_competitors(clean_topic),
        # Certifications
        _search_certifications(clean_topic),
        # Target audience insights
        _search_audience(clean_topic),
    ]
    
    results = await asyncio.gather(*search_tasks, return_exceptions=True)
    
    competitors = results[0] if isinstance(results[0], list) else []
    certifications = results[1] if isinstance(results[1], list) else []
    audiences = results[2] if isinstance(results[2], list) else []
    
    print(f"✅ PLAN DISCOVERY: Found {len(competitors)} competitors, {len(certifications)} certifications, {len(audiences)} audience types")
    
    return {
        "industry": clean_topic,  # Use cleaned topic name
        "original_query": industry,  # Keep original for reference
        "competitors": competitors,
        "certifications": certifications,
        "target_audiences": audiences,
        "success": True,
    }


async def _search_competitors(industry: str) -> list:
    """Search for main training providers/competitors in the industry."""
    try:
        # Extract the core industry term (e.g., "HVAC" from "HVAC technician training")
        core_industry = industry.split()[0] if industry else "industry"
        
        # Search for training providers - prioritize industry-specific over MOOCs
        queries = [
            f"best {industry} training programs providers",
            f"top {industry} schools certification courses",
            f"{core_industry} industry training companies professional",
            f"{core_industry} apprenticeship programs trade schools",
            f"{core_industry} certification training accredited",
        ]
        
        all_results = []
        for query in queries:
            results = await serpapi_client.search(query, num_results=10)
            all_results.extend(results)
        
        # Use Claude to extract and categorize competitors
        context = "\n".join([
            f"- {r.get('title', '')} | {r.get('link', '')} | {r.get('snippet', '')[:150]}"
            for r in all_results[:20]
        ])
        
        prompt = f"""Analyze these search results for {industry} training and extract the main training providers/competitors.

SEARCH RESULTS:
{context}

Extract 8-15 unique training providers. PRIORITIZE industry-specific providers over general MOOCs.

For EACH provider, include:
- name: Company/platform name
- type: "industry_specialist" | "mooc" | "bootcamp" | "trade_school" | "certification_body"
- description: Brief 1-sentence description of what they offer
- url: Their website if found

Categorize them as:
- industry_specialist: PRIORITY - Specialized training companies for THIS SPECIFIC field (e.g., HVACREdu, SkillCat, Carrier University for HVAC)
- certification_body: Organizations that offer industry certifications (e.g., NATE, HVAC Excellence)
- trade_school: Vocational/technical schools with hands-on programs
- bootcamp: Intensive training programs
- mooc: General platforms like Coursera, Udemy, edX (INCLUDE FEWER OF THESE)

IMPORTANT: 
- Favor industry-specific providers over generic platforms
- Include at least 4-6 industry specialists or trade schools
- Limit MOOCs to 2-3 maximum

Return ONLY this JSON:
{{
    "competitors": [
        {{"name": "Provider Name", "type": "industry_specialist", "description": "Brief description", "url": "https://..."}}
    ]
}}"""

        result = await claude_client.complete(
            prompt=prompt,
            system="Extract training providers from search results. Return only valid JSON.",
            temperature=0,
            max_tokens=2000,
        )
        
        # Parse response
        result = result.strip()
        if "```json" in result:
            result = result.split("```json")[1].split("```")[0]
        elif "```" in result:
            result = result.split("```")[1].split("```")[0]
        
        data = json.loads(result.strip())
        competitors = data.get("competitors", [])
        
        # Sort by type priority (industry specialists first, MOOCs last)
        type_order = {"industry_specialist": 0, "certification_body": 1, "trade_school": 2, "bootcamp": 3, "mooc": 4}
        competitors.sort(key=lambda x: type_order.get(x.get("type", "mooc"), 5))
        
        return competitors[:12]
        
    except Exception as e:
        print(f"❌ Competitor search error: {e}")
        return []


async def _search_certifications(industry: str) -> list:
    """Search for relevant certifications in the industry."""
    try:
        queries = [
            f"{industry} certifications required",
            f"{industry} professional certification programs",
        ]
        
        all_results = []
        for query in queries:
            results = await serpapi_client.search(query, num_results=8)
            all_results.extend(results)
        
        context = "\n".join([
            f"- {r.get('title', '')} | {r.get('snippet', '')[:200]}"
            for r in all_results[:15]
        ])
        
        prompt = f"""Analyze these search results and extract the main certifications for {industry}.

SEARCH RESULTS:
{context}

Extract 4-8 relevant certifications. For EACH certification:
- name: Certification name (e.g., "EPA 608", "NATE Certification")
- issuer: Organization that issues it
- description: Brief description of what it certifies
- importance: "required" | "highly_recommended" | "optional"

Return ONLY this JSON:
{{
    "certifications": [
        {{"name": "Cert Name", "issuer": "Issuing Org", "description": "What it certifies", "importance": "required"}}
    ]
}}"""

        result = await claude_client.complete(
            prompt=prompt,
            system="Extract certifications from search results. Return only valid JSON.",
            temperature=0,
            max_tokens=1500,
        )
        
        result = result.strip()
        if "```json" in result:
            result = result.split("```json")[1].split("```")[0]
        elif "```" in result:
            result = result.split("```")[1].split("```")[0]
        
        data = json.loads(result.strip())
        certs = data.get("certifications", [])
        
        # Sort by importance
        importance_order = {"required": 0, "highly_recommended": 1, "optional": 2}
        certs.sort(key=lambda x: importance_order.get(x.get("importance", "optional"), 3))
        
        return certs[:8]
        
    except Exception as e:
        print(f"❌ Certification search error: {e}")
        return []


async def _search_audience(industry: str) -> list:
    """Identify typical target audiences for training in this industry."""
    try:
        query = f"{industry} training who should take target audience career path"
        results = await serpapi_client.search(query, num_results=8)
        
        context = "\n".join([
            f"- {r.get('title', '')} | {r.get('snippet', '')[:200]}"
            for r in results[:10]
        ])
        
        prompt = f"""Analyze these search results and identify the typical target audiences for {industry} training.

SEARCH RESULTS:
{context}

Identify 3-5 target audience segments. For EACH audience:
- name: Audience segment name (e.g., "Entry-level technicians", "Career changers")
- description: Who they are and why they need this training
- experience_level: "beginner" | "intermediate" | "advanced"

Return ONLY this JSON:
{{
    "audiences": [
        {{"name": "Entry-level technicians", "description": "People new to the field seeking foundational skills", "experience_level": "beginner"}}
    ]
}}"""

        result = await claude_client.complete(
            prompt=prompt,
            system="Identify target audiences from search results. Return only valid JSON.",
            temperature=0,
            max_tokens=1000,
        )
        
        result = result.strip()
        if "```json" in result:
            result = result.split("```json")[1].split("```")[0]
        elif "```" in result:
            result = result.split("```")[1].split("```")[0]
        
        data = json.loads(result.strip())
        audiences = data.get("audiences", [])
        
        return audiences[:5]
        
    except Exception as e:
        print(f"❌ Audience search error: {e}")
        # Return default audiences if search fails
        return [
            {"name": "Entry-level beginners", "description": "People new to the field", "experience_level": "beginner"},
            {"name": "Career changers", "description": "Professionals transitioning from other fields", "experience_level": "beginner"},
            {"name": "Experienced practitioners", "description": "Those seeking advancement or specialization", "experience_level": "intermediate"},
        ]

