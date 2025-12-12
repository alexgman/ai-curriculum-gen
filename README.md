# AI Curriculum Builder

An AI-powered research tool for curriculum development. Uses LangGraph with a ReAct + Reflection pattern to prevent hallucination and ensure research accuracy.

## Features

- **Competitor Research**: Automatically find and analyze online courses
- **Curriculum Extraction**: Scrape and extract curriculum structures
- **Sentiment Analysis**: Analyze Reddit, Quora, podcasts, and blogs
- **Trend Discovery**: Identify trending topics in any industry
- **ChatGPT-style UI**: Intuitive chat interface with streaming responses

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    LangGraph Agent Engine                       │
│                                                                 │
│  User Message → REASONING → TOOL → REFLECTION → RESPONSE        │
│                     ↑                   │                       │
│                     └───────────────────┘                       │
│                    (loop until sufficient)                      │
└─────────────────────────────────────────────────────────────────┘
```

### Available Tools

| Tool | Description |
|------|-------------|
| `search_google` | Find competitors and courses via SerpAPI |
| `scrape_webpage` | Extract content from course pages via Firecrawl |
| `search_reddit` | Get discussions from Reddit via PRAW |
| `search_quora` | Find Q&A from Quora |
| `find_podcasts` | Discover industry podcasts |
| `find_blogs` | Discover industry blogs |
| `analyze_content` | Deep analysis with Claude |
| `save_research` | Persist research data |
| `generate_report` | Create comprehensive reports |

## Quick Start

### 1. Clone and Setup

```bash
cd ai_curriculam
cp .env.example .env
# Edit .env with your API keys
```

### 2. Get API Keys

| API | Where | Free Tier |
|-----|-------|-----------|
| Anthropic | [console.anthropic.com](https://console.anthropic.com/) | Pay-as-you-go |
| SerpAPI | [serpapi.com](https://serpapi.com/) | 100 searches/month |
| Firecrawl | [firecrawl.dev](https://www.firecrawl.dev/) | 500 pages/month |
| Reddit | [reddit.com/prefs/apps](https://www.reddit.com/prefs/apps) | Free |

### 3. Run with Docker

```bash
docker-compose up -d
```

Or run locally:

```bash
# Backend
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload

# Frontend (new terminal)
cd frontend
npm install
npm run dev
```

### 4. Open the App

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

## Usage

1. Open the chat interface at http://localhost:3000
2. Type a research query, e.g., "Research data center technician courses"
3. Watch as the AI:
   - Searches for competitors
   - Extracts curricula
   - Analyzes sentiment
   - Generates a comprehensive report

## Tech Stack

- **Backend**: FastAPI, LangGraph, SQLAlchemy
- **Frontend**: Next.js 14, React, Tailwind CSS
- **Database**: PostgreSQL, Redis
- **AI**: Claude 4.5 (Anthropic)
- **APIs**: SerpAPI, Firecrawl, Reddit (PRAW)

## Project Structure

```
ai_curriculam/
├── backend/
│   ├── app/
│   │   ├── api/v1/          # API endpoints
│   │   ├── graph/           # LangGraph agent
│   │   │   ├── nodes/       # Agent nodes
│   │   │   └── state.py     # State schema
│   │   ├── tools/           # Research tools
│   │   ├── services/        # External API clients
│   │   └── prompts/         # System prompts
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── app/             # Next.js pages
│   │   ├── components/      # React components
│   │   └── types/           # TypeScript types
│   └── package.json
├── docker-compose.yml
└── .env.example
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/chat` | Chat with SSE streaming |
| POST | `/api/v1/chat/sync` | Synchronous chat |
| POST | `/api/v1/sessions` | Create new session |
| GET | `/api/v1/sessions/{id}/research` | Get research data |
| POST | `/api/v1/sessions/{id}/report` | Generate report |

## License

Private - Qosmos EdTech
