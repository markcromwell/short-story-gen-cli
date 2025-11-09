"""
A story generator powered by AI models via LiteLLM.

Supports multiple AI providers:
- OpenAI (GPT models)
- Anthropic (Claude models)
- xAI (Grok models)
- Ollama (local models like llama2, qwen3, mistral)
"""

import json
from typing import Optional

import litellm

from storygen.models import Story


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

    def generate(
        self, prompt: str, max_tokens: Optional[int] = 1000, structured: bool = False
    ) -> str:
        """
        Generate a short story from a prompt.

        Args:
            prompt: The story prompt or theme
            max_tokens: Maximum length of the generated story (use 2000+ for reasoning models)
            structured: If True, returns JSON with title and scenes

        Returns:
            Generated story as a string (plain text or JSON if structured=True)

        Raises:
            ValueError: If the response is empty or invalid
        """
        system_content = (
            "You are a creative writer. Write engaging short stories based on the user's prompt."
        )

        if structured:
            system_content += """

Return the story as JSON in this exact format:
{
    "title": "Story Title",
    "genre": "Genre (e.g., Sci-Fi, Fantasy, Mystery)",
    "summary": "Brief one-sentence summary",
    "scenes": [
        {
            "number": 1,
            "title": "Scene Title",
            "setting": "Where this scene takes place",
            "characters": ["Character1", "Character2"],
            "content": "The actual scene content/narrative"
        }
    ]
}

Write 2-4 scenes with rich narrative content."""

        response = litellm.completion(
            model=self.provider,
            messages=[
                {"role": "system", "content": system_content},
                {"role": "user", "content": prompt},
            ],
            max_tokens=max_tokens,
        )

        # Type-safe access to response content
        # Note: LiteLLM returns dynamic types, suppress type checker warnings
        if not response or not hasattr(response, "choices") or not response.choices:  # type: ignore
            raise ValueError("Invalid response from AI provider")

        content = response.choices[0].message.content  # type: ignore
        if content is None:
            raise ValueError("AI provider returned empty content")

        return str(content)

    def generate_structured(self, prompt: str, max_tokens: Optional[int] = 2000) -> Story:
        """
        Generate a structured story with title, scenes, and metadata.

        Args:
            prompt: The story prompt or theme
            max_tokens: Maximum length (use 2000+ for detailed stories)

        Returns:
            Story object with structured data

        Raises:
            ValueError: If the response is empty, invalid, or not valid JSON
        """
        content = self.generate(prompt, max_tokens=max_tokens, structured=True)

        # Extract JSON from markdown code blocks if present
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()

        try:
            return Story.from_json(content)
        except (json.JSONDecodeError, KeyError) as e:
            raise ValueError(f"Failed to parse structured story: {e}\n\nContent: {content}")
