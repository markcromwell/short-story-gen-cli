"""
Title generator for stories.

Generates compelling titles based on story idea, genres, and themes.
"""

from storygen.iterative.exceptions import ValidationError
from storygen.iterative.generators.base import BaseGenerator, GenerationError


class TitleGenerationError(GenerationError):
    """Raised when title generation fails."""

    pass


class TitleGenerator(BaseGenerator[str]):
    """Generates story titles using AI."""

    def __init__(
        self,
        model: str = "gpt-4",
        max_retries: int = 3,
        timeout: int = 600,
        verbose: bool = False,
    ):
        """
        Initialize title generator.

        Args:
            model: LiteLLM model identifier
            max_retries: Maximum retry attempts on failure
            timeout: Timeout in seconds for AI calls (default: 600 = 10 minutes)
            verbose: Print detailed progress
        """
        super().__init__(model=model, max_retries=max_retries, timeout=timeout, verbose=verbose)

    def generate(
        self,
        raw_idea: str,
        one_sentence: str,
        genres: list[str],
        themes: list[str],
        tone: str,
        scene_sequels: list | None = None,
    ) -> str:
        """
        Generate a compelling title for the story.

        Args:
            raw_idea: Original story concept
            one_sentence: One-sentence story hook
            genres: List of genres
            themes: List of themes
            tone: Story tone
            scene_sequels: Optional list of SceneSequel objects with actual story content

        Returns:
            Generated title (2-5 words, punchy and memorable)
        """
        if self.verbose:
            print(f"📖 Generating title with {self.model}...")
            if scene_sequels:
                print(f"   Analyzing {len(scene_sequels)} scenes from the complete story...")

        # Store parameters for use in _build_prompt
        self._raw_idea = raw_idea
        self._one_sentence = one_sentence
        self._genres = genres
        self._themes = themes
        self._tone = tone
        self._scene_sequels = scene_sequels

        # Parser that validates the title
        def parse_and_validate(response_text: str) -> str:
            title = self._parse_response(response_text)
            self._validate_title(title)
            return title

        # Build prompts
        system_prompt, user_prompt = self._build_prompt()

        # Use base class retry logic
        title = self._generate_with_retry(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            parser=parse_and_validate,
            temperature=0.8,  # Higher temperature for creative titles
            error_class=TitleGenerationError,
        )

        if self.verbose:
            print(f"✅ Generated title: {title}")

        return title

    def _build_prompt(self) -> tuple[str, str]:
        """Build prompts for title generation."""
        system_prompt = self._build_system_prompt()
        user_prompt = self._build_user_prompt(
            self._raw_idea,
            self._one_sentence,
            self._genres,
            self._themes,
            self._tone,
            self._scene_sequels,
        )
        return (system_prompt, user_prompt)

    def _build_system_prompt(self) -> str:
        """Build system prompt for title generation."""
        return """You are an expert book title creator. Generate compelling, marketable titles that:

1. Are 2-5 words (rarely more)
2. Evoke the story's atmosphere and genre
3. Are memorable and punchy
4. Avoid clichés and overused phrases
5. Could plausibly appear on a book cover

Output ONLY the title, nothing else. No quotes, no explanation, no alternate options."""

    def _build_user_prompt(
        self,
        raw_idea: str,
        one_sentence: str,
        genres: list[str],
        themes: list[str],
        tone: str,
        scene_sequels: list | None,
    ) -> str:
        """Build user prompt with story details."""
        genres_str = ", ".join(genres)
        themes_str = ", ".join(themes)

        prompt = f"""Generate a compelling title for this story:

**Original Concept:** {raw_idea}

**One-Sentence Hook:** {one_sentence}

**Genres:** {genres_str}

**Themes:** {themes_str}

**Tone:** {tone}
"""

        # If we have the actual story content, analyze it
        if scene_sequels:
            story_analysis = self._analyze_story_content(scene_sequels)
            prompt += f"""
**STORY ANALYSIS (from complete manuscript):**

{story_analysis}

Based on the ACTUAL STORY above (not just the concept), generate a title that reflects what the story truly becomes - its emotional core, character arcs, and ultimate meaning. The title should resonate with readers who finish the story.
"""
        else:
            prompt += """
Create a title that captures the essence of this story. Consider the genre conventions and thematic elements. The title should be intriguing and make readers want to know more.
"""

        prompt += "\nOutput only the title, nothing else."
        return prompt

    def _analyze_story_content(self, scene_sequels: list) -> str:
        """
        Analyze actual story content to extract key elements for title generation.

        Args:
            scene_sequels: List of SceneSequel objects with prose content

        Returns:
            Formatted analysis of story content
        """
        if not scene_sequels:
            return ""

        # Get opening scene
        opening = scene_sequels[0]
        opening_summary = opening.summary if hasattr(opening, "summary") and opening.summary else ""

        # Get climax/resolution (last 2-3 scenes)
        climax_scenes = scene_sequels[-3:] if len(scene_sequels) >= 3 else scene_sequels[-2:]
        climax_summaries = []
        for scene in climax_scenes:
            if hasattr(scene, "summary") and scene.summary:
                climax_summaries.append(scene.summary)

        # Get key character moments (scenes with decisions or disasters)
        key_moments = []
        for scene in scene_sequels:
            if hasattr(scene, "disaster") and scene.disaster:
                key_moments.append(f"Disaster: {scene.disaster}")
            if hasattr(scene, "decision") and scene.decision:
                key_moments.append(f"Decision: {scene.decision}")

        # Limit key moments to most significant ones
        key_moments = key_moments[:5]

        # Get total word count and scene count
        total_words = sum(getattr(scene, "actual_word_count", 0) for scene in scene_sequels)

        # Build analysis
        analysis = f"**Story Length:** {len(scene_sequels)} scenes, {total_words:,} words\n\n"

        if opening_summary:
            analysis += f"**Opening:** {opening_summary}\n\n"

        if key_moments:
            analysis += "**Key Turning Points:**\n"
            for moment in key_moments:
                analysis += f"- {moment}\n"
            analysis += "\n"

        if climax_summaries:
            analysis += "**Climax/Resolution:**\n"
            for summary in climax_summaries:
                analysis += f"- {summary}\n"
            analysis += "\n"

        # Extract a sample of actual prose from opening and ending
        opening_prose = ""
        if hasattr(opening, "content") and opening.content:
            # Get first paragraph
            paragraphs = opening.content.split("\n\n")
            opening_prose = paragraphs[0][:300] if paragraphs else opening.content[:300]

        ending_prose = ""
        last_scene = scene_sequels[-1]
        if hasattr(last_scene, "content") and last_scene.content:
            # Get last paragraph
            paragraphs = last_scene.content.split("\n\n")
            ending_prose = paragraphs[-1][:300] if paragraphs else last_scene.content[-300:]

        if opening_prose:
            analysis += f"**Opening Prose Sample:**\n{opening_prose}...\n\n"

        if ending_prose:
            analysis += f"**Ending Prose Sample:**\n{ending_prose}...\n\n"

        return analysis

    def _parse_response(self, content: str) -> str:
        """Parse title from AI response."""
        # Remove any quotes
        title = content.strip().strip('"').strip("'")

        # Remove any explanatory text (sometimes AI adds "Title: " prefix)
        if ":" in title and title.index(":") < 10:
            title = title.split(":", 1)[1].strip()

        # Remove "The " prefix if it makes title too long
        if title.lower().startswith("the ") and len(title.split()) > 5:
            title = title[4:]

        # Take first line if multi-line
        title = title.split("\n")[0].strip()

        return title

    def _validate_title(self, title: str) -> None:
        """Validate generated title."""
        if not title:
            raise ValidationError("Generated title is empty")

        if len(title) < 3:
            raise ValidationError(f"Title too short: {title}")

        if len(title) > 100:
            raise ValidationError(f"Title too long: {title}")

        # Check for too many words
        word_count = len(title.split())
        if word_count > 15:
            raise ValidationError(f"Title has too many words ({word_count}): {title}")
