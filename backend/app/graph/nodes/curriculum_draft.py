"""Curriculum drafting node - Step 2 of the curriculum builder.

This node handles:
1. Collecting expert-added course data
2. Generating curriculum proposals
3. Refining proposals based on user feedback
4. Generating the final detailed curriculum
"""
import json
import re
from langchain_core.messages import AIMessage, HumanMessage
from langchain_anthropic import ChatAnthropic
from app.graph.state import (
    AgentState, 
    CurriculumDraft, 
    ExpertCourse,
    CurriculumProposal,
)
from app.config import settings
from app.prompts.curriculum import (
    PARSE_EXPERT_INPUT_PROMPT,
    CURRICULUM_PROPOSAL_PROMPT,
    CURRICULUM_REFINEMENT_PROMPT,
    CURRICULUM_GENERATION_PROMPT,
    format_proposal_for_display,
    format_refinement_display,
)


def _is_curriculum_trigger(message: str, has_research: bool) -> bool:
    """
    Detect if a message indicates the user wants to start curriculum drafting.
    
    Triggers:
    - User mentions adding courses/modules
    - User explicitly says to create/draft curriculum
    - Research is complete and user provides expert input
    """
    msg_lower = message.lower().strip()
    
    # Explicit curriculum triggers
    curriculum_triggers = [
        "create curriculum", "draft curriculum", "generate curriculum",
        "build curriculum", "make curriculum", "design curriculum",
        "create the course", "draft the course", "structure the course",
        "i also found", "i have these", "add these courses", "add these modules",
        "here are additional", "from my research", "expert input",
        "include these", "also include", "my sources",
    ]
    
    return any(trigger in msg_lower for trigger in curriculum_triggers) and has_research


def _is_approval(message: str) -> bool:
    """Detect if user is approving the proposal."""
    msg_lower = message.lower().strip()
    
    approval_patterns = [
        r"\bgenerate\b", r"\bapproved?\b", r"\blooks good\b", 
        r"\bgo ahead\b", r"\bproceed\b", r"\bperfect\b",
        r"\bcreate it\b", r"\bdo it\b", r"\bthat'?s? good\b",
        r"\byes\b", r"\bok\b", r"\bokay\b",
    ]
    
    # Must be a short message (not detailed feedback)
    is_short = len(message) < 50
    has_approval = any(re.search(p, msg_lower) for p in approval_patterns)
    
    # Check for feedback indicators (not approval)
    feedback_patterns = [
        r"\badd\b", r"\bremove\b", r"\bchange\b", r"\bsplit\b",
        r"\bmerge\b", r"\bmore\b", r"\bless\b", r"\bfocus\b",
    ]
    has_feedback = any(re.search(p, msg_lower) for p in feedback_patterns)
    
    return is_short and has_approval and not has_feedback


async def _parse_expert_input(user_input: str) -> dict:
    """Parse user's natural language input to extract courses/modules."""
    llm = ChatAnthropic(
        model=settings.anthropic_model,
        api_key=settings.anthropic_api_key,
        temperature=0,
        max_tokens=2000,
    )
    
    prompt = PARSE_EXPERT_INPUT_PROMPT.format(user_input=user_input)
    
    response = await llm.ainvoke([HumanMessage(content=prompt)])
    
    try:
        # Extract JSON from response
        content = response.content
        # Find JSON in response
        json_match = re.search(r'\{[\s\S]*\}', content)
        if json_match:
            return json.loads(json_match.group())
    except (json.JSONDecodeError, AttributeError):
        pass
    
    return {"courses": [], "has_content": False}


