# 🔑 API Keys Setup Guide

This guide walks you through getting all the API keys needed for the AI Curriculum Builder.

---

## 📋 Summary: All API Keys Needed

| API | Purpose | Cost | Priority |
|-----|---------|------|----------|
| **Anthropic** | Claude AI (core) | ~$15/1M tokens | ⭐ REQUIRED |
| **AWS** | EC2 hosting + S3 | ~$20-50/mo | ⭐ REQUIRED |
| **Firecrawl** | Web scraping | Free tier: 500 pages/mo | ⭐ REQUIRED |
| **Serper** | Google search | Free tier: 2,500 searches/mo | ⭐ REQUIRED |
| **Reddit** | Forum sentiment | FREE (no API needed!) | ✅ BUILT-IN |
| **Tavily** | AI search (backup) | Free tier: 1,000 searches/mo | Optional |
| **Listen Notes** | Podcast search | Free tier: 300 requests/mo | Optional |

---

## 1. Anthropic API Key ⭐ REQUIRED

**What it's for:** Claude AI - the brain of the entire system

### Steps to Get:
1. Go to **https://console.anthropic.com/**
2. Click "Sign Up" (or "Log In" if you have an account)
3. Verify your email
4. Go to **Settings → API Keys**
5. Click **"Create Key"**
6. Copy the key (starts with `sk-ant-...`)

### Pricing:
- Claude 3.5 Sonnet: $3/1M input tokens, $15/1M output tokens
- Claude 4: ~$15/1M input, $75/1M output
- For this project: ~$50-100/month depending on usage

```bash
# Add to .env
ANTHROPIC_API_KEY=sk-ant-api03-xxxxxxxxxxxxx
```

---

## 2. AWS Access Keys ⭐ REQUIRED

**What it's for:** EC2 hosting + S3 storage

### Steps to Get:
1. Go to **https://aws.amazon.com/**
2. Click "Create an AWS Account" (or sign in)
3. Complete registration (requires credit card)
4. Go to **IAM → Users → Add User**
5. Create a user with programmatic access
6. Attach policies: `AmazonEC2FullAccess`, `AmazonS3FullAccess`
7. Download the credentials CSV

### Alternative (if client provides):
Ask Gabriel for AWS credentials or have him create an IAM user for you.

```bash
# Add to .env
AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE
AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
AWS_REGION=us-east-1
```

---

## 3. Firecrawl API Key ⭐ REQUIRED

**What it's for:** Scraping competitor course websites and extracting curriculum

### Steps to Get:
1. Go to **https://www.firecrawl.dev/**
2. Click "Get Started" or "Sign Up"
3. Create account (can use GitHub/Google)
4. Go to Dashboard → API Keys
5. Copy your API key

### Pricing:
- **Free:** 500 credits/month (1 credit = 1 page)
- **Hobby:** $19/mo for 3,000 credits
- **Standard:** $99/mo for 100,000 credits

```bash
# Add to .env
FIRECRAWL_API_KEY=fc-xxxxxxxxxxxxxxxxxxxxxxxx
```

---

## 4. Serper API Key ⭐ REQUIRED

**What it's for:** Google search results to find competitors

### Steps to Get:
1. Go to **https://serper.dev/**
2. Click "Get Started"
3. Sign up with Google or email
4. Go to Dashboard → API Key
5. Copy your API key

### Pricing:
- **Free:** 2,500 searches/month
- **Starter:** $50/mo for 50,000 searches

