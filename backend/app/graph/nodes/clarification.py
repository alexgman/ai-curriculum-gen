"""Planning node - discovers research plan and iteratively refines with user."""
import json
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_anthropic import ChatAnthropic
from app.graph.state import AgentState, ClarificationState, ResearchPlan
from app.config import settings
from app.tools.plan_discovery import discover_research_plan


def _is_new_research_request(message: str, current_industry: str | None) -> bool:
    """
    Detect if a message is a NEW research topic request (not feedback on existing plan).
    
    Indicators of a NEW request:
    - Contains research intent phrases like "I want to", "research on", "courses about", etc.
    - Does NOT match typical feedback patterns (remove, add, focus, proceed, etc.)
    - Topic keywords are significantly different from current industry
    """
    msg_lower = message.lower().strip()
    
    # New research intent phrases
    new_research_indicators = [
        "i want to", "want to research", "research on", "research about",
        "courses on", "courses about", "courses for", "training on", "training for",
        "curriculum for", "curriculum on", "write a course", "create a course",
        "build a course", "develop a course", "learn about", "teach me",
        "i need courses", "looking for courses", "find courses",
    ]
    
    # Feedback patterns (user editing existing plan)
    feedback_patterns = [
        "remove", "add ", "focus on", "proceed", "yes", "no", "ok", "okay",
        "looks good", "go ahead", "confirm", "start research", "approved",
        "include", "exclude", "target", "great", "perfect", "change",
    ]
    
    # Check if message looks like a new research request
    has_research_intent = any(phrase in msg_lower for phrase in new_research_indicators)
    looks_like_feedback = any(pattern in msg_lower for pattern in feedback_patterns) and len(message) < 100
    
    # If it has research intent and doesn't look like feedback, it's a new request
    if has_research_intent and not looks_like_feedback:
        # Additional check: if current industry exists, see if message is about a different topic
        if current_industry:
            current_keywords = set(current_industry.lower().split())
            message_keywords = set(msg_lower.split())
            # If there's little overlap, it's likely a new topic
            overlap = current_keywords & message_keywords
            if len(overlap) < 2:
                return True
        else:
            return True
    
    return False