async def _generate_proposal(
    industry: str,
    target_audience: str,
    research_data: dict,
    expert_courses: list[ExpertCourse],
) -> CurriculumProposal:
    """Generate curriculum proposal from combined knowledge base."""
    llm = ChatAnthropic(
        model=settings.anthropic_model,
        api_key=settings.anthropic_api_key,
        temperature=0.3,
        max_tokens=8000,  # Increased for detailed descriptions
    )
    
    # Format research data
    courses = research_data.get("courses", [])
    module_inventory = research_data.get("module_inventory", [])
    certifications = research_data.get("certifications", [])
    trending = research_data.get("trending_topics", [])
    
    # Format module inventory with DESCRIPTIONS
    if isinstance(module_inventory, list) and module_inventory:
        module_lines = []
        for m in module_inventory[:60]:  # Include more modules
            if isinstance(m, dict):
                name = m.get("name", str(m))
                desc = m.get("description", "")
                freq = m.get("frequency", "")
                if desc:
                    module_lines.append(f"- **{name}** ({freq}): {desc}")
                else:
                    module_lines.append(f"- {name} ({freq})")
            else:
                module_lines.append(f"- {m}")
        module_inv_str = "\n".join(module_lines)
    else:
        module_inv_str = "No modules found"
    
    print(f"📝 Module inventory for proposal: {len(module_inventory) if isinstance(module_inventory, list) else 0} items")
    
    # Format expert courses
    expert_str = ""
    for ec in expert_courses:
        expert_str += f"\n**{ec.get('source', 'Expert')}:**\n"
        for mod in ec.get("modules", []):
            expert_str += f"- {mod}\n"
        if ec.get("notes"):
            expert_str += f"  Notes: {ec.get('notes')}\n"
    
    if not expert_str:
        expert_str = "No additional courses added by expert."
    
    # Format certifications - get from research plan if not in research_data
    if certifications:
        cert_list = [c.get("name", str(c)) if isinstance(c, dict) else str(c) for c in certifications[:10]]
        certs_str = ", ".join(cert_list)
    else:
        certs_str = "None specified"
    
    prompt = CURRICULUM_PROPOSAL_PROMPT.format(
        industry=industry,
        target_audience=target_audience,
        research_course_count=len(courses),
        research_module_count=len(module_inventory) if isinstance(module_inventory, list) else 0,
        certifications=certs_str,
        trending_topics=", ".join(trending[:10]) if trending else "None identified",
        module_inventory=module_inv_str,
        expert_courses=expert_str,
    )
    
    print(f"📝 Calling Claude for curriculum proposal...")
    response = await llm.ainvoke([HumanMessage(content=prompt)])
    
    try:
        content = response.content
        print(f"📝 Claude response length: {len(content)} chars")
        
        # Find the JSON object in the response
        json_match = re.search(r'\{[\s\S]*\}', content)
        if json_match:
            proposal = json.loads(json_match.group())
            sections = proposal.get("sections", [])
            print(f"📝 Parsed proposal: {len(sections)} sections")
            
            # Verify sections have content
            if sections:
                total_mods = sum(len(s.get("modules", [])) for s in sections)
                print(f"📝 Total modules in proposal: {total_mods}")
                return proposal
            else:
                print(f"⚠️ Proposal has empty sections, raw response preview: {content[:500]}")
        else:
            print(f"⚠️ No JSON found in response, preview: {content[:500]}")
            
    except json.JSONDecodeError as e:
        print(f"⚠️ JSON decode error: {e}")
        print(f"⚠️ Response preview: {content[:500] if content else 'empty'}")
    except Exception as e:
        print(f"⚠️ Error parsing proposal: {e}")
    
    # Fallback proposal - generate a basic structure using module inventory
    print("📝 Using fallback proposal generation")
    return _create_fallback_proposal(industry, target_audience, module_inventory, certifications)


def _create_fallback_proposal(industry: str, target_audience: str, module_inventory: list, certifications: list) -> dict:
    """Create a basic proposal when Claude fails to generate one."""
    sections = []
    
    if isinstance(module_inventory, list) and module_inventory:
        # Group modules by frequency
        vital = []
        important = []
        useful = []
        
        for m in module_inventory:
            if isinstance(m, dict):
                freq = m.get("frequency", "").lower()
                if "vital" in freq:
                    vital.append(m)
                elif "important" in freq:
                    important.append(m)
                else:
                    useful.append(m)
        
        # Create sections
        if vital:
            sections.append({
                "name": "Section 1: Core Fundamentals",
                "overview": "Essential foundational knowledge required for all practitioners.",
                "duration_hours": 8,
                "modules": [
                    {
                        "name": m.get("name", "Unknown"),
                        "description": m.get("description", "Fundamental concepts and skills."),
                        "source": "research",
                        "duration_minutes": 30
                    } for m in vital[:10]
                ]
            })
        
        if important:
            sections.append({
                "name": "Section 2: Technical Skills",
                "overview": "Important technical competencies for professional practice.",
                "duration_hours": 6,
                "modules": [
                    {
                        "name": m.get("name", "Unknown"),
                        "description": m.get("description", "Technical skills and methods."),
                        "source": "research",
                        "duration_minutes": 25
                    } for m in important[:8]
                ]
            })
        
        if useful:
            sections.append({
                "name": "Section 3: Advanced Topics",
                "overview": "Specialized knowledge for career advancement.",
                "duration_hours": 4,
                "modules": [
                    {
                        "name": m.get("name", "Unknown"),
                        "description": m.get("description", "Advanced concepts and applications."),
                        "source": "research",
                        "duration_minutes": 20
                    } for m in useful[:6]
                ]
            })
    
    total_modules = sum(len(s.get("modules", [])) for s in sections)
    total_hours = sum(s.get("duration_hours", 0) for s in sections)
    
    cert_focus = []
    if certifications:
        cert_focus = [c.get("name", str(c)) if isinstance(c, dict) else str(c) for c in certifications[:5]]
    
    return {
        "title": f"{industry} Training Program",
        "summary": f"A comprehensive training program designed for {target_audience}. This program covers fundamental concepts, technical skills, and advanced topics essential for success in {industry}.",
        "target_audience": target_audience,
        "certification_focus": cert_focus,
        "duration_hours": total_hours,
        "total_modules": total_modules,
        "sections": sections,
    }


