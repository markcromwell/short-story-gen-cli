"""Outline generator for story creation with flexible structure templates."""

import json
from typing import Any

from storygen.iterative.exceptions import ConfigError
from storygen.iterative.generators.base import BaseGenerator, GenerationError
from storygen.iterative.models import Act, Character, Location, Outline, StoryIdea
from storygen.iterative.outline_templates import get_template, list_available_structures


class OutlineGenerationError(GenerationError):
    """Raised when outline generation fails."""

    pass


class OutlineGenerator(BaseGenerator[Outline]):
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
        timeout: int = 600,
        verbose: bool = False,
    ):
        """
        Initialize the outline generator.

        Args:
            model: The AI model to use (default: gpt-4)
            structure_type: Structure template to use (default: three-act)
                Options: three-act, hero-journey, fichtean
            max_retries: Maximum number of retry attempts (default: 3)
            timeout: Timeout in seconds for AI calls (default: 600 = 10 minutes)
            verbose: Enable verbose logging of prompts and responses (default: False)

        Raises:
            ValueError: If structure_type is not recognized
        """
        super().__init__(model=model, max_retries=max_retries, timeout=timeout, verbose=verbose)
        self.structure_type = structure_type

        # Validate structure type
        if structure_type not in list_available_structures():
            valid = ", ".join(list_available_structures())
            raise ConfigError(f"Unknown structure type '{structure_type}'. Valid options: {valid}")

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
                f'{prefix}"percentage": {act.percentage}' + ("," if act.sub_acts else ""),
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
You are a strict JSON generator. Do not add explanations, markdown formatting, or any text outside the JSON structure.

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

CRITICAL JSON FORMAT REQUIREMENTS:
1. Your response MUST be a valid JSON ARRAY that starts with [ and ends with ]
2. The array MUST contain ALL acts (typically 3 acts for three-act structure)
3. Do NOT output separate JSON objects - wrap everything in a single array
4. Do NOT add any text before [ or after ] - output ONLY the JSON array
5. Keep all fields (title, description, percentage, sub_acts structure) exactly as provided
6. ONLY fill in the "story_application" fields
7. Maintain the exact nested sub_acts structure

Example of correct format (all acts in ONE array):
[
  {{"title": "Act 1: Setup", "description": "...", "story_application": "YOUR CONTENT HERE", "percentage": 0.25, "sub_acts": [...]}},
  {{"title": "Act 2: Confrontation", "description": "...", "story_application": "YOUR CONTENT HERE", "percentage": 0.5, "sub_acts": [...]}},
  {{"title": "Act 3: Resolution", "description": "...", "story_application": "YOUR CONTENT HERE", "percentage": 0.25, "sub_acts": [...]}}
]

