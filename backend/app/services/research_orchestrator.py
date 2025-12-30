"""Curriculum Research Orchestrator - 3-Phase Deep Research Flow.

Manages the conversational research flow:
1. Clarifying questions (natural, like claude.ai)
2. Phase 1: Competitive Research (courses, pricing, lessons)
3. Phase 2: Industry Expertise (podcasts, blogs, trends)
4. Phase 3: Consumer Sentiment (Reddit, forums, FAQs)
5. Final Synthesis (comprehensive curriculum)
"""
import asyncio
from enum import Enum
from typing import AsyncGenerator, Dict, Any, List, Optional
from dataclasses import dataclass, field

from app.services.mcp_research import MCPDeepResearchService
from app.config import settings


class ResearchPhase(Enum):
    """Research phases."""
    INITIAL = "initial"
    CLARIFICATION = "clarification"
    COMPETITIVE = "competitive"
    EXPERTISE = "expertise"
    SENTIMENT = "sentiment"
    SYNTHESIS = "synthesis"
    COMPLETE = "complete"


@dataclass
class ResearchState:
    """State for the research process."""
    topic: str = ""
    phase: ResearchPhase = ResearchPhase.INITIAL
    clarifications: Dict[str, Any] = field(default_factory=dict)
    findings: Dict[str, str] = field(default_factory=dict)
    history: List[str] = field(default_factory=list)
    awaiting_feedback: bool = False