async def clarification_node(state: AgentState) -> dict:
    """
    Planning node that:
    1. Does preliminary research to discover competitors, certifications, audiences
    2. Presents a draft research plan to the user
    3. Iteratively refines based on user feedback
    4. Confirms and proceeds when user approves
    
    Stages:
    - "discovery": Initial research to find competitors/certs
    - "presenting_plan": Show the discovered plan to user
    - "refining": User gave feedback, update plan
    - "confirmed": User approved, ready to proceed
    """
    
    clarification = state.get("clarification")
    research_plan = state.get("research_plan")
    
    # Get the latest user message
    last_user_message = ""
    for msg in reversed(state.get("messages", [])):
        if isinstance(msg, HumanMessage):
            last_user_message = msg.content
            break
    
    # Count user messages to detect first message in session
    user_message_count = sum(1 for msg in state.get("messages", []) if isinstance(msg, HumanMessage))
    
    # Determine current stage
    stage = clarification.get("stage") if clarification else "discovery"
    
    print(f"📋 PLANNING NODE: Stage={stage}, has_plan={research_plan is not None}, user_msgs={user_message_count}")
    
    # ===== SAFETY CHECK: Detect if user is starting a NEW research topic =====
    # This handles cases where old session state is loaded but user wants to start fresh
    current_industry = research_plan.get("industry") if research_plan else None
    is_new_topic = _is_new_research_request(last_user_message, current_industry)
    
    # Force fresh discovery if:
    # 1. This is the first message in the session, OR
    # 2. User is asking about a new topic (different from current plan)
    if user_message_count == 1 or (is_new_topic and research_plan):
        print(f"🔄 FORCING FRESH DISCOVERY: first_msg={user_message_count==1}, new_topic={is_new_topic}")
        stage = "discovery"
        research_plan = None  # Clear old plan
    
    # ===== STAGE 1: DISCOVERY =====
    if stage == "discovery" or not research_plan:
        # Get the industry from the user's initial message
        industry = state.get("industry") or last_user_message
        
        print(f"🔍 Starting preliminary research for: {industry}")
        
        # Do quick research to discover the landscape
        discovery_result = await discover_research_plan(industry)
        
        if not discovery_result.get("success"):
            # Fallback if discovery fails
            return {
                "messages": [AIMessage(content=f"I'm having trouble researching '{industry}'. Could you provide more details about what you're looking for?")],
                "awaiting_clarification": True,
                "next_node": "end",
            }
        
        # Create the research plan from discovery
        # Use the cleaned industry name from discovery (not raw user input)
        clean_industry = discovery_result.get("industry", industry)
        competitors = discovery_result.get("competitors", [])
        certifications = discovery_result.get("certifications", [])
        audiences = discovery_result.get("target_audiences", [])
        
        research_plan = ResearchPlan(
            industry=clean_industry,  # Use cleaned topic name
            competitors=competitors,
            certifications=certifications,
            target_audiences=audiences,
            selected_competitors=[c["name"] for c in competitors],  # Default: all
            selected_certifications=[c["name"] for c in certifications],  # Default: all
            selected_audience="All levels",  # Default
            is_confirmed=False,
        )
        
        # Present the plan
        plan_message = _format_plan_presentation(research_plan, is_initial=True)
        
        return {
            "messages": [AIMessage(content=plan_message)],
            "research_plan": research_plan,
            "industry": clean_industry,  # Use cleaned topic name
            "clarification": ClarificationState(
                stage="presenting_plan",
                iteration=1,
                user_feedback=[],
                is_complete=False,
            ),
            "awaiting_clarification": True,
            "next_node": "end",
        }
    
    # ===== STAGE 2: PROCESSING USER FEEDBACK =====
    if stage in ["presenting_plan", "refining"]:
        # Check if user confirmed - use word boundaries to avoid false positives
        # e.g., "starters" should NOT match "start"
        import re
        confirmation_patterns = [
            r"\byes\b", r"\bproceed\b", r"\bgo ahead\b", r"\blooks good\b", 
            r"\bconfirmed?\b", r"\bstart research\b", r"\bapprove[d]?\b", 
            r"\bok\b", r"\bokay\b", r"\bperfect\b", r"\bgreat\b",
            r"\blet'?s go\b", r"\bdo it\b", r"\bbegin\b",
        ]
        msg_lower = last_user_message.lower().strip()
        
        # Must match a confirmation pattern AND be a short message (not detailed feedback)
        is_confirmation_pattern = any(re.search(p, msg_lower) for p in confirmation_patterns)
        is_short_message = len(last_user_message) < 50
        
        # Also check for explicit non-confirmations (feedback indicators)
        feedback_indicators = [
            r"\btarget\b", r"\bfocus\b", r"\bremove\b", r"\badd\b", 
            r"\bchange\b", r"\bupdate\b", r"\binclude\b", r"\bexclude\b",
            r"\bbeginners?\b", r"\bstarters?\b", r"\badvanced\b", r"\bintermediate\b",
            r"\baudienc", r"\bprovider", r"\bcertif",
        ]
        has_feedback_indicators = any(re.search(p, msg_lower) for p in feedback_indicators)
        
        is_confirmed = is_confirmation_pattern and is_short_message and not has_feedback_indicators
        
        if is_confirmed:
            # User confirmed - proceed to research
            print("✅ User confirmed the research plan!")
            
            # Update plan as confirmed
            research_plan["is_confirmed"] = True
            
            confirmation_message = _format_confirmation_message(research_plan)
            
            return {
                "messages": [AIMessage(content=confirmation_message)],
                "research_plan": research_plan,
                "clarification": ClarificationState(
                    stage="confirmed",
                    iteration=clarification.get("iteration", 1),
                    user_feedback=clarification.get("user_feedback", []) + [last_user_message],
                    is_complete=True,
                ),
                "awaiting_clarification": False,
                "next_node": "reasoning",  # Proceed to actual research
            }
        
        # User gave feedback - update the plan
        print(f"📝 Processing user feedback: {last_user_message[:100]}...")
        
        updated_plan = await _update_plan_from_feedback(research_plan, last_user_message)
        iteration = clarification.get("iteration", 1) + 1
        
        # Present updated plan
        plan_message = _format_plan_presentation(updated_plan, is_initial=False, iteration=iteration)
        
        return {
            "messages": [AIMessage(content=plan_message)],
            "research_plan": updated_plan,
            "clarification": ClarificationState(
                stage="refining",
                iteration=iteration,
                user_feedback=clarification.get("user_feedback", []) + [last_user_message],
                is_complete=False,
            ),
            "awaiting_clarification": True,
            "next_node": "end",
        }
    
    # ===== STAGE 3: CONFIRMED - PROCEED =====
    if stage == "confirmed":
        print("✅ Plan confirmed, proceeding to research")
        return {
            "awaiting_clarification": False,
            "next_node": "reasoning",
        }
    
    # Default - shouldn't reach here
    return {
        "next_node": "reasoning",
    }


