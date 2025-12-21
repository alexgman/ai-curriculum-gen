"""Prompts for curriculum drafting (Step 2)."""

# ===== PARSE EXPERT INPUT PROMPT =====
# Extract courses/modules from user's natural language input

PARSE_EXPERT_INPUT_PROMPT = """You are extracting course and module information from user input.

The user is adding additional courses/modules that the automated research didn't find.
Parse their natural language into structured data.

USER INPUT:
{user_input}

Extract into this JSON format:
{{
    "courses": [
        {{
            "source": "Provider or source name",
            "modules": ["Module 1", "Module 2", "Module 3"],
            "notes": "Any additional context the user provided"
        }}
    ],
    "has_content": true or false (whether user provided actual course data)
}}

Rules:
- Extract the source/provider name if mentioned
- List individual modules/topics as separate items
- If user just gives a list of topics without a source, use "User Expert Knowledge" as source
- Set has_content to false if user didn't provide any actual course/module data
- Be generous in interpretation - any topics or lessons count as modules

Return ONLY valid JSON, no other text."""


# ===== PROPOSAL PROMPT =====
# Generate initial curriculum proposal from combined knowledge base

CURRICULUM_PROPOSAL_PROMPT = """You are a professional curriculum designer creating a training program structure.

INDUSTRY/TOPIC: {industry}
TARGET AUDIENCE: {target_audience}

KNOWLEDGE BASE FROM RESEARCH (Auto-discovered):
- Total courses analyzed: {research_course_count}
- Total modules found: {research_module_count}
- Certifications: {certifications}
- Trending topics: {trending_topics}

Module inventory from research:
{module_inventory}

KNOWLEDGE BASE FROM EXPERT (User-added):
{expert_courses}

Create a comprehensive curriculum proposal with DETAILED module descriptions.

REQUIRED OUTPUT FORMAT:

1. **Title**: A compelling, professional course title
2. **Summary**: 2-3 paragraph overview of what students will learn
3. **Target Audience**: Who this course is for  
4. **Certification Focus**: Key certifications this prepares for
5. **Duration**: Estimated total hours
6. **Sections**: 4-8 logical sections
7. **Modules**: Each section should have 4-12 modules WITH DETAILED DESCRIPTIONS

CRITICAL: Each module MUST have a detailed description (2-4 sentences) explaining:
- What the module covers
- Key skills or knowledge students will gain
- Why it's important in this field

Output as JSON:
{{
    "title": "Course Title",
    "summary": "Program overview...",
    "target_audience": "Who this is for",
    "certification_focus": ["Cert 1", "Cert 2"],
    "duration_hours": 20,
    "total_modules": 35,
    "sections": [
        {{
            "name": "Section 1: Foundations",
            "overview": "Introduction to core concepts...",
            "duration_hours": 3,
            "modules": [
                {{
                    "name": "Introduction to X",
                    "description": "Comprehensive introduction to X covering the fundamental principles and practical applications. Students will learn the core concepts that form the foundation for all advanced topics. Essential for understanding how X works in real-world scenarios.",
                    "source": "research",
                    "duration_minutes": 30
                }},
                {{
                    "name": "Understanding Y", 
                    "description": "Detailed study of Y including theoretical foundations and hands-on techniques. Covers common challenges, best practices, and troubleshooting methods. Students master both the 'how' and 'why' of Y operations.",
                    "source": "expert",
                    "duration_minutes": 25
                }}
            ]
        }}
    ]
}}

IMPORTANT RULES:
1. EVERY module MUST have a "description" field with 2-4 detailed sentences
2. Descriptions should be specific to the industry/topic, not generic
3. Use knowledge from the research module inventory to write accurate descriptions
4. Mark each module's source accurately ("research" or "expert")
5. Organize logically from foundational to advanced
6. Ensure certification prep modules are included if relevant
7. Total duration should be realistic (15-40 hours typical)

Return ONLY valid JSON."""


# ===== REFINEMENT PROMPT =====
# Update proposal based on user feedback

CURRICULUM_REFINEMENT_PROMPT = """You are updating a curriculum proposal based on user feedback.

CURRENT PROPOSAL:
{current_proposal}

USER'S FEEDBACK:
"{user_feedback}"

Update the proposal according to the user's instructions. Common requests:
- Add/remove sections
- Add/remove modules  
- Split or merge sections
- Change title or summary
- Adjust duration
- Change focus or emphasis
- Reorder content

CRITICAL: When adding new modules, ALWAYS include a detailed "description" field (2-4 sentences).
Preserve existing module descriptions unless specifically asked to change them.

Return the COMPLETE updated proposal as JSON with FULL module descriptions:
{{
    "title": "...",
    "summary": "...",
    "target_audience": "...",
    "certification_focus": [...],
    "duration_hours": X,
    "total_modules": X,
    "sections": [
        {{
            "name": "Section Name",
            "overview": "Section overview...",
            "duration_hours": X,
            "modules": [
                {{
                    "name": "Module Name",
                    "description": "Detailed 2-4 sentence description of what this module covers...",
                    "source": "research",
                    "duration_minutes": 30
                }}
            ]
        }}
    ]
}}

Also include a "changes_made" array describing what you changed:
{{
    "proposal": {{ ... the full updated proposal ... }},
    "changes_made": [
        "Changed title from X to Y",
        "Added new section: Business Skills",
        "Removed module: Advanced X from Section 2"
    ]
}}

Return ONLY valid JSON."""


# ===== GENERATION PROMPT =====
# Generate the final detailed curriculum document

