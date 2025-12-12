"""Firecrawl client for web scraping."""
import httpx
from typing import Optional
from app.config import settings


class FirecrawlClient:
    """Client for Firecrawl web scraping API."""
    
    BASE_URL = "https://api.firecrawl.dev/v1"
    
    def __init__(self):
        self.api_key = settings.firecrawl_api_key
    
    async def scrape(self, url: str) -> dict:
        """
        Scrape a webpage and extract content.
        
        Args:
            url: The URL to scrape
        
        Returns:
            Extracted content as markdown and metadata
        """
        if not self.api_key:
            # Return mock data if no API key
            return self._mock_scrape(url)
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        
        payload = {
            "url": url,
            "formats": ["markdown", "html"],
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.BASE_URL}/scrape",
                headers=headers,
                json=payload,
                timeout=60.0,
            )
            response.raise_for_status()
            data = response.json()
        
        return {
            "url": url,
            "title": data.get("data", {}).get("metadata", {}).get("title", ""),
            "description": data.get("data", {}).get("metadata", {}).get("description", ""),
            "markdown": data.get("data", {}).get("markdown", ""),
            "html": data.get("data", {}).get("html", ""),
        }
    
    async def crawl(self, url: str, max_pages: int = 10) -> list[dict]:
        """
        Crawl a website and extract content from multiple pages.
        
        Args:
            url: Starting URL
            max_pages: Maximum pages to crawl
        
        Returns:
            List of extracted pages
        """
        if not self.api_key:
            return [self._mock_scrape(url)]
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        
        payload = {
            "url": url,
            "limit": max_pages,
            "scrapeOptions": {
                "formats": ["markdown"],
            }
        }
        
        async with httpx.AsyncClient() as client:
            # Start crawl
            response = await client.post(
                f"{self.BASE_URL}/crawl",
                headers=headers,
                json=payload,
                timeout=30.0,
            )
            response.raise_for_status()
            crawl_data = response.json()
            
            crawl_id = crawl_data.get("id")
            if not crawl_id:
                return []
            
            # Poll for results (simplified - in production use webhooks)
            import asyncio
            for _ in range(30):  # Max 30 attempts
                await asyncio.sleep(2)
                status_response = await client.get(
                    f"{self.BASE_URL}/crawl/{crawl_id}",
                    headers=headers,
                    timeout=30.0,
                )
                status_data = status_response.json()
                
                if status_data.get("status") == "completed":
                    return status_data.get("data", [])
                elif status_data.get("status") == "failed":
                    raise Exception(f"Crawl failed: {status_data.get('error')}")
        
        return []
    
    def _mock_scrape(self, url: str) -> dict:
        """Return mock data for testing."""
        return {
            "url": url,
            "title": "Mock Course Page",
            "description": "This is a mock course page for testing.",
            "markdown": """
# Course Curriculum

## Module 1: Introduction
- Lesson 1.1: Getting Started
- Lesson 1.2: Basic Concepts

## Module 2: Core Skills
- Lesson 2.1: Fundamental Techniques
- Lesson 2.2: Advanced Methods

## Module 3: Practical Application
- Lesson 3.1: Real-world Projects
- Lesson 3.2: Case Studies
""",
            "html": "<html><body>Mock HTML content</body></html>",
        }


# Singleton instance
firecrawl_client = FirecrawlClient()