def _format_plan_presentation(plan: ResearchPlan, is_initial: bool = True, iteration: int = 1) -> str:
    """Format the research plan in a clean, consistent visual structure."""
    
    industry = plan.get("industry", "your field")
    competitors = plan.get("competitors", [])
    certifications = plan.get("certifications", [])
    audiences = plan.get("target_audiences", [])
    
    selected_competitors = plan.get("selected_competitors", [])
    selected_certifications = plan.get("selected_certifications", [])
    selected_audience = plan.get("selected_audience", "All levels")
    
    lines = []
    
    # Header (industry is already properly formatted from _extract_clean_topic)
    if is_initial:
        lines.append(f"## Research Plan: {industry}")
    else:
        lines.append(f"## Updated Plan (v{iteration})")
    lines.append("")
    
    # ===== TRAINING PROVIDERS =====
    lines.append("---")
    lines.append("")
    lines.append(f"**Training Providers:** ({len(selected_competitors)}/{len(competitors)} selected)")
    
    # Group by type
    industry_specialists = [c for c in competitors if c.get("type") == "industry_specialist"]
    cert_bodies = [c for c in competitors if c.get("type") == "certification_body"]
    trade_schools = [c for c in competitors if c.get("type") == "trade_school"]
    bootcamps = [c for c in competitors if c.get("type") == "bootcamp"]
    moocs = [c for c in competitors if c.get("type") == "mooc"]
    
    def format_provider_line(providers: list, label: str) -> str:
        if not providers:
            return ""
        names = [p["name"] for p in providers]
        selected = [n for n in names if n in selected_competitors]
        return f"- {label}: {', '.join(selected)}" if selected else ""
    
    for group, label in [
        (industry_specialists, "Industry Specialists"),
        (cert_bodies, "Certification Bodies"),
        (trade_schools, "Trade Schools"),
        (bootcamps, "Bootcamps"),
        (moocs, "Online Platforms"),
    ]:
        line = format_provider_line(group, label)
        if line:
            lines.append(line)
    
    lines.append("")
    
    # ===== CERTIFICATIONS =====
    lines.append("---")
    lines.append("")
    lines.append(f"**Certifications:** ({len(selected_certifications)}/{len(certifications)} selected)")
    
    required = [c for c in certifications if c.get("importance") == "required"]
    recommended = [c for c in certifications if c.get("importance") == "highly_recommended"]
    optional = [c for c in certifications if c.get("importance") not in ["required", "highly_recommended"]]
    
    if required:
        selected = [c["name"] for c in required if c["name"] in selected_certifications]
        if selected:
            lines.append(f"- Required: {', '.join(selected)}")
    
    if recommended:
        selected = [c["name"] for c in recommended if c["name"] in selected_certifications]
        if selected:
            lines.append(f"- Recommended: {', '.join(selected)}")
    
    if optional:
        selected = [c["name"] for c in optional if c["name"] in selected_certifications]
        if selected:
            lines.append(f"- Optional: {', '.join(selected)}")
    
    lines.append("")
    
    # ===== TARGET AUDIENCE =====
    lines.append("---")
    lines.append("")
    lines.append("**Target Audience:**")
    
    selected_audiences = []
    for aud in audiences:
        is_selected = aud["name"] == selected_audience or selected_audience == "All levels"
        if is_selected:
            selected_audiences.append(aud["name"])
    
    lines.append(f"- {', '.join(selected_audiences)}")
    lines.append("")
    
    # ===== CURRENT SELECTION =====
    lines.append("---")
    lines.append("")
    lines.append("**Current Selection:**")
    lines.append(f"- Topic: {industry}")
    lines.append(f"- Providers: {len(selected_competitors)}")
    lines.append(f"- Certifications: {len(selected_certifications)}")
    lines.append(f"- Audience: {selected_audience}")
    lines.append("")
    
    # ===== ACTION =====
    lines.append("---")
    lines.append("")
    lines.append("**Edit this plan** (tell me in your own words):")
    lines.append("")
    
    # Context-aware examples
    example_provider = competitors[-1]["name"] if competitors else "Provider X"
    example_cert = certifications[0]["name"] if certifications else "Certification Y"
    
    lines.append("**Providers:**")
    lines.append(f'- "Remove {example_provider}"')
    lines.append('- "Add [any provider name]" — even if not listed above')
    lines.append('- "Only use X, Y, Z" — specify exactly which providers')
    lines.append("")
    lines.append("**Certifications:**")
    lines.append(f'- "Remove {example_cert}"')
    lines.append('- "Add [any certification]" — even if not listed above')
    lines.append("")
    lines.append("**Target Audience:**")
    lines.append('- Just tell me who: "Target real starters" or "For senior professionals"')
    lines.append('- I\'ll use your exact words, no mapping.')
    lines.append("")
    lines.append('Type **"Proceed"** or **"Looks good"** when ready.')
    lines.append("")
    
    return "\n".join(lines)


