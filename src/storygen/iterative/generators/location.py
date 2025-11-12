"""Location generator for story creation."""

import json
import time

import litellm

from storygen.iterative.models import Location, StoryIdea


class LocationGenerationError(Exception):
    """Raised when location generation fails."""

    pass


class LocationGenerator:
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
        self.model = model
        self.max_retries = max_retries
        self.timeout = timeout
        self.verbose = verbose

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
        # Remove markdown code blocks if present
        text = response_text.strip()
        if text.startswith("```"):
            lines = text.split("\n")
            text = "\n".join(lines[1:-1]) if len(lines) > 2 else text
            if text.startswith("json"):
                text = text[4:].strip()

        # Parse JSON
        try:
            data = json.loads(text)
        except json.JSONDecodeError as e:
            raise LocationGenerationError(f"Invalid JSON response: {e}")

        # Validate structure
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
                    temperature=0.8,
                    stream=False,
                )

                # Extract response
                if not hasattr(response, "choices") or not response.choices:  # type: ignore[union-attr]
                    raise LocationGenerationError("Invalid response format from AI model")

                response_text = response.choices[0].message.content  # type: ignore[union-attr]
                if not response_text:
                    raise LocationGenerationError("Empty response from AI model")

                if self.verbose:
                    print("\n" + "=" * 80)
                    print("RECEIVED FROM AI MODEL:")
                    print("=" * 80)
                    print(f"\n{response_text}\n")
                    print("=" * 80)

                # Parse and validate
                loc_dicts = self._parse_response(response_text)

                if self.verbose:
                    print("\n" + "=" * 80)
                    print("PARSED LOCATIONS:")
                    print("=" * 80)
                    for i, loc in enumerate(loc_dicts, 1):
                        print(f"\n{i}. {loc['name']}")
                        print(f"   Atmosphere: {loc['atmosphere']}")
                    print("=" * 80)

                # Create Location objects
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

            except Exception as e:
                last_error = e

                # Don't retry on validation errors (bad prompt/model)
                if isinstance(e, LocationGenerationError | ValueError):
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
        raise LocationGenerationError(
            f"Failed to generate locations after {self.max_retries} attempts. "
            f"Last error: {last_error}"
        )
