"""Anthropic Claude client with rate limit handling."""
import asyncio
from anthropic import AsyncAnthropic, RateLimitError, APIError
from typing import Optional, AsyncGenerator
from app.config import settings


class ClaudeClient:
    """Client for Anthropic Claude API with retry logic."""
    
    def __init__(self):
        self.api_key = settings.anthropic_api_key
        self.model = settings.anthropic_model
        self._client = None
        self._max_retries = 3
        self._retry_delay = 2.0  # seconds
    
    @property
    def client(self) -> AsyncAnthropic:
        """Lazy initialization of Anthropic client."""
        if self._client is None:
            self._client = AsyncAnthropic(api_key=self.api_key)
        return self._client
    
    async def complete(
        self,
        prompt: str,
        system: Optional[str] = None,
        max_tokens: int = 4096,
        temperature: float = 0,
    ) -> str:
        """
        Get a completion from Claude with retry logic.
        
        Args:
            prompt: User prompt
            system: System prompt
            max_tokens: Maximum tokens in response
            temperature: Temperature for sampling
        
        Returns:
            Claude's response text
        """
        messages = [{"role": "user", "content": prompt}]
        
        kwargs = {
            "model": self.model,
            "max_tokens": max_tokens,
            "messages": messages,
            "temperature": temperature,
        }
        
        if system:
            kwargs["system"] = system
        
        last_error = None
        for attempt in range(self._max_retries):
            try:
                print(f"🔄 Claude API request (attempt {attempt + 1}/{self._max_retries})")
                # Add timeout of 120 seconds per request
                response = await asyncio.wait_for(
                    self.client.messages.create(**kwargs),
                    timeout=120.0
                )
                print(f"✅ Claude API response received")
                return response.content[0].text
            except asyncio.TimeoutError as e:
                last_error = e
                wait_time = self._retry_delay * (attempt + 1)
                print(f"⚠️ Claude API timeout, waiting {wait_time}s (attempt {attempt+1}/{self._max_retries})")
                await asyncio.sleep(wait_time)
            except RateLimitError as e:
                last_error = e
                wait_time = self._retry_delay * (attempt + 1)
                print(f"⚠️ Rate limited, waiting {wait_time}s (attempt {attempt+1}/{self._max_retries})")
                await asyncio.sleep(wait_time)
            except APIError as e:
                last_error = e
                if "overloaded" in str(e).lower():
                    wait_time = self._retry_delay * (attempt + 1)
                    print(f"⚠️ API overloaded, waiting {wait_time}s")
                    await asyncio.sleep(wait_time)
                else:
                    print(f"❌ Claude API error: {e}")
                    raise
            except Exception as e:
                print(f"❌ Unexpected Claude error: {e}")
                raise
        
        # If all retries failed
        raise last_error or Exception("Claude API failed after retries")
    
    async def stream(
        self,
        prompt: str,
        system: Optional[str] = None,
        max_tokens: int = 4096,
        temperature: float = 0,
    ) -> AsyncGenerator[str, None]:
        """
        Stream a completion from Claude.
        
        Args:
            prompt: User prompt
            system: System prompt
            max_tokens: Maximum tokens in response
            temperature: Temperature for sampling
        
        Yields:
            Chunks of Claude's response
        """
        messages = [{"role": "user", "content": prompt}]
        
        kwargs = {
            "model": self.model,
            "max_tokens": max_tokens,
            "messages": messages,
            "temperature": temperature,
        }
        
        if system:
            kwargs["system"] = system
        
        async with self.client.messages.stream(**kwargs) as stream:
            async for text in stream.text_stream:
                yield text
    
    async def analyze(
        self,
        content: str,
        task: str,
        output_format: str = "json",
    ) -> str:
        """
        Analyze content with a specific task.
        
        Args:
            content: Content to analyze
            task: Analysis task description
            output_format: Expected output format
        
        Returns:
            Analysis result
        """
        system = f"""You are an expert analyst. 
Your task: {task}
Output format: {output_format}
Be precise and factual. Only analyze what's in the content provided."""

        prompt = f"""Analyze the following content:

{content}

Provide your analysis:"""

        return await self.complete(prompt, system=system)


# Singleton instance
claude_client = ClaudeClient()

