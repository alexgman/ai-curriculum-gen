"""Anthropic Claude client."""
from anthropic import AsyncAnthropic
from typing import Optional, AsyncGenerator
from app.config import settings


class ClaudeClient:
    """Client for Anthropic Claude API."""
    
    def __init__(self):
        self.api_key = settings.anthropic_api_key
        self.model = settings.anthropic_model
        self._client = None
    
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
        Get a completion from Claude.
        
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
        
        response = await self.client.messages.create(**kwargs)
        
        return response.content[0].text
    
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

