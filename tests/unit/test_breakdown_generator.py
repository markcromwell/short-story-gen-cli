"""Unit tests for BreakdownGenerator."""

from unittest.mock import MagicMock, patch

import pytest

from storygen.iterative.generators.breakdown import (
    BreakdownGenerationError,
    BreakdownGenerator,
)
from storygen.iterative.models import (
    Act,
    Character,
    Location,
    Outline,
    StoryIdea,
)


class TestBreakdownGeneratorInitialization:
    """Tests for BreakdownGenerator initialization."""

    def test_initialization_defaults(self):
        """Test generator initializes with default values."""
        generator = BreakdownGenerator()

        assert generator.model == "gpt-4"
        assert generator.max_retries == 3
        assert generator.timeout == 600  # Updated to 10 minutes for slower models
        assert generator.verbose is False

    def test_initialization_custom(self):
        """Test generator initializes with custom values."""
        generator = BreakdownGenerator(
            model="ollama/qwen3:30b",
            max_retries=5,
            timeout=600,
            verbose=True,
        )

        assert generator.model == "ollama/qwen3:30b"
        assert generator.max_retries == 5
        assert generator.timeout == 600
        assert generator.verbose is True


class TestBreakdownGeneratorGetLeafActs:
    """Tests for _get_leaf_acts method."""

    def test_get_leaf_acts_flat_structure(self):
        """Test extracting leaf acts from flat structure."""
        generator = BreakdownGenerator()
        acts = [
            Act(
                title="Setup",
                description="Beginning",
                percentage=0.33,
                story_application="Establish world",
            ),
            Act(
                title="Confrontation",
                description="Middle",
                percentage=0.34,
                story_application="Rising action",
            ),
            Act(
                title="Resolution",
                description="End",
                percentage=0.33,
                story_application="Wrap up",
            ),
        ]

        leaf_acts = generator._get_leaf_acts(acts)

        assert len(leaf_acts) == 3
        assert leaf_acts[0].title == "Setup"
        assert leaf_acts[1].title == "Confrontation"
        assert leaf_acts[2].title == "Resolution"

    def test_get_leaf_acts_nested_structure(self):
        """Test extracting leaf acts from nested structure."""
        generator = BreakdownGenerator()
        acts = [
            Act(
                title="Act 1",
                description="Beginning",
                percentage=0.5,
                story_application="Setup",
                sub_acts=[
                    Act(
                        title="Opening",
                        description="Start",
                        percentage=0.25,
                        story_application="Introduce",
                    ),
                    Act(
                        title="Setup",
                        description="Continue",
                        percentage=0.25,
                        story_application="Build",
                    ),
                ],
            ),
            Act(
                title="Act 2",
                description="End",
                percentage=0.5,
                story_application="Wrap up",
            ),
        ]

        leaf_acts = generator._get_leaf_acts(acts)

        assert len(leaf_acts) == 3
        assert leaf_acts[0].title == "Opening"
        assert leaf_acts[1].title == "Setup"
        assert leaf_acts[2].title == "Act 2"

    def test_get_leaf_acts_deeply_nested(self):
        """Test extracting leaf acts from deeply nested structure."""
        generator = BreakdownGenerator()
        acts = [
            Act(
                title="Root",
                description="Top",
                percentage=1.0,
                story_application="Story",
                sub_acts=[
                    Act(
                        title="Branch",
                        description="Middle",
                        percentage=0.5,
                        story_application="Part",
                        sub_acts=[
                            Act(
                                title="Leaf1",
                                description="Detail",
                                percentage=0.25,
                                story_application="Scene",
                            ),
                            Act(
                                title="Leaf2",
                                description="Detail",
                                percentage=0.25,
                                story_application="Scene",
                            ),
                        ],
                    ),
                    Act(
                        title="Leaf3",
                        description="Detail",
                        percentage=0.5,
                        story_application="Scene",
                    ),
                ],
            ),
        ]

        leaf_acts = generator._get_leaf_acts(acts)

        assert len(leaf_acts) == 3
        assert leaf_acts[0].title == "Leaf1"
        assert leaf_acts[1].title == "Leaf2"
        assert leaf_acts[2].title == "Leaf3"

    def test_get_leaf_acts_empty_list(self):
        """Test extracting leaf acts from empty list."""
        generator = BreakdownGenerator()
        leaf_acts = generator._get_leaf_acts([])

        assert len(leaf_acts) == 0


