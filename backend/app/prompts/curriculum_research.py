"""Conversational Curriculum Research Prompts."""

# Conversational system prompt - understands natural language
CONVERSATIONAL_SYSTEM_PROMPT = """You are a curriculum research assistant that understands natural human language.

KEY PRINCIPLES:
1. Understand conversational language - if user says "move X to optional", "add Y", "remove Z", etc., interpret naturally
2. Be flexible - don't require rigid formats
3. Show ALL data - never truncate or cut off results
4. Use clear bullet point formatting
5. When asked to modify, understand context and intent

You're having a natural conversation, not following a rigid script. Adapt to how the user communicates."""


def get_providers_research_prompt(topic: str) -> str:
    """Step 1: Deep dive into course providers."""
    return f"""# Step 1: Course Providers Research

Topic: **{topic}**

I need you to do a DEEP, COMPREHENSIVE search to find EVERY online course provider that teaches {topic}.

Search thoroughly across:
- MOOCs (Coursera, Udemy, edX, LinkedIn Learning, Skillshare, etc.)
- Trade schools and vocational programs
- Specialized training providers
- Industry-specific academies
- Bootcamps
- Professional certification bodies
- University programs
- Any other relevant sources

For EACH provider you find, format as:

**Provider Name**
- Course Name: [full course name]
- Link: [direct URL]

IMPORTANT:
- List EVERY provider you find - don't limit to 10 or 20
- If there are 50 providers, list all 50
- Show the COMPLETE list with no cutoffs
- Use simple bullet point format
- Include the actual course URL

After listing ALL providers, tell me the total count.

Then ask me naturally:
- Should I add any specific providers?
- Any I should remove or skip?
- Ready to move to certifications?

Be conversational - understand if I say things like "add X", "remove Y and Z", "looks good, continue", etc."""


def get_certifications_research_prompt(topic: str, selected_providers: list = None) -> str:
    """Step 2: Deep dive into certifications."""
    provider_context = ""
    if selected_providers:
        provider_context = f"\n\nFocus on certifications related to these providers:\n" + "\n".join([f"- {p}" for p in selected_providers[:20]])
    
    return f"""# Step 2: Certifications Research

Topic: **{topic}**
{provider_context}

Do a COMPREHENSIVE search for ALL certifications related to {topic}.

Find:
- Industry certifications
- Professional certifications
- Vendor-specific certifications (e.g., from manufacturers)
- Government/regulatory certifications
- Trade organization certifications
- Beginner to advanced level certifications

For EACH certification, format as:

**Certification Name**
- Certifier: [organization that issues it]
- Description: [1-2 sentences explaining what it is and who it's for - make it clear if it's beginner, intermediate, or advanced]

IMPORTANT:
- List EVERY certification you find
- No limits - if there are 30, list all 30
- Show complete list, no cutoffs
- Make descriptions clear about skill level
- Include less common/specialized certifications too

After listing ALL certifications, tell me the total count.

Then ask conversationally:
- Should I add any specific certifications?
- Should any be marked as "Optional" or "Priority"?
- Any to remove?
- Ready to move to target audience?

Understand natural language - "move X, Y, Z to optional", "remove A", etc."""


def get_target_audience_prompt(topic: str) -> str:
    """Step 3: Define target audience."""
    return f"""# Step 3: Target Audience

Topic: **{topic}**

Based on the providers and certifications we've found, suggest target audiences for this curriculum.

Format as bullet points:

**Suggested Target Audiences:**
- [Audience 1]: [1-2 sentence description of who they are and why this curriculum fits them]
- [Audience 2]: [description]
- [Audience 3]: [description]
- [etc.]

Show the FULL description for each - don't cut off text.

After listing options, ask conversationally:
- Which audience(s) should we focus on?
- Should I suggest other audiences to consider?
- Ready to move to publications research?

Be flexible - understand if I say "focus on audience 1 and 3", "add beginners", etc."""


def get_publications_research_prompt(topic: str, selected_providers: list = None, selected_certs: list = None) -> str:
    """Step 4: Deep dive into publications (podcasts, blogs, Reddit, etc.)."""
    context = f"\n\nContext from previous steps:"
    if selected_providers:
        context += f"\nProviders: {', '.join(selected_providers[:10])}"
    if selected_certs:
        context += f"\nCertifications: {', '.join(selected_certs[:10])}"
    
    return f"""# Step 4: Publications & Community Research

Topic: **{topic}**
{context}

Do COMPREHENSIVE research on industry publications, podcasts, blogs, and communities.

Find:
1. **Podcasts** - Top industry podcasts professionals listen to
2. **Blogs** - Leading blogs and websites
3. **Reddit** - Relevant subreddits and popular discussions
4. **Forums** - Industry forums and communities
5. **YouTube Channels** - Educational channels
6. **LinkedIn Groups** - Professional groups
7. **Publications** - Trade magazines, industry publications

For EACH source, format as:

**[Type]: Source Name**
- Link: [URL]
- Audience Size: [subscribers/members/followers if available]
- Relevance: [1 sentence on why this matters for {topic}]

IMPORTANT:
- Find at least 20-30 sources across all categories
- Show COMPLETE list, no cutoffs
- Include audience metrics when available
- Focus on sources employers and professionals actually use

After listing ALL publications, ask conversationally:
- Should I add any specific sources?
- Any to remove?
- Ready to generate curriculum modules?

Understand natural language requests."""


