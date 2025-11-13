"""Location generator for story creation."""

from typing import Any

from storygen.iterative.generators.base import BaseGenerator, GenerationError
from storygen.iterative.models import Location, StoryIdea


class LocationGenerationError(GenerationError):
    """Raised when location generation fails."""

    pass


class LocationGenerator(BaseGenerator[list[Location]]):
    """
    Generate locations for a story using AI.

    Generates 3-7 key locations that fit the story's setting, genre, and tone.
    Each location includes name, description, significance, and atmosphere.
    """

    def __init__(
        self,
        model: str = "gpt-4",
        max_retries: int = 3,
        timeout: int = 600,
        verbose: bool = False,
    ):
        """
        Initialize the location generator.

        Args:
            model: The AI model to use (default: gpt-4)
            max_retries: Maximum number of retry attempts (default: 3)
            timeout: Timeout in seconds for AI calls (default: 600 = 10 minutes)
            verbose: Enable verbose logging of prompts and responses (default: False)
        """
        super().__init__(model=model, max_retries=max_retries, timeout=timeout, verbose=verbose)

    def _build_prompt(
        self, story_idea: StoryIdea, story_type: str = "short-story"
    ) -> tuple[str, str]:
        """
        Build the system and user prompts for location generation.

        Args:
            story_idea: The story concept to generate locations for
            story_type: Type of story (flash-fiction, short-story, novelette, novella, novel)

        Returns:
            Tuple of (system_prompt, user_prompt)
        """
        # Location count guidance based on story type
        loc_counts = {
            "flash-fiction": (1, 2, "1-2 locations (single scene focus)"),
            "short-story": (2, 4, "2-4 locations (limited scope)"),
            "novelette": (3, 6, "3-6 locations (moderate world-building)"),
            "novella": (5, 8, "5-8 locations (expanded world)"),
            "novel": (8, 12, "8-12+ locations (rich world-building)"),
        }

        min_locs, max_locs, count_desc = loc_counts.get(story_type, (2, 4, "2-4 locations"))

        system_prompt = f"""You are an expert world-builder and location designer for creative writing.

STORY LENGTH: {story_type.upper()}
LOCATION COUNT: {count_desc}

Generate {min_locs}-{max_locs} key locations for a story that will serve as important settings for scenes and plot events.

Each location should be vivid, atmospheric, and serve the story's narrative needs.

Return ONLY valid JSON in this exact format:
{{
  "locations": [
    {{
      "name": "The location's name",
      "description": "Physical details - what it looks like, smells like, sounds like (2-4 sentences)",
      "significance": "Why this location matters to the story and plot (1-2 sentences)",
      "atmosphere": "The mood and feeling of this place (1 sentence)"
    }}
  ]
}}

Requirements:
- Generate {min_locs}-{max_locs} locations appropriate for a {story_type}
- Each location MUST have: name, description, significance, atmosphere
- Locations should fit the story's genre, tone, and setting
- Include variety: indoor/outdoor, public/private, safe/dangerous
- Make descriptions sensory and vivid
- Ensure significance ties to plot or character development"""

        user_prompt = f"""Generate locations for this story:

One Sentence: {story_idea.one_sentence}

Expanded: {story_idea.expanded}

Genres: {', '.join(story_idea.genres)}
Tone: {story_idea.tone}
Themes: {', '.join(story_idea.themes)}
Setting: {story_idea.setting}

IMPORTANT: All locations must be consistent with the setting "{story_idea.setting}".
Consider the time period, technology level, cultural context, and physical geography.
Ensure location names and descriptions match the setting's era and place.

Generate {min_locs}-{max_locs} key locations that fit this {story_type}'s world and scope."""

        return system_prompt, user_prompt

    def _parse_response(self, response_text: str) -> list[dict]:
        """
        Parse and validate the AI response.

        Args:
            response_text: Raw JSON response from AI

        Returns:
            List of location dictionaries

        Raises:
            LocationGenerationError: If response is invalid
        """
        # Use base class JSON parsing
        data = self.parse_json_response(response_text, error_class=LocationGenerationError)

        # Validate structure specific to locations
        if not isinstance(data, dict):
            raise LocationGenerationError("Response must be a JSON object")

        if "locations" not in data:
            raise LocationGenerationError("Response missing 'locations' field")

        if not isinstance(data["locations"], list):
            raise LocationGenerationError("'locations' must be a list")

        locations = data["locations"]

        # Validate count (1-12 to accommodate all story types)
        if len(locations) < 1:
            raise LocationGenerationError(
                f"Must generate at least 1 location, got {len(locations)}"
            )

        if len(locations) > 12:
            raise LocationGenerationError(
                f"Must generate at most 12 locations, got {len(locations)}"
            )

        # Validate each location
        required_fields = {"name", "description", "significance", "atmosphere"}
        for i, loc in enumerate(locations):
            if not isinstance(loc, dict):
                raise LocationGenerationError(f"Location {i} must be a dictionary")

            missing = required_fields - set(loc.keys())
            if missing:
                raise LocationGenerationError(f"Location {i} missing required fields: {missing}")

            # Validate field types and non-empty
            for field in required_fields:
                if not isinstance(loc[field], str) or not loc[field].strip():
                    raise LocationGenerationError(
                        f"Location {i} field '{field}' must be a non-empty string"
                    )

        return locations

    def generate(self, story_idea: StoryIdea, story_type: str = "short-story") -> list[Location]:
        """
        Generate locations for a story idea.

        Args:
            story_idea: The story concept to generate locations for
            story_type: Type of story (flash-fiction, short-story, novelette, novella, novel)

        Returns:
            List of Location objects

        Raises:
            LocationGenerationError: If generation fails after all retries
        """
        system_prompt, user_prompt = self._build_prompt(story_idea, story_type)

        # Parser that converts response text to list of Locations
        def parse_to_locations(response_text: str) -> list[Location]:
            loc_dicts = self._parse_response(response_text)
            locations: list[Location] = []
            for loc_data in loc_dicts:
                loc = Location(  # type: ignore
                    name=loc_data["name"],
                    description=loc_data["description"],
                    significance=loc_data["significance"],
                    atmosphere=loc_data["atmosphere"],
                )
                locations.append(loc)  # type: ignore
            return locations

        # Use base class retry logic
        return self._generate_with_retry(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            parser=parse_to_locations,
            temperature=0.8,
            error_class=LocationGenerationError,
        )

    def _log_parsed(self, parsed_data: Any) -> None:
        """Override to provide custom logging for location data."""
        if self.verbose:
            print("\n" + "=" * 80)
            print("PARSED LOCATIONS:")
            print("=" * 80)
            if isinstance(parsed_data, list):
                for i, loc in enumerate(parsed_data, 1):
                    if isinstance(loc, Location):
                        print(f"\n{i}. {loc.name}")
                        print(f"   Atmosphere: {loc.atmosphere}")
                    elif isinstance(loc, dict):
                        print(f"\n{i}. {loc['name']}")
                        print(f"   Atmosphere: {loc['atmosphere']}")
            print("=" * 80)