async def _refine_proposal(
    current_proposal: dict,
    user_feedback: str,
) -> tuple[dict, list[str]]:
    """Refine proposal based on user feedback. Returns (updated_proposal, changes_made)."""
    llm = ChatAnthropic(
        model=settings.anthropic_model,
        api_key=settings.anthropic_api_key,
        temperature=0.3,
        max_tokens=4000,
    )
    
    prompt = CURRICULUM_REFINEMENT_PROMPT.format(
        current_proposal=json.dumps(current_proposal, indent=2),
        user_feedback=user_feedback,
    )
    
    response = await llm.ainvoke([HumanMessage(content=prompt)])
    
    try:
        content = response.content
        json_match = re.search(r'\{[\s\S]*\}', content, re.DOTALL)
        if json_match:
            result = json.loads(json_match.group())
            proposal = result.get("proposal", result)
            changes = result.get("changes_made", ["Updated based on feedback"])
            return proposal, changes
    except (json.JSONDecodeError, AttributeError):
        pass
    
    return current_proposal, ["Unable to process feedback"]


async def _generate_final_curriculum(
    proposal: dict,
    research_data: dict,
    expert_courses: list[ExpertCourse],
) -> str:
    """Generate the final detailed curriculum document."""
    llm = ChatAnthropic(
        model=settings.anthropic_model,
        api_key=settings.anthropic_api_key,
        temperature=0.3,
        max_tokens=8000,
    )
    
    # Format research summary
    courses = research_data.get("courses", [])
    research_summary = f"Analyzed {len(courses)} courses from research.\n\n"
    
    # Add some course details
    for course in courses[:10]:
        name = course.get("name", course.get("title", "Unknown"))
        provider = course.get("provider", "Unknown")
        modules = course.get("curriculum", course.get("modules", []))
        if isinstance(modules, list) and modules:
            mod_list = ", ".join(str(m.get("title", m) if isinstance(m, dict) else m) for m in modules[:5])
            research_summary += f"- **{name}** ({provider}): {mod_list}...\n"
        else:
            research_summary += f"- **{name}** ({provider})\n"
    
    # Format expert courses
    expert_str = ""
    for ec in expert_courses:
        expert_str += f"\n**{ec.get('source', 'Expert')}:** "
        expert_str += ", ".join(ec.get("modules", []))
    
    if not expert_str:
        expert_str = "None"
    
    prompt = CURRICULUM_GENERATION_PROMPT.format(
        approved_proposal=json.dumps(proposal, indent=2),
        research_summary=research_summary,
        expert_courses=expert_str,
        title=proposal.get("title", "Training Program"),
    )
    
    response = await llm.ainvoke([HumanMessage(content=prompt)])
    
    return response.content