Respond as a strict JSON generator only."""

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
Setting: {story_idea.setting}

IMPORTANT: Story takes place in "{story_idea.setting}".
Consider setting constraints when planning plot:
- Technology level and available tools
- Cultural norms and social structures
- Period-appropriate conflicts and solutions
- Time/place-specific opportunities and limitations

{char_context}
{loc_context}

Outline Template ({self.structure_type}):
{template_str}

INSTRUCTIONS:
1. Fill in the "story_application" for EVERY act (including all sub-acts) based on the story above
2. Return the COMPLETE array structure - ALL acts must be in a SINGLE JSON array
3. Your response MUST begin with [ and end with ]
4. Do NOT output acts as separate objects
5. Include ALL acts from the template in your response

Return ONLY the complete JSON array, nothing else."""

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

        # Try to extract JSON - handle both array format and multiple objects
        # Look for array first: [ {...}, {...}, {...} ]
        array_start = text.find("[")

        if array_start != -1:
            # Find matching closing bracket for array
            bracket_count = 0
            end_idx = -1
            for i in range(array_start, len(text)):
                if text[i] == "[":
                    bracket_count += 1
                elif text[i] == "]":
                    bracket_count -= 1
                    if bracket_count == 0:
                        end_idx = i + 1
                        break

            if end_idx != -1:
                json_text = text[array_start:end_idx]
                try:
                    data = json.loads(json_text)
                    if isinstance(data, list):
                        # Successfully parsed array format
                        pass
                except json.JSONDecodeError:
                    # Array parsing failed, fall through to object extraction
                    data = None
            else:
                data = None
        else:
            data = None

        # If array format failed, try extracting multiple { } objects
        if data is None:
            objects = []
            pos = 0
            while pos < len(text):
                # Find next object start
                obj_start = text.find("{", pos)
                if obj_start == -1:
                    break

                # Find matching closing brace
                brace_count = 0
                obj_end = -1
                for i in range(obj_start, len(text)):
                    if text[i] == "{":
                        brace_count += 1
                    elif text[i] == "}":
                        brace_count -= 1
                        if brace_count == 0:
                            obj_end = i + 1
                            break

                if obj_end == -1:
                    break

                # Try to parse this object
                obj_text = text[obj_start:obj_end]
                try:
                    obj = json.loads(obj_text)
                    # Only add if it looks like an act (has 'title' field)
                    if isinstance(obj, dict) and "title" in obj:
                        objects.append(obj)
                except json.JSONDecodeError:
                    pass

                pos = obj_end

            if objects:
                data = objects
            else:
                raise OutlineGenerationError("No valid JSON array or objects found in response")

        # Validate it's a list of acts
        if not isinstance(data, list):
            raise OutlineGenerationError("Response must be a JSON array of acts")

        if not data:
            raise OutlineGenerationError("Response must contain at least one act")

        # Convert to Act objects and auto-assign order based on position
        try:
            acts = [
                Act.from_dict({**act_data, "order": i} if "order" not in act_data else act_data)
                for i, act_data in enumerate(data)
            ]
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
        error_feedback = None

        for attempt in range(self.max_retries):
            try:
                # Add error feedback to user prompt on retries
                current_user_prompt = user_prompt
                if error_feedback:
                    # Provide specific guidance based on the error
                    fix_guidance = ""
                    if (
                        "25.00% but should be 100%" in error_feedback
                        or "total" in error_feedback.lower()
                    ):
                        fix_guidance = "\nYou only returned ONE act. You MUST return ALL acts in a SINGLE array: [act1, act2, act3]"
                    elif "No valid JSON array" in error_feedback:
                        fix_guidance = "\nYour response must be a JSON array starting with [ and ending with ]. Do NOT output separate objects."

                    current_user_prompt = f"""{user_prompt}

⚠️ PREVIOUS ATTEMPT FAILED with error:
{error_feedback}{fix_guidance}

FIX REQUIRED: Return a SINGLE JSON array containing ALL acts like this:
[
  {{"title": "Act 1: Setup", ...}},
  {{"title": "Act 2: Confrontation", ...}},
  {{"title": "Act 3: Resolution", ...}}
]

Return ONLY the corrected JSON array, no explanations."""

                # Use lower temperature on retries for more deterministic JSON structure
                temperature = 0.3 if error_feedback else 0.5

                if self.verbose and error_feedback:
                    print(f"   Using temperature={temperature} for retry\n")

                # Log request using base class
                self._log_request(system_prompt, current_user_prompt)

                # Build additional API kwargs with JSON mode for OpenAI models
                extra_kwargs: dict[str, Any] = {}
                if self.model.startswith("gpt-"):
                    extra_kwargs["response_format"] = {"type": "json_object"}

                # Call AI using base class helper
                response = self._call_ai(
                    system_prompt,
                    current_user_prompt,
                    temperature=temperature,
                    stream=False,
                    **extra_kwargs,
                )

                # Log response using base class
                self._log_response(response)

                # Parse and validate
                acts = self._parse_response(response)

                if self.verbose:
                    print("\n" + "=" * 80)
                    print("PARSED OUTLINE STRUCTURE:")
                    print("=" * 80)
                    for i, act in enumerate(acts):
                        print(f"\nTop-level Act {i+1}: {act.title}")
                        print(f"  Percentage: {act.percentage}")
                        print(f"  get_total_percentage(): {act.get_total_percentage()}")
                        if act.sub_acts:
                            print(f"  Sub-acts ({len(act.sub_acts)}):")
                            for sub in act.sub_acts:
                                print(f"    - {sub.title}: {sub.percentage}")
                    total = sum(act.get_total_percentage() for act in acts)
                    print(f"\nTotal percentage (sum of get_total_percentage()): {total:.2%}")
                    print("=" * 80)

                # Create Outline object
                outline = Outline(structure_type=self.structure_type, acts=acts)

                # Validate the outline structure
                errors = outline.validate()
                if errors:
                    if self.verbose:
                        print(f"\n❌ VALIDATION ERRORS: {errors}")
                    raise OutlineGenerationError(f"Outline validation failed: {errors}")

                return outline

            except Exception as e:
                last_error = e

                # Capture error message for feedback to AI on retry
                if isinstance(e, OutlineGenerationError):
                    error_feedback = str(e)
                elif isinstance(e, ValueError):
                    error_feedback = f"ValueError: {e}"
                else:
                    error_feedback = f"Error: {e}"

                if self.verbose:
                    print(f"\n⚠️  Attempt {attempt + 1} failed: {error_feedback}")

                # Retry on validation errors or network/timeout errors
                if attempt < self.max_retries - 1:
                    wait_time = 2**attempt  # Exponential backoff
                    if self.verbose:
                        print(f"   Retrying in {wait_time} seconds...\n")
                    # Use exponential backoff (base class has time imported)
                    import time

                    time.sleep(wait_time)
                    continue

                # Last attempt failed
                break

        # All retries exhausted
        raise OutlineGenerationError(
            f"Failed to generate outline after {self.max_retries} attempts. "
            f"Last error: {last_error}"
        )