def get_module_synthesis_prompt(
    topic: str,
    providers_data: list,
    certifications_data: list,
    publications_data: list,
    target_audience: str,
) -> str:
    """Final step: Synthesize 100s of unique topics from all research."""
    
    # Limit data shown in prompt to avoid token overflow
    providers_summary = "\n".join([f"- {p.get('name', p)}" for p in providers_data[:30]])
    certs_summary = "\n".join([f"- {c.get('name', c)}" for c in certifications_data[:20]])
    pubs_summary = "\n".join([f"- {p.get('name', p)}" for p in publications_data[:20]])
    
    return f"""# Module Synthesis: Extract All Unique Topics

Topic: **{topic}**
Target Audience: **{target_audience}**

You've done deep research on:
- {len(providers_data)} course providers
- {len(certifications_data)} certifications
- {len(publications_data)} publications/sources

Now, synthesize ALL unique curriculum topics from your research.

**CRITICAL INSTRUCTIONS:**

1. **Extract TOPICS/CONCEPTS, not exact module names**
   - BAD: "015-1 Contractor Soft Skills" (too specific to one course)
   - GOOD: "Contractor Communication Skills", "Business Etiquette", "Customer Service"

2. **Deduplicate rigorously**
   - "Introduction to HVAC" and "HVAC Basics" = same topic
   - Combine similar topics into one clear topic name

3. **Think broadly across ALL your research**
   - What did providers teach?
   - What do certifications cover?
   - What do publications discuss?
   - What are emerging trends?
   - What do communities ask about?

4. **Aim for 100+ unique topics**
   - You researched extensively - there should be MANY topics
   - Break down broad areas into specific topics
   - Include fundamentals AND advanced topics
   - Include practical AND theoretical

5. **Format each topic as:**

**Topic Name**
- Category: [Fundamentals/Technical Skills/Business Skills/Advanced/Troubleshooting/Safety/etc.]
- Description: [2-3 FULL sentences describing what students learn, why it matters, and how it's used]
- Frequency: [How often this appeared across your research - High/Medium/Low]
- Source Types: [Courses/Certifications/Publications - where you found this]

**SHOW ALL TOPICS - NO CUTOFFS**

Target: 100+ topics minimum. If you found 200 unique topics, list all 200.

After listing ALL topics, provide:
- Total count of unique topics
- Breakdown by category
- Any gaps you noticed

Be thorough - this is the final output that determines the curriculum quality."""


def parse_user_feedback(feedback: str, current_list: list, item_type: str = "items") -> dict:
    """
    Parse natural language feedback to understand user intent.
    
    Handles:
    - "add X" / "include Y" / "add Z"
    - "remove X" / "delete Y" / "skip Z"
    - "move X to optional" / "make Y priority"
    - "continue" / "looks good" / "proceed"
    - "go back" / "previous step"
    
    Returns: {
        "action": "add" | "remove" | "modify" | "approve" | "back",
        "items": [...],
        "modifications": {...}
    }
    """
    feedback_lower = feedback.lower()
    
    # Check for navigation
    if any(word in feedback_lower for word in ["back", "previous", "go back", "return"]):
        return {"action": "back"}
    
    # Check for approval
    if any(word in feedback_lower for word in ["continue", "proceed", "looks good", "next", "approved", "yes"]):
        return {"action": "approve"}
    
    # Check for add
    if any(word in feedback_lower for word in ["add", "include", "also"]):
        # Extract what to add (simple approach - can be enhanced)
        return {"action": "add", "items": [feedback]}  # AI will interpret
    
    # Check for remove
    if any(word in feedback_lower for word in ["remove", "delete", "skip", "exclude"]):
        return {"action": "remove", "items": [feedback]}  # AI will interpret
    
    # Check for modifications
    if any(word in feedback_lower for word in ["move", "change", "make", "set"]):
        return {"action": "modify", "modifications": feedback}  # AI will interpret
    
    # Default - treat as conversational feedback
    return {"action": "feedback", "content": feedback}
