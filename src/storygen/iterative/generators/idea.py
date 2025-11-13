"""
Story idea generation using AI.
"""

from typing import Any

from storygen.iterative.generators.base import BaseGenerator, GenerationError
from storygen.iterative.models import StoryIdea


class IdeaGenerationError(GenerationError):
    """Raised when idea generation fails."""

    pass


class IdeaGenerator(BaseGenerator[StoryIdea]):
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
        super().__init__(model=model, max_retries=max_retries, timeout=timeout, verbose=verbose)

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
        # Use base class JSON parsing
        data = self.parse_json_response(
            response_text,
            required_fields=[
                "raw_idea",
                "one_sentence",
                "expanded",
                "genres",
                "tone",
                "themes",
                "setting",
            ],
            error_class=IdeaGenerationError,
        )

        # Additional validation specific to ideas
        if not isinstance(data["genres"], list) or not data["genres"]:
            raise IdeaGenerationError("genres must be a non-empty list")

        if not isinstance(data["themes"], list) or not data["themes"]:
            raise IdeaGenerationError("themes must be a non-empty list")

        return data

    def _log_parsed(self, parsed_data: Any) -> None:
        """Override to provide custom logging for idea data."""
        if self.verbose:
            self.logger.debug("=" * 80)
            self.logger.debug("PARSED STORY IDEA:")
            self.logger.debug("=" * 80)
            self.logger.debug(f"One-sentence: {parsed_data['one_sentence']}")
            self.logger.debug(f"Genres: {', '.join(parsed_data['genres'])}")
            self.logger.debug(f"Tone: {parsed_data['tone']}")
            self.logger.debug(f"Themes: {', '.join(parsed_data['themes'])}")
            self.logger.debug(f"Setting: {parsed_data['setting']}")
            self.logger.debug("=" * 80)

    def generate(
        self, user_prompt: str, story_type: str = "short-story"
    ) -> tuple[StoryIdea, dict[str, Any]]:
        """
        Generate a story idea from a user prompt.

        Args:
            user_prompt: The user's story concept
            story_type: Type of story (flash-fiction, short-story, novelette, novella, novel)

        Returns:
            Tuple of (StoryIdea object, usage_info dict)

        Raises:
            IdeaGenerationError: If generation fails after all retries
        """
        system_prompt = self._build_prompt(user_prompt, story_type)

        # Use the new JSON parser method
        data, usage_info = self.generate_with_json_parser(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            required_fields=[
                "raw_idea",
                "one_sentence",
                "expanded",
                "genres",
                "tone",
                "themes",
                "setting",
            ],
            temperature=0.8,
            error_class=IdeaGenerationError,
        )

        # Convert to StoryIdea object
        story_idea = StoryIdea(
            raw_idea=data["raw_idea"],
            one_sentence=data["one_sentence"],
            expanded=data["expanded"],
            genres=data["genres"],
            tone=data["tone"],
            themes=data["themes"],
            setting=data["setting"],
        )

        return story_idea, usage_info
