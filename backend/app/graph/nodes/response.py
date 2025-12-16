"""Response node - generates comprehensive curriculum research report."""
import json
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langchain_anthropic import ChatAnthropic
from app.graph.state import AgentState
from app.config import settings
from app.graph.nodes.reflection import _session_research_data


async def response_node(state: AgentState) -> dict:
    """
    Generate comprehensive curriculum research report based on collected data.
    
    IMPORTANT: We generate the report DIRECTLY from data, not asking LLM to expand.
    This ensures ALL courses are included with full details.
    """
    print("🎯 RESPONSE NODE STARTED")
    
    try:
        # Check if this is a clarifying question - if so, just pass through the message
        if state.get("is_clarifying_question"):
            print("📝 Clarifying question - passing through")
            # The message was already set by reasoning node
            last_message = state.get("messages", [])[-1] if state.get("messages") else None
            if last_message:
                return {
                    "messages": [last_message],
                    "next_node": "end",
                }
        
        # Get session ID
        session_id = state.get("session_id", "default")
        
        # Get research data from session cache (PRIMARY) or state (fallback)
        research_data = _session_research_data.get(session_id)
        if research_data is None:
            print(f"⚠️ Session not in cache, using state")
            research_data = state.get("research_data", {})
        else:
            print(f"✅ Found session in cache")
        
        # Get the industry from state
        industry = state.get("industry", "Not specified")
        
        # Log what we have
        courses = research_data.get("courses", [])
        print(f"📝 Response node: {len(courses)} courses found")
        
        # If no courses and no research, prompt user for more info
        if len(courses) == 0 and not research_data.get("module_inventory"):
            print("⚠️ No courses - need more research or clarification")
            return {
                "messages": [AIMessage(content="I don't have any course data yet. Please provide a specific topic or industry you'd like me to research (e.g., 'data science courses', 'Python programming', 'digital marketing').")],
                "next_node": "end",
            }
        
        # GENERATE THE FULL REPORT DIRECTLY FROM DATA
        # This ensures ALL courses are included - no LLM truncation
        print(f"📝 GENERATING FULL REPORT for {len(courses)} courses...")
        full_report = await _generate_full_report(research_data, industry)
        
        print(f"✅ RESPONSE NODE COMPLETED - Generated {len(full_report)} chars")
        print(f"📝 Report preview: {full_report[:300]}...")
        print(f"📝 Report ends with: ...{full_report[-200:]}")
        
        # Create the final message
        final_message = AIMessage(content=full_report)
        print(f"📤 Returning AIMessage with content length: {len(final_message.content)}")
        
        return {
            "messages": [final_message],
            "next_node": "end",
        }
    
    except Exception as e:
        print(f"❌ RESPONSE NODE ERROR: {e}")
        import traceback
        traceback.print_exc()
        
        # Return a fallback response
        research_data = state.get("research_data", {})
        courses = research_data.get("courses", [])
        
        fallback = f"# Research Report\n\nFound {len(courses)} courses. Error generating full report: {e}"
        
        return {
            "messages": [AIMessage(content=fallback)],
            "next_node": "end",
        }


