# AI Curriculum Builder - Development Plan

## 🎯 Project Overview

Building an AI-powered curriculum development system for Qosmos with:
- **Backend:** FastAPI (Python)
- **Frontend:** Next.js (React)
- **Database:** PostgreSQL + pgvector
- **AI:** Claude 4.5 (Anthropic)
- **Hosting:** AWS EC2

---

## 📁 Project Structure

```
ai_curriculum/
├── backend/                    # FastAPI Backend
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py             # FastAPI app entry
│   │   ├── config.py           # Settings & env vars
│   │   ├── database.py         # DB connection
│   │   │
│   │   ├── api/                # API Routes
│   │   │   ├── __init__.py
│   │   │   ├── v1/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── router.py
│   │   │   │   ├── research.py     # Phase 1 endpoints
│   │   │   │   ├── curriculum.py   # Phase 2 endpoints
│   │   │   │   └── scripts.py      # Phase 3 endpoints
│   │   │   └── deps.py         # Dependencies
│   │   │
│   │   ├── models/             # SQLAlchemy Models
│   │   │   ├── __init__.py
│   │   │   ├── brand.py
│   │   │   ├── course.py
│   │   │   ├── lesson.py
│   │   │   ├── module.py
│   │   │   ├── research.py
│   │   │   ├── instructor.py
│   │   │   └── conversation.py
│   │   │
│   │   ├── schemas/            # Pydantic Schemas
│   │   │   ├── __init__.py
│   │   │   ├── research.py
│   │   │   ├── curriculum.py
│   │   │   └── script.py
│   │   │
│   │   ├── services/           # Business Logic
│   │   │   ├── __init__.py
│   │   │   ├── claude_service.py       # Anthropic API
│   │   │   ├── research_service.py     # Phase 1 logic
│   │   │   ├── curriculum_service.py   # Phase 2 logic
│   │   │   ├── script_service.py       # Phase 3 logic
│   │   │   └── scraping/
│   │   │       ├── __init__.py
│   │   │       ├── reddit_scraper.py
│   │   │       ├── web_scraper.py
│   │   │       └── search_scraper.py
│   │   │
│   │   └── utils/              # Utilities
│   │       ├── __init__.py
│   │       ├── prompts.py      # Claude prompts
│   │       └── helpers.py
│   │
│   ├── alembic/                # DB Migrations
│   ├── tests/
│   ├── requirements.txt
│   └── Dockerfile
│
├── frontend/                   # Next.js Frontend
│   ├── src/
│   │   ├── app/                # App Router
│   │   │   ├── layout.tsx
│   │   │   ├── page.tsx
│   │   │   ├── research/       # Phase 1 UI
│   │   │   ├── curriculum/     # Phase 2 UI
│   │   │   └── scripts/        # Phase 3 UI
│   │   │
│   │   ├── components/
│   │   │   ├── ui/             # Shadcn components
│   │   │   ├── chat/           # Chat interface
│   │   │   ├── research/
│   │   │   ├── curriculum/
│   │   │   └── scripts/
│   │   │
│   │   ├── lib/
│   │   │   ├── api.ts          # API client
│   │   │   └── utils.ts
│   │   │
│   │   └── types/
│   │       └── index.ts
│   │
│   ├── package.json
│   └── Dockerfile
│
├── docker-compose.yml
├── .env
├── .env.example
└── README.md
```

---

## 🗓️ Development Timeline

### Total: 2 Weeks (10 Working Days)

---

## 📦 PHASE 1: Research Bot (Days 1-4)

### Day 1: Project Setup & Infrastructure

**Backend Setup:**
- [ ] Initialize FastAPI project structure
- [ ] Set up PostgreSQL with pgvector extension
- [ ] Configure SQLAlchemy + Alembic migrations
- [ ] Create database models (Brand, Research, Conversation)
- [ ] Set up Redis for caching
- [ ] Configure environment variables

**Frontend Setup:**
- [ ] Initialize Next.js 14 with App Router
- [ ] Set up Tailwind CSS + Shadcn/ui
- [ ] Create base layout with sidebar navigation
- [ ] Set up API client with fetch/axios

