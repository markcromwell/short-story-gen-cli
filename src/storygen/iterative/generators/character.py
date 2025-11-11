"""
Character generation using AI.
"""

import json
import time
from typing import Any

import litellm

from storygen.iterative.models import Character, StoryIdea


class CharacterGenerationError(Exception):
    """Raised when character generation fails."""

    pass


class CharacterGenerator:
    """Generates characters using AI with retry logic."""

    def __init__(self, model: str = "gpt-4", max_retries: int = 3, timeout: int = 60):
        """
        Initialize the character generator.

        Args:
            model: LiteLLM model string (e.g., "gpt-4", "ollama/qwen3:30b")
            max_retries: Maximum number of retry attempts on failure
            timeout: Timeout in seconds for each API call
        """
        self.model = model
        self.max_retries = max_retries
        self.timeout = timeout

    def _build_prompt(self, story_idea: StoryIdea) -> tuple[str, str]:
        """
        Build the system and user prompt for character generation.

        Args:
            story_idea: The story idea to generate characters for

        Returns:
            Tuple of (system_prompt, user_prompt)
        """
        system_prompt = """You are a creative writing assistant helping to develop characters for a story.

Your task is to create 3-5 well-developed characters that fit the story concept.

Return your response as valid JSON with this structure:
{
  "characters": [
    {
      "name": "Full character name",
      "role": "protagonist|antagonist|mentor|ally|foil",
      "bio": "2-3 sentence background and personality",
      "goal": "What they want in this story",
      "flaw": "Their main weakness or character flaw",
      "arc": "How they might change (optional, can be null)"
    }
  ]
}

Requirements:
- Generate 3-5 characters total
- Must include: 1 protagonist, 1 antagonist
- May include: mentor, ally, foil, or other supporting roles
- Each character should be distinct and complement the others
- Goals should create conflict and drive the story
- Flaws should be meaningful and create obstacles

Return ONLY valid JSON, no other text or markdown formatting."""

        user_prompt = f"""Story Concept:
Title idea: {story_idea.one_sentence}

Full premise:
{story_idea.expanded}

Genres: {', '.join(story_idea.genres)}
Tone: {story_idea.tone}
Themes: {', '.join(story_idea.themes)}

Generate 3-5 characters for this story."""

        return system_prompt, user_prompt

    def _parse_response(self, response_text: str) -> list[dict[str, Any]]:
        """
        Parse and validate AI response.

        Args:
            response_text: Raw text from AI

        Returns:
            List of character dicts

        Raises:
            CharacterGenerationError: If response is invalid
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
            raise CharacterGenerationError(f"Failed to parse JSON response: {e}")

        # Validate structure
        if "characters" not in data:
            raise CharacterGenerationError("Response missing 'characters' field")

        characters = data["characters"]
        if not isinstance(characters, list):
            raise CharacterGenerationError("'characters' must be a list")

        if len(characters) < 3 or len(characters) > 5:
            raise CharacterGenerationError(f"Must generate 3-5 characters, got {len(characters)}")

        # Validate each character has required fields
        required_fields = ["name", "role", "bio", "goal", "flaw"]
        for i, char in enumerate(characters):
            missing = [f for f in required_fields if f not in char]
            if missing:
                raise CharacterGenerationError(f"Character {i} missing required fields: {missing}")

        # Validate roles
        roles = [c["role"] for c in characters]
        if "protagonist" not in roles:
            raise CharacterGenerationError("Must have at least one protagonist")
        if "antagonist" not in roles:
            raise CharacterGenerationError("Must have at least one antagonist")

        return characters

    def generate(self, story_idea: StoryIdea) -> list[Character]:
        """
        Generate characters for a story idea.

        Args:
            story_idea: The story concept to generate characters for

        Returns:
            List of Character objects

        Raises:
            CharacterGenerationError: If generation fails after all retries
        """
        system_prompt, user_prompt = self._build_prompt(story_idea)

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
                    temperature=0.8,
                    stream=False,
                )

                # Extract response
                if not hasattr(response, "choices") or not response.choices:  # type: ignore[union-attr]
                    raise CharacterGenerationError("Invalid response format from AI model")

                response_text = response.choices[0].message.content  # type: ignore[union-attr]
                if not response_text:
                    raise CharacterGenerationError("Empty response from AI model")

                # Parse and validate
                char_dicts = self._parse_response(response_text)

                # Create Character objects
                characters = []
                for char_data in char_dicts:
                    char = Character(
                        name=char_data["name"],
                        role=char_data["role"],
                        bio=char_data["bio"],
                        goal=char_data["goal"],
                        flaw=char_data["flaw"],
                        arc=char_data.get("arc"),  # Optional field
                    )
                    characters.append(char)

                return characters

            except Exception as e:
                last_error = e

                # Don't retry on validation errors (bad prompt/model)
                if isinstance(e, CharacterGenerationError | ValueError):
                    # Wait briefly before retry
                    if attempt < self.max_retries - 1:
                        wait_time = 2**attempt  # Exponential backoff
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
        raise CharacterGenerationError(
            f"Failed to generate characters after {self.max_retries} attempts. "
            f"Last error: {last_error}"
        )
