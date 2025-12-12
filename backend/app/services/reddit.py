"""Reddit scraping service using Serper + Firecrawl + RSS feeds."""
import re
import httpx
import feedparser
from typing import Optional, Literal
from datetime import datetime
from textblob import TextBlob
from app.config import settings
from app.services.serpapi import serpapi_client
from app.services.firecrawl import firecrawl_client


class RedditScrapingClient:
    """Client for Reddit data without API keys - uses scraping and RSS."""
    
    # Target subreddits for career/education research
    DEFAULT_SUBREDDITS = [
        "careerguidance",
        "ITCareerQuestions",
        "cscareerquestions",
        "learnprogramming",
        "jobs",
        "GetEmployed",
        "computerscience",
        "datascience",
        "webdev",
    ]
    
    def __init__(self):
        self.serpapi = serpapi_client
        self.firecrawl = firecrawl_client
    
    # =========================================================================
    # RSS FEED METHODS (Free, No API Key Required)
    # =========================================================================
    
    async def get_subreddit_rss(
        self,
        subreddit: str,
        limit: int = 25,
        sort: str = "new"
    ) -> list[dict]:
        """
        Get recent posts from subreddit via RSS (no API key needed!).
        
        Args:
            subreddit: Subreddit name (without r/)
            limit: Number of posts (max 25 per RSS feed)
            sort: Sort method (new, hot, top, rising)
        
        Returns:
            List of posts with title, url, summary, score
        """
        url = f"https://www.reddit.com/r/{subreddit}/{sort}/.rss"
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, timeout=10.0)
                response.raise_for_status()
            
            feed = feedparser.parse(response.text)
            
            posts = []
            for entry in feed.entries[:limit]:
                # Extract upvote count from title (format: "[score] title")
                upvotes = self._extract_upvotes_from_rss(entry.get('title', ''))
                
                posts.append({
                    "id": entry.get('id', '').split('/')[-1],
                    "title": self._clean_rss_title(entry.get('title', '')),
                    "url": entry.get('link', ''),
                    "subreddit": subreddit,
                    "summary": self._clean_html(entry.get('summary', '')),
                    "published": entry.get('published', ''),
                    "upvotes": upvotes,
                    "source": "rss"
                })
            
            return posts
        
        except Exception as e:
            print(f"RSS fetch error for r/{subreddit}: {e}")
            return []
    
    async def get_recent_posts_bulk(
        self,
        subreddits: Optional[list[str]] = None,
        limit_per_sub: int = 10
    ) -> list[dict]:
        """
        Get recent posts from multiple subreddits via RSS.
        Fast and free - no API keys needed!
        """
        if not subreddits:
            subreddits = self.DEFAULT_SUBREDDITS
        
        all_posts = []
        for subreddit in subreddits:
            posts = await self.get_subreddit_rss(subreddit, limit=limit_per_sub)
            all_posts.extend(posts)
        
        # Sort by published date
        all_posts.sort(key=lambda x: x.get('published', ''), reverse=True)
        return all_posts
    
    # =========================================================================
    # SEARCH + SCRAPING METHODS (Uses Serper + Firecrawl)
    # =========================================================================
    
    async def search_and_scrape(
        self,
        query: str,
        subreddits: Optional[list[str]] = None,
        limit: int = 10,
        time_filter: str = "year"
    ) -> list[dict]:
        """
        Search Reddit via Google and scrape full content.
        
        Args:
            query: Search query
            subreddits: Specific subreddits to search (or None for all)
            limit: Number of results
            time_filter: Time filter (day, week, month, year)
        
        Returns:
            List of scraped posts with full content and metrics
        """
        # Build search query
        if subreddits:
            site_filter = " OR ".join([f"site:reddit.com/r/{sub}" for sub in subreddits])
        else:
            site_filter = "site:reddit.com"
        
        # Add time filter
        time_query = ""
        if time_filter == "day":
            time_query = "after:1d"
        elif time_filter == "week":
            time_query = "after:7d"
        elif time_filter == "month":
            time_query = "after:30d"
        elif time_filter == "year":
            time_query = "after:365d"
        
        search_query = f'({site_filter}) {query} {time_query}'
        
        # Search Google for Reddit threads
        search_results = await self.serpapi.search(search_query, num_results=limit * 2)
        
        # Filter for Reddit URLs only
        reddit_urls = [
            r for r in search_results 
            if 'reddit.com' in r.get('url', '') and '/comments/' in r.get('url', '')
        ][:limit]
        
        # Scrape each Reddit post
        scraped_posts = []
        for result in reddit_urls:
            try:
                scraped_data = await self._scrape_reddit_post(result['url'])
                if scraped_data:
                    scraped_data['search_title'] = result.get('title', '')
                    scraped_data['search_snippet'] = result.get('snippet', '')
                    scraped_posts.append(scraped_data)
            except Exception as e:
                print(f"Error scraping {result['url']}: {e}")
                continue
        
        return scraped_posts
    
    async def _scrape_reddit_post(self, url: str) -> Optional[dict]:
        """
        Scrape a single Reddit post using Firecrawl.
        Extracts upvotes, comments, ratio, and content.
        """
        try:
            # Use Firecrawl to scrape
            scraped = await self.firecrawl.scrape_url(url)
            
            markdown = scraped.get('markdown', '')
            metadata = scraped.get('metadata', {})
            
            # Extract metrics from the page
            upvotes = self._extract_upvotes(markdown)
            comments_count = self._extract_comment_count(markdown)
            upvote_ratio = self._extract_upvote_ratio(markdown)
            
            # Extract post content
            title = metadata.get('title', '') or self._extract_title(markdown)
            post_content = self._extract_post_content(markdown)
            top_comments = self._extract_top_comments(markdown, limit=5)
            
            # Extract subreddit from URL
            subreddit_match = re.search(r'/r/([^/]+)/', url)
            subreddit = subreddit_match.group(1) if subreddit_match else "unknown"
            
            return {
                "url": url,
                "title": title,
                "subreddit": subreddit,
                "upvotes": upvotes,
                "comments_count": comments_count,
                "upvote_ratio": upvote_ratio,
                "engagement_score": self._calculate_engagement(upvotes, comments_count, upvote_ratio),
                "post_content": post_content,
                "top_comments": top_comments,
                "full_markdown": markdown,
                "source": "scraped"
            }
        
        except Exception as e:
            print(f"Error in _scrape_reddit_post: {e}")
            return None
    
    # =========================================================================
    # MARKET VALIDATION METHODS
    # =========================================================================
    
    async def analyze_course_demand(
        self,
        course_topic: str,
        min_engagement_score: int = 100
    ) -> dict:
        """
        Analyze if a course topic is highly accepted or rejected on Reddit.
        
        Returns:
            Dictionary with highly_accepted, low_interest, and sentiment data
        """
        # Search for course discussions
        query = f'"{course_topic}" (worth it OR recommended OR "waste of time" OR review)'
        posts = await self.search_and_scrape(query, limit=15)
        
        highly_accepted = []
        low_interest = []
        neutral = []
        
        for post in posts:
            engagement = post.get('engagement_score', 0)
            ratio = post.get('upvote_ratio', 0.5)
            upvotes = post.get('upvotes', 0)
            
            # Classify based on engagement metrics
            if upvotes > 100 and ratio > 0.85:
                highly_accepted.append(post)
            elif upvotes < 20 or ratio < 0.65:
                low_interest.append(post)
            else:
                neutral.append(post)
        
        # Sentiment analysis
        overall_sentiment = await self._analyze_sentiment_bulk(posts)
        
        return {
            "topic": course_topic,
            "total_discussions": len(posts),
            "highly_accepted": highly_accepted,
            "low_interest": low_interest,
            "neutral": neutral,
            "sentiment": overall_sentiment,
            "recommendation": self._generate_recommendation(
                highly_accepted, low_interest, overall_sentiment
            )
        }
    
    async def compare_courses(
        self,
        course_options: list[str],
        topic_context: str = ""
    ) -> dict:
        """
        Compare multiple course options to find the most recommended.
        
        Args:
            course_options: List of course names to compare
            topic_context: Additional context (e.g., "Python", "AWS")
        
        Returns:
            Rankings and comparison data
        """
        rankings = {}
        
        for course in course_options:
            query = f'"{course}" {topic_context} (review OR experience OR vs OR best)'
            posts = await self.search_and_scrape(query, limit=8)
            
            if posts:
                total_upvotes = sum(p.get('upvotes', 0) for p in posts)
                avg_ratio = sum(p.get('upvote_ratio', 0.5) for p in posts) / len(posts)
                total_engagement = sum(p.get('engagement_score', 0) for p in posts)
                sentiment = await self._analyze_sentiment_bulk(posts)
                
                rankings[course] = {
                    "total_upvotes": total_upvotes,
                    "avg_upvote_ratio": round(avg_ratio, 2),
                    "total_engagement": total_engagement,
                    "mentions_found": len(posts),
                    "sentiment_score": sentiment['average_score'],
                    "positive_mentions": sentiment['positive_count'],
                    "negative_mentions": sentiment['negative_count'],
                    "sample_posts": posts[:3]  # Top 3 posts
                }
        
        # Sort by total engagement
        sorted_rankings = sorted(
            rankings.items(),
            key=lambda x: x[1]['total_engagement'],
            reverse=True
        )
        
        return {
            "comparison_query": topic_context,
            "courses_analyzed": len(course_options),
            "top_choice": sorted_rankings[0][0] if sorted_rankings else None,
            "least_recommended": sorted_rankings[-1][0] if sorted_rankings else None,
            "full_rankings": dict(sorted_rankings)
        }
    
    async def find_trending_skills(
        self,
        industry: str,
        limit: int = 20
    ) -> dict:
        """
        Find trending skills and topics in an industry based on Reddit discussions.
        """
        # Get recent discussions from relevant subreddits
        recent_posts = await self.get_recent_posts_bulk(limit_per_sub=limit)
        
        # Search for industry-specific trends
        query = f'{industry} (skills OR learning OR certification OR career path)'
        searched_posts = await self.search_and_scrape(query, limit=limit)
        
        all_posts = recent_posts + searched_posts
        
        # Extract trending topics
        trending = self._extract_trending_topics(all_posts)
        
        return {
            "industry": industry,
            "total_discussions_analyzed": len(all_posts),
            "trending_skills": trending['skills'],
            "hot_topics": trending['topics'],
            "certifications_mentioned": trending['certifications'],
        }
    
    # =========================================================================
    # SENTIMENT ANALYSIS
    # =========================================================================
    
    async def _analyze_sentiment_bulk(self, posts: list[dict]) -> dict:
        """Analyze sentiment across multiple posts."""
        if not posts:
            return {
                "average_score": 0.0,
                "positive_count": 0,
                "negative_count": 0,
                "neutral_count": 0
            }
        
        sentiments = []
        positive = 0
        negative = 0
        neutral = 0
        
        for post in posts:
            # Analyze title + content + top comments
            text = f"{post.get('title', '')} {post.get('post_content', '')}"
            
            # Add top comments to analysis
            for comment in post.get('top_comments', [])[:3]:
                text += f" {comment.get('text', '')}"
            
            blob = TextBlob(text)
            polarity = blob.sentiment.polarity
            
            sentiments.append(polarity)
            
            if polarity > 0.1:
                positive += 1
            elif polarity < -0.1:
                negative += 1
            else:
                neutral += 1
        
        return {
            "average_score": round(sum(sentiments) / len(sentiments), 3),
            "positive_count": positive,
            "negative_count": negative,
            "neutral_count": neutral
        }
    
    # =========================================================================
    # UTILITY METHODS
    # =========================================================================
    
    def _extract_upvotes(self, markdown: str) -> int:
        """Extract upvote count from scraped markdown."""
        # Look for patterns like "1.2k upvotes", "847 upvotes", etc.
        patterns = [
            r'(\d+\.?\d*[kK]?)\s*upvotes?',
            r'(\d+\.?\d*[kK]?)\s*points?',
            r'Score:\s*(\d+\.?\d*[kK]?)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, markdown, re.IGNORECASE)
            if match:
                return self._parse_number(match.group(1))
        
        return 0
    
    def _extract_comment_count(self, markdown: str) -> int:
        """Extract comment count from markdown."""
        patterns = [
            r'(\d+\.?\d*[kK]?)\s*comments?',
            r'(\d+\.?\d*[kK]?)\s*replies',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, markdown, re.IGNORECASE)
            if match:
                return self._parse_number(match.group(1))
        
        return 0
    
    def _extract_upvote_ratio(self, markdown: str) -> float:
        """Extract upvote ratio (e.g., 94% upvoted)."""
        pattern = r'(\d+)%\s*upvoted'
        match = re.search(pattern, markdown, re.IGNORECASE)
        
        if match:
            return int(match.group(1)) / 100.0
        
        return 0.5  # Default neutral ratio
    
    def _extract_title(self, markdown: str) -> str:
        """Extract post title from markdown."""
        # Usually the first heading
        lines = markdown.split('\n')
        for line in lines[:10]:
            if line.startswith('#'):
                return line.lstrip('#').strip()
        return ""
    
    def _extract_post_content(self, markdown: str) -> str:
        """Extract main post content (not comments)."""
        # Take content before the first "comments" section
        parts = re.split(r'comments?:', markdown, flags=re.IGNORECASE)
        if parts:
            # Get first 500 characters
            content = parts[0].strip()[:500]
            return content
        return ""
    
    def _extract_top_comments(self, markdown: str, limit: int = 5) -> list[dict]:
        """Extract top comments from markdown."""
        comments = []
        
        # Look for comment-like patterns (indented text, bullet points)
        lines = markdown.split('\n')
        
        for i, line in enumerate(lines):
            # Look for upvote counts that indicate comments
            if re.search(r'\d+\s*points?', line, re.IGNORECASE):
                comment_text = ""
                # Get next few lines as comment text
                for j in range(i+1, min(i+4, len(lines))):
                    if lines[j].strip() and not re.search(r'\d+\s*points?', lines[j]):
                        comment_text += lines[j].strip() + " "
                
                if comment_text:
                    upvotes = self._extract_upvotes(line)
                    comments.append({
                        "text": comment_text[:200],
                        "upvotes": upvotes
                    })
                
                if len(comments) >= limit:
                    break
        
        return comments
    
    def _calculate_engagement(self, upvotes: int, comments: int, ratio: float) -> int:
        """Calculate overall engagement score."""
        return int(upvotes * ratio + comments * 0.5)
    
    def _parse_number(self, num_str: str) -> int:
        """Parse numbers like '1.2k' to 1200."""
        num_str = num_str.strip().lower()
        
        if 'k' in num_str:
            return int(float(num_str.replace('k', '')) * 1000)
        
        return int(float(num_str))
    
    def _clean_rss_title(self, title: str) -> str:
        """Clean RSS feed title."""
        # Remove score prefix if present
        title = re.sub(r'^\[\d+\]\s*', '', title)
        return title.strip()
    
    def _clean_html(self, html: str) -> str:
        """Remove HTML tags from text."""
        return re.sub(r'<[^>]+>', '', html)
    
    def _extract_upvotes_from_rss(self, title: str) -> int:
        """Extract upvotes from RSS title format: [score] title."""
        match = re.match(r'\[(\d+)\]', title)
        if match:
            return int(match.group(1))
        return 0
    
    def _generate_recommendation(
        self,
        highly_accepted: list,
        low_interest: list,
        sentiment: dict
    ) -> str:
        """Generate a recommendation based on analysis."""
        if not highly_accepted and not low_interest:
            return "Insufficient data to make recommendation"
        
        if len(highly_accepted) > len(low_interest) * 2 and sentiment['average_score'] > 0.1:
            return "HIGHLY RECOMMENDED - Strong positive sentiment and engagement"
        elif len(highly_accepted) > len(low_interest):
            return "RECOMMENDED - Moderate positive sentiment"
        elif len(low_interest) > len(highly_accepted):
            return "NOT RECOMMENDED - Low engagement or negative sentiment"
        else:
            return "NEUTRAL - Mixed signals, needs more research"
    
    def _extract_trending_topics(self, posts: list[dict]) -> dict:
        """Extract trending topics from posts."""
        # Common skill keywords
        skill_keywords = {
            'python', 'javascript', 'java', 'react', 'aws', 'docker', 'kubernetes',
            'machine learning', 'ai', 'data science', 'cloud', 'devops', 'sql',
            'typescript', 'node', 'angular', 'vue', 'mongodb', 'postgresql'
        }
        
        cert_keywords = {
            'aws certified', 'azure', 'google cloud', 'comptia', 'cisco', 'cka',
            'ckad', 'pmp', 'scrum master', 'security+'
        }
        
        skill_mentions = {}
        cert_mentions = {}
        
        for post in posts:
            text = f"{post.get('title', '')} {post.get('summary', '')} {post.get('post_content', '')}".lower()
            
            for skill in skill_keywords:
                if skill in text:
                    skill_mentions[skill] = skill_mentions.get(skill, 0) + 1
            
            for cert in cert_keywords:
                if cert in text:
                    cert_mentions[cert] = cert_mentions.get(cert, 0) + 1
        
        # Sort by mentions
        top_skills = sorted(skill_mentions.items(), key=lambda x: x[1], reverse=True)[:10]
        top_certs = sorted(cert_mentions.items(), key=lambda x: x[1], reverse=True)[:5]
        
        return {
            "skills": [{"skill": k, "mentions": v} for k, v in top_skills],
            "certifications": [{"cert": k, "mentions": v} for k, v in top_certs],
            "topics": []  # Could extract more topics with NLP
        }
    
    # =========================================================================
    # MOCK DATA (for testing without API keys)
    # =========================================================================
    
    def _mock_search(self, query: str, limit: int) -> list[dict]:
        """Return mock data for testing."""
        return [
            {
                "id": "mock1",
                "title": f"Discussion about {query} - Career advice needed",
                "subreddit": "careerguidance",
                "upvotes": 150,
                "upvote_ratio": 0.92,
                "comments_count": 45,
                "engagement_score": 160,
                "url": "https://reddit.com/r/careerguidance/mock1",
                "post_content": f"I'm looking to get into {query}. What certifications should I get?",
                "top_comments": [
                    {"text": "I recommend starting with the fundamentals...", "upvotes": 50},
                    {"text": "Online courses are great for beginners!", "upvotes": 30},
                ],
                "source": "mock"
            },
            {
                "id": "mock2",
                "title": f"Best resources for learning {query}?",
                "subreddit": "learnprogramming",
                "upvotes": 89,
                "upvote_ratio": 0.88,
                "comments_count": 23,
                "engagement_score": 90,
                "url": "https://reddit.com/r/learnprogramming/mock2",
                "post_content": f"What are the best courses or books for {query}?",
                "top_comments": [
                    {"text": "Check out these top platforms...", "upvotes": 25},
                ],
                "source": "mock"
            },
        ][:limit]


# Singleton instance
reddit_client = RedditScrapingClient()