**Database Schema (Phase 1):**
```sql
-- Brands (ELDT Nation, BOOM Marketing, etc.)
CREATE TABLE brands (
    id UUID PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(255) UNIQUE,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Research Sessions
CREATE TABLE research_sessions (
    id UUID PRIMARY KEY,
    brand_id UUID REFERENCES brands(id),
    sector VARCHAR(255),          -- "data center technician"
    status VARCHAR(50),           -- pending, in_progress, completed
    created_at TIMESTAMP DEFAULT NOW()
);

-- Research Results
CREATE TABLE research_results (
    id UUID PRIMARY KEY,
    session_id UUID REFERENCES research_sessions(id),
    source_type VARCHAR(50),      -- competitor, reddit, podcast, blog
    source_url TEXT,
    title VARCHAR(500),
    content TEXT,
    sentiment FLOAT,              -- -1 to 1
    extracted_topics JSONB,       -- ["topic1", "topic2"]
    created_at TIMESTAMP DEFAULT NOW()
);

-- Conversations (Chat History)
CREATE TABLE conversations (
    id UUID PRIMARY KEY,
    session_id UUID REFERENCES research_sessions(id),
    role VARCHAR(20),             -- user, assistant
    content TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);
```

### Day 2: Scraping Infrastructure

**Web Scraping Service:**
- [ ] Playwright setup for dynamic sites
- [ ] BeautifulSoup for static HTML parsing
- [ ] Competitor course extraction logic
- [ ] Rate limiting & retry logic

**Reddit Scraping:**
- [ ] PRAW integration
- [ ] Subreddit search functionality
- [ ] Comment extraction
- [ ] Sentiment analysis integration

**Google Search (via Serper API):**
- [ ] Search for competitor courses
- [ ] Search for industry podcasts/blogs
- [ ] Extract and categorize results

### Day 3: Claude Integration & Research Logic

**Claude Service:**
- [ ] Anthropic API client setup
- [ ] Streaming response support
- [ ] Prompt templates for research phase
- [ ] Content categorization prompts
- [ ] Module extraction prompts

**Research Prompts:**
```python
RESEARCH_SYSTEM_PROMPT = """
You are an AI curriculum research assistant for Qosmos, 
a digital vocational school. Your job is to:

1. Analyze competitor courses and extract their curriculum structure
2. Identify what students want to learn from Reddit/forum discussions
3. Find bleeding-edge knowledge from podcasts and blogs
4. Organize findings into potential modules and lessons

Always cite your sources and organize output clearly.
"""

COMPETITOR_ANALYSIS_PROMPT = """
Analyze this competitor course content and extract:
1. Course structure (modules/lessons)
2. Key topics covered
3. Unique selling points
4. Gaps or weaknesses

Content: {content}
"""
```

### Day 4: Research UI & Testing

**Frontend - Research Interface:**
- [ ] Chat interface component (Claude-style)
- [ ] Research session management
- [ ] Real-time streaming responses
- [ ] Source citation display
- [ ] Export research to JSON/Markdown

**API Endpoints (Phase 1):**
```
POST   /api/v1/research/sessions              # Create new research session
GET    /api/v1/research/sessions              # List all sessions
GET    /api/v1/research/sessions/{id}         # Get session details
POST   /api/v1/research/sessions/{id}/chat    # Send message (streaming)
POST   /api/v1/research/sessions/{id}/scrape  # Trigger scraping
GET    /api/v1/research/sessions/{id}/results # Get research results
POST   /api/v1/research/sessions/{id}/export  # Export to JSON/Markdown
```

**Deliverable:** Working research bot that can:
- ✅ Scrape competitor course URLs
- ✅ Search Reddit for industry discussions
- ✅ Analyze content with Claude
- ✅ Generate structured module/lesson suggestions
- ✅ Chat interface for refinement

---

## 📦 PHASE 2: Curriculum Organization (Days 5-7)

### Day 5: Curriculum Data Models