class TestBreakdownGeneratorParseResponse:
    """Tests for _parse_response method."""

    def test_parse_response_valid_scene(self):
        """Test parsing valid scene response."""
        generator = BreakdownGenerator()
        response = """[
  {
    "id": "ss_001",
    "type": "scene",
    "source_act": "Opening",
    "pov_character": "Detective Maya",
    "location": "Police Station",
    "start_hours": 0.0,
    "duration_hours": 1.0,
    "goal": "Find the killer",
    "conflict": "Evidence is missing",
    "disaster": "Witness is murdered",
    "target_word_count": 500
  }
]"""

        scene_sequels = generator._parse_response(response, "Opening")

        assert len(scene_sequels) == 1
        assert scene_sequels[0].id == "ss_001"
        assert scene_sequels[0].type == "scene"
        assert scene_sequels[0].source_act == "Opening"
        assert scene_sequels[0].pov_character == "Detective Maya"
        assert scene_sequels[0].location == "Police Station"
        assert scene_sequels[0].start_hours == 0.0
        assert scene_sequels[0].duration_hours == 1.0
        assert scene_sequels[0].goal == "Find the killer"
        assert scene_sequels[0].conflict == "Evidence is missing"
        assert scene_sequels[0].disaster == "Witness is murdered"
        assert scene_sequels[0].target_word_count == 500

    def test_parse_response_valid_sequel(self):
        """Test parsing valid sequel response."""
        generator = BreakdownGenerator()
        response = """[
  {
    "id": "ss_002",
    "type": "sequel",
    "source_act": "Opening",
    "pov_character": "Detective Maya",
    "location": "Maya's Apartment",
    "start_hours": 1.0,
    "duration_hours": 0.5,
    "reaction": "Maya feels defeated",
    "dilemma": "Give up or continue?",
    "decision": "She decides to push forward",
    "target_word_count": 300
  }
]"""

        scene_sequels = generator._parse_response(response, "Opening")

        assert len(scene_sequels) == 1
        assert scene_sequels[0].id == "ss_002"
        assert scene_sequels[0].type == "sequel"
        assert scene_sequels[0].reaction == "Maya feels defeated"
        assert scene_sequels[0].dilemma == "Give up or continue?"
        assert scene_sequels[0].decision == "She decides to push forward"

    def test_parse_response_multiple_scene_sequels(self):
        """Test parsing multiple scene-sequels."""
        generator = BreakdownGenerator()
        response = """[
  {
    "id": "ss_001",
    "type": "scene",
    "source_act": "Opening",
    "pov_character": "Maya",
    "location": "Station",
    "start_hours": 0.0,
    "duration_hours": 1.0,
    "goal": "Test",
    "conflict": "Test",
    "disaster": "Test",
    "target_word_count": 500
  },
  {
    "id": "ss_002",
    "type": "sequel",
    "source_act": "Opening",
    "pov_character": "Maya",
    "location": "Home",
    "start_hours": 1.0,
    "duration_hours": 0.5,
    "reaction": "Test",
    "target_word_count": 300
  }
]"""

        scene_sequels = generator._parse_response(response, "Opening")

        assert len(scene_sequels) == 2
        assert scene_sequels[0].type == "scene"
        assert scene_sequels[1].type == "sequel"

    def test_parse_response_with_markdown_fences(self):
        """Test parsing response with markdown code fences."""
        generator = BreakdownGenerator()
        response = """```json
[
  {
    "id": "ss_001",
    "type": "scene",
    "source_act": "Opening",
    "pov_character": "Maya",
    "location": "Station",
    "start_hours": 0.0,
    "duration_hours": 1.0,
    "goal": "Test",
    "conflict": "Test",
    "disaster": "Test",
    "target_word_count": 500
  }
]
```"""

        scene_sequels = generator._parse_response(response, "Opening")

        assert len(scene_sequels) == 1
        assert scene_sequels[0].id == "ss_001"

    def test_parse_response_with_prose_before_json(self):
        """Test parsing response with prose before JSON."""
        generator = BreakdownGenerator()
        response = """Here is the scene breakdown:

[
  {
    "id": "ss_001",
    "type": "scene",
    "source_act": "Opening",
    "pov_character": "Maya",
    "location": "Station",
    "start_hours": 0.0,
    "duration_hours": 1.0,
    "goal": "Test",
    "conflict": "Test",
    "disaster": "Test",
    "target_word_count": 500
  }
]"""

        scene_sequels = generator._parse_response(response, "Opening")

        assert len(scene_sequels) == 1

    def test_parse_response_invalid_json_raises(self):
        """Test parsing invalid JSON raises error."""
        generator = BreakdownGenerator()
        response = "This is not valid JSON"

        with pytest.raises(BreakdownGenerationError) as exc_info:
            generator._parse_response(response, "Opening")

        assert "No valid JSON array or objects found" in str(exc_info.value)

    def test_parse_response_not_array_raises(self):
        """Test parsing non-array JSON raises error."""
        generator = BreakdownGenerator()
        response = """{"id": "ss_001", "type": "scene"}"""

        with pytest.raises(BreakdownGenerationError) as exc_info:
            generator._parse_response(response, "Opening")

        assert "Scene-sequel missing required fields" in str(exc_info.value)

    def test_parse_response_empty_array(self):
        """Test parsing empty array returns empty list."""
        generator = BreakdownGenerator()
        response = "[]"

        scene_sequels = generator._parse_response(response, "Opening")

        assert len(scene_sequels) == 0

    def test_parse_response_missing_required_field_raises(self):
        """Test parsing scene-sequel missing required field raises error."""
        generator = BreakdownGenerator()
        response = """[
  {
    "id": "ss_001",
    "type": "scene",
    "pov_character": "Maya",
    "location": "Station",
    "start_hours": 0.0,
    "duration_hours": 1.0,
    "goal": "Test",
    "conflict": "Test",
    "disaster": "Test"
  }
]"""

        with pytest.raises(BreakdownGenerationError) as exc_info:
            generator._parse_response(response, "Opening")

        assert (
            "missing" in str(exc_info.value).lower() and "source_act" in str(exc_info.value).lower()
        )


