"""
A story generator powered by AI models via LiteLLM.

Supports multiple AI providers:
- OpenAI (GPT models)
- Anthropic (Claude models)
- xAI (Grok models)
- Ollama (local models like llama2, qwen3, mistral)
"""

import litellm
from typing import Optional


class StoryGenerator:
    """Generate creative short stories using various AI models."""
    
    def __init__(self, provider: str = "gpt-4o-mini"):
        """
        Initialize the story generator.
        
        Args:
            provider: AI model to use (e.g., "gpt-4o-mini", "claude-3-5-sonnet-20241022", 
                     "grok-2-1212", "ollama/llama2", "ollama/qwen3:30b")
                     
        Note: Reasoning models (like qwen3) need higher max_tokens (2000+) to complete
        their thinking process before outputting the story.
        """
        self.provider = provider
    
    def generate(self, prompt: str, max_tokens: Optional[int] = 1000) -> str:
        """
        Generate a short story from a prompt.
        
        Args:
            prompt: The story prompt or theme
            max_tokens: Maximum length of the generated story (use 2000+ for reasoning models)
            
        Returns:
            Generated story as a string
            
        Raises:
            ValueError: If the response is empty or invalid
        """
        response = litellm.completion(
            model=self.provider,
            messages=[
                {
                    "role": "system",
                    "content": "You are a creative writer. Write engaging short stories based on the user's prompt."
                },
                {"role": "user", "content": prompt}
            ],
            max_tokens=max_tokens
        )
        
        # Type-safe access to response content
        # Note: LiteLLM returns dynamic types, suppress type checker warnings
        if not response or not hasattr(response, 'choices') or not response.choices:  # type: ignore
            raise ValueError("Invalid response from AI provider")
        
        content = response.choices[0].message.content  # type: ignore
        if content is None:
            raise ValueError("AI provider returned empty content")
        
        return str(content)