**Database Schema (Phase 2):**
```sql
-- Courses
CREATE TABLE courses (
    id UUID PRIMARY KEY,
    brand_id UUID REFERENCES brands(id),
    research_session_id UUID REFERENCES research_sessions(id),
    title VARCHAR(500),
    description TEXT,
    status VARCHAR(50),           -- draft, review, published
    version INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Lessons
CREATE TABLE lessons (
    id UUID PRIMARY KEY,
    course_id UUID REFERENCES courses(id),
    order_index INTEGER,
    title VARCHAR(500),
    description TEXT,
    objectives JSONB,             -- ["objective1", "objective2"]
    duration_minutes INTEGER,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Modules
CREATE TABLE modules (
    id UUID PRIMARY KEY,
    lesson_id UUID REFERENCES lessons(id),
    order_index INTEGER,
    title VARCHAR(500),
    description TEXT,
    topics JSONB,
    target_word_count INTEGER DEFAULT 1500,
    prerequisites JSONB,          -- [module_id1, module_id2]
    created_at TIMESTAMP DEFAULT NOW()
);

-- Instructor Profiles
CREATE TABLE instructor_profiles (
    id UUID PRIMARY KEY,
    brand_id UUID REFERENCES brands(id),
    name VARCHAR(255),
    voice_sample TEXT,            -- Writing sample for voice matching
    characteristics JSONB,        -- {"tone": "professional", "humor": true}
    created_at TIMESTAMP DEFAULT NOW()
);
```

### Day 6: Curriculum Generation Logic

**Curriculum Service:**
- [ ] Import research results
- [ ] Merge with manual curriculum input
- [ ] Claude-powered organization
- [ ] Learning objective generation
- [ ] Prerequisite mapping
- [ ] Duration estimation

**Curriculum Prompts:**
```python
CURRICULUM_ORGANIZATION_PROMPT = """
You are organizing a curriculum for {course_title}.

Research Data:
{research_data}

Manual Input from Expert:
{expert_input}

Create a structured curriculum with:
1. Logical lesson flow (beginner → advanced)
2. Clear learning objectives per module
3. Prerequisite dependencies
4. Estimated duration per module

Output as structured JSON.
"""
```

### Day 7: Curriculum UI

**Frontend - Curriculum Interface:**
- [ ] Drag-and-drop lesson/module organizer
- [ ] Hierarchy tree view (Course → Lesson → Module)
- [ ] Inline editing for titles/descriptions
- [ ] Learning objective editor
- [ ] Import from research session
- [ ] Export to Google Docs format

**API Endpoints (Phase 2):**
```
POST   /api/v1/curriculum/courses                    # Create course
GET    /api/v1/curriculum/courses                    # List courses
GET    /api/v1/curriculum/courses/{id}               # Get course with lessons/modules
PUT    /api/v1/curriculum/courses/{id}               # Update course
POST   /api/v1/curriculum/courses/{id}/generate      # AI generate structure
POST   /api/v1/curriculum/courses/{id}/lessons       # Add lesson
PUT    /api/v1/curriculum/lessons/{id}               # Update lesson
POST   /api/v1/curriculum/lessons/{id}/modules       # Add module
PUT    /api/v1/curriculum/modules/{id}               # Update module
POST   /api/v1/curriculum/courses/{id}/reorder       # Reorder lessons/modules
POST   /api/v1/curriculum/courses/{id}/export        # Export
```

**Deliverable:** Working curriculum organizer that can:
- ✅ Import research findings
- ✅ Accept manual curriculum input
- ✅ AI-organize into coherent structure
- ✅ Generate learning objectives
- ✅ Drag-and-drop reordering
- ✅ Export to structured format

---

## 📦 PHASE 3: Script Writing (Days 8-10)

### Day 8: Script Generation Engine

