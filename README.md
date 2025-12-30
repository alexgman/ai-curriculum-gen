# AI Curriculum Builder - MCP Deep Research

Automated curriculum research tool using Claude's Deep Research capabilities via Model Context Protocol (MCP).

## Features

- **5-Step Interactive Research Flow**
  - Providers discovery and selection
  - Certifications analysis
  - Target audience definition
  - Publications research (podcasts, blogs, Reddit)
  - Module synthesis (100+ unique topics)

- **Conversational Interface**
  - Natural language understanding ("add X", "remove Y", "go back")
  - Step-by-step with user approval
  - Backward navigation

- **Comprehensive Research**
  - 115 web searches across all steps
  - Claude Extended Thinking for deep reasoning
  - Shows ALL data (no cutoffs)
  - Generates 100+ unique curriculum topics

- **Export Options**
  - Download reports as DOCX
  - Professional formatting

## Quick Start

### 1. Setup Conda Environment

Already created: `curriculum` environment with Python 3.11

### 2. Start Backend

```bash
cd /home/ubuntu/Dev/ai-curriculum-gen
./RUN_IN_CONDA.sh
```

### 3. Start Frontend

```bash
cd frontend
npm run dev
```

### 4. Open Browser

http://localhost:3000 (local) or http://3.150.159.160:3000 (remote)

## Usage

1. Enter a topic (e.g., "HVAC service technician")
2. Review providers research → approve or modify
3. Review certifications → approve or modify
4. Select target audience
5. Review publications → approve or modify
6. Get 100+ curriculum topics → download as DOCX

## Natural Language Commands

The system understands:
- `add TechNow` - Add a provider/certification/source
- `remove Udemy` - Remove an item
- `move X, Y to optional` - Mark as optional
- `go back` - Return to previous step
- `continue` / `looks good` - Proceed to next step

## Cost

~$3.40 per complete research session
- 115 web searches: $1.15
- 150K Claude tokens: $2.25

Returns: 100+ unique curriculum topics

## Documentation

- **START_HERE.md** - Complete testing and deployment guide
- **API_KEYS_GUIDE.md** - API key setup instructions
- **RUN_IN_CONDA.sh** - Startup script for conda environment

## API Endpoints

- `POST /api/v1/research/start` - Start research
- `POST /api/v1/research/feedback` - Submit feedback
- `GET /api/v1/research/{session_id}/report/docx` - Download DOCX

## Requirements

- Python 3.11 (conda env: `curriculum`)
- Node.js (for frontend)
- Anthropic API key
- PostgreSQL (for database)

## Architecture

```
User Topic → MCP Deep Research Service → Claude API (with web search)
    ↓
5-Step Research Flow (with user approval between steps)
    ↓
Module Synthesis (100+ topics)
    ↓
Downloadable Report (DOCX)
```

## Status

✅ All systems operational
✅ Tested and verified
✅ Ready for production use

See **START_HERE.md** for detailed instructions.