```bash
# Add to .env
SERPER_API_KEY=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

---

## 5. Reddit - NO API KEY NEEDED! ✅ 

**What it's for:** Scraping Reddit for industry sentiment and market validation

### ✨ NEW: No API Key Required!

We've updated the Reddit integration to work **without** an API key using:
- **RSS Feeds** (free, unlimited, instant access)
- **Web Scraping** via Serper + Firecrawl (uses your existing keys)

### How It Works:
- **Recent Posts:** Uses Reddit's public RSS feeds
- **Historical Search:** Uses Google Search (via Serper) + Firecrawl scraping
- **Market Validation:** Analyzes upvotes, comments, sentiment automatically

### Setup:
**No setup needed!** Just make sure you have:
- ✅ Serper API key (for search)
- ✅ Firecrawl API key (for scraping)

Both are already required for other features.

### Optional (if you want direct API access):
If you still want to use Reddit's official API, follow these steps:
1. Go to **https://www.reddit.com/prefs/apps**
2. Create app (but Reddit now requires manual approval)
3. **We recommend using our scraping approach instead!**

```bash
# Optional - Not needed anymore!
# REDDIT_CLIENT_ID=xxxxxxxxxxxxx
# REDDIT_CLIENT_SECRET=xxxxxxxxxxxxxxxxxxxxxxxx
# REDDIT_USER_AGENT=curriculum_builder/1.0
```

---

## 6. Tavily API Key (Optional - Backup Search)

**What it's for:** AI-optimized search (used by GPT-Researcher)

### Steps to Get:
1. Go to **https://tavily.com/**
2. Click "Get API Key"
3. Sign up with Google or email
4. Copy your API key from dashboard

### Pricing:
- **Free:** 1,000 searches/month
- **Pro:** $100/mo for 10,000 searches

```bash
# Add to .env (optional)
TAVILY_API_KEY=tvly-xxxxxxxxxxxxxxxxxxxxxxxx
```

---

## 7. Listen Notes API (Optional - Podcasts)

**What it's for:** Finding industry podcasts

### Steps to Get:
1. Go to **https://www.listennotes.com/api/**
2. Click "Get Started"
3. Sign up for free account
4. Go to Dashboard → API Keys
5. Copy your API key

### Pricing:
- **Free:** 300 requests/month
- **Basic:** $9/mo for 3,000 requests

```bash
# Add to .env (optional)
LISTENNOTES_API_KEY=xxxxxxxxxxxxxxxxxxxxxxxx
```

---

## 📝 Complete .env File Template

```bash
# =============================================================================
# AI Curriculum Builder - Environment Variables
# =============================================================================

# -----------------------------------------------------------------------------
# CORE: Anthropic Claude AI (REQUIRED)
# Get at: https://console.anthropic.com/
# -----------------------------------------------------------------------------
ANTHROPIC_API_KEY=sk-ant-api03-your-key-here

# -----------------------------------------------------------------------------
# CORE: AWS (REQUIRED)
# Get at: https://aws.amazon.com/ → IAM → Users
# -----------------------------------------------------------------------------
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
AWS_REGION=us-east-1
AWS_S3_BUCKET=curriculum-builder-storage

# -----------------------------------------------------------------------------
# SCRAPING: Firecrawl (REQUIRED)
# Get at: https://www.firecrawl.dev/
# -----------------------------------------------------------------------------
FIRECRAWL_API_KEY=fc-your-key-here

# -----------------------------------------------------------------------------
# SEARCH: Serper - Google Search (REQUIRED)
# Get at: https://serper.dev/
# -----------------------------------------------------------------------------
SERPER_API_KEY=your-serper-key-here

# -----------------------------------------------------------------------------
# SENTIMENT: Reddit API (REQUIRED)
# Get at: https://www.reddit.com/prefs/apps
# -----------------------------------------------------------------------------
REDDIT_CLIENT_ID=your-reddit-client-id
REDDIT_CLIENT_SECRET=your-reddit-client-secret
REDDIT_USER_AGENT=curriculum_builder/1.0

# -----------------------------------------------------------------------------
# SEARCH: Tavily (OPTIONAL - backup search)
# Get at: https://tavily.com/
# -----------------------------------------------------------------------------
TAVILY_API_KEY=tvly-your-key-here

# -----------------------------------------------------------------------------
# PODCASTS: Listen Notes (OPTIONAL)
# Get at: https://www.listennotes.com/api/
# -----------------------------------------------------------------------------
LISTENNOTES_API_KEY=your-listennotes-key

# -----------------------------------------------------------------------------
# DATABASE
# -----------------------------------------------------------------------------
DATABASE_URL=postgresql://postgres:password@localhost:5432/curriculum_builder
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your-db-password
POSTGRES_DB=curriculum_builder

# -----------------------------------------------------------------------------
# REDIS
# -----------------------------------------------------------------------------
REDIS_URL=redis://localhost:6379/0

# -----------------------------------------------------------------------------
# APPLICATION
# -----------------------------------------------------------------------------
SECRET_KEY=generate-a-random-secret-key-here
APP_ENV=development
DEBUG=true
BACKEND_PORT=8000
FRONTEND_URL=http://localhost:3000
```

---

## ⏱️ Time to Get All Keys

| API | Time | Difficulty |
|-----|------|------------|
| Anthropic | 5 min | Easy |
| AWS | 15 min | Medium (if new account) |
| Firecrawl | 2 min | Easy |
| Serper | 2 min | Easy |
| Reddit | 5 min | Easy |
| Tavily | 2 min | Easy |
| Listen Notes | 2 min | Easy |

**Total: ~30-45 minutes** to get all keys

---

## 🚀 Quick Start Order

Get these keys in this order:

1. **Anthropic** - Sign up, get key (5 min)
2. **Reddit** - Create app (5 min)  
3. **Serper** - Sign up, get key (2 min)
4. **Firecrawl** - Sign up, get key (2 min)
5. **AWS** - Ask Gabriel or create account (varies)

Once you have these 5, we can start building!