**Multi-Agent Architecture:**
```python
class ScriptGenerationPipeline:
    """
    Multi-agent pipeline for script generation
    """
    
    async def generate(self, module: Module, instructor: InstructorProfile):
        # Step 1: Structure Agent - Create outline
        outline = await self.structure_agent.create_outline(module)
        
        # Step 2: Content Agent - Generate base content
        content = await self.content_agent.write_script(
            outline, 
            target_words=module.target_word_count
        )
        
        # Step 3: Voice Agent - Apply instructor personality
        voiced = await self.voice_agent.apply_voice(
            content, 
            instructor.voice_sample,
            instructor.characteristics
        )
        
        # Step 4: Enhancement Agent - Add examples, humor, callouts
        enhanced = await self.enhancement_agent.enhance(
            voiced,
            add_examples=True,
            add_animation_callouts=True
        )
        
        # Step 5: Validation Agent - Check quality
        final = await self.validation_agent.validate(
            enhanced,
            learning_objectives=module.objectives,
            word_count_target=module.target_word_count
        )
        
        return final
```

**Database Schema (Phase 3):**
```sql
-- Scripts
CREATE TABLE scripts (
    id UUID PRIMARY KEY,
    module_id UUID REFERENCES modules(id),
    instructor_id UUID REFERENCES instructor_profiles(id),
    version INTEGER DEFAULT 1,
    content TEXT,
    word_count INTEGER,
    status VARCHAR(50),           -- draft, review, approved
    animation_callouts JSONB,     -- [{"timestamp": "2:30", "description": "..."}]
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Script Revisions
CREATE TABLE script_revisions (
    id UUID PRIMARY KEY,
    script_id UUID REFERENCES scripts(id),
    content TEXT,
    feedback TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);
```

### Day 9: Script UI & Editing

**Frontend - Script Interface:**
- [ ] Module selector (from curriculum)
- [ ] Word count configuration per module
- [ ] Instructor voice selector
- [ ] Script generation trigger
- [ ] Real-time streaming output
- [ ] Inline editing
- [ ] Animation callout highlighting
- [ ] Version history
- [ ] Export (PDF, Google Docs, Plain Text)

**Script Prompts:**
```python
SCRIPT_WRITING_PROMPT = """
Write a video script for module: {module_title}

Learning Objectives:
{objectives}

Instructor Voice Sample:
{voice_sample}

Requirements:
- Target word count: {word_count} words
- Include [ANIMATION: description] callouts for visuals
- Match the instructor's tone and style
- Cover all learning objectives
- Use practical examples

Write the script now:
"""

VOICE_ADAPTATION_PROMPT = """
Rewrite this script to match this instructor's voice:

Voice Sample:
{voice_sample}

Voice Characteristics:
- Tone: {tone}
- Uses humor: {humor}
- Speaking style: {style}

Original Script:
{script}

Rewritten Script:
"""
```

### Day 10: Polish, Testing & Deployment

**Backend:**
- [ ] Error handling & validation
- [ ] Rate limiting
- [ ] API documentation (Swagger)
- [ ] Unit tests for core services
- [ ] Integration tests

**Frontend:**
- [ ] Responsive design check
- [ ] Loading states & error handling
- [ ] Toast notifications
- [ ] Keyboard shortcuts
- [ ] Dark/light mode