def _format_confirmation_message(plan: ResearchPlan) -> str:
    """Format the confirmation message when user approves the plan."""
    
    industry = plan.get("industry", "your field")
    selected_competitors = plan.get("selected_competitors", [])
    selected_certifications = plan.get("selected_certifications", [])
    selected_audience = plan.get("selected_audience", "All levels")
    
    certs_display = ', '.join(selected_certifications[:3])
    if len(selected_certifications) > 3:
        certs_display += f" (+{len(selected_certifications) - 3} more)"
    
    lines = [
        f"## Plan Confirmed - Starting Research",
        f"",
        f"I'll now conduct a comprehensive analysis of **{industry}** training programs.",
        f"",
        f"**Research scope:**",
        f"- {len(selected_competitors)} training providers",
        f"- {len(selected_certifications)} certifications ({certs_display})",
        f"- Target: {selected_audience}",
        f"",
        f"---",
        f"",
        f"*Searching course catalogs and analyzing curricula...*",
        f"*This typically takes 1-2 minutes.*",
    ]
    
    return "\n".join(lines)


async def _update_plan_from_feedback(plan: ResearchPlan, feedback: str) -> ResearchPlan:
    """
    Update the research plan based on user feedback using Claude.
    
    Supports:
    - Removing items from selection
    - Adding NEW items not in original discovery
    - Changing target audience
    - Focusing on specific items
    """
    
    llm = ChatAnthropic(
        model=settings.anthropic_model,
        api_key=settings.anthropic_api_key,
        temperature=0,
        max_tokens=2000,
    )
    
    current_competitors = plan.get("selected_competitors", [])
    current_certs = plan.get("selected_certifications", [])
    current_audience = plan.get("selected_audience", "All levels")
    
    # Get all discovered items
    all_competitors = [c["name"] for c in plan.get("competitors", [])]
    all_certs = [c["name"] for c in plan.get("certifications", [])]
    all_audiences = [a["name"] for a in plan.get("target_audiences", [])]
    
    industry = plan.get("industry", "")
    
    prompt = f"""You are helping a user EDIT their research plan for "{industry}" training courses.

This is an EDITING MODE - accept the user's exact words, don't map or interpret them.

CURRENT PLAN:
- Selected Providers: {current_competitors}
- Selected Certifications: {current_certs}
- Selected Audience: {current_audience}

DISCOVERED OPTIONS (suggestions only - user can add anything):
- Providers: {all_competitors}
- Certifications: {all_certs}
- Audiences: {all_audiences}

USER'S EDIT REQUEST:
"{feedback}"

EDITING RULES:

1. PROVIDERS:
   - "Remove X" or "Don't include X" → remove X from selected_competitors
   - "Add X" or "Include X" → add X to selected_competitors (even if not discovered)
   - "Only use X, Y" → set selected_competitors to exactly [X, Y]
   - "Keep all" → keep current selection

2. CERTIFICATIONS:
   - Same rules as providers

3. TARGET AUDIENCE:
   - Use the user's EXACT words. Don't map or translate.
   - "Target audience is the real starters" → selected_audience: "the real starters"
   - "For complete beginners" → selected_audience: "complete beginners"  
   - "Professionals and career changers" → selected_audience: "Professionals and career changers"
   - Accept whatever the user says verbatim.

4. ADDING NEW ITEMS:
   - If user adds a provider/cert not in discovered list, include it in new_competitors/new_certifications
   - The user can add ANY provider, cert, or audience - not limited to discovered options

Return ONLY this JSON:
{{
    "selected_competitors": ["exact list user wants"],
    "selected_certifications": ["exact list user wants"],
    "selected_audience": "user's exact words for audience",
    "new_competitors": [{{"name": "Name", "type": "industry_specialist|mooc|bootcamp|trade_school|certification_body", "description": "desc"}}],
    "new_certifications": [{{"name": "Name", "importance": "required|highly_recommended|optional", "issuer": "org", "description": "desc"}}]
}}

If no changes to a field, keep its current value. Only include new_* arrays if user added items not in discovered list."""

    messages = [
        SystemMessage(content="Update research plan based on user feedback. Users can ADD new items not in the original list. Return only valid JSON."),
        HumanMessage(content=prompt),
    ]
    
    try:
        response = await llm.ainvoke(messages)
        result = response.content.strip()
        
        if "```json" in result:
            result = result.split("```json")[1].split("```")[0]
        elif "```" in result:
            result = result.split("```")[1].split("```")[0]
        
        updates = json.loads(result.strip())
        
        # Add new competitors to the plan
        new_competitors = updates.get("new_competitors", [])
        if new_competitors:
            existing_names = {c["name"] for c in plan.get("competitors", [])}
            for new_comp in new_competitors:
                if new_comp.get("name") and new_comp["name"] not in existing_names:
                    plan["competitors"].append({
                        "name": new_comp["name"],
                        "type": new_comp.get("type", "industry_specialist"),
                        "description": new_comp.get("description", f"Added by user: {new_comp['name']}"),
                        "url": new_comp.get("url", ""),
                    })
                    print(f"+ Added new provider: {new_comp['name']}")
        
        # Add new certifications to the plan
        new_certs = updates.get("new_certifications", [])
        if new_certs:
            existing_names = {c["name"] for c in plan.get("certifications", [])}
            for new_cert in new_certs:
                if new_cert.get("name") and new_cert["name"] not in existing_names:
                    plan["certifications"].append({
                        "name": new_cert["name"],
                        "importance": new_cert.get("importance", "recommended"),
                        "issuer": new_cert.get("issuer", "Various"),
                        "description": new_cert.get("description", f"Added by user: {new_cert['name']}"),
                    })
                    print(f"+ Added new certification: {new_cert['name']}")
        
        # Add new audiences to the plan
        new_audiences = updates.get("new_audiences", [])
        if new_audiences:
            existing_names = {a["name"] for a in plan.get("target_audiences", [])}
            for new_aud in new_audiences:
                if new_aud.get("name") and new_aud["name"] not in existing_names:
                    plan["target_audiences"].append({
                        "name": new_aud["name"],
                        "description": new_aud.get("description", f"Added by user: {new_aud['name']}"),
                        "experience_level": new_aud.get("experience_level", "mixed"),
                    })
                    print(f"+ Added new audience: {new_aud['name']}")
        
        # Update selections
        plan["selected_competitors"] = updates.get("selected_competitors", current_competitors)
        plan["selected_certifications"] = updates.get("selected_certifications", current_certs)
        plan["selected_audience"] = updates.get("selected_audience", current_audience)
        
        return plan
        
    except Exception as e:
        print(f"Error updating plan: {e}")
        import traceback
        traceback.print_exc()
        return plan