class TestBreakdownGeneratorBuildPrompt:
    """Tests for _build_prompt method."""

    def test_build_prompt_basic_structure(self):
        """Test prompt building has required sections."""
        generator = BreakdownGenerator()

        story_idea = StoryIdea(
            raw_idea="Mystery story",
            one_sentence="A detective solves a murder",
            expanded="Mystery story",
            genres=["mystery"],
            tone="test",
            themes=["justice"],
            setting="Test setting",
        )

        characters = [
            Character(
                name="Detective Maya",
                role="protagonist",
                bio="A skilled detective",
                goal="Solve the case",
                flaw="Too trusting",
            )
        ]

        locations = [
            Location(
                name="Police Station",
                description="Where Maya works",
                atmosphere="Busy",
                significance="Central hub",
            )
        ]

        act = Act(
            title="Opening",
            description="The beginning",
            percentage=0.5,
            story_application="Introduce Maya",
        )

        system_prompt, user_prompt = generator._build_prompt(
            act=act,
            story_idea=story_idea,
            characters=characters,
            locations=locations,
            act_word_count=1000,
            scene_guidelines={
                "total_scene_units": 5,
                "min_scenes": 3,
                "max_scenes": 4,
                "min_sequels": 1,
                "max_sequels": 2,
                "min_words_per_unit": 600,
                "max_words_per_unit": 1800,
            },
            current_time=0.0,
            starting_id=1,
            target_words=5000,
        )

        # Check system prompt
        assert "Scene-Sequel structure" in system_prompt or "SCENE-SEQUEL" in system_prompt
        assert "JSON" in system_prompt
        assert "goal" in system_prompt
        assert "conflict" in system_prompt
        assert "disaster" in system_prompt

        # Check user prompt
        assert "Opening" in user_prompt
        assert "The beginning" in user_prompt
        assert "Introduce Maya" in user_prompt
        assert "Detective Maya" in user_prompt
        assert "Police Station" in user_prompt
        assert "1000" in user_prompt
        assert "0.0" in user_prompt

    def test_build_prompt_includes_all_characters(self):
        """Test prompt includes all character information."""
        generator = BreakdownGenerator()

        story_idea = StoryIdea(
            raw_idea="Test",
            one_sentence="Test story",
            expanded="Test",
            genres=["test"],
            tone="test",
            themes=["test"],
            setting="Test setting",
        )

        characters = [
            Character(
                name="Hero",
                role="protagonist",
                bio="The hero",
                goal="Win",
                flaw="Impulsive",
            ),
            Character(
                name="Villain",
                role="antagonist",
                bio="The villain",
                goal="Destroy",
                flaw="Arrogant",
            ),
        ]

        locations = [
            Location(
                name="Castle",
                description="Big castle",
                atmosphere="Dark",
                significance="Final battle",
            )
        ]

        act = Act(
            title="Test",
            description="Test",
            percentage=1.0,
            story_application="Test",
        )

        system_prompt, user_prompt = generator._build_prompt(
            act=act,
            story_idea=story_idea,
            characters=characters,
            locations=locations,
            act_word_count=500,
            scene_guidelines={
                "total_scene_units": 5,
                "min_scenes": 3,
                "max_scenes": 4,
                "min_sequels": 1,
                "max_sequels": 2,
                "min_words_per_unit": 600,
                "max_words_per_unit": 1800,
            },
            current_time=0.0,
            starting_id=1,
            target_words=5000,
        )

        assert "Hero" in user_prompt
        assert "Villain" in user_prompt
        assert "protagonist" in user_prompt
        assert "antagonist" in user_prompt

    def test_build_prompt_includes_all_locations(self):
        """Test prompt includes all location information."""
        generator = BreakdownGenerator()

        story_idea = StoryIdea(
            raw_idea="Test",
            one_sentence="Test story",
            expanded="Test",
            genres=["test"],
            tone="test",
            themes=["test"],
            setting="Test setting",
        )

        characters = [
            Character(
                name="Hero",
                role="protagonist",
                bio="The hero",
                goal="Win",
                flaw="Impulsive",
            )
        ]

        locations = [
            Location(
                name="Castle",
                description="Big castle",
                atmosphere="Dark",
                significance="Final battle",
            ),
            Location(
                name="Forest",
                description="Dense woods",
                atmosphere="Mysterious",
                significance="Where hero trains",
            ),
        ]

        act = Act(
            title="Test",
            description="Test",
            percentage=1.0,
            story_application="Test",
        )

        system_prompt, user_prompt = generator._build_prompt(
            act=act,
            story_idea=story_idea,
            characters=characters,
            locations=locations,
            act_word_count=500,
            scene_guidelines={
                "total_scene_units": 5,
                "min_scenes": 3,
                "max_scenes": 4,
                "min_sequels": 1,
                "max_sequels": 2,
                "min_words_per_unit": 600,
                "max_words_per_unit": 1800,
            },
            current_time=0.0,
            starting_id=1,
            target_words=5000,
        )

        assert "Castle" in user_prompt
        assert "Forest" in user_prompt