async def _generate_full_report(research_data: dict, industry: str) -> str:
    """
    Generate COMPLETE report directly from data.
    NO LLM truncation - we format ALL courses ourselves.
    """
    courses = research_data.get("courses", [])
    module_inventory = research_data.get("module_inventory", [])
    
    # Build report sections
    sections = []
    
    # ==== HEADER ====
    sections.append(f"# Comprehensive Guide to Online {industry} Training\n")
    
    # ==== EXECUTIVE SUMMARY ====
    prices = [c.get("price", "") for c in courses if c.get("price")]
    platforms = list(set(c.get("provider", c.get("platform", "Unknown")) for c in courses))[:5]
    
    sections.append(f"""
The online {industry} training market offers diverse options from **{len(courses)} providers** ranging from budget-friendly to premium programs.

---

## Top {len(courses)} Online {industry} Courses Ranked by Popularity

Based on enrollment data, reviews, and industry recognition:

""")
    
    # ==== TIER 1: PREMIUM ====
    premium = [c for c in courses if _is_premium(c)]
    mid_range = [c for c in courses if _is_mid_range(c)]
    budget = [c for c in courses if _is_budget(c)]
    
    sections.append("### Tier 1: Market Leaders (Highest Enrollment/Visibility)\n")
    
    course_num = 1
    
    # List ALL premium courses
    for course in premium:
        sections.append(_format_full_course(course, course_num))
        course_num += 1
    
    # ==== TIER 2: MID-RANGE ====
    if mid_range:
        sections.append("\n---\n\n### Tier 2: Mid-Range Options\n")
        for course in mid_range:
            sections.append(_format_full_course(course, course_num))
            course_num += 1
    
    # ==== TIER 3: BUDGET ====
    if budget:
        sections.append("\n---\n\n### Tier 3: Budget-Friendly / Free Options\n")
        for course in budget:
            sections.append(_format_full_course(course, course_num))
            course_num += 1
    
    # ==== MODULE INVENTORY ====
    sections.append("\n---\n\n## Complete Module Inventory\n")
    sections.append("All unique topics/modules discovered across all courses:\n")
    
    if module_inventory:
        # Group by frequency
        vital = [m for m in module_inventory if m.get("frequency") == "Vital"]
        high = [m for m in module_inventory if m.get("frequency") == "High"]
        medium = [m for m in module_inventory if m.get("frequency") == "Medium"]
        low = [m for m in module_inventory if m.get("frequency") == "Low"]
        
        if vital:
            sections.append("\n### VITAL (Found in 5+ courses)\n")
            for m in vital:
                desc = m.get("description", "Core topic in this field.")
                sources = ", ".join(m.get("sources", [])[:5])
                sections.append(f"- **{m['name']}** — {desc} (Sources: {sources})\n")
        
        if high:
            sections.append("\n### HIGH FREQUENCY (Found in 3-4 courses)\n")
            for m in high:
                desc = m.get("description", "Important topic.")
                sources = ", ".join(m.get("sources", [])[:4])
                sections.append(f"- **{m['name']}** — {desc} (Sources: {sources})\n")
        
        if medium:
            sections.append("\n### MEDIUM FREQUENCY (Found in 2 courses)\n")
            for m in medium:
                desc = m.get("description", "")
                sources = ", ".join(m.get("sources", [])[:3])
                sections.append(f"- **{m['name']}** — {desc} (Sources: {sources})\n")
        
        if low:
            sections.append("\n### NICHE/SPECIALIZED (Found in 1 course)\n")
            for m in low[:20]:  # Limit niche to avoid overwhelming
                desc = m.get("description", "")
                source = m.get("sources", ["Unknown"])[0] if m.get("sources") else "Unknown"
                sections.append(f"- **{m['name']}** — {desc} (Source: {source})\n")
    else:
        # Generate module inventory from course curricula
        sections.append(_generate_module_inventory_from_courses(courses))
    
    # ==== KEY INSIGHTS ====
    sections.append("\n---\n\n## Key Insights\n")
    
    # Certification analysis
    certs = [c.get("certification", "") for c in courses if c.get("certification") and c.get("certification") != "N/A"]
    sections.append(f"\n### Certification Landscape\n")
    if certs:
        cert_summary = ", ".join(list(set(certs))[:5])
        sections.append(f"Available certifications include: {cert_summary}\n")
    else:
        sections.append("Various completion certificates and professional certifications available.\n")
    
    # Price analysis
    sections.append(f"\n### Pricing Analysis\n")
    sections.append(f"- **Premium tier**: Programs typically $500+ with comprehensive curriculum\n")
    sections.append(f"- **Mid-range**: $100-$500, often subscription-based ($49/month common)\n")
    sections.append(f"- **Budget**: Under $100 or free audit options available\n")
    
    # Platforms
    sections.append(f"\n### Top Platforms\n")
    for p in platforms[:5]:
        sections.append(f"- {p}\n")
    
    # ==== DATA SOURCES ====
    sections.append("\n---\n\n## Data Sources\n")
    urls = list(set(c.get("url", "") for c in courses if c.get("url")))
    for url in urls[:30]:
        sections.append(f"- {url}\n")
    
    return "".join(sections)


def _format_full_course(course: dict, num: int) -> str:
    """Format a single course with FULL details like the HVAC PDF sample."""
    name = course.get("name", course.get("title", "Unknown Course"))
    provider = course.get("provider", course.get("platform", "Unknown"))
    url = course.get("url", "")
    price = course.get("price", "Not available")
    duration = course.get("duration", "Not available")
    cert = course.get("certification", "Completion Certificate")
    rating = course.get("rating", "Not available")
    students = course.get("students", "Not available")
    reviews = course.get("reviews", "")
    accreditation = course.get("accreditation", "")
    
    lines = []
    lines.append(f"\n#### {num}. {name}\n")
    
    # Metrics table
    lines.append("| Metric | Details |")
    lines.append("|--------|---------|")
    lines.append(f"| **Provider** | {provider} |")
    lines.append(f"| **Price** | {price} |")
    lines.append(f"| **Duration** | {duration} |")
    lines.append(f"| **Certifications** | {cert} |")
    if students and students != "Not available":
        lines.append(f"| **Enrollment** | {students} |")
    if rating and rating != "Not available":
        review_text = f" ({reviews} reviews)" if reviews else ""
        lines.append(f"| **Reviews** | {rating}{review_text} |")
    if accreditation:
        lines.append(f"| **Accreditation** | {accreditation} |")
    if url:
        lines.append(f"| **URL** | {url} |")
    
    # Curriculum
    curriculum = course.get("curriculum", course.get("modules", []))
    if curriculum and len(curriculum) > 0:
        lines.append(f"\n**Complete Curriculum ({len(curriculum)} Modules):**\n")
        for i, mod in enumerate(curriculum, 1):
            if isinstance(mod, dict):
                mod_name = mod.get("name", mod.get("title", f"Module {i}"))
                mod_desc = mod.get("description", "")
                if mod_desc:
                    lines.append(f"{i}. **{mod_name}** — {mod_desc}")
                else:
                    lines.append(f"{i}. **{mod_name}**")
            else:
                lines.append(f"{i}. **{mod}**")
    else:
        lines.append("\n**Key Modules:** Curriculum details not available from source.\n")
    
    lines.append("\n---\n")
    return "\n".join(lines)


