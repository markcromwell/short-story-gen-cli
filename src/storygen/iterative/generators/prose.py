"""
Prose generator for iterative story creation.

Generates markdown-formatted prose for each scene-sequel based on
the Scene-Sequel structure, story context, and writing style.
"""

import re
from typing import Any

from storygen.iterative.generators.base import BaseGenerator, GenerationError
from storygen.iterative.models import Character, Location, SceneSequel, StoryIdea


class ProseGenerationError(GenerationError):
    """Raised when prose generation fails."""

    pass


class ProseGenerator(BaseGenerator[Any]):  # type: ignore[type-arg]
    """
    Generates prose for scene-sequels using AI.

    Takes a breakdown (list of scene-sequels) and generates markdown-formatted
    prose for each one, maintaining continuity through summaries and key points.

    Note: Uses BaseGenerator for _generate_with_retry but has custom generate()
    that returns list[SceneSequel] instead of the generic type.
    """

    def __init__(
        self,
        model: str = "gpt-4",
        max_retries: int = 3,
        timeout: int = 600,
        temperature: float = 0.7,
        context_window: int = 3,
        verbose: bool = False,
    ):
        """
        Initialize prose generator.

        Args:
            model: LiteLLM model identifier (e.g., "gpt-4", "ollama/qwen3:30b")
            max_retries: Maximum retry attempts for failed API calls
            timeout: Timeout in seconds for each API call (default: 600 = 10 minutes)
            temperature: Sampling temperature (0.0-1.0, higher = more creative)
            context_window: Number of previous scene-sequels to include for continuity
            verbose: Whether to print detailed progress
        """
        super().__init__(model=model, max_retries=max_retries, timeout=timeout, verbose=verbose)
        self.temperature = temperature
        self.context_window = context_window

    def generate(
        self,
        story_idea: StoryIdea,
        characters: list[Character],
        locations: list[Location],
        scene_sequels: list[SceneSequel],
        writing_style: str | None = None,
        output_path: str | None = None,
    ) -> tuple[list[SceneSequel], dict[str, Any]]:
        """
        Generate prose for all scene-sequels in order.

        Args:
            story_idea: The story concept
            characters: List of all characters
            locations: List of all locations
            scene_sequels: List of scene-sequels to generate prose for
            writing_style: Optional writing style (auto-inferred if not provided)
            output_path: Optional path to save progress incrementally after each scene

        Returns:
            Tuple of (updated list of scene-sequels with content, usage information dict)

        Raises:
            ProseGenerationError: If generation fails after all retries
        """
        # Infer writing style if not provided
        if writing_style is None:
            writing_style = self.infer_writing_style(story_idea.tone, story_idea.genres)
            if self.verbose:
                print(f"Inferred writing style: {writing_style}")

        if self.verbose:
            print(f"\nGenerating prose for {len(scene_sequels)} scene-sequels...")
            print(f"   Model: {self.model}")
            print(f"   Temperature: {self.temperature}")
            print(f"   Context window: {self.context_window} previous scenes")
            print(f"   Writing style: {writing_style}\n")

        # Track usage across all scene generations
        total_usage = {
            "total_tokens": 0,
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_cost": 0.0,
            "retries": 0,
            "duration": 0.0,
        }

        # Generate prose for each scene-sequel in order
        for i, ss in enumerate(scene_sequels):
            # Skip if already has content (resume from saved progress)
            if ss.content and ss.actual_word_count > 0:
                if self.verbose:
                    print(f"\n{'='*70}")
                    print(f"⏭️  [{i+1}/{len(scene_sequels)}] {ss.id} - SKIPPED (already complete)")
                    print(f"   Words: {ss.actual_word_count}")
                continue

            if self.verbose:
                print(f"\n{'='*70}")
                print(f"📄 [{i+1}/{len(scene_sequels)}] {ss.id} - {ss.type.upper()}")
                print(f"   POV: {ss.pov_character}")
                print(f"   Location: {ss.location}")
                print(f"   Time: {ss.get_time_summary()}")
                print(f"   Target: {ss.target_word_count} words")

            # Generate prose for this scene-sequel
            usage_info = self._generate_scene_sequel_prose(
                scene_sequel=ss,
                current_index=i,
                all_scene_sequels=scene_sequels,
                story_idea=story_idea,
                characters=characters,
                locations=locations,
                writing_style=writing_style,
            )

            # Accumulate usage
            if usage_info:
                total_usage["total_tokens"] += usage_info.get("total_tokens", 0)
                total_usage["prompt_tokens"] += usage_info.get("prompt_tokens", 0)
                total_usage["completion_tokens"] += usage_info.get("completion_tokens", 0)
                total_usage["total_cost"] += usage_info.get("total_cost", 0.0)
                total_usage["retries"] += usage_info.get("retries", 0)
                total_usage["duration"] += usage_info.get("duration", 0.0)

            if self.verbose:
                print(f"   Generated: {ss.actual_word_count} words")
                print(f"   Summary: {ss.summary[:80]}...")
                print(f"   Key points: {len(ss.key_points)}")

            # Save progress incrementally if output_path provided
            if output_path:
                self._save_progress(scene_sequels, output_path)
                if self.verbose:
                    print(f"   Progress saved to {output_path}")

        if self.verbose:
            print(f"\n{'='*70}")
            print("✅ Prose generation complete!")
            print(f"   Total words: {sum(ss.actual_word_count for ss in scene_sequels)}")

        return scene_sequels, total_usage

    def infer_writing_style(self, tone: str, genres: list[str]) -> str:
        """
        Infer appropriate writing style from tone and genres.

        Args:
            tone: Story tone/mood
            genres: List of story genres

        Returns:
            Writing style description
        """
        tone_lower = tone.lower()
        genre_str = " ".join(genres).lower()

        # Check tone keywords
        if any(word in tone_lower for word in ["psychological", "introspective", "unreliable"]):
            return "close third-person with stream of consciousness"

        if any(word in tone_lower for word in ["tense", "claustrophobic", "suspenseful"]):
            return "tight prose with short, punchy sentences"

        if any(word in tone_lower for word in ["dark", "noir", "gritty"]):
            return "hard-boiled with sparse dialogue"

        if any(word in tone_lower for word in ["atmospheric", "lyrical", "poetic"]):
            return "literary with rich sensory details"

        # Check genres
        if "thriller" in genre_str or "mystery" in genre_str:
            return "fast-paced with lean descriptions"
        elif "literary" in genre_str:
            return "literary with complex sentences and deep introspection"
        elif "horror" in genre_str:
            return "visceral with mounting dread"
        elif "romance" in genre_str:
            return "emotional with focus on internal feelings"

        # Default
        return "balanced prose with clear, vivid descriptions"

    def _generate_scene_sequel_prose(
        self,
        scene_sequel: SceneSequel,
        current_index: int,
        all_scene_sequels: list[SceneSequel],
        story_idea: StoryIdea,
        characters: list[Character],
        locations: list[Location],
        writing_style: str,
    ) -> dict[str, Any]:
        """
        Generate prose for a single scene-sequel.

        Updates the scene_sequel object in place with content, summary, and key_points.

        Args:
            scene_sequel: Scene-sequel to generate prose for
            current_index: Index in the full list
            all_scene_sequels: Full list of all scene-sequels
            story_idea: Story concept
            characters: All characters
            locations: All locations
            writing_style: Writing style to use

        Returns:
            Usage information dict from the AI call
        """
        # Store scene-specific parameters for _build_prompt
        self._scene_sequel = scene_sequel
        self._current_index = current_index
        self._all_scene_sequels = all_scene_sequels
        self._story_idea = story_idea
        self._characters = characters
        self._locations = locations
        self._writing_style = writing_style

        if self.verbose:
            print("\n   🤖 Calling AI...")

        # Parser that validates word count and updates scene-sequel
        def parse_and_validate(response_text: str) -> tuple[str, str, list[str]]:
            content, summary, key_points = self._parse_response(response_text)

            # Validate
            word_count = len(content.split())
            issues = self._validate_prose(scene_sequel, content, word_count)

            if issues and self.verbose:
                print(f"   Validation issues: {', '.join(issues)}")

            # Check if word count is acceptable (±30% - relaxed for smaller models)
            target = scene_sequel.target_word_count
            min_words = int(target * 0.7)
            max_words = int(target * 1.3)
            if word_count < min_words or word_count > max_words:
                self.logger.warning(
                    f"Word count {word_count} outside acceptable range {min_words}-{max_words} words (target {target}, ±30%)"
                )
                # Don't raise exception, just warn and continue

            return (content, summary, key_points)

        # Build prompts
        system_prompt, user_prompt = self._build_prompt()

        # Use base class retry logic
        (result, usage_info) = self._generate_with_retry(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            parser=parse_and_validate,
            temperature=self.temperature,
            error_class=ProseGenerationError,
        )
        content, summary, key_points = result

        # Update scene-sequel
        scene_sequel.content = content
        scene_sequel.summary = summary
        scene_sequel.key_points = key_points
        scene_sequel.actual_word_count = len(content.split())

        return usage_info

    def _build_prompt(self) -> tuple[str, str]:
        """Build prompts for prose generation using stored parameters."""
        return self._build_prompt_impl(
            scene_sequel=self._scene_sequel,
            current_index=self._current_index,
            all_scene_sequels=self._all_scene_sequels,
            story_idea=self._story_idea,
            characters=self._characters,
            locations=self._locations,
            writing_style=self._writing_style,
        )

    def _build_prompt_impl(
        self,
        scene_sequel: SceneSequel,
        current_index: int,
        all_scene_sequels: list[SceneSequel],
        story_idea: StoryIdea,
        characters: list[Character],
        locations: list[Location],
        writing_style: str,
    ) -> tuple[str, str]:
        """
        Build system and user prompts for prose generation.

        Args:
            scene_sequel: Current scene-sequel to write
            current_index: Index in full list
            all_scene_sequels: Full list of scene-sequels
            story_idea: Story concept
            characters: All characters
            locations: All locations
            writing_style: Writing style to use

        Returns:
            Tuple of (system_prompt, user_prompt)
        """
        # Get character details
        pov_char = next((c for c in characters if c.name == scene_sequel.pov_character), None)

        # Build system prompt
        system_prompt = f"""You are a professional fiction writer crafting prose for a story.

WRITING STYLE: {writing_style}
{self._get_style_examples(writing_style)}

MARKDOWN FORMATTING RULES:
- Use *italics* for character thoughts and emphasis
- Use **bold** sparingly for strong emphasis only
- Use proper dialogue formatting: "Hello," she said.
- Write in past tense, third person limited POV
- Show, don't tell - use sensory details and action

DO NOT USE:
- Markdown headers (##, ###) - handled by chapter system
- Horizontal rules (---) - each scene-sequel is atomic
- Section breaks - write continuous prose for this scene/sequel only

OUTPUT FORMAT:
[PROSE]
Your prose content here as continuous markdown...
[/PROSE]

[SUMMARY]
2-3 sentence summary of key events, revelations, and emotional beats.
[/SUMMARY]

[KEY_POINTS]
- Bullet point 1: Critical detail for continuity
- Bullet point 2: Character state change
- Bullet point 3: Plot revelation
- etc. (provide 3-5 key points)
[/KEY_POINTS]

CRITICAL RULES FOR [PROSE] SECTION:
- Write ONLY the story content - no metadata, instructions, or system messages
- No parenthetical notes like "(Word count: 123)"
- No formatting instructions or reminders
- No references to word counts or targets
- Just pure narrative prose with dialogue and descriptions
- Use markdown formatting (*italics*, **bold**) as needed for the story

OUTPUT: Return the complete formatted response with all three sections."""

        # Build user prompt
        user_prompt = f"""Generate prose for scene-sequel #{current_index + 1}/{len(all_scene_sequels)}:

=== STORY OVERVIEW ===
{story_idea.one_sentence}
Tone: {story_idea.tone}
Themes: {', '.join(story_idea.themes)}
Setting: {story_idea.setting}

CRITICAL: Maintain setting consistency throughout the prose.
The story takes place in "{story_idea.setting}".
- Use period-appropriate language and references
- Describe technology, clothing, architecture consistent with the setting
- Ensure cultural norms and social behaviors match the time/place
- Avoid anachronisms or out-of-setting details

=== POV CHARACTER ===
{pov_char.name if pov_char else scene_sequel.pov_character}
"""
        if pov_char:
            user_prompt += f"""Role: {pov_char.role}
Bio: {pov_char.bio}
Goal: {pov_char.goal}
Flaw: {pov_char.flaw}
"""

        user_prompt += f"""
=== LOCATION ===
{scene_sequel.location}
Time: {scene_sequel.get_time_summary()}

"""

        # Add outline structure
        user_prompt += self._format_outline(all_scene_sequels, current_index)

        # Add recent context
        if current_index > 0:
            user_prompt += self._format_recent_context(
                all_scene_sequels[max(0, current_index - self.context_window) : current_index]
            )

        # Add current scene-sequel structure
        user_prompt += f"""
=== CURRENT {scene_sequel.type.upper()} TO WRITE ===
ID: {scene_sequel.id}
Type: {scene_sequel.type}
Source Act: {scene_sequel.source_act}
"""

        if scene_sequel.type == "scene":
            user_prompt += f"""
SCENE STRUCTURE:
Goal: {scene_sequel.goal}
Conflict: {scene_sequel.conflict}
Disaster: {scene_sequel.disaster}

Write this scene showing:
1. The character actively pursuing their goal
2. Obstacles/opposition creating conflict
3. The disaster that prevents success or complicates things
4. Action and external events
"""
        else:  # sequel
            user_prompt += f"""
SEQUEL STRUCTURE:
Reaction: {scene_sequel.reaction}
"""
            if scene_sequel.dilemma:
                user_prompt += f"Dilemma: {scene_sequel.dilemma}\n"
            user_prompt += f"Decision: {scene_sequel.decision}\n"

            user_prompt += """
Write this sequel showing:
1. Character's emotional/physical reaction to previous disaster
2. Internal processing and weighing options (if applicable)
3. The decision that leads to the next goal
4. Introspection and character development
"""

        user_prompt += f"""
TARGET WORD COUNT: {scene_sequel.target_word_count} words (±20% acceptable)

=== INSTRUCTIONS ===
1. Write from {scene_sequel.pov_character}'s perspective
2. Maintain continuity with previous scenes
3. Advance toward upcoming scene-sequels
4. Use the specified writing style consistently
5. Hit the target word count
6. Provide prose, summary, and key points in the required format

CRITICAL: DO NOT include any metadata, word counts, instructions, or system messages in the [PROSE] section. The [PROSE] section should contain ONLY the story content - no parenthetical notes, no formatting instructions, no word count references."""

        return system_prompt, user_prompt

    def _get_style_examples(self, style: str) -> str:
        """Get concrete examples for the specified writing style."""
        examples = {
            "tight prose with short, punchy sentences": """
Apply these techniques:
- Short sentences. Active voice. Minimal adjectives.
- Fast pacing. Direct action.
- Example: "She ran. The door slammed. Silence filled the hall."
""",
            "close third-person with stream of consciousness": """
Apply these techniques:
- Deep POV with character's immediate thoughts.
- Blend narrative and internal monologue seamlessly.
- Example: "The room spun. *Was she dying?* No, no, she couldn't be. But the edges darkened anyway."
""",
            "literary with rich sensory details": """
Apply these techniques:
- Layered descriptions with metaphor and sensory richness.
- Complex sentences with rhythm.
- Example: "She moved through the room like smoke, her presence both there and not there, a whisper of jasmine trailing behind her like an unanswered question."
""",
            "hard-boiled with sparse dialogue": """
Apply these techniques:
- Terse, cynical narration. Minimal but sharp dialogue.
- Noir atmosphere and moral ambiguity.
- Example: "The dame had a story. They all did. I lit a smoke and waited for the part where it got interesting."
""",
            "fast-paced with lean descriptions": """
Apply these techniques:
- Economy of language. Focus on plot momentum.
- Just enough detail to anchor the scene.
- Example: "The killer turned left. Maya followed, keeping distance. Two blocks. The warehouse loomed ahead."
""",
        }

        return examples.get(
            style, "Write clear, engaging prose with vivid details and strong character voice."
        )

    def _format_outline(self, all_scene_sequels: list[SceneSequel], current_index: int) -> str:
        """
        Format the full outline showing what's complete, current, and upcoming.

        Args:
            all_scene_sequels: All scene-sequels
            current_index: Index of current scene-sequel

        Returns:
            Formatted outline string
        """
        outline = "\n=== STORY STRUCTURE (Full Outline) ===\n"

        for i, ss in enumerate(all_scene_sequels):
            if i < current_index:
                # Completed - show summary
                status = "✓"
                detail = f"Summary: {ss.summary[:60]}..." if ss.summary else "(no summary)"
            elif i == current_index:
                # Current
                status = "⚡"
                if ss.type == "scene":
                    detail = f"Goal: {ss.goal}"
                else:
                    detail = f"Reaction/Decision: {ss.reaction or ''} / {ss.decision or ''}"
                detail += " ← YOU ARE HERE"
            else:
                # Upcoming
                status = "⏸"
                if ss.type == "scene":
                    goal_text = ss.goal or "TBD"
                    detail = f"Goal: {goal_text[:60]}..."
                else:
                    decision_text = ss.decision or "TBD"
                    detail = f"Decision: {decision_text[:60]}..."

            outline += f"{status} {ss.id} [{ss.type.upper()}] {ss.source_act}\n"
            outline += f"   {detail}\n"

        return outline

    def _format_recent_context(self, recent_scene_sequels: list[SceneSequel]) -> str:
        """
        Format recent scene-sequels with full content for continuity.

        Args:
            recent_scene_sequels: Last N scene-sequels

        Returns:
            Formatted context string
        """
        if not recent_scene_sequels:
            return ""

        context = f"\n=== RECENT CONTEXT (Last {len(recent_scene_sequels)} Scene-Sequels) ===\n"

        for ss in recent_scene_sequels:
            context += f"\n--- {ss.id} [{ss.type.upper()}] ---\n"
            context += (
                f"POV: {ss.pov_character} | Location: {ss.location} | {ss.get_time_summary()}\n"
            )

            if ss.summary:
                context += f"Summary: {ss.summary}\n"

            if ss.key_points:
                context += "Key Points:\n"
                for point in ss.key_points:
                    context += f"  - {point}\n"

            # Include actual content for immediate continuity
            if ss.content:
                # Truncate if very long (keep last 1000 chars for flow)
                content_preview = (
                    ss.content if len(ss.content) <= 1000 else "..." + ss.content[-1000:]
                )
                context += f"\nContent (excerpt):\n{content_preview}\n"

        return context

    def _parse_response(self, response: str) -> tuple[str, str, list[str]]:
        """
        Parse AI response into prose, summary, and key points.

        Args:
            response: Raw AI response text

        Returns:
            Tuple of (content, summary, key_points)

        Raises:
            ProseGenerationError: If parsing fails
        """
        # Extract prose section
        prose_match = re.search(r"\[PROSE\](.*?)\[/PROSE\]", response, re.DOTALL)
        if not prose_match:
            raise ProseGenerationError("No [PROSE] section found in response")
        content = prose_match.group(1).strip()

        # Clean up content - remove any metadata that might have slipped through
        content = self._clean_prose_content(content)

        # Extract summary section
        summary_match = re.search(r"\[SUMMARY\](.*?)\[/SUMMARY\]", response, re.DOTALL)
        summary = summary_match.group(1).strip() if summary_match else ""

        # Extract key points section
        key_points = []
        key_points_match = re.search(r"\[KEY_POINTS\](.*?)\[/KEY_POINTS\]", response, re.DOTALL)
        if key_points_match:
            points_text = key_points_match.group(1).strip()
            # Parse bullet points
            key_points = [
                line.strip("- ").strip()
                for line in points_text.split("\n")
                if line.strip() and line.strip().startswith("-")
            ]

        if not content:
            raise ProseGenerationError("Empty prose content")

        return content, summary, key_points

    def _clean_prose_content(self, content: str) -> str:
        """
        Clean prose content by removing any metadata or system messages that might have slipped through.

        Args:
            content: Raw prose content

        Returns:
            Cleaned prose content
        """
        import re

        # Remove parenthetical metadata like "(Word count: 1023)"
        content = re.sub(r"\(\s*Word count:\s*\d+\s*\)", "", content, flags=re.IGNORECASE)

        # Remove other common metadata patterns
        content = re.sub(r"\(\s*Target words?:\s*\d+\s*\)", "", content, flags=re.IGNORECASE)
        content = re.sub(
            r"\(\s*Approximately\s*\d+\s*words?\s*\)", "", content, flags=re.IGNORECASE
        )

        # Remove any lines that look like instructions
        lines = content.split("\n")
        cleaned_lines = []
        for line in lines:
            line = line.strip()
            # Skip lines that look like metadata or instructions
            if re.match(
                r"^(Word count|Target|Approximately|Instructions?|Note:)", line, re.IGNORECASE
            ):
                continue
            if (
                line.startswith("(")
                and ("word" in line.lower() or "count" in line.lower())
                and line.endswith(")")
            ):
                continue
            cleaned_lines.append(line)

        return "\n".join(cleaned_lines).strip()

    def _validate_prose(
        self, scene_sequel: SceneSequel, content: str, word_count: int
    ) -> list[str]:
        """
        Validate generated prose.

        Args:
            scene_sequel: Scene-sequel being generated
            content: Generated prose content
            word_count: Actual word count

        Returns:
            List of validation issues (empty if valid)
        """
        issues = []

        target = scene_sequel.target_word_count

        # Check word count (±20% tolerance)
        if word_count < target * 0.8:
            issues.append(f"Too short: {word_count} words (target: {target})")
        elif word_count > target * 1.2:
            issues.append(f"Too long: {word_count} words (target: {target})")

        # Check has actual content
        if not content.strip():
            issues.append("Empty content")

        # Warn about markdown headers (shouldn't be used)
        if re.search(r"^#+\s", content, re.MULTILINE):
            issues.append("Contains markdown headers (should be avoided)")

        return issues

    def _save_progress(self, scene_sequels: list[SceneSequel], output_path: str) -> None:
        """
        Save current progress to JSON file.

        Args:
            scene_sequels: List of scene-sequels (some may still be empty)
            output_path: Path to save JSON file
        """
        import json
        from pathlib import Path

        # Calculate total words generated so far
        total_words = sum(ss.actual_word_count or 0 for ss in scene_sequels)

        # Save to JSON
        prose_dict = {
            "scene_sequels": [ss.to_dict() for ss in scene_sequels],
            "total_actual_words": total_words,
        }

        output = Path(output_path)
        output.parent.mkdir(parents=True, exist_ok=True)

        with open(output, "w", encoding="utf-8") as f:
            json.dump(prose_dict, f, indent=2, ensure_ascii=False)
