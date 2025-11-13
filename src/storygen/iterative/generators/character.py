"""
Character generation using AI.
"""

from typing import Any

from storygen.iterative.generators.base import BaseGenerator, GenerationError
from storygen.iterative.models import Character, StoryIdea


class CharacterGenerationError(GenerationError):
    """Raised when character generation fails."""

    pass


class CharacterGenerator(BaseGenerator[list[Character]]):
    """Generates characters using AI with retry logic."""

    def __init__(
        self, model: str = "gpt-4", max_retries: int = 3, timeout: int = 600, verbose: bool = False
    ):
        """
        Initialize the character generator.

        Args:
            model: LiteLLM model string (e.g., "gpt-4", "ollama/qwen3:30b")
            max_retries: Maximum number of retry attempts on failure
            timeout: Timeout in seconds for each API call (default: 600 = 10 minutes)
            verbose: Enable verbose logging of prompts and responses (default: False)
        """
        super().__init__(model=model, max_retries=max_retries, timeout=timeout, verbose=verbose)

    def _get_naming_guidance(self, genres: list[str], tone: str) -> str:
        """
        Generate style-appropriate naming guidance based on genre and tone.

        Args:
            genres: List of story genres
            tone: Story tone

        Returns:
            Naming guidance string for the prompt
        """
        # Check for specific styles that need special naming
        genres_lower = [g.lower() for g in genres]
        tone_lower = tone.lower()

        # Clark Ashton Smith / Weird Fiction
        if any(word in tone_lower for word in ["baroque", "decadent", "archaic", "ornate"]) or any(
            g in genres_lower for g in ["cosmic horror", "weird fiction"]
        ):
            return """NAMING GUIDELINES (Clark Ashton Smith / Weird Fiction style):
- Use archaic, exotic names with unusual phonemes: Malygris, Namirrha, Tsathoggua, Xeethra
- Avoid common fantasy names (NO: Elara, Kael, Aiden, Lyra, Aria)
- Consider: invented words, ancient-sounding syllables, names that evoke decay/beauty
- Examples: Zothique, Cylarne, Vacharn, Haon-Dor, Yadar, Uoht"""

        # Historical periods
        elif any(word in tone_lower for word in ["victorian", "regency", "medieval", "ancient"]):
            return """NAMING GUIDELINES (Historical):
- Research period-appropriate names for the setting
- Avoid anachronistic modern names
- Consider social class, ethnicity, and time period"""

        # Hard SF / Futuristic
        elif any(g in genres_lower for g in ["hard science fiction", "cyberpunk", "space opera"]):
            return """NAMING GUIDELINES (Science Fiction):
- Consider cultural diversity and future naming trends
- Mix traditional and invented names
- Avoid fantasy tropes (no Elara, Zephyr, etc.)
- Examples: surnames-as-first-names, multicultural names, tech-influenced names"""

        # Contemporary
        elif any(
            g in genres_lower for g in ["contemporary", "literary fiction", "thriller", "mystery"]
        ):
            return """NAMING GUIDELINES (Contemporary):
- Use realistic, diverse modern names
- Consider character ethnicity, age, background
- Avoid fantasy/sci-fi naming conventions"""

        # Generic fantasy (least restrictive but still warn about overused names)
        elif any(g in genres_lower for g in ["fantasy", "dark fantasy", "epic fantasy"]):
            return """NAMING GUIDELINES (Fantasy):
- AVOID overused AI-favorite names: Elara, Kael, Aiden, Lyra, Aria, Zara, Thorne
- Create unique names fitting your specific world
- Consider: cultural influences, invented languages, meaningful etymology"""

        # Default
        return """NAMING GUIDELINES:
- Choose names appropriate to the story's setting and tone
- Avoid generic or overused names
- Make names memorable and distinct from each other"""

    def _build_prompt(
        self, story_idea: StoryIdea, story_type: str = "short-story"
    ) -> tuple[str, str]:
        """
        Build the system and user prompt for character generation.

        Args:
            story_idea: The story idea to generate characters for
            story_type: Type of story (flash-fiction, short-story, novelette, novella, novel)

        Returns:
            Tuple of (system_prompt, user_prompt)
        """
        # Character count guidance based on story type
        char_counts = {
            "flash-fiction": (1, 2, "1-2 core characters (minimal cast for focused moment)"),
            "short-story": (1, 3, "1-3 core characters (tight focus on protagonist)"),
            "novelette": (2, 3, "2-3 core characters (room for deeper relationships)"),
            "novella": (3, 5, "3-5 core characters (multiple perspectives possible)"),
            "novel": (5, 8, "5-8+ core characters (expansive cast with depth)"),
        }

        min_chars, max_chars, count_desc = char_counts.get(
            story_type, (1, 3, "1-3 core characters")
        )

        # Build style-aware naming guidance
        naming_guidance = self._get_naming_guidance(story_idea.genres, story_idea.tone)

        system_prompt = f"""You are a creative writing assistant helping to develop characters for a story.

STORY LENGTH: {story_type.upper()}
CHARACTER COUNT: {count_desc}

Your task is to create {min_chars}-{max_chars} CORE characters that are absolutely essential to the story premise.

{naming_guidance}

Return your response as valid JSON with this structure:
{{
  "characters": [
    {{
      "name": "Character name (follow naming guidelines above)",
      "role": "protagonist|antagonist|mentor|ally|foil",
      "bio": "2-3 sentence background and personality",
      "goal": "What they want in this story",
      "flaw": "Their main weakness or character flaw",
      "arc": "How they might change (optional, can be null)"
    }}
  ]
}}

Requirements:
- Generate {min_chars}-{max_chars} CORE characters only
- Must include: 1 protagonist
- Only include antagonist if absolutely central to the premise
- AVOID: Generic fantasy names (Elara, Aiden, Kael), modern names in historical/fantasy settings
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
Setting: {story_idea.setting}

IMPORTANT: Generate characters with names appropriate to the setting "{story_idea.setting}".
Consider the time period, culture, and location when choosing names and character details.

Generate {min_chars}-{max_chars} characters appropriate for a {story_type}."""

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
        # Use base class JSON parsing (without required_fields since we validate structure below)
        data = self.parse_json_response(response_text, error_class=CharacterGenerationError)

        # Validate structure specific to characters
        if "characters" not in data:
            raise CharacterGenerationError("Response missing 'characters' field")

        characters = data["characters"]
        if not isinstance(characters, list):
            raise CharacterGenerationError("'characters' must be a list")

        if len(characters) < 1 or len(characters) > 8:
            raise CharacterGenerationError(
                f"Must generate 1-8 core characters, got {len(characters)}"
            )

        # Validate each character has required fields
        required_fields = ["name", "role", "bio", "goal", "flaw"]
        for i, char in enumerate(characters):
            missing = [f for f in required_fields if f not in char]
            if missing:
                raise CharacterGenerationError(f"Character {i} missing required fields: {missing}")

        # Validate roles - only require protagonist
        roles = [c["role"] for c in characters]
        if "protagonist" not in roles:
            raise CharacterGenerationError("Must have at least one protagonist")

        return characters

    def generate(self, story_idea: StoryIdea, story_type: str = "short-story") -> list[Character]:
        """
        Generate characters for a story idea.

        Args:
            story_idea: The story concept to generate characters for
            story_type: Type of story (flash-fiction, short-story, novelette, novella, novel)

        Returns:
            List of Character objects

        Raises:
            CharacterGenerationError: If generation fails after all retries
        """
        system_prompt, user_prompt = self._build_prompt(story_idea, story_type)

        # Parser that converts response text to list of Characters
        def parse_to_characters(response_text: str) -> list[Character]:
            char_dicts = self._parse_response(response_text)
            characters: list[Character] = []
            for char_data in char_dicts:
                char = Character(  # type: ignore
                    name=char_data["name"],
                    role=char_data["role"],
                    bio=char_data["bio"],
                    goal=char_data["goal"],
                    flaw=char_data["flaw"],
                    arc=char_data.get("arc"),  # Optional field
                )
                characters.append(char)  # type: ignore
            return characters

        # Use base class retry logic
        return self._generate_with_retry(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            parser=parse_to_characters,
            temperature=0.8,
            error_class=CharacterGenerationError,
        )

    def _log_parsed(self, parsed_data: Any) -> None:
        """Override to provide custom logging for character data."""
        if self.verbose:
            self.logger.debug("=" * 80)
            self.logger.debug("PARSED CHARACTERS:")
            self.logger.debug("=" * 80)
            if isinstance(parsed_data, list):
                # If it's already Character objects
                if parsed_data and isinstance(parsed_data[0], Character):
                    for i, char in enumerate(parsed_data, 1):
                        self.logger.debug(f"{i}. {char.name} ({char.role})")
                        self.logger.debug(f"   Goal: {char.goal}")
                        self.logger.debug(f"   Flaw: {char.flaw}")
                # If it's still dict data (during parsing)
                elif parsed_data and isinstance(parsed_data[0], dict):
                    for i, char in enumerate(parsed_data, 1):
                        self.logger.debug(f"{i}. {char['name']} ({char['role']})")
                        self.logger.debug(f"   Goal: {char['goal']}")
                        self.logger.debug(f"   Flaw: {char['flaw']}")
            self.logger.debug("=" * 80)
