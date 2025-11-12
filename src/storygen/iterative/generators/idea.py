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

    def __init__(
        self, model: str = "gpt-4", max_retries: int = 3, timeout: int = 600, verbose: bool = False
    ):
        """
        Initialize the idea generator.

        Args:
            model: LiteLLM model string (e.g., "gpt-4", "ollama/qwen3:30b")
            max_retries: Maximum number of retry attempts on failure
            timeout: Timeout in seconds for each API call (default: 600 = 10 minutes)
            verbose: Enable verbose logging of prompts and responses (default: False)
        """
        self.model = model
        self.max_retries = max_retries
        self.timeout = timeout
        self.verbose = verbose

    def _build_prompt(self, user_prompt: str, story_type: str) -> str:
        """
        Build the system and user prompt for idea generation.

        Args:
            user_prompt: The user's story idea prompt
            story_type: Type of story (flash-fiction, short-story, novelette, novella, novel)

        Returns:
            Formatted prompt string
        """
        # Scope guidance based on story type
        scope_guidance = {
            "flash-fiction": "This is FLASH FICTION (<1,500 words): Focus on a SINGLE moment or revelation. One scene, minimal characters, immediate impact.",
            "short-story": "This is a SHORT STORY (1,500-7,500 words): Focus on a single plot thread with clear beginning/middle/end. Limited characters (2-3 main), tight timeframe.",
            "novelette": "This is a NOVELETTE (7,500-17,500 words): Can include a subplot and more character development. Still focused, but room for complexity.",
            "novella": "This is a NOVELLA (17,500-40,000 words): Full story arc with subplots allowed. Multiple character arcs, deeper world-building.",
            "novel": "This is a NOVEL (40,000+ words): Expansive story with multiple plot threads, extensive world-building, complex character development.",
        }

        scope = scope_guidance.get(story_type, scope_guidance["short-story"])

        system_prompt = f"""You are a creative writing assistant helping to develop story ideas.

{scope}

Your task is to take a brief story concept and expand it into a detailed story idea APPROPRIATE FOR THIS LENGTH.

Return your response as valid JSON with these exact fields:
{{
  "raw_idea": "The original user prompt",
  "one_sentence": "A single compelling sentence that captures the core premise with a hook",
  "expanded": "2-3 detailed paragraphs expanding the concept, including main conflict and stakes",
  "genres": ["genre1", "genre2"],  // 1-3 specific genres (lowercase)
  "tone": "Descriptive tone/mood of the story",
  "themes": ["theme1", "theme2", "theme3"],  // 2-4 major themes
  "setting": "Where/when the story takes place"  // e.g., "1950s Paris", "Modern NYC", "Hyperborea"
}}

Requirements:
- one_sentence: Must be exactly ONE sentence with subject, conflict, and stakes
- expanded: Must be 2-3 full paragraphs (150-250 words total) - SCOPE the plot complexity to fit {story_type}
- genres: Be specific (e.g., ["sci-fi", "horror"] not just ["fiction"])
- themes: Universal themes that connect to premise (e.g., "mortality", "trust", "identity")
- setting: Specific time/place context. Scale detail to story length:
  * Flash/Short: Brief ("modern NYC", "1920s Paris")
  * Novelette+: More detail ("Hyperborea - ancient sorcerous empire", "Post-apocalyptic Detroit, 2087")

CRITICAL: The expanded premise should match the scope of a {story_type}. Don't suggest epic quests for flash fiction or single moments for novels.

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
        required_fields = [
            "raw_idea",
            "one_sentence",
            "expanded",
            "genres",
            "tone",
            "themes",
            "setting",
        ]
        missing = [f for f in required_fields if f not in data]
        if missing:
            raise IdeaGenerationError(f"Missing required fields: {missing}")

        # Validate types
        if not isinstance(data["genres"], list) or not data["genres"]:
            raise IdeaGenerationError("genres must be a non-empty list")

        if not isinstance(data["themes"], list) or not data["themes"]:
            raise IdeaGenerationError("themes must be a non-empty list")

        return data  # type: ignore[no-any-return]

    def generate(self, user_prompt: str, story_type: str = "short-story") -> StoryIdea:
        """
        Generate a story idea from a user prompt.

        Args:
            user_prompt: The user's story concept
            story_type: Type of story (flash-fiction, short-story, novelette, novella, novel)

        Returns:
            StoryIdea object

        Raises:
            IdeaGenerationError: If generation fails after all retries
        """
        system_prompt = self._build_prompt(user_prompt, story_type)

        last_error = None
        for attempt in range(self.max_retries):
            try:
                if self.verbose:
                    print("\n" + "=" * 80)
                    print("SENDING TO AI MODEL:")
                    print("=" * 80)
                    print(f"\nSYSTEM PROMPT:\n{system_prompt}\n")
                    print(f"\nUSER PROMPT:\n{user_prompt}\n")
                    print("=" * 80)

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

                if self.verbose:
                    print("\n" + "=" * 80)
                    print("RECEIVED FROM AI MODEL:")
                    print("=" * 80)
                    print(f"\n{response_text}\n")
                    print("=" * 80)

                # Parse and validate
                data = self._parse_response(response_text)

                if self.verbose:
                    print("\n" + "=" * 80)
                    print("PARSED STORY IDEA:")
                    print("=" * 80)
                    print(f"One-sentence: {data['one_sentence']}")
                    print(f"Genres: {', '.join(data['genres'])}")
                    print(f"Tone: {data['tone']}")
                    print(f"Themes: {', '.join(data['themes'])}")
                    print(f"Setting: {data['setting']}")
                    print("=" * 80)

                # Create StoryIdea (this validates and normalizes genres/themes)
                idea = StoryIdea(
                    raw_idea=data["raw_idea"],
                    one_sentence=data["one_sentence"],
                    expanded=data["expanded"],
                    genres=data["genres"],
                    tone=data["tone"],
                    themes=data["themes"],
                    setting=data["setting"],
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
