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
    ) -> list[SceneSequel]:
        """
        Generate scene-sequel breakdown from outline.

        Args:
            story_idea: The story concept
            characters: List of characters
            locations: List of major locations (AI can add more)
            outline: Story outline with hierarchical acts
            target_words: Target word count for entire story

        Returns:
            List of SceneSequel objects

        Raises:
            BreakdownGenerationError: If generation fails after retries
        """
        # Get leaf-level acts (acts without sub-acts)
        leaf_acts = self._get_leaf_acts(outline.acts)

        if self.verbose:
            print(f"\n📝 Expanding {len(leaf_acts)} leaf-level acts into scene-sequels...")
            print(f"🎯 Target word count: {target_words}")

        scene_sequels: list[SceneSequel] = []
        current_time = 0.0  # Track story time
        ss_counter = 1

        for act in leaf_acts:
            if self.verbose:
                print(f"\n{'=' * 80}")
                print(f"EXPANDING ACT: {act.title}")
                print(f"{'=' * 80}")

            # Calculate word count for this act
            act_word_count = int(target_words * act.percentage)

            # Generate scene-sequels for this act
            act_scenes = self._generate_act_breakdown(
                act=act,
                story_idea=story_idea,
                characters=characters,
                locations=locations,
                act_word_count=act_word_count,
                current_time=current_time,
                starting_id=ss_counter,
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

        return scene_sequels

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
        current_time: float,
        starting_id: int,
    ) -> list[SceneSequel]:
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
            List of SceneSequel objects for this act

        Raises:
            BreakdownGenerationError: If generation fails after retries
        """
        system_prompt, user_prompt = self._build_prompt(
            act=act,
            story_idea=story_idea,
            characters=characters,
            locations=locations,
            act_word_count=act_word_count,
            current_time=current_time,
            starting_id=starting_id,
        )

        # Parser that converts response text to list of SceneSequels
        def parse_to_scene_sequels(response_text: str) -> list[SceneSequel]:
            return self._parse_breakdown_response(response_text, act.title)

        # Use base class retry logic
        return self._generate_with_retry(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            parser=parse_to_scene_sequels,
            temperature=0.7,
            error_class=BreakdownGenerationError,
        )

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
        current_time: float,
        starting_id: int,
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

STORY CONTEXT:
{story_idea.one_sentence}

CHARACTERS (choose POV from this list):
{char_list}

LOCATIONS (use these OR create new specific ones):
{loc_list}

INSTRUCTIONS:
Generate 1-3 scene-sequel pairs for this act. Consider:
- How many scenes does this act need? (1 simple act vs 2-3 complex act)
- Should you include sequels for emotional processing? (action scenes may skip, but character moments need them)
- Balance word count across scene-sequels

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
For sequels (optional): reaction, dilemma, decision

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