async def curriculum_draft_node(state: AgentState) -> dict:
    """
    Curriculum drafting node that:
    1. Collects expert-added course data
    2. Generates curriculum proposals
    3. Refines based on user feedback
    4. Generates final curriculum when approved
    
    Stages:
    - "collecting": Parsing user's expert input
    - "proposing": Generated initial proposal, waiting for feedback
    - "refining": User gave feedback, update proposal
    - "generating": User approved, generate final curriculum
    - "complete": Final curriculum generated
    """
    
    curriculum_draft = state.get("curriculum_draft")
    research_data = state.get("research_data", {})
    research_plan = state.get("research_plan", {})
    
    # Get the latest user message
    last_user_message = ""
    for msg in reversed(state.get("messages", [])):
        if isinstance(msg, HumanMessage):
            last_user_message = msg.content
            break
    
    # Get industry and target audience from research plan
    industry = research_plan.get("industry", state.get("industry", "Unknown"))
    target_audience = research_plan.get("selected_audience", "All levels")
    
    # Determine current stage
    stage = curriculum_draft.get("stage") if curriculum_draft else "collecting"
    
    print(f"📝 CURRICULUM DRAFT NODE: Stage={stage}")
    
    # ===== STAGE 1: COLLECTING EXPERT INPUT =====
    if stage == "collecting" or not curriculum_draft:
        print("📝 Stage: Collecting expert input")
        
        # Parse user's input for courses/modules
        parsed = await _parse_expert_input(last_user_message)
        
        expert_courses = []
        if parsed.get("has_content") and parsed.get("courses"):
            for course in parsed["courses"]:
                expert_courses.append(ExpertCourse(
                    source=course.get("source", "Expert Input"),
                    modules=course.get("modules", []),
                    notes=course.get("notes"),
                ))
        
        # Generate initial proposal
        proposal = await _generate_proposal(
            industry=industry,
            target_audience=target_audience,
            research_data=research_data,
            expert_courses=expert_courses,
        )
        
        # Format for display
        display_text = format_proposal_for_display(proposal)
        
        # Calculate totals
        total_modules = sum(len(s.get("modules", [])) for s in proposal.get("sections", []))
        proposal["total_modules"] = total_modules
        
        return {
            "messages": [AIMessage(content=display_text)],
            "curriculum_draft": CurriculumDraft(
                stage="proposing",
                expert_courses=expert_courses,
                proposal=proposal,
                iteration=1,
                user_feedback=[],
                is_approved=False,
            ),
            "awaiting_curriculum_input": True,
            "next_node": "end",
        }
    
    # ===== STAGE 2: USER APPROVED - GENERATE FINAL =====
    if stage == "proposing" or stage == "refining":
        if _is_approval(last_user_message):
            print("📝 Stage: User approved - generating final curriculum")
            
            proposal = curriculum_draft.get("proposal", {})
            expert_courses = curriculum_draft.get("expert_courses", [])
            
            # Generate final curriculum
            final_curriculum = await _generate_final_curriculum(
                proposal=proposal,
                research_data=research_data,
                expert_courses=expert_courses,
            )
            
            return {
                "messages": [AIMessage(content=final_curriculum)],
                "curriculum_draft": CurriculumDraft(
                    stage="complete",
                    expert_courses=curriculum_draft.get("expert_courses", []),
                    proposal=proposal,
                    iteration=curriculum_draft.get("iteration", 1),
                    user_feedback=curriculum_draft.get("user_feedback", []) + [last_user_message],
                    is_approved=True,
                ),
                "awaiting_curriculum_input": False,
                "next_node": "end",
            }
        
        # ===== STAGE 3: REFINING - User gave feedback =====
        print("📝 Stage: Refining based on user feedback")
        
        current_proposal = curriculum_draft.get("proposal", {})
        iteration = curriculum_draft.get("iteration", 1) + 1
        
        # Refine proposal
        updated_proposal, changes = await _refine_proposal(
            current_proposal=current_proposal,
            user_feedback=last_user_message,
        )
        
        # Recalculate totals
        total_modules = sum(len(s.get("modules", [])) for s in updated_proposal.get("sections", []))
        updated_proposal["total_modules"] = total_modules
        
        # Format display with changes
        display_text = format_refinement_display(updated_proposal, changes, iteration)
        
        return {
            "messages": [AIMessage(content=display_text)],
            "curriculum_draft": CurriculumDraft(
                stage="refining",
                expert_courses=curriculum_draft.get("expert_courses", []),
                proposal=updated_proposal,
                iteration=iteration,
                user_feedback=curriculum_draft.get("user_feedback", []) + [last_user_message],
                is_approved=False,
            ),
            "awaiting_curriculum_input": True,
            "next_node": "end",
        }
    
    # Default: return current state
    return {
        "awaiting_curriculum_input": True,
        "next_node": "end",
    }


