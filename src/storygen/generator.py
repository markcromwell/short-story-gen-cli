"""
Story Generator using LiteLLM for multi-provider support
"""
import litellm
from typing import Optional


class StoryGenerator:
    """
    Generate short stories using various AI providers via LiteLLM.
    
    Supports:
    - OpenAI: gpt-4, gpt-3.5-turbo
    - Anthropic: claude-3-sonnet, claude-3-opus
    - Local: ollama/llama2, ollama/mistral
    - Free: openrouter free models
    """
    
    def __init__(self, provider: str = "gpt-3.5-turbo"):
        """
        Initialize the story generator with a specific AI provider.
        
        Args:
            provider: Model identifier (e.g., "gpt-4", "claude-3-sonnet", "ollama/llama2")
        """
        self.provider = provider
        
    def generate(self, prompt: str, max_tokens: Optional[int] = 1000) -> str:
        """
        Generate a short story from a prompt.
        
        Args:
            prompt: The story prompt or theme
            max_tokens: Maximum length of the generated story
            
        Returns:
            Generated story as a string
        """
        system_message = (
            "You are a creative short story writer. "
            "Generate an engaging short story based on the user's prompt. "
            "Keep it concise, vivid, and complete."
        )
        
        response = litellm.completion(
            model=self.provider,
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": prompt}
            ],
            max_tokens=max_tokens
        )
        
        return response.choices[0].message.content
