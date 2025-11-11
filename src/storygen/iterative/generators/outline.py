"""Outline generator for story creation."""

import json
import time

import litellm

from storygen.iterative.models import Character, Location, Outline, StoryIdea


class OutlineGenerationError(Exception):
    """Raised when outline generation fails."""

    pass


class OutlineGenerator:
    """
    Generate a 3-act story outline using AI.

    Creates a structured outline with 7 key plot points across 3 acts,
    incorporating the story idea, characters, and locations.
    """

    def __init__(
        self,
        model: str = "gpt-4",
        max_retries: int = 3,
        timeout: int = 60,
    ):
        """
        Initialize the outline generator.

        Args:
            model: The AI model to use (default: gpt-4)
            max_retries: Maximum number of retry attempts (default: 3)
            timeout: Timeout in seconds for AI calls (default: 60)
        """
        self.model = model
        self.max_retries = max_retries
        self.timeout = timeout

    def _build_prompt(
        self,
        story_idea: StoryIdea,
        characters: list[Character],
        locations: list[Location],
    ) -> tuple[str, str]:
        """
        Build the system and user prompts for outline generation.

        Args:
            story_idea: The story concept
            characters: List of characters
            locations: List of locations

        Returns:
            Tuple of (system_prompt, user_prompt)
        """
        system_prompt = """You are an expert story architect specializing in plot structure.
Generate a 3-act story outline with 7 key plot points that create a compelling narrative arc.

Return ONLY valid JSON in this exact format:
{
  "act1_setup": "Introduce the protagonist in their normal world. Establish the status quo, their wants/needs, and the story world. (~25% of story)",
  "act1_inciting_incident": "The event that disrupts the status quo and sets the story in motion. Forces the protagonist to take action.",
  "act2_rising_action": "The protagonist pursues their goal but faces escalating obstacles. Complications arise, stakes increase. (~50% of story, first half)",
  "act2_midpoint": "A major revelation, turning point, or shift in the story. Changes what the protagonist believes or wants. (Center of story)",
  "act2_crisis": "The darkest moment - all seems lost. The protagonist faces their greatest challenge or failure. Forces a crucial decision. (End of Act 2)",
  "act3_climax": "The final confrontation. The protagonist faces the antagonist/challenge with everything they've learned. High tension, decisive action. (~25% of story)",
  "act3_resolution": "The aftermath. How the protagonist and world have changed. New status quo. Tie up loose ends."
}

Requirements:
- All 7 plot points MUST be present
- Each should be 2-4 sentences describing what happens
- Integrate the provided characters naturally
- Use the provided locations where appropriate
- Maintain consistency with the story's genre, tone, and themes
- Create a clear cause-and-effect chain through the acts
- Ensure escalating tension and stakes"""

        # Build character context
        char_context = "\nCharacters:\n"
        for char in characters:
            char_context += f"- {char.name} ({char.role}): {char.bio[:100]}... Goal: {char.goal}\n"

        # Build location context
        loc_context = "\nKey Locations:\n"
        for loc in locations:
            loc_context += f"- {loc.name}: {loc.significance}\n"

        user_prompt = f"""Generate a 3-act outline for this story:

One Sentence: {story_idea.one_sentence}

Expanded: {story_idea.expanded}

Genres: {', '.join(story_idea.genres)}
Tone: {story_idea.tone}
Themes: {', '.join(story_idea.themes)}
{char_context}
{loc_context}

Create a compelling 3-act structure with all 7 plot points, weaving together these characters and locations into a cohesive narrative."""

        return system_prompt, user_prompt

    def _parse_response(self, response_text: str) -> dict:
        """
        Parse and validate the AI response.

        Args:
            response_text: Raw JSON response from AI

        Returns:
            Dictionary with outline fields

        Raises:
            OutlineGenerationError: If response is invalid
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
            raise OutlineGenerationError(f"Invalid JSON response: {e}")

        # Validate structure
        if not isinstance(data, dict):
            raise OutlineGenerationError("Response must be a JSON object")

        # Validate all required fields are present
        required_fields = {
            "act1_setup",
            "act1_inciting_incident",
            "act2_rising_action",
            "act2_midpoint",
            "act2_crisis",
            "act3_climax",
            "act3_resolution",
        }

        missing = required_fields - set(data.keys())
        if missing:
            raise OutlineGenerationError(f"Response missing required fields: {missing}")

        # Validate each field is a non-empty string
        for field in required_fields:
            if not isinstance(data[field], str) or not data[field].strip():
                raise OutlineGenerationError(f"Field '{field}' must be a non-empty string")

        return data

    def generate(
        self,
        story_idea: StoryIdea,
        characters: list[Character],
        locations: list[Location],
    ) -> Outline:
        """
        Generate a 3-act outline for the story.

        Args:
            story_idea: The story concept
            characters: List of characters
            locations: List of locations

        Returns:
            Outline object with 7 plot points

        Raises:
            OutlineGenerationError: If generation fails after all retries
        """
        system_prompt, user_prompt = self._build_prompt(story_idea, characters, locations)

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
                    raise OutlineGenerationError("Invalid response format from AI model")

                response_text = response.choices[0].message.content  # type: ignore[union-attr]
                if not response_text:
                    raise OutlineGenerationError("Empty response from AI model")

                # Parse and validate
                outline_data = self._parse_response(response_text)

                # Create Outline object
                outline = Outline(
                    act1_setup=outline_data["act1_setup"],
                    act1_inciting_incident=outline_data["act1_inciting_incident"],
                    act2_rising_action=outline_data["act2_rising_action"],
                    act2_midpoint=outline_data["act2_midpoint"],
                    act2_crisis=outline_data["act2_crisis"],
                    act3_climax=outline_data["act3_climax"],
                    act3_resolution=outline_data["act3_resolution"],
                )

                return outline

            except Exception as e:
                last_error = e

                # Don't retry on validation errors (bad prompt/model)
                if isinstance(e, OutlineGenerationError | ValueError):
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
        raise OutlineGenerationError(
            f"Failed to generate outline after {self.max_retries} attempts. "
            f"Last error: {last_error}"
        )