**Deployment:**
- [ ] Docker compose setup
- [ ] AWS EC2 deployment
- [ ] Nginx reverse proxy
- [ ] SSL certificate (Let's Encrypt)
- [ ] Environment configuration

**API Endpoints (Phase 3):**
```
POST   /api/v1/scripts/generate                # Generate script for module
GET    /api/v1/scripts/{id}                    # Get script
PUT    /api/v1/scripts/{id}                    # Update script
POST   /api/v1/scripts/{id}/regenerate         # Regenerate with feedback
GET    /api/v1/scripts/{id}/revisions          # Get revision history
POST   /api/v1/scripts/{id}/export             # Export script
GET    /api/v1/instructors                     # List instructors
POST   /api/v1/instructors                     # Create instructor profile
PUT    /api/v1/instructors/{id}                # Update instructor
```

**Deliverable:** Complete script writing system that can:
- ✅ Select module from curriculum
- ✅ Configure word count
- ✅ Select instructor voice
- ✅ Generate script with Claude
- ✅ Include animation callouts
- ✅ Edit and revise
- ✅ Export in multiple formats

---

## 🎨 UI Design Overview

### Chat Interface (Claude-style)
```
┌─────────────────────────────────────────────────────────────┐
│  AI Curriculum Builder                    [Research] [Cur.] │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ 🤖 Assistant                                        │   │
│  │ I'll help you research the data center technician  │   │
│  │ industry. I found 5 competitor courses:            │   │
│  │                                                     │   │
│  │ 1. CompTIA Data Center+ Certification              │   │
│  │ 2. Coursera: Google Data Center Operations         │   │
│  │ ...                                                 │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ 👤 You                                              │   │
│  │ What are students saying on Reddit about these?    │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ 🤖 Assistant                                        │   │
│  │ Analyzing r/datacenter and r/ITCareerQuestions... │   │
│  │ ████████░░ 80%                                      │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────────┐   │
│  │ Type your message...                          [Send]│   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

### Curriculum Organizer
```
┌─────────────────────────────────────────────────────────────┐
│  📚 Real Estate Agent Masterclass                    [Save] │
├───────────────────┬─────────────────────────────────────────┤
│ COURSE STRUCTURE  │  MODULE DETAILS                         │
│                   │                                         │
│ ▼ Lesson 1        │  📝 Agent Specialization                │
│   ├─ Module 1A    │                                         │
│   ├─ Module 1B ◄──│──┤ Description:                         │
│   └─ Module 1C    │  │ High-level of different real estate │
│                   │  │ markets (residential, commercial)   │
│ ▶ Lesson 2        │  │                                      │
│ ▶ Lesson 3        │  │ Learning Objectives:                 │
│ ▶ Lesson 4        │  │ □ Understand market types            │
│                   │  │ □ Choose specialization              │
│ [+ Add Lesson]    │  │                                      │
│                   │  │ Word Count Target: [1500] words      │
│                   │  │                                      │
│                   │  │ [Generate Script →]                  │
└───────────────────┴─────────────────────────────────────────┘
```

---

## 🔑 API Keys Required

| Service | Purpose | Get Key At |
|---------|---------|------------|
| **Anthropic** | Claude AI | console.anthropic.com |
| **AWS** | EC2 + S3 | aws.amazon.com |
| **Reddit** | Forum scraping | reddit.com/prefs/apps |
| **Serper** | Google search | serper.dev |

---

## 📊 Success Metrics

| Metric | Target |
|--------|--------|
| Research → Module List | < 2 minutes |
| Curriculum Organization | < 1 minute |
| Script Generation | < 45 seconds |
| First-draft acceptance | > 80% |
| System uptime | > 99% |

---

## 🚀 Deployment Architecture

```
                    ┌─────────────────┐
                    │   CloudFlare    │
                    │   (DNS + CDN)   │
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │   AWS EC2       │
                    │   (Nginx)       │
                    └────────┬────────┘
                             │
              ┌──────────────┴──────────────┐
              │                             │
     ┌────────▼────────┐          ┌────────▼────────┐
     │   Frontend      │          │    Backend      │
     │   (Next.js)     │          │   (FastAPI)     │
     │   Port 3000     │          │   Port 8000     │
     └─────────────────┘          └────────┬────────┘
                                           │
                         ┌─────────────────┼─────────────────┐
                         │                 │                 │
                ┌────────▼───────┐ ┌───────▼──────┐ ┌───────▼──────┐
                │   PostgreSQL   │ │    Redis     │ │   AWS S3     │
                │   + pgvector   │ │   (Cache)    │ │  (Storage)   │
                └────────────────┘ └──────────────┘ └──────────────┘
```

---

## ✅ Acceptance Criteria

### Phase 1 (Research Bot)
- [ ] Can scrape 3+ competitor URLs
- [ ] Can search Reddit for industry topics
- [ ] Generates structured module suggestions
- [ ] Chat interface with streaming responses
- [ ] Export research to JSON

### Phase 2 (Curriculum)
- [ ] Import research into curriculum
- [ ] Create/edit course hierarchy
- [ ] Generate learning objectives
- [ ] Drag-and-drop reordering
- [ ] Export curriculum structure

### Phase 3 (Scripts)
- [ ] Generate scripts from modules
- [ ] Configurable word count
- [ ] Instructor voice matching
- [ ] Animation callout insertion
- [ ] Export to PDF/Docs

