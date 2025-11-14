"""Scene-sequel breakdown generator - expands outline acts into scene-sequel pairs."""

from typing import Any

from storygen.iterative.generators.base import BaseGenerator, GenerationError
from storygen.iterative.models import (
    Act,
    Character,
    Location,
    Outline,
    SceneSequel,
    StoryIdea,
)


class BreakdownGenerationError(GenerationError):
    """Raised when scene-sequel breakdown generation fails."""

    pass


class BreakdownGenerator(BaseGenerator[list[SceneSequel]]):
    """
    Generate scene-sequel breakdown from story outline.

    Expands each leaf-level act (acts without sub-acts) into one or more
    scene-sequel pairs with proper goal/conflict/disaster structure.
    """

    def __init__(
        self,
        model: str = "gpt-4",
        max_retries: int = 3,
        timeout: int = 600,
        verbose: bool = False,
    ):
        """
        Initialize the breakdown generator.

        Args:
            model: The AI model to use (default: gpt-4)
            max_retries: Maximum number of retry attempts (default: 3)
            timeout: Timeout in seconds for AI calls (default: 600 = 10 minutes)
            verbose: Enable verbose logging of prompts and responses (default: False)
        """
        super().__init__(model=model, max_retries=max_retries, timeout=timeout, verbose=verbose)

    def generate(
        self,
        story_idea: StoryIdea,
        characters: list[Character],
        locations: list[Location],
        outline: Outline,
        target_words: int = 2000,
        story_type: str = "short-story",
    ) -> tuple[list[SceneSequel], dict[str, Any]]:
        """
        Generate scene-sequel breakdown from outline.

        Args:
            story_idea: The story concept
            characters: List of characters
            locations: List of major locations (AI can add more)
            outline: Story outline with hierarchical acts
            target_words: Target word count for entire story
            story_type: Type of story (flash-fiction, short-story, novelette, novella, novel)

        Returns:
            Tuple of (list of SceneSequel objects, usage_info dict)

        Raises:
            BreakdownGenerationError: If generation fails after retries
        """
        # Get leaf-level acts (acts without sub-acts)
        leaf_acts = self._get_leaf_acts(outline.acts)

        if self.verbose:
            print(f"\n📝 Expanding {len(leaf_acts)} leaf-level acts into scene-sequels...")
            print(f"🎯 Target word count: {target_words}")

        # Calculate scene count guidelines based on target word count
        scene_guidelines = self._calculate_scene_guidelines(target_words, story_type)
        if self.verbose:
            print(f"📊 Scene guidelines: {scene_guidelines['total_scene_units']} total units")
            print(f"   Scenes: {scene_guidelines['min_scenes']}-{scene_guidelines['max_scenes']}")
            print(
                f"   Sequels: {scene_guidelines['min_sequels']}-{scene_guidelines['max_sequels']}"
            )
            print(
                f"📏 Words per unit: {scene_guidelines['min_words_per_unit']}-{scene_guidelines['max_words_per_unit']} words"
            )

        scene_sequels: list[SceneSequel] = []
        current_time = 0.0  # Track story time
        ss_counter = 1

        # Initialize usage accumulator
        usage_accumulator = {
            "duration": 0.0,
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0,
            "retries": 0,
        }

        for act in leaf_acts:
            if self.verbose:
                print(f"\n{'=' * 80}")
                print(f"EXPANDING ACT: {act.title}")
                print(f"{'=' * 80}")

            # Calculate word count for this act
            act_word_count = int(target_words * act.percentage)

            # Generate scene-sequels for this act
            act_scenes, act_usage = self._generate_act_breakdown(
                act=act,
                story_idea=story_idea,
                characters=characters,
                locations=locations,
                act_word_count=act_word_count,
                scene_guidelines=scene_guidelines,
                current_time=current_time,
                starting_id=ss_counter,
                target_words=target_words,
            )

            # Accumulate usage
            usage_accumulator["duration"] += act_usage.get("duration", 0.0)
            usage_accumulator["prompt_tokens"] += act_usage.get("prompt_tokens", 0)
            usage_accumulator["completion_tokens"] += act_usage.get("completion_tokens", 0)
            usage_accumulator["total_tokens"] += act_usage.get("total_tokens", 0)
            usage_accumulator["retries"] = max(
                usage_accumulator["retries"], act_usage.get("retries", 0)
            )

            # Validate and add to list
            for ss in act_scenes:
                validation_errors = ss.validate()
                if validation_errors:
                    raise BreakdownGenerationError(
                        f"Generated scene-sequel {ss.id} has validation errors: {', '.join(validation_errors)}"
                    )

                scene_sequels.append(ss)
                current_time = ss.end_hours  # Update time tracker
                ss_counter += 1

            if self.verbose:
                print(f"✅ Generated {len(act_scenes)} scene-sequel(s) for {act.title}")

        if self.verbose:
            print(f"\n{'=' * 80}")
            print(f"✅ Total: {len(scene_sequels)} scene-sequels")
            print(f"📊 Story duration: {current_time:.1f} hours (~{current_time/24:.1f} days)")
            print(f"{'=' * 80}\n")

        return scene_sequels, usage_accumulator

    def _calculate_scene_guidelines(self, target_words: int, story_type: str) -> dict[str, int]:
        """
        Calculate appropriate scene count and word count guidelines based on target word count and story type.

        FICTION_LENGTH_RULESET:
        - All fiction built from SCENES (800-1800 words) and SEQUELS (200-800 words)
        - Scene Density Rule: Shorter works use FEWER, LONGER scenes; longer works use MORE, SHORTER scenes
        - Formula: total_scenes = WORD_COUNT / 1,500 (rounded)
        - Distribution: 70-85% scenes, 15-30% sequels
        - Minimum viable units by form

        Args:
            target_words: Target word count for the entire story
            story_type: Type of story (flash-fiction, short-story, novelette, novella, novel)

        Returns:
            Dict with scene count guidelines and word count ranges
        """
        # Base formula: total scene units = word_count / 1500 (rounded)
        total_scene_units = round(target_words / 1500)

        # Minimum viable units by form (overrides formula for very short works)
        min_units_by_type = {
            "flash-fiction": 1,  # under 1,500 words
            "short-story": 2,  # 1,500–7,500 words
            "novelette": 6,  # 7,500–17,000 words
            "novella": 12,  # 17,000–40,000 words
            "novel": 25,  # 40,000–120,000+ words
        }

        # Ensure minimum viable units
        total_scene_units = max(total_scene_units, min_units_by_type.get(story_type, 1))

        # Distribution: 70-85% scenes, 15-30% sequels
        # Handle small unit counts specially
        if total_scene_units == 1:
            # Flash fiction: usually 1 scene
            min_scenes = 1
            max_scenes = 1
            min_sequels = 0
            max_sequels = 0
        elif total_scene_units == 2:
            # Very short works: 1-2 scenes, 0-1 sequels
            min_scenes = 1
            max_scenes = 2
            min_sequels = 0
            max_sequels = 1
        else:
            # Normal distribution for longer works
            min_scenes = max(1, int(total_scene_units * 0.70))
            max_scenes = int(total_scene_units * 0.85)
            min_sequels = total_scene_units - max_scenes
            max_sequels = total_scene_units - min_scenes

        # Word count ranges based on scene density rule
        # Shorter works: fewer, longer scenes; longer works: more, shorter scenes
        if target_words < 1500:  # Flash fiction
            min_words_per_unit = 800  # Longer units for short works
            max_words_per_unit = 1500
        elif target_words < 7500:  # Short story
            min_words_per_unit = 600
            max_words_per_unit = 1800
        elif target_words < 17000:  # Novelette
            min_words_per_unit = 500
            max_words_per_unit = 1500
        elif target_words < 40000:  # Novella
            min_words_per_unit = 400
            max_words_per_unit = 1200
        else:  # Novel
            min_words_per_unit = 300  # Shorter units for long works
            max_words_per_unit = 1000

        return {
            "total_scene_units": total_scene_units,
            "min_scenes": min_scenes,
            "max_scenes": max_scenes,
            "min_sequels": min_sequels,
            "max_sequels": max_sequels,
            "min_words_per_unit": min_words_per_unit,
            "max_words_per_unit": max_words_per_unit,
        }

    def _get_leaf_acts(self, acts: list[Act]) -> list[Act]:
        """
        Recursively extract leaf-level acts (acts without sub-acts).

        Args:
            acts: List of acts (potentially with sub-acts)

        Returns:
            Flat list of leaf-level acts
        """
        leaves = []
        for act in acts:
            if act.sub_acts:
                # Recurse into sub-acts
                leaves.extend(self._get_leaf_acts(act.sub_acts))
            else:
                # This is a leaf - add it
                leaves.append(act)
        return leaves

    def _generate_act_breakdown(
        self,
        act: Act,
        story_idea: StoryIdea,
        characters: list[Character],
        locations: list[Location],
        act_word_count: int,
        scene_guidelines: dict[str, int],
        current_time: float,
        starting_id: int,
        target_words: int,
    ) -> tuple[list[SceneSequel], dict[str, Any]]:
        """
        Generate scene-sequel pairs for a single act.

        Args:
            act: The act to expand
            story_idea: Story concept
            characters: List of characters
            locations: List of major locations
            act_word_count: Word count allocated to this act
            current_time: Current story time in hours
            starting_id: Starting ID number for scene-sequels

        Returns:
            Tuple of (list of SceneSequel objects, usage_info dict)

        Raises:
            BreakdownGenerationError: If generation fails after retries
        """
        system_prompt, user_prompt = self._build_prompt(
            act=act,
            story_idea=story_idea,
            characters=characters,
            locations=locations,
            act_word_count=act_word_count,
            scene_guidelines=scene_guidelines,
            current_time=current_time,
            starting_id=starting_id,
            target_words=target_words,
        )

        # Parser that converts response text to list of SceneSequels
        def parse_to_scene_sequels(response_text: str) -> list[SceneSequel]:
            return self._parse_breakdown_response(response_text, act.title)

        # Use base class retry logic
        scene_sequels, usage_info = self._generate_with_retry(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            parser=parse_to_scene_sequels,
            temperature=0.7,
            error_class=BreakdownGenerationError,
        )

        return scene_sequels, usage_info

    def _log_parsed(self, parsed_data: Any) -> None:
        """Override to provide custom logging for breakdown data."""
        if self.verbose and isinstance(parsed_data, list):
            print(f"{'=' * 80}")
            print("PARSED SCENE-SEQUELS:")
            print(f"{'=' * 80}\n")
            for ss in parsed_data:
                if isinstance(ss, SceneSequel):
                    print(f"{ss.id} ({ss.type}): {ss.pov_character} @ {ss.location}")
                    print(f"  Time: {ss.start_hours:.1f}h - {ss.end_hours:.1f}h ({ss.time_of_day})")
                    if ss.type == "scene":
                        print(f"  Goal: {ss.goal}")
                        print(f"  Disaster: {ss.disaster}")
                    print()
            print(f"{'=' * 80}\n")

    def _build_prompt(
        self,
        act: Act,
        story_idea: StoryIdea,
        characters: list[Character],
        locations: list[Location],
        act_word_count: int,
        scene_guidelines: dict[str, int],
        current_time: float,
        starting_id: int,
        target_words: int,
    ) -> tuple[str, str]:
        """
        Build prompts for AI to generate scene-sequel breakdown.

        Args:
            act: Act to expand
            story_idea: Story concept
            characters: List of characters
            locations: List of major locations
            act_word_count: Word count for this act
            current_time: Current story time
            starting_id: Starting ID number

        Returns:
            Tuple of (system_prompt, user_prompt)
        """
        # Format characters with their roles
        char_list = "\n".join([f"- {c.name} ({c.role}): {c.bio[:100]}..." for c in characters])

        # Format locations
        loc_list = "\n".join([f"- {loc.name}: {loc.significance[:100]}..." for loc in locations])

        system_prompt = """You are an expert story architect specializing in scene structure.
You are a strict JSON generator. Do not add explanations, markdown formatting, or any text outside the JSON structure.

You will receive a story ACT to expand into 1-3 SCENE-SEQUEL pairs.

SCENE-SEQUEL STRUCTURE (Dwight Swain method):
- SCENE: External action unit with goal/conflict/disaster (REQUIRED)
- SEQUEL: Internal reaction unit with reaction/dilemma/decision (OPTIONAL)

CRITICAL REQUIREMENTS:
1. Each scene-sequel MUST have:
   - pov_character: Choose from provided character list (REQUIRED)
   - location: Use provided locations OR create new specific ones (REQUIRED)
   - start_hours: When it begins relative to story start (REQUIRED)
   - duration_hours: How long it lasts (0.25 to 2.0 hours typical) (REQUIRED)

2. SCENES (type="scene") MUST have:
   - goal: What POV character wants (specific, immediate)
   - conflict: Opposition they face (internal or external)
   - disaster: How it goes wrong or succeeds with complications

3. SEQUELS (type="sequel") are OPTIONAL but if included should have at least one of:
   - reaction: Emotional response to disaster
   - dilemma: Options being weighed
   - decision: Choice that leads to next scene

4. Your response MUST be a valid JSON ARRAY starting with [ and ending with ]

5. Do NOT add any text before [ or after ] - output ONLY the JSON array

Respond as a strict JSON generator only."""

        user_prompt = f"""ACT TO EXPAND:
Title: {act.title}
Description: {act.description}
Story Application: {act.story_application}

Word Count Budget: {act_word_count} words
Current Story Time: {current_time:.1f} hours

OVERALL STORY GUIDELINES:
- Total target word count: {target_words} words
- Scene units: {scene_guidelines['total_scene_units']} total ({scene_guidelines['min_scenes']}-{scene_guidelines['max_scenes']} scenes, {scene_guidelines['min_sequels']}-{scene_guidelines['max_sequels']} sequels)
- Words per unit: {scene_guidelines['min_words_per_unit']}-{scene_guidelines['max_words_per_unit']} words

FICTION STRUCTURE RULES:
- SCENES (70-85% of units): 800-1,800 words, external action with goal/conflict/disaster
- SEQUELS (15-30% of units): 200-800 words, internal processing with reaction/dilemma/decision
- Combined units: 1,000-2,500 words

STORY CONTEXT:
{story_idea.one_sentence}

CHARACTERS (choose POV from this list):
{char_list}

LOCATIONS (use these OR create new specific ones):
{loc_list}

INSTRUCTIONS:
Generate 1-3 scene-sequel units for this act. Consider:
- Balance between scenes (action) and sequels (reflection) per distribution rules
- Shorter works use fewer, longer units; longer works use more, shorter units
- Each unit should fit the word count ranges above
- Ensure total units across ALL acts stay within overall guidelines

Each scene-sequel must include:
- id: Sequential ID starting from "ss_{starting_id:03d}"
- type: "scene" or "sequel"
- source_act: "{act.title}"
- pov_character: Character name from list above
- location: Specific location (can be new)
- start_hours: Starts at {current_time:.1f} or later
- duration_hours: How long it lasts (0.25-2.0 hours)
- target_word_count: Portion of {act_word_count} words

For scenes: goal, conflict, disaster
For sequels: reaction, dilemma, decision

OUTPUT FORMAT:
[
  {{
    "id": "ss_{starting_id:03d}",
    "type": "scene",
    "source_act": "{act.title}",
    "pov_character": "Character Name",
    "location": "Specific Location",
    "start_hours": {current_time:.1f},
    "duration_hours": 0.5,
    "goal": "What character wants",
    "conflict": "Opposition they face",
    "disaster": "How it goes wrong",
    "target_word_count": {act_word_count // 2}
  }},
  {{
    "id": "ss_{starting_id + 1:03d}",
    "type": "sequel",
    "source_act": "{act.title}",
    "pov_character": "Character Name",
    "location": "Specific Location",
    "start_hours": {current_time + 0.5:.1f},
    "duration_hours": 0.25,
    "reaction": "Emotional response",
    "decision": "Choice they make",
    "target_word_count": {act_word_count // 2}
  }}
]

Return ONLY the valid JSON array, nothing else."""

        return system_prompt, user_prompt

    def _parse_response(self, response_text: str, act_title: str = "") -> Any:  # type: ignore[override]
        """
        Parse breakdown response - delegates to _parse_breakdown_response.

        Note: Overrides base signature to add act_title parameter.
        """
        return self._parse_breakdown_response(response_text, act_title)

    def _parse_breakdown_response(self, response: str, act_title: str) -> list[SceneSequel]:
        """
        Parse AI response into SceneSequel objects.

        Args:
            response: Raw AI response
            act_title: Title of act being expanded (for error context)

        Returns:
            List of SceneSequel objects

        Raises:
            BreakdownGenerationError: If parsing fails
        """
        try:
            # Use base class JSON array parsing
            data = self.parse_json_array_response(
                response, min_items=0, error_class=BreakdownGenerationError
            )

            # Convert to SceneSequel objects
            scene_sequels = []
            for item in data:
                if not isinstance(item, dict):
                    raise BreakdownGenerationError(
                        f"Expected scene-sequel object, got {type(item)}"
                    )

                # Validate required fields
                required = [
                    "id",
                    "type",
                    "pov_character",
                    "location",
                    "start_hours",
                    "duration_hours",
                ]
                missing = [f for f in required if f not in item]
                if missing:
                    raise BreakdownGenerationError(
                        f"Scene-sequel missing required fields: {', '.join(missing)}"
                    )

                # Create SceneSequel object
                ss = SceneSequel.from_dict(item)
                scene_sequels.append(ss)

            return scene_sequels

        except BreakdownGenerationError:
            # Re-raise with act context
            raise
        except Exception as e:
            raise BreakdownGenerationError(f"Failed to parse response for act '{act_title}': {e}")
