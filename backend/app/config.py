"""Application configuration using Pydantic Settings."""
from pydantic_settings import BaseSettings
from functools import lru_cache
import os
from pathlib import Path

# Get the project root directory (two levels up from this file)
PROJECT_ROOT = Path(__file__).parent.parent.parent
ENV_FILE = PROJECT_ROOT / ".env"


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Application
    app_name: str = "AI Curriculum Builder"
    app_env: str = "development"
    debug: bool = True
    api_version: str = "v1"
    
    # Server
    backend_host: str = "0.0.0.0"
    backend_port: int = 8000
    
    # Database
    database_url: str = "postgresql+asyncpg://postgres:password@localhost:5432/curriculum_builder"
    
    # Redis
    redis_url: str = "redis://localhost:6379/0"
    
    # Anthropic (Claude)
    anthropic_api_key: str = ""
    anthropic_model: str = "claude-sonnet-4-20250514"
    
    # SerpAPI / Serper (Google Search)
    serpapi_api_key: str = ""
    serper_api_key: str = ""  # Alternative name
    
    @property
    def search_api_key(self) -> str:
        """Get search API key (supports both SERPER and SERPAPI)."""
        return self.serper_api_key or self.serpapi_api_key
    
    # Firecrawl (Web Scraping)
    firecrawl_api_key: str = ""
    
    # Reddit
    reddit_client_id: str = ""
    reddit_client_secret: str = ""
    reddit_user_agent: str = "curriculum_builder/1.0"
    
    # Listen Notes (Podcast Search)
    listennotes_api_key: str = ""
    
    # CORS
    cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000"
    
    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",")]
    
    class Config:
        env_file = str(ENV_FILE)
        env_file_encoding = "utf-8"
        extra = "ignore"  # Ignore extra fields in .env


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


settings = get_settings()