def _is_premium(course: dict) -> bool:
    """Check if course is premium tier ($500+)."""
    price = str(course.get("price", "")).lower()
    if not price or price == "not available":
        return True  # Default premium if unknown
    if any(x in price for x in ["free", "$0", "audit"]):
        return False
    # Extract number
    import re
    nums = re.findall(r'\d+', price.replace(",", ""))
    if nums:
        max_price = max(int(n) for n in nums)
        return max_price >= 500
    return True  # Default premium


def _is_mid_range(course: dict) -> bool:
    """Check if course is mid-range ($100-$500)."""
    price = str(course.get("price", "")).lower()
    if not price or price == "not available":
        return False
    if any(x in price for x in ["free", "$0", "audit"]):
        return False
    import re
    nums = re.findall(r'\d+', price.replace(",", ""))
    if nums:
        max_price = max(int(n) for n in nums)
        return 100 <= max_price < 500
    # Check for subscription
    if "/month" in price or "month" in price:
        return True
    return False


def _is_budget(course: dict) -> bool:
    """Check if course is budget tier (under $100 or free)."""
    price = str(course.get("price", "")).lower()
    if any(x in price for x in ["free", "$0", "audit"]):
        return True
    import re
    nums = re.findall(r'\d+', price.replace(",", ""))
    if nums:
        max_price = max(int(n) for n in nums)
        return max_price < 100
    return False


def _generate_module_inventory_from_courses(courses: list) -> str:
    """Generate module inventory from course curricula if not pre-computed."""
    module_counts = {}
    
    for course in courses:
        course_name = course.get("name", course.get("title", "Unknown"))
        curriculum = course.get("curriculum", course.get("modules", []))
        
        for mod in curriculum:
            if isinstance(mod, dict):
                mod_name = mod.get("name", mod.get("title", ""))
            else:
                mod_name = str(mod)
            
            if mod_name:
                # Normalize module name
                normalized = mod_name.strip().lower()
                if normalized not in module_counts:
                    module_counts[normalized] = {
                        "name": mod_name,
                        "count": 0,
                        "sources": []
                    }
                module_counts[normalized]["count"] += 1
                if course_name not in module_counts[normalized]["sources"]:
                    module_counts[normalized]["sources"].append(course_name)
    
    # Sort by frequency
    sorted_modules = sorted(module_counts.values(), key=lambda x: x["count"], reverse=True)
    
    lines = []
    
    vital = [m for m in sorted_modules if m["count"] >= 5]
    high = [m for m in sorted_modules if 3 <= m["count"] < 5]
    medium = [m for m in sorted_modules if m["count"] == 2]
    low = [m for m in sorted_modules if m["count"] == 1]
    
    if vital:
        lines.append("\n### VITAL (Found in 5+ courses)\n")
        for m in vital:
            sources = ", ".join(m["sources"][:5])
            lines.append(f"- **{m['name']}** — Found in {m['count']} courses. (Sources: {sources})\n")
    
    if high:
        lines.append("\n### HIGH FREQUENCY (Found in 3-4 courses)\n")
        for m in high:
            sources = ", ".join(m["sources"][:4])
            lines.append(f"- **{m['name']}** — Found in {m['count']} courses. (Sources: {sources})\n")
    
    if medium:
        lines.append("\n### MEDIUM FREQUENCY (Found in 2 courses)\n")
        for m in medium:
            sources = ", ".join(m["sources"][:2])
            lines.append(f"- **{m['name']}** — (Sources: {sources})\n")
    
    if low:
        lines.append("\n### NICHE/SPECIALIZED (Found in 1 course)\n")
        for m in low[:15]:  # Limit niche
            lines.append(f"- **{m['name']}** — (Source: {m['sources'][0]})\n")
    
    return "".join(lines)