class TestBreakdownGeneratorGenerate:
    """Tests for generate method."""

    @patch("storygen.iterative.generators.base.litellm")
    def test_generate_success(self, mock_litellm):
        """Test successful generation of scene-sequels."""
        # Mock AI response
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = """[
  {
    "id": "ss_001",
    "type": "scene",
    "source_act": "Opening",
    "pov_character": "Maya",
    "location": "Station",
    "start_hours": 0.0,
    "duration_hours": 1.0,
    "goal": "Solve case",
    "conflict": "No evidence",
    "disaster": "Witness dies",
    "target_word_count": 500
  }
]"""
        mock_litellm.completion.return_value = mock_response

        generator = BreakdownGenerator(model="test-model")

        story_idea = StoryIdea(
            raw_idea="Test",
            one_sentence="Test story",
            expanded="Test",
            genres=["test"],
            tone="test",
            themes=["test"],
            setting="Test setting",
        )

        characters = [
            Character(
                name="Maya",
                role="protagonist",
                bio="Detective",
                goal="Solve case",
                flaw="Too trusting",
            )
        ]

        locations = [
            Location(
                name="Station",
                description="Police station",
                atmosphere="Busy",
                significance="Work",
            )
        ]

        outline = Outline(
            structure_type="three-act",
            acts=[
                Act(
                    title="Opening",
                    description="Beginning",
                    percentage=1.0,
                    story_application="Start",
                )
            ],
        )

        scene_sequels, usage_info = generator.generate(
            story_idea=story_idea,
            characters=characters,
            locations=locations,
            outline=outline,
            target_words=1000,
        )

        assert len(scene_sequels) == 1
        assert scene_sequels[0].id == "ss_001"
        assert scene_sequels[0].pov_character == "Maya"
        assert scene_sequels[0].location == "Station"

    @patch("storygen.iterative.generators.base.litellm")
    def test_generate_multiple_acts(self, mock_litellm):
        """Test generation with multiple acts."""
        # Mock AI response
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = """[
  {
    "id": "ss_001",
    "type": "scene",
    "source_act": "Act",
    "pov_character": "Maya",
    "location": "Station",
    "start_hours": 0.0,
    "duration_hours": 1.0,
    "goal": "Test",
    "conflict": "Test",
    "disaster": "Test",
    "target_word_count": 333
  }
]"""
        mock_litellm.completion.return_value = mock_response

        generator = BreakdownGenerator(model="test-model")

        story_idea = StoryIdea(
            raw_idea="Test",
            one_sentence="Test",
            expanded="Test",
            genres=["test"],
            tone="test",
            themes=["test"],
            setting="Test setting",
        )

        characters = [
            Character(
                name="Maya",
                role="protagonist",
                bio="Test",
                goal="Test",
                flaw="Test",
            )
        ]

        locations = [
            Location(
                name="Station",
                description="Test",
                atmosphere="Test",
                significance="Test",
            )
        ]

        outline = Outline(
            structure_type="three-act",
            acts=[
                Act(
                    title="Act1",
                    description="Test",
                    percentage=0.33,
                    story_application="Test",
                ),
                Act(
                    title="Act2",
                    description="Test",
                    percentage=0.34,
                    story_application="Test",
                ),
                Act(
                    title="Act3",
                    description="Test",
                    percentage=0.33,
                    story_application="Test",
                ),
            ],
        )

        scene_sequels, usage_info = generator.generate(
            story_idea=story_idea,
            characters=characters,
            locations=locations,
            outline=outline,
            target_words=1000,
        )

        # Should have 3 scene-sequels (one per act)
        assert len(scene_sequels) == 3
        assert mock_litellm.completion.call_count == 3

    @patch("storygen.iterative.generators.base.litellm")
    def test_generate_tracks_time_progression(self, mock_litellm):
        """Test that generation tracks time progression across acts."""
        # Mock AI response with different start times
        responses = [
            """[{"id": "ss_001", "type": "scene", "source_act": "Act1", "pov_character": "Maya", "location": "A", "start_hours": 0.0, "duration_hours": 1.0, "goal": "Test", "conflict": "Test", "disaster": "Test", "target_word_count": 500}]""",
            """[{"id": "ss_002", "type": "scene", "source_act": "Act2", "pov_character": "Maya", "location": "B", "start_hours": 1.0, "duration_hours": 2.0, "goal": "Test", "conflict": "Test", "disaster": "Test", "target_word_count": 500}]""",
        ]

        mock_litellm.completion.side_effect = [
            self._create_mock_response(responses[0]),
            self._create_mock_response(responses[1]),
        ]

        generator = BreakdownGenerator(model="test-model")

        story_idea = StoryIdea(
            raw_idea="Test",
            one_sentence="Test",
            expanded="Test",
            genres=["test"],
            tone="test",
            themes=["test"],
            setting="Test setting",
        )

        characters = [
            Character(
                name="Maya",
                role="protagonist",
                bio="Test",
                goal="Test",
                flaw="Test",
            )
        ]

        locations = [
            Location(
                name="A",
                description="Test",
                atmosphere="Test",
                significance="Test",
            )
        ]

        outline = Outline(
            structure_type="two-act",
            acts=[
                Act(
                    title="Act1",
                    description="Test",
                    percentage=0.5,
                    story_application="Test",
                ),
                Act(
                    title="Act2",
                    description="Test",
                    percentage=0.5,
                    story_application="Test",
                ),
            ],
        )

        scene_sequels, usage_info = generator.generate(
            story_idea=story_idea,
            characters=characters,
            locations=locations,
            outline=outline,
            target_words=1000,
        )

        assert len(scene_sequels) == 2
        assert scene_sequels[0].start_hours == 0.0
        assert scene_sequels[0].end_hours == 1.0
        assert scene_sequels[1].start_hours == 1.0
        assert scene_sequels[1].end_hours == 3.0

    @staticmethod
    def _create_mock_response(content):
        """Helper to create mock response."""
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = content
        return mock_response

    @patch("storygen.iterative.generators.base.litellm")
    def test_generate_retry_on_failure(self, mock_litellm):
        """Test that generation retries on failure."""
        # First call fails, second succeeds
        mock_litellm.completion.side_effect = [
            Exception("API Error"),
            self._create_mock_response(
                """[{"id": "ss_001", "type": "scene", "source_act": "Act", "pov_character": "Maya", "location": "A", "start_hours": 0.0, "duration_hours": 1.0, "goal": "Test", "conflict": "Test", "disaster": "Test", "target_word_count": 500}]"""
            ),
        ]

        generator = BreakdownGenerator(model="test-model", max_retries=3)

        story_idea = StoryIdea(
            raw_idea="Test",
            one_sentence="Test",
            expanded="Test",
            genres=["test"],
            tone="test",
            themes=["test"],
            setting="Test setting",
        )

        characters = [
            Character(
                name="Maya",
                role="protagonist",
                bio="Test",
                goal="Test",
                flaw="Test",
            )
        ]

        locations = [
            Location(
                name="A",
                description="Test",
                atmosphere="Test",
                significance="Test",
            )
        ]

        outline = Outline(
            structure_type="one-act",
            acts=[
                Act(
                    title="Act",
                    description="Test",
                    percentage=1.0,
                    story_application="Test",
                )
            ],
        )

        scene_sequels, usage_info = generator.generate(
            story_idea=story_idea,
            characters=characters,
            locations=locations,
            outline=outline,
            target_words=1000,
        )

        assert len(scene_sequels) == 1
        assert mock_litellm.completion.call_count == 2

    @patch("storygen.iterative.generators.base.litellm")
    def test_generate_fails_after_max_retries(self, mock_litellm):
        """Test that generation fails after max retries."""
        mock_litellm.completion.side_effect = Exception("API Error")

        generator = BreakdownGenerator(model="test-model", max_retries=2)

        story_idea = StoryIdea(
            raw_idea="Test",
            one_sentence="Test",
            expanded="Test",
            genres=["test"],
            tone="test",
            themes=["test"],
            setting="Test setting",
        )

        characters = [
            Character(
                name="Maya",
                role="protagonist",
                bio="Test",
                goal="Test",
                flaw="Test",
            )
        ]

        locations = [
            Location(
                name="A",
                description="Test",
                atmosphere="Test",
                significance="Test",
            )
        ]

        outline = Outline(
            structure_type="one-act",
            acts=[
                Act(
                    title="Act",
                    description="Test",
                    percentage=1.0,
                    story_application="Test",
                )
            ],
        )

        with pytest.raises(BreakdownGenerationError) as exc_info:
            generator.generate(
                story_idea=story_idea,
                characters=characters,
                locations=locations,
                outline=outline,
                target_words=1000,
            )

        assert "Failed to generate after 2 attempts" in str(exc_info.value)
        assert mock_litellm.completion.call_count == 2