CURRICULUM_GENERATION_PROMPT = """You are generating a comprehensive, professional curriculum document.

APPROVED PROPOSAL:
{approved_proposal}

KNOWLEDGE BASE - Research Data:
{research_summary}

KNOWLEDGE BASE - Expert Added:
{expert_courses}

Generate the FULL curriculum document with detailed content for EVERY module.

Format:

# [Course Title]
## Complete Training Program

### Program Overview
(Write 2-3 paragraphs summarizing what students will learn, the approach, and outcomes)

### Program Details
| Attribute | Value |
|-----------|-------|
| Duration | X hours |
| Modules | X |
| Sections | X |
| Target Audience | X |
| Certification Prep | X |

---

## Section 1: [Name]
*X modules | X hours | Prerequisites: None*

[Brief section overview paragraph]

### 1.1 [Module Name]
**Duration:** X min

[2-3 sentence description of what this module covers]

**Learning Objectives:**
- Objective 1
- Objective 2
- Objective 3

**Prerequisites:** None / Module 1.X

---

### 1.2 [Next Module Name]
**Duration:** X min

[Description...]

**Learning Objectives:**
- ...

---

[Continue for ALL modules in ALL sections]

---

## Section 2: [Name]
*X modules | X hours | Prerequisites: Section 1*

[Continue same format...]

---

## Appendix: Resources & Next Steps
- Key certifications to pursue
- Recommended tools/equipment
- Further learning paths

---

CRITICAL RULES:
1. Include EVERY module from the approved proposal
2. Each module needs: duration, description, 3-5 learning objectives
3. Use knowledge from research data to write accurate descriptions
4. Incorporate expert-added modules naturally
5. Maintain logical flow and prerequisites
6. Professional, consistent formatting throughout
7. Total word count: 3000-6000 words for complete curriculum"""


# ===== FORMATTING HELPERS =====

def format_proposal_for_display(proposal: dict) -> str:
    """Format a curriculum proposal for user display in chat with detailed module descriptions."""
    lines = []
    
    title = proposal.get("title", "Untitled Curriculum")
    summary = proposal.get("summary", "")
    target = proposal.get("target_audience", "General audience")
    certs = proposal.get("certification_focus", [])
    duration = proposal.get("duration_hours", 0)
    total_modules = proposal.get("total_modules", 0)
    sections = proposal.get("sections", [])
    
    lines.append(f"## Proposed Curriculum: {title}")
    lines.append("")
    lines.append("### Program Overview")
    lines.append(summary)
    lines.append("")
    lines.append("### Summary")
    lines.append("| Attribute | Value |")
    lines.append("|-----------|-------|")
    lines.append(f"| Duration | {duration} hours |")
    lines.append(f"| Modules | {total_modules} |")
    lines.append(f"| Sections | {len(sections)} |")
    lines.append(f"| Target Audience | {target} |")
    if certs:
        lines.append(f"| Certification Focus | {', '.join(certs)} |")
    lines.append("")
    lines.append("---")
    lines.append("")
    
    # Detailed module listing with descriptions
    for i, section in enumerate(sections, 1):
        sec_name = section.get("name", f"Section {i}")
        sec_duration = section.get("duration_hours", 0)
        sec_overview = section.get("overview", section.get("description", ""))
        modules = section.get("modules", [])
        
        lines.append(f"## {sec_name}")
        lines.append(f"*{len(modules)} modules | {sec_duration} hours*")
        lines.append("")
        
        if sec_overview:
            lines.append(sec_overview)
            lines.append("")
        
        # Each module with description
        for j, m in enumerate(modules, 1):
            mod_name = m.get('name', 'Unnamed')
            mod_desc = m.get('description', '')
            mod_duration = m.get('duration_minutes', 30)
            source = m.get('source', 'research')
            source_marker = " *(expert)*" if source == "expert" else ""
            
            lines.append(f"**{i}.{j} — {mod_name}**{source_marker}")
            
            if mod_desc:
                lines.append(f"{mod_desc}")
            else:
                lines.append(f"*Duration: {mod_duration} min*")
            
            lines.append("")
        
        lines.append("---")
        lines.append("")
    
    lines.append("### What would you like to change?")
    lines.append("")
    lines.append("You can adjust:")
    lines.append("- **Title/Overview:** \"Change the title to...\" or \"Make summary more...\"")
    lines.append("- **Duration/Scope:** \"Make it shorter\" or \"Expand to 25 hours\"")
    lines.append("- **Sections:** \"Add section on...\" or \"Remove section X\" or \"Split/merge...\"")
    lines.append("- **Modules:** \"Add module on X\" or \"Remove advanced topics\"")
    lines.append("- **Focus:** \"Emphasize X more\" or \"Less theory, more hands-on\"")
    lines.append("")
    lines.append("Tell me what to change, or say **\"Generate\"** when the structure looks good.")
    
    return "\n".join(lines)


def format_refinement_display(proposal: dict, changes: list, iteration: int) -> str:
    """Format an updated proposal showing what changed with detailed module descriptions."""
    lines = []
    
    lines.append(f"## Updated Curriculum (v{iteration})")
    lines.append("")
    lines.append("### Changes Made")
    for change in changes:
        lines.append(f"- {change}")
    lines.append("")
    lines.append("---")
    lines.append("")
    
    # Add the full proposal display with module descriptions
    proposal_display = format_proposal_for_display(proposal)
    # Replace the title to show it's updated
    proposal_display = proposal_display.replace("## Proposed Curriculum:", "### Current Structure:")
    lines.append(proposal_display)
    
    return "\n".join(lines)

