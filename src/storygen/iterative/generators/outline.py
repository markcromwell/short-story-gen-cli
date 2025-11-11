"""Outline generator for story creation with flexible structure templates."""

import json
import time

import litellm

from storygen.iterative.models import Act, Character, Location, Outline, StoryIdea
from storygen.iterative.outline_templates import get_template, list_available_structures


class OutlineGenerationError(Exception):
    """Raised when outline generation fails."""

    pass


class OutlineGenerator:
    """
    Generate story outlines using flexible structure templates.

    Supports multiple structure types (three-act, hero's journey, fichtean)
    with AI-powered story application. Loads a template and asks AI to fill
    in how each act applies to the specific story.
    """

    def __init__(
        self,
        model: str = "gpt-4",
        structure_type: str = "three-act",
        max_retries: int = 3,
        timeout: int = 60,
    ):
        """
        Initialize the outline generator.

        Args:
            model: The AI model to use (default: gpt-4)
            structure_type: Structure template to use (default: three-act)
                Options: three-act, hero-journey, fichtean
            max_retries: Maximum number of retry attempts (default: 3)
            timeout: Timeout in seconds for AI calls (default: 60)

        Raises:
            ValueError: If structure_type is not recognized
        """
        self.model = model
        self.structure_type = structure_type
        self.max_retries = max_retries
        self.timeout = timeout

        # Validate structure type
        if structure_type not in list_available_structures():
            valid = ", ".join(list_available_structures())
            raise ValueError(f"Unknown structure type '{structure_type}'. Valid options: {valid}")

    def _build_prompt(
        self,
        story_idea: StoryIdea,
        characters: list[Character],
        locations: list[Location],
        template: list[Act],
    ) -> tuple[str, str]:
        """
        Build prompts for AI to fill story_application for each act.

        Args:
            story_idea: The story concept
            characters: List of characters
            locations: List of locations
            template: Act template structure

        Returns:
            Tuple of (system_prompt, user_prompt)
        """

        # Serialize template structure for AI
        def serialize_act(act: Act, indent=0) -> str:
            """Convert act to readable string format."""
            prefix = "  " * indent
            lines = [
                f'{prefix}"title": "{act.title}",',
                f'{prefix}"description": "{act.description}",',
                f'{prefix}"story_application": "FILL THIS IN - how does this act apply to the specific story?",',
                f'{prefix}"percentage": {act.percentage}',
            ]

            if act.sub_acts:
                lines.append(f'{prefix}"sub_acts": [')
                for i, sub_act in enumerate(act.sub_acts):
                    lines.append(f"{prefix}  {{")
                    lines.append(serialize_act(sub_act, indent + 2))
                    lines.append(f"{prefix}  }}" + ("," if i < len(act.sub_acts) - 1 else ""))
                lines.append(f"{prefix}]")

            return "\n".join(lines)

        template_str = "[\n"
        for i, act in enumerate(template):
            template_str += "  {\n"
            template_str += serialize_act(act, 2)
            template_str += "\n  }" + ("," if i < len(template) - 1 else "") + "\n"
        template_str += "]"

        system_prompt = f"""You are an expert story architect specializing in plot structure.

You will receive a story outline TEMPLATE with generic descriptions of each act.
Your task is to fill in the "story_application" field for EACH act, explaining how that act applies to the specific story provided.

The template shows the structure type: {self.structure_type}

Each act has:
- title: The name of this act/beat
- description: Generic explanation of what happens in this act (DO NOT change this)
- story_application: HOW THIS ACT APPLIES TO THE SPECIFIC STORY (YOU FILL THIS IN)
- percentage: What % of the story this act represents (DO NOT change this)

For story_application, write 2-4 sentences explaining:
- What specifically happens in THIS story during this act
- Which characters are involved and what they do
- Which locations might be used
- How this advances the specific plot

Return the COMPLETE template structure as valid JSON, with ONLY the story_application fields filled in.
Keep all other fields (title, description, percentage, sub_acts structure) exactly as provided.

CRITICAL: Maintain the exact JSON structure including all nested sub_acts."""

        # Build character context
        char_context = "\nCharacters:\n"
        for char in characters:
            char_context += f"- {char.name} ({char.role}): {char.bio[:100]}...\n  Goal: {char.goal}\n  Flaw: {char.flaw}\n"

        # Build location context
        loc_context = "\nKey Locations:\n"
        for loc in locations:
            loc_context += f"- {loc.name}: {loc.significance}\n"

        user_prompt = f"""Story to outline:

Title/Concept: {story_idea.one_sentence}

Full Description: {story_idea.expanded}

Genres: {', '.join(story_idea.genres)}
Tone: {story_idea.tone}
Themes: {', '.join(story_idea.themes)}
{char_context}
{loc_context}

Outline Template ({self.structure_type}):
{template_str}

Fill in the "story_application" for EVERY act (including all sub-acts) based on the story above.
Return the complete structure as valid JSON."""

        return system_prompt, user_prompt

    def _parse_response(self, response_text: str) -> list[Act]:
        """
        Parse AI response and convert to Act objects.

        Args:
            response_text: Raw JSON response from AI

        Returns:
            List of Act objects with story_application filled in

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

        # Try to extract JSON array - look for outermost [ ]
        # This handles cases where AI adds explanatory text before/after JSON
        start_idx = text.find("[")
        if start_idx == -1:
            raise OutlineGenerationError("No JSON array found in response")
        
        # Find matching closing bracket
        bracket_count = 0
        end_idx = -1
        for i in range(start_idx, len(text)):
            if text[i] == "[":
                bracket_count += 1
            elif text[i] == "]":
                bracket_count -= 1
                if bracket_count == 0:
                    end_idx = i + 1
                    break
        
        if end_idx == -1:
            raise OutlineGenerationError("Malformed JSON array - no closing bracket")
        
        json_text = text[start_idx:end_idx]

        # Parse JSON
        try:
            data = json.loads(json_text)
        except json.JSONDecodeError as e:
            raise OutlineGenerationError(f"Invalid JSON response: {e}")

        # Validate it's a list of acts
        if not isinstance(data, list):
            raise OutlineGenerationError("Response must be a JSON array of acts")

        if not data:
            raise OutlineGenerationError("Response must contain at least one act")

        # Convert to Act objects
        try:
            acts = [Act.from_dict(act_data) for act_data in data]
        except (TypeError, ValueError) as e:
            raise OutlineGenerationError(f"Failed to parse acts: {e}")

        # Validate each act has story_application filled in
        def validate_act(act: Act, path: str = ""):
            if not act.story_application or not act.story_application.strip():
                raise OutlineGenerationError(f"Act '{path}{act.title}' missing story_application")
            # Recursively validate sub-acts
            for i, sub_act in enumerate(act.sub_acts):
                validate_act(sub_act, f"{path}{act.title} > ")

        for act in acts:
            validate_act(act)

        return acts

    def generate(
        self,
        story_idea: StoryIdea,
        characters: list[Character],
        locations: list[Location],
    ) -> Outline:
        """
        Generate outline for the story using the specified structure template.

        Args:
            story_idea: The story concept
            characters: List of characters
            locations: List of locations

        Returns:
            Outline object with acts containing story_application

        Raises:
            OutlineGenerationError: If generation fails after all retries
        """
        # Load template for the specified structure type
        template = get_template(self.structure_type)

        # Build prompts
        system_prompt, user_prompt = self._build_prompt(story_idea, characters, locations, template)

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
                acts = self._parse_response(response_text)

                # Create Outline object
                outline = Outline(structure_type=self.structure_type, acts=acts)

                # Validate the outline structure
                errors = outline.validate()
                if errors:
                    raise OutlineGenerationError(f"Outline validation failed: {errors}")

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
