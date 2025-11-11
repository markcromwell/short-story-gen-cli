"""
Story idea generation using AI.
"""

import json
import time
from typing import Any

import litellm

from storygen.iterative.models import StoryIdea


class IdeaGenerationError(Exception):
    """Raised when idea generation fails."""

    pass


class IdeaGenerator:
    """Generates story ideas using AI with retry logic."""

    def __init__(self, model: str = "gpt-4", max_retries: int = 3, timeout: int = 60):
        """
        Initialize the idea generator.

        Args:
            model: LiteLLM model string (e.g., "gpt-4", "ollama/qwen3:30b")
            max_retries: Maximum number of retry attempts on failure
            timeout: Timeout in seconds for each API call
        """
        self.model = model
        self.max_retries = max_retries
        self.timeout = timeout

    def _build_prompt(self, user_prompt: str) -> str:
        """
        Build the system and user prompt for idea generation.

        Args:
            user_prompt: The user's story idea prompt

        Returns:
            Formatted prompt string
        """
        system_prompt = """You are a creative writing assistant helping to develop story ideas.

Your task is to take a brief story concept and expand it into a detailed story idea.

Return your response as valid JSON with these exact fields:
{
  "raw_idea": "The original user prompt",
  "one_sentence": "A single compelling sentence that captures the core premise with a hook",
  "expanded": "2-3 detailed paragraphs expanding the concept, including main conflict and stakes",
  "genres": ["genre1", "genre2"],  // 1-3 specific genres (lowercase)
  "tone": "Descriptive tone/mood of the story",
  "themes": ["theme1", "theme2", "theme3"]  // 2-4 major themes
}

Requirements:
- one_sentence: Must be exactly ONE sentence with subject, conflict, and stakes
- expanded: Must be 2-3 full paragraphs (150-250 words total)
- genres: Be specific (e.g., ["sci-fi", "horror"] not just ["fiction"])
- themes: Universal themes that connect to premise (e.g., "mortality", "trust", "identity")

Return ONLY valid JSON, no other text or markdown formatting."""

        return system_prompt

    def _parse_response(self, response_text: str) -> dict[str, Any]:
        """
        Parse and validate AI response.

        Args:
            response_text: Raw text from AI

        Returns:
            Parsed JSON dict

        Raises:
            IdeaGenerationError: If response is invalid
        """
        # Try to extract JSON if wrapped in markdown code blocks
        text = response_text.strip()
        if text.startswith("```json"):
            text = text[7:]
        if text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]
        text = text.strip()

        try:
            data = json.loads(text)
        except json.JSONDecodeError as e:
            raise IdeaGenerationError(f"Failed to parse JSON response: {e}")

        # Validate required fields
        required_fields = ["raw_idea", "one_sentence", "expanded", "genres", "tone", "themes"]
        missing = [f for f in required_fields if f not in data]
        if missing:
            raise IdeaGenerationError(f"Missing required fields: {missing}")

        # Validate types
        if not isinstance(data["genres"], list) or not data["genres"]:
            raise IdeaGenerationError("genres must be a non-empty list")

        if not isinstance(data["themes"], list) or not data["themes"]:
            raise IdeaGenerationError("themes must be a non-empty list")

        return data  # type: ignore[no-any-return]

    def generate(self, user_prompt: str) -> StoryIdea:
        """
        Generate a story idea from a user prompt.

        Args:
            user_prompt: The user's story concept

        Returns:
            StoryIdea object

        Raises:
            IdeaGenerationError: If generation fails after all retries
        """
        system_prompt = self._build_prompt(user_prompt)

        last_error = None
        for attempt in range(self.max_retries):
            try:
                # Call AI
                response = litellm.completion(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    timeout=self.timeout,
                    temperature=0.8,  # Creative but not too random
                    stream=False,  # Explicitly disable streaming
                )

                # Extract response
                # Note: litellm has complex return types, we use type: ignore for dynamic attributes
                if not hasattr(response, "choices") or not response.choices:  # type: ignore[union-attr]
                    raise IdeaGenerationError("Invalid response format from AI model")

                response_text = response.choices[0].message.content  # type: ignore[union-attr]
                if not response_text:
                    raise IdeaGenerationError("Empty response from AI model")

                # Parse and validate
                data = self._parse_response(response_text)

                # Create StoryIdea (this validates and normalizes genres/themes)
                idea = StoryIdea(
                    raw_idea=data["raw_idea"],
                    one_sentence=data["one_sentence"],
                    expanded=data["expanded"],
                    genres=data["genres"],
                    tone=data["tone"],
                    themes=data["themes"],
                )

                return idea

            except Exception as e:
                last_error = e

                # Don't retry on validation errors (bad prompt/model)
                if isinstance(e, IdeaGenerationError | ValueError):
                    # Wait briefly before retry
                    if attempt < self.max_retries - 1:
                        wait_time = 2**attempt  # Exponential backoff: 1s, 2s, 4s
                        time.sleep(wait_time)
                    continue

                # Retry on network/timeout errors
                if attempt < self.max_retries - 1:
                    wait_time = 2**attempt
                    time.sleep(wait_time)
                    continue

                # Last attempt failed
                break

        # All retries exhausted
        raise IdeaGenerationError(
            f"Failed to generate idea after {self.max_retries} attempts. "
            f"Last error: {last_error}"
        )