class CurriculumResearchOrchestrator:
    """Orchestrates the 3-phase curriculum research process."""
    
    def __init__(self):
        self.research_service = MCPDeepResearchService()
        self.state = {
            "topic": "",
            "phase": ResearchPhase.INITIAL,
            "clarifications": {},
            "findings": {},
            "history": [],
            "awaiting_feedback": False,
        }
    
    def get_state(self) -> Dict[str, Any]:
        """Get serializable state."""
        return {
            "topic": self.state["topic"],
            "phase": self.state["phase"].value if isinstance(self.state["phase"], ResearchPhase) else self.state["phase"],
            "clarifications": self.state["clarifications"],
            "findings": self.state["findings"],
            "history": self.state["history"],
            "awaiting_feedback": self.state["awaiting_feedback"],
        }
    
    def restore_state(self, saved_state: Dict[str, Any]):
        """Restore state from saved data."""
        if saved_state:
            self.state["topic"] = saved_state.get("topic", "")
            phase_value = saved_state.get("phase", "initial")
            if isinstance(phase_value, str):
                try:
                    self.state["phase"] = ResearchPhase(phase_value)
                except ValueError:
                    self.state["phase"] = ResearchPhase.INITIAL
            self.state["clarifications"] = saved_state.get("clarifications", {})
            self.state["findings"] = saved_state.get("findings", {})
            self.state["history"] = saved_state.get("history", [])
            self.state["awaiting_feedback"] = saved_state.get("awaiting_feedback", False)
    
    async def process_message(self, message: str) -> AsyncGenerator[Dict[str, Any], None]:
        """Process user message based on current phase."""
        phase = self.state["phase"]
        
        if phase == ResearchPhase.INITIAL:
            # New topic - ask clarifying questions
            self.state["topic"] = message
            self.state["phase"] = ResearchPhase.CLARIFICATION
            async for event in self._run_clarifying_questions_step():
                yield event
        
        elif phase == ResearchPhase.CLARIFICATION:
            # Got clarification answers - start competitive research
            self.state["clarifications"]["user_context"] = message
            self.state["phase"] = ResearchPhase.COMPETITIVE
            yield {"type": "status", "content": "Starting **Phase 1: Competitive Research**..."}
            async for event in self._run_competitive_research():
                yield event
        
        elif phase == ResearchPhase.COMPETITIVE:
            # Got feedback on competitive research
            async for event in self._handle_competitive_feedback(message):
                yield event
        
        elif phase == ResearchPhase.EXPERTISE:
            # Got feedback on expertise research
            async for event in self._handle_expertise_feedback(message):
                yield event
        
        elif phase == ResearchPhase.SENTIMENT:
            # Got feedback on sentiment research
            async for event in self._handle_sentiment_feedback(message):
                yield event
        
        elif phase == ResearchPhase.SYNTHESIS:
            # Final synthesis feedback
            async for event in self._handle_synthesis_feedback(message):
                yield event
        
        else:
            # Default - start fresh
            self.state["topic"] = message
            self.state["phase"] = ResearchPhase.CLARIFICATION
            async for event in self._run_clarifying_questions_step():
                yield event
    
    async def _run_clarifying_questions_step(self) -> AsyncGenerator[Dict[str, Any], None]:
        """Generate natural clarifying questions like claude.ai."""
        topic = self.state["topic"]
        
        yield {"type": "status", "content": "Understanding your curriculum needs..."}
        
        prompt = f"""The user wants to create a curriculum for: {topic}

Ask 2-4 brief, natural clarifying questions to understand their needs better. Be conversational like a helpful colleague would ask.

Consider asking about:
- Target audience (beginners vs experienced)
- Geographic focus (for certifications/regulations)
- Specific focus areas (residential, commercial, specialized)
- Program duration preferences

Keep it brief and friendly - like claude.ai would ask. Don't be overly formal."""

        clarification_text = ""
        
        async for event in self.research_service.deep_research(
            prompt=prompt,
            system="You are a helpful curriculum development assistant. Ask brief, natural clarifying questions.",
            max_searches=1,
            enable_thinking=True,
            thinking_budget=4000,
            max_tokens=8000,
        ):
            event_type = event.get("type", "")
            
            if event_type == "thinking":
                yield {"type": "thinking", "content": event.get("content", "")}
            elif event_type == "text":
                chunk = event.get("content", "")
                clarification_text += chunk
                yield {"type": "text_stream", "content": chunk}
        
        self.state["clarifications"]["questions"] = clarification_text
        
        yield {
            "type": "clarification_needed",
            "content": clarification_text,
            "phase": "clarification",
        }
    
    async def _run_competitive_research(self) -> AsyncGenerator[Dict[str, Any], None]:
        """Phase 1: Competitive Research - courses, pricing, lessons."""
        self.state["phase"] = ResearchPhase.COMPETITIVE
        
        topic = self.state["topic"]
        context = self.state["clarifications"].get("user_context", "")
        
        yield {
            "type": "phase_start",
            "phase": "competitive",
            "phase_number": 1,
            "total_phases": 3,
            "title": "Competitive Research",
            "description": "Finding online courses, pricing, certifications, and lesson lists",
        }
        
        prompt = f"""# COMPETITIVE MARKET RESEARCH: {topic}

User Context: {context}

## YOUR TASK:

Assemble a **COMPREHENSIVE list of ALL online courses or online schools** that teach courses or materials relevant to {topic}.

## FOR EACH COURSE, CAPTURE:

1. **URL/Link** - direct link to the course page
2. **Pricing** - exact cost, payment plans if available
3. **Length of course** - duration in hours/weeks/months
4. **Certifications** - what credentials you get upon completion
5. **Comprehensive lesson list** - ALL lessons taught with 2-3 sentence descriptions

## RANKING REQUIREMENTS:

**Rank all courses by POPULARITY using these metrics:**
- Total Google reviews (search "[course name] reviews")
- SEO ranking / search visibility
- Commercial sales size / enrollment numbers if available
- Industry recognition and accreditations

**Where to find ranking data:**
- Google Trends for search interest
- Course platform review counts (Udemy, Coursera ratings)
- BBB ratings and accreditation status
- Indeed/Glassdoor reviews for career schools
- Social media following / engagement

## SOURCES TO SEARCH (Be exhaustive):

1. **Major Learning Platforms:** Udemy, Coursera, LinkedIn Learning, edX, Skillshare, Pluralsight
2. **Career/Vocational Schools:** Penn Foster, U.S. Career Institute, Ashworth College, CareerStep
3. **Community Colleges:** Online programs via ed2go, local CC distance learning
4. **Industry-Specific Training:** Professional associations, certification bodies, manufacturer training
5. **Mobile/App Platforms:** SkillCat, apps specific to the industry
6. **YouTube/Free Resources:** Structured free courses with curriculum

## OUTPUT FORMAT:

---

### COURSE 1: [Course Name]

| Field | Details |
|-------|---------|
| **Provider** | [Platform/School] |
| **URL** | [Direct link to course page] |
| **Price** | $[amount] |
| **Duration** | [length] |
| **Certifications** | [What you earn] |
| **Popularity Metrics** | [Reviews: X, Rating: X/5, Enrollment: X] |

**Complete Lesson List:**

1. **[Lesson Title]** — [2-3 sentences: What students learn, skills developed, practical applications]
2. **[Lesson Title]** — [2-3 sentences describing content and outcomes]
3. **[Lesson Title]** — [Continue for ALL lessons]
... (list EVERY lesson - do NOT stop at 5)

---

### COURSE 2: [Next Course]
(Repeat same format)

---

## MINIMUM REQUIREMENTS:

⚠️ **YOU MUST FIND AND DOCUMENT AT LEAST 20-30 COURSES**

- If there are 20+ courses available, list the TOP 20 ranked by popularity
- If fewer exist, list ALL available courses
- Each course MUST have complete lesson list (not truncated)
- Each lesson MUST have 2-3 sentence description

---

## FINAL SUMMARY (After listing all courses):

### Top 20 Courses Ranked by Popularity

| Rank | Course Name | Provider | URL | Price | Reviews/Rating |
|------|-------------|----------|-----|-------|----------------|
| 1 | [Name] | [Provider] | [Link] | $X | X reviews, X/5 |
| 2 | [Name] | [Provider] | [Link] | $X | X reviews, X/5 |
... (continue to 20)

### Exhaustive Lesson Inventory

Rank ALL unique lessons by how frequently they appear across courses:

| Rank | Lesson Topic | Appears In | Frequency |
|------|--------------|------------|-----------|
| 1 | [Topic] | X out of Y courses | X% |
| 2 | [Topic] | X out of Y courses | X% |
... (list ALL unique lessons found)

### Price Analysis

| Tier | Price Range | Example Courses |
|------|-------------|-----------------|
| Budget | $X - $X | [names] |
| Mid-range | $X - $X | [names] |
| Premium | $X - $X | [names] |

Now begin searching and documenting courses:"""

        findings_text = ""
        search_count = 0
        
        print(f"🔍 Starting competitive research for: {topic}")
        
        async for event in self.research_service.deep_research(
            prompt=prompt,
            system="""You are a professional curriculum market researcher. Your task is to find and document ALL available online courses comprehensively.

CRITICAL REQUIREMENTS:
1. Find AT LEAST 20-30 courses - search multiple platforms thoroughly
2. For EACH course, list the COMPLETE curriculum - every single lesson
3. Each lesson needs 2-3 sentence description of what students learn
4. Include real pricing, reviews, ratings, and enrollment data
5. Rank courses by popularity using Google reviews, ratings, enrollment numbers
6. After listing all courses, create the summary tables showing:
   - Top 20 courses ranked by popularity
   - ALL lessons ranked by frequency across courses
   - Price analysis by tier

DO NOT truncate lesson lists. DO NOT stop at 10 courses. Be EXHAUSTIVE.

Output format: Use clean markdown tables for metrics, numbered lists for lessons.""",
            max_searches=50,
            enable_thinking=True,
            thinking_budget=15000,
            max_tokens=60000,
        ):
            event_type = event.get("type", "")
            
            if event_type == "thinking":
                yield {"type": "thinking", "content": event.get("content", "")}
            elif event_type == "text":
                chunk = event.get("content", "")
                findings_text += chunk
                if len(findings_text) % 1000 < len(chunk):
                    print(f"📝 Research text accumulated: {len(findings_text)} chars")
                yield {"type": "text_stream", "content": chunk}
            elif event_type == "tool_start":
                search_count += 1
                print(f"🔎 Search #{search_count}")
                yield {"type": "search_status", "search_number": search_count}
            elif event_type == "complete":
                print(f"✅ Research complete: {len(findings_text)} chars, {event.get('total_searches', search_count)} searches")
                yield {"type": "search_complete", "total_searches": event.get("total_searches", search_count)}
        
        print(f"📊 Final findings length: {len(findings_text)} chars")
        self.state["findings"]["competitive"] = findings_text
        
        yield {
            "type": "phase_complete",
            "phase": "competitive",
            "findings": findings_text,
            "search_count": search_count,
        }
        
        yield {
            "type": "feedback_request",
            "content": """**Phase 1 Complete: Competitive Research**

Review the courses and lessons above. You can:
- Ask me to dig deeper into specific courses
- Add courses you know about that I missed
- Tell me to continue to Phase 2 (Industry Expertise research)

Just respond naturally - what would you like to do?""",
            "phase": "competitive",
            "awaiting_response": True,
        }
    
    async def _handle_competitive_feedback(self, feedback: str) -> AsyncGenerator[Dict[str, Any], None]:
        """Handle feedback on competitive research."""
        lower = feedback.lower().strip()
        
        continue_signals = ["continue", "next", "proceed", "looks good", "move on", "phase 2", 
                          "expertise", "go ahead", "ok", "okay", "yes", "good", "great", "perfect"]
        
        if any(signal in lower for signal in continue_signals):
            self.state["history"].append(ResearchPhase.COMPETITIVE.value)
            yield {"type": "status", "content": "Moving to **Phase 2: Recent Industry Expertise**..."}
            async for event in self._run_expertise_research():
                yield event
        else:
            async for event in self._refine_research("competitive", feedback):
                yield event
    
    async def _run_expertise_research(self) -> AsyncGenerator[Dict[str, Any], None]:
        """Phase 2: Recent Expertise - podcasts, blogs, industry trends."""
        self.state["phase"] = ResearchPhase.EXPERTISE
        
        topic = self.state["topic"]
        context = self.state["clarifications"].get("user_context", "")
        
        yield {
            "type": "phase_start",
            "phase": "expertise",
            "phase_number": 2,
            "total_phases": 3,
            "title": "Recent Industry Expertise",
            "description": "Finding podcasts, blogs, publications, and emerging trends",
        }
        
        prompt = f"""# RECENT INDUSTRY EXPERTISE RESEARCH: {topic}

User Context: {context}

## YOUR TASK:

**STEP 1: Compile an EXHAUSTIVE list of the most popular/highest-ranking industry media**

Find and rank by viewer/reader counts or how often they are cited as industry-leading:

### A. PODCASTS (Find 10+ and rank top 5)

| Rank | Podcast Name | Host | URL/Link | Listener Count/Reviews | Episodes |
|------|--------------|------|----------|------------------------|----------|
| 1 | [Name] | [Host] | [Link to podcast] | [metrics] | [count] |
| 2 | [Name] | [Host] | [Link] | [metrics] | [count] |
| 3 | [Name] | [Host] | [Link] | [metrics] | [count] |
| 4 | [Name] | [Host] | [Link] | [metrics] | [count] |
| 5 | [Name] | [Host] | [Link] | [metrics] | [count] |

*Focus on podcasts that prospective EMPLOYERS in this industry listen to*

### B. BLOGS (Find 10+ and rank top 5)

| Rank | Blog/Website | URL | Author/Organization | Monthly Readers/DA | Update Frequency |
|------|--------------|-----|---------------------|-------------------|------------------|
| 1 | [Name] | [Link] | [Author] | [metrics] | [frequency] |
| 2 | [Name] | [Link] | [Author] | [metrics] | [frequency] |
| 3 | [Name] | [Link] | [Author] | [metrics] | [frequency] |
| 4 | [Name] | [Link] | [Author] | [metrics] | [frequency] |
| 5 | [Name] | [Link] | [Author] | [metrics] | [frequency] |

### C. TRADE PUBLICATIONS (Find 10+ and rank top 5)

| Rank | Publication | URL | Publisher | Circulation/Citations | Frequency |
|------|-------------|-----|-----------|----------------------|-----------|
| 1 | [Name] | [Link] | [Publisher] | [metrics] | [frequency] |
| 2 | [Name] | [Link] | [Publisher] | [metrics] | [frequency] |
| 3 | [Name] | [Link] | [Publisher] | [metrics] | [frequency] |
| 4 | [Name] | [Link] | [Publisher] | [metrics] | [frequency] |
| 5 | [Name] | [Link] | [Publisher] | [metrics] | [frequency] |

---

## STEP 2: Extract Recent Developments (Last 3 Years)

**For the TOP 5 in EACH subcategory (podcasts, blogs, publications)**, go through their content from 2022-2025 and extract:

- New technologies
- New information/developments
- Innovations
- Regulatory changes
- Industry shifts

---

## STEP 3: Convert to Potential Lessons (AT LEAST 20+)

Rank each topic by:
1. How RELEVANT it is to getting employed
2. How OFTEN it comes up across sources

### OUTPUT FORMAT FOR EACH LESSON:

---

### LESSON [#]: [Topic Title]

**What to Teach (3 sentences):**
[Detailed description of what should be taught, specific skills/knowledge, and practical applications]

**Frequency:** [How often this topic appeared across sources - High/Medium/Low with count]

**Source:** [Which podcast/blog/publication discussed this, with specific episode/article if possible]

**Why Include in Curriculum:**
[Explain your reasoning for why this should be in the curriculum - how it helps students get employed, why it's relevant to the industry, what makes it timely/important]

---

## MINIMUM REQUIREMENTS:

⚠️ **YOU MUST PRODUCE AT LEAST 20+ LESSON RECOMMENDATIONS**

Each lesson must have:
- 3 sentence description of what to teach
- Source citation (where you found this)
- Reasoning for why it belongs in curriculum
- Relevance ranking

---

Now search for industry podcasts, blogs, and publications, then extract recent trends:"""

        findings_text = ""
        search_count = 0
        
        async for event in self.research_service.deep_research(
            prompt=prompt,
            system="""You are an industry research expert compiling media sources and extracting curriculum-relevant trends.

CRITICAL REQUIREMENTS:
1. Find and rank AT LEAST 10 sources in EACH category (podcasts, blogs, publications)
2. For the TOP 5 in each category, research their content from the last 3 years
3. Extract ALL new technologies, developments, innovations mentioned
4. Convert findings into AT LEAST 20+ potential lessons
5. Each lesson must have:
   - 3 sentence description of what to teach
   - Source citation (specific podcast/blog/publication)
   - Reasoning for curriculum inclusion
   - Employment relevance explanation

Focus on what EMPLOYERS in this industry care about. The goal is to identify what makes graduates employable.""",
            max_searches=40,
            enable_thinking=True,
            thinking_budget=15000,
            max_tokens=50000,
        ):
            event_type = event.get("type", "")
            
            if event_type == "thinking":
                yield {"type": "thinking", "content": event.get("content", "")}
            elif event_type == "text":
                chunk = event.get("content", "")
                findings_text += chunk
                yield {"type": "text_stream", "content": chunk}
            elif event_type == "tool_start":
                search_count += 1
                yield {"type": "search_status", "search_number": search_count}
            elif event_type == "complete":
                yield {"type": "search_complete", "total_searches": event.get("total_searches", search_count)}
        
        self.state["findings"]["expertise"] = findings_text
        
        yield {
            "type": "phase_complete",
            "phase": "expertise",
            "findings": findings_text,
            "search_count": search_count,
        }
        
        yield {
            "type": "feedback_request",
            "content": """**Phase 2 Complete: Industry Expertise**

Review the podcasts, blogs, and emerging topics above. You can:
- Ask me to explore specific trends deeper
- Add sources you know about
- Tell me to continue to Phase 3 (Consumer Sentiment research)

What would you like to do?""",
            "phase": "expertise",
            "awaiting_response": True,
        }
    
    async def _handle_expertise_feedback(self, feedback: str) -> AsyncGenerator[Dict[str, Any], None]:
        """Handle feedback on expertise research."""
        lower = feedback.lower().strip()
        
        continue_signals = ["continue", "next", "proceed", "looks good", "move on", "phase 3",
                          "sentiment", "go ahead", "ok", "okay", "yes", "good", "great", "perfect"]
        
        if any(signal in lower for signal in continue_signals):
            self.state["history"].append(ResearchPhase.EXPERTISE.value)
            yield {"type": "status", "content": "Moving to **Phase 3: Consumer Sentiment**..."}
            async for event in self._run_sentiment_research():
                yield event
        else:
            async for event in self._refine_research("expertise", feedback):
                yield event
    
    async def _run_sentiment_research(self) -> AsyncGenerator[Dict[str, Any], None]:
        """Phase 3: Consumer Sentiment - Reddit, forums, FAQs."""
        self.state["phase"] = ResearchPhase.SENTIMENT
        
        topic = self.state["topic"]
        context = self.state["clarifications"].get("user_context", "")
        
        yield {
            "type": "phase_start",
            "phase": "sentiment",
            "phase_number": 3,
            "total_phases": 3,
            "title": "Consumer Sentiment",
            "description": "Analyzing Reddit, Quora, forums for common questions and pain points",
        }
        
        prompt = f"""# CONSUMER SENTIMENT RESEARCH: {topic}

User Context: {context}

## YOUR TASK:

For any online community tied to {topic}, compile a **COMPREHENSIVE list** of:

1. **Most popular posts** - highest upvoted/engaged discussions
2. **Most frequently asked questions** - what beginners always ask
3. **Topics people LOVE discussing** - what generates the most engagement
4. **Topics people feel FRUSTRATED not understanding** - pain points and struggles
5. **Most recent conversation topics** - new developments being discussed

## PLATFORMS TO SEARCH:

- **Reddit:** Find ALL relevant subreddits (r/[topic], r/[specialty], etc.)
- **Quora:** Search for career questions, how-to questions, industry questions
- **Industry-specific forums:** Identify and search forums specific to this field
- **Stack Exchange:** If applicable to this topic
- **Facebook groups:** Professional groups in this field
- **LinkedIn discussions:** Industry professional conversations
- **Discord servers:** If relevant professional communities exist

---

## OUTPUT FORMAT:

### PART 1: Communities Found

| Platform | Community Name | Members/Size | Activity Level | Focus Area |
|----------|---------------|--------------|----------------|------------|
| Reddit | r/[name] | X members | [Active/Moderate] | [What they discuss] |
| Forum | [name] | X members | [Activity] | [Focus] |
| ... | ... | ... | ... | ... |

---

### PART 2: Popular Topics & Questions

For each topic, provide:

---

#### TOPIC [#]: [Topic Title]

**What it is:** [3 sentence description of what this topic covers, what must be taught, and what students need to understand]

**Popularity Metric:** [Upvotes/Comments/Views - be specific with numbers]

**Platform(s):** [Where this was found - Reddit r/X, Quora, Forum name]

**Sample Posts/Questions:**
- "[Actual question or post title]"
- "[Another example]"

**Curriculum Implication:** [How should this be addressed in training?]

---

### PART 3: Ranking by Popularity

| Rank | Topic | Popularity Score | Platform(s) | Urgency |
|------|-------|------------------|-------------|---------|
| 1 | [Topic] | [Score/metric] | [Where found] | [High/Med/Low] |
| 2 | [Topic] | [Score/metric] | [Where found] | [Urgency] |
| ... | ... | ... | ... | ... |

---

## CATEGORIES TO IDENTIFY:

1. **Technical Skills** - What technical knowledge do people ask about most?
2. **Common Struggles** - What do beginners find hardest?
3. **Career Questions** - Job hunting, certifications, career paths
4. **Tools & Equipment** - What tools confuse people?
5. **Industry Changes** - New developments people are discussing
6. **Frustrations** - What makes people angry or confused?

---

## MINIMUM REQUIREMENTS:

⚠️ **YOU MUST FIND AT LEAST 30+ DISTINCT TOPICS/QUESTIONS**

Each topic must include:
- 3 sentence description of what must be taught
- Specific popularity metric (upvotes, comments, views)
- Platform source citation
- Ranking by engagement/popularity

Use a CONSISTENT popularity metric across all platforms to enable fair ranking.

---

Now search the online communities and compile findings:"""

        findings_text = ""
        search_count = 0
        
        async for event in self.research_service.deep_research(
            prompt=prompt,
            system="""You are a community research expert analyzing online discussions to identify curriculum needs.

CRITICAL REQUIREMENTS:
1. Search Reddit, Quora, and industry-specific forums thoroughly
2. Find AT LEAST 30 distinct topics/questions being discussed
3. For EACH topic provide:
   - 3 sentence description of what must be taught
   - Specific popularity metric (upvotes, comments, engagement)
   - Platform and source citation
4. Rank ALL topics by popularity using consistent metrics
5. Identify the communities found with member counts
6. Include actual post titles or questions as examples

The goal is to understand what REAL people struggle with and want to learn.""",
            max_searches=35,
            enable_thinking=True,
            thinking_budget=12000,
            max_tokens=45000,
        ):
            event_type = event.get("type", "")
            
            if event_type == "thinking":
                yield {"type": "thinking", "content": event.get("content", "")}
            elif event_type == "text":
                chunk = event.get("content", "")
                findings_text += chunk
                yield {"type": "text_stream", "content": chunk}
            elif event_type == "tool_start":
                search_count += 1
                yield {"type": "search_status", "search_number": search_count}
            elif event_type == "complete":
                yield {"type": "search_complete", "total_searches": event.get("total_searches", search_count)}
        
        self.state["findings"]["sentiment"] = findings_text
        
        yield {
            "type": "phase_complete",
            "phase": "sentiment",
            "findings": findings_text,
            "search_count": search_count,
        }
        
        yield {
            "type": "feedback_request",
            "content": """**Phase 3 Complete: Consumer Sentiment**

Review the community insights above. You can:
- Ask me to explore specific topics deeper
- Add communities I should check
- Tell me to generate the **Final Curriculum Synthesis**

What would you like to do?""",
            "phase": "sentiment",
            "awaiting_response": True,
        }
    
    async def _handle_sentiment_feedback(self, feedback: str) -> AsyncGenerator[Dict[str, Any], None]:
        """Handle feedback on sentiment research."""
        lower = feedback.lower().strip()
        
        continue_signals = ["continue", "next", "proceed", "looks good", "move on", "final",
                          "synthesis", "generate", "go ahead", "ok", "okay", "yes", "good", "great", "perfect"]
        
        if any(signal in lower for signal in continue_signals):
            self.state["history"].append(ResearchPhase.SENTIMENT.value)
            yield {"type": "status", "content": "Generating **Final Curriculum Synthesis**..."}
            async for event in self._run_final_synthesis():
                yield event
        else:
            async for event in self._refine_research("sentiment", feedback):
                yield event
    
    async def _run_final_synthesis(self) -> AsyncGenerator[Dict[str, Any], None]:
        """Final synthesis - combine all research into curriculum."""
        self.state["phase"] = ResearchPhase.SYNTHESIS
        
        topic = self.state["topic"]
        competitive = self.state["findings"].get("competitive", "")
        expertise = self.state["findings"].get("expertise", "")
        sentiment = self.state["findings"].get("sentiment", "")
        
        yield {
            "type": "phase_start",
            "phase": "synthesis",
            "phase_number": 4,
            "total_phases": 4,
            "title": "Final Curriculum Synthesis",
            "description": "Combining all research into comprehensive curriculum",
        }
        
        prompt = f"""# {topic} Master Curriculum Module Inventory

## Document Purpose

This master inventory consolidates all modules identified through three comprehensive research exercises:

**Research Sources:**
1. **Competitive Analysis:** Analysis of top online training programs (modules from competitor curriculum analysis)
2. **Industry Media Analysis:** Top podcasts, blogs, and trade publications (emerging trend modules)
3. **Community Research:** Reddit, industry forums, Quora (community-validated modules)

---

## RESEARCH DATA:

### From Competitive Research:
{competitive[:12000] if competitive else "Not available"}

### From Industry Expertise Research:
{expertise[:8000] if expertise else "Not available"}

### From Consumer Sentiment Research:
{sentiment[:8000] if sentiment else "Not available"}

---

# CREATE THE MASTER MODULE INVENTORY

## Output Format - Use This EXACT Table Structure:

---

# SECTION A: CORE TECHNICAL MODULES

## A1. [First Major Topic Area]

| # | Module Title | Description | Priority | Source |
|---|--------------|-------------|----------|--------|
| A1-01 | **[Module Name]** | [3-4 sentence comprehensive description of what this module covers. Include specific skills, techniques, and learning outcomes. Explain how this prepares students for real-world work.] | Critical | Programs (X/20), Community (CES XX) |
| A1-02 | **[Module Name]** | [Description...] | Critical | Programs (X/20) |
| A1-03 | **[Module Name]** | [Description...] | High | Industry (★★★★☆) |
| A1-04 | **[Module Name]** | [Description...] | High | Community (CES XX) |
| A1-05 | **[Module Name]** | [Description...] | Standard | Programs (X/20) |

## A2. [Second Major Topic Area]

| # | Module Title | Description | Priority | Source |
|---|--------------|-------------|----------|--------|
| A2-01 | **[Module Name]** | [Description...] | Critical | [Source indicators] |
| A2-02 | **[Module Name]** | [Description...] | High | [Source] |

## A3. [Third Major Topic Area]

*(Continue pattern)*

---

# SECTION B: ELECTRICAL AND CONTROLS MODULES

| # | Module Title | Description | Priority | Source |
|---|--------------|-------------|----------|--------|
| B1-01 | **[Module Name]** | [Description...] | [Priority] | [Source] |

---

# SECTION C: SYSTEMS AND INSTALLATION MODULES

| # | Module Title | Description | Priority | Source |
|---|--------------|-------------|----------|--------|
| C1-01 | **[Module Name]** | [Description...] | [Priority] | [Source] |

---

# SECTION D: TROUBLESHOOTING AND DIAGNOSTICS MODULES

| # | Module Title | Description | Priority | Source |
|---|--------------|-------------|----------|--------|
| D1-01 | **[Module Name]** | [Description...] | [Priority] | [Source] |

---

# SECTION E: SAFETY AND COMPLIANCE MODULES

| # | Module Title | Description | Priority | Source |
|---|--------------|-------------|----------|--------|
| E1-01 | **[Module Name]** | [Description...] | [Priority] | [Source] |

---

# SECTION F: PROFESSIONAL AND CAREER MODULES

| # | Module Title | Description | Priority | Source |
|---|--------------|-------------|----------|--------|
| F1-01 | **[Module Name]** | [Description...] | [Priority] | [Source] |

---

# SECTION G: EMERGING TECHNOLOGY MODULES

| # | Module Title | Description | Priority | Source |
|---|--------------|-------------|----------|--------|
| G1-01 | **[Module Name]** | [Description...] | [Priority] | [Source] |

---

## CURRICULUM STATISTICS

| Metric | Count |
|--------|-------|
| **Total Unique Modules** | [XXX]+ |
| **Critical Priority** | [XX] modules |
| **High Priority** | [XX] modules |
| **Standard Priority** | [XX] modules |
| **From Competitive Analysis** | [XX] modules |
| **From Industry Trends** | [XX] modules |
| **From Community Research** | [XX] modules |

---

## PRIORITY DEFINITIONS

| Priority | Criteria |
|----------|----------|
| **Critical** | Appears in 70%+ of competitor programs OR CES 90+ OR ★★★★★ industry rating OR legally required |
| **High** | Appears in 40-70% of programs OR CES 70-89 OR ★★★★☆ industry rating |
| **Standard** | Appears in 20-40% of programs OR CES 50-69 OR ★★★☆☆ industry rating |

---

## REQUIREMENTS:
1. Include ALL modules from ALL three research phases
2. Deduplicate similar modules and note which sources identified them
3. Use consistent module numbering (A1-01, A1-02, etc.)
4. Each description should be 3-4 sentences covering content, skills, and outcomes
5. Priority based on frequency across sources
6. Target: 150-250+ unique modules total
7. Organize logically by section (A through G)

Now synthesize all research into the master inventory:"""

        synthesis_text = ""
        search_count = 0
        
        async for event in self.research_service.deep_research(
            prompt=prompt,
            system="""You are a master curriculum architect creating the definitive module inventory.

CRITICAL INSTRUCTIONS:
1. Synthesize ALL modules from the three research phases into one organized inventory
2. Use the EXACT table format provided with columns: #, Module Title, Description, Priority, Source
3. Each description must be 3-4 sentences explaining content, skills, and outcomes
4. Assign priority based on how often the topic appeared across sources
5. Include source indicators showing where each module was identified
6. Organize into logical sections (A-G as shown)
7. Target 150-250+ total modules - be comprehensive
8. Deduplicate similar modules but note all sources that identified them

This is the final deliverable - make it comprehensive and professional.""",
            max_searches=5,
            enable_thinking=True,
            thinking_budget=20000,
            max_tokens=60000,
        ):
            event_type = event.get("type", "")
            
            if event_type == "thinking":
                yield {"type": "thinking", "content": event.get("content", "")}
            elif event_type == "text":
                chunk = event.get("content", "")
                synthesis_text += chunk
                yield {"type": "text_stream", "content": chunk}
            elif event_type == "tool_start":
                search_count += 1
                yield {"type": "search_status", "search_number": search_count}
            elif event_type == "complete":
                yield {"type": "search_complete", "total_searches": event.get("total_searches", search_count)}
        
        self.state["findings"]["synthesis"] = synthesis_text
        self.state["phase"] = ResearchPhase.COMPLETE
        
        yield {
            "type": "research_complete",
            "final_report": synthesis_text,
            "topic": topic,
        }
        
        yield {
            "type": "completion_message",
            "content": """**🎉 Curriculum Research Complete!**

Your comprehensive curriculum has been generated above. You can:
- Download as PDF or Word document
- Ask me to modify specific modules
- Start a new research topic

The curriculum includes lessons from competitive analysis, industry trends, and community insights.""",
        }
    
    async def _handle_synthesis_feedback(self, feedback: str) -> AsyncGenerator[Dict[str, Any], None]:
        """Handle feedback on final synthesis."""
        yield {"type": "status", "content": "Processing your feedback on the curriculum..."}
        async for event in self._refine_research("synthesis", feedback):
            yield event
    
    async def _refine_research(self, phase: str, feedback: str) -> AsyncGenerator[Dict[str, Any], None]:
        """Refine research based on feedback."""
        topic = self.state["topic"]
        current_findings = self.state["findings"].get(phase, "")
        
        prompt = f"""# Refine {phase.title()} Research: {topic}

User Feedback: {feedback}

Current Findings Summary:
{current_findings[:3000] if current_findings else "Starting fresh"}

Based on the user's feedback, provide additional research or modifications.
Use clean markdown tables for any new information.
Address the user's specific requests directly."""

        findings_text = ""
        
        async for event in self.research_service.deep_research(
            prompt=prompt,
            system="You are refining curriculum research based on user feedback. Address their specific requests and use clean markdown tables.",
            max_searches=15,
            enable_thinking=True,
            thinking_budget=8000,
            max_tokens=15000,
        ):
            event_type = event.get("type", "")
            
            if event_type == "thinking":
                yield {"type": "thinking", "content": event.get("content", "")}
            elif event_type == "text":
                chunk = event.get("content", "")
                findings_text += chunk
                yield {"type": "text_stream", "content": chunk}
            elif event_type == "tool_start":
                yield {"type": "search_status", "search_number": 1}
            elif event_type == "complete":
                yield {"type": "search_complete", "total_searches": event.get("total_searches", 0)}
        
        if findings_text:
            self.state["findings"][phase] = current_findings + "\n\n---\n\n" + findings_text
        
        yield {
            "type": "refinement_complete",
            "phase": phase,
        }
        
        yield {
            "type": "feedback_request",
            "content": f"""I've updated the {phase} research based on your feedback.

Would you like to:
- Make more changes to this phase
- Continue to the next phase

Just let me know!""",
            "phase": phase,
        }


# Singleton instance
research_orchestrator = CurriculumResearchOrchestrator()
curriculum_orchestrator = research_orchestrator  # Alias for compatibility


