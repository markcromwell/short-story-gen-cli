"""Unit tests for OutlineGenerator."""

import json
from unittest.mock import Mock, patch

import pytest

from storygen.iterative.generators.outline import OutlineGenerationError, OutlineGenerator
from storygen.iterative.models import Act, Character, Location, Outline, StoryIdea
from storygen.iterative.outline_templates import get_template


class TestOutlineGeneratorInitialization:
    """Test OutlineGenerator initialization."""

    def test_initialization_defaults(self):
        """Test initialization with default values."""
        generator = OutlineGenerator()
        assert generator.model == "gpt-4"
        assert generator.structure_type == "three-act"
        assert generator.max_retries == 3
        assert generator.timeout == 600  # Updated to 10 minutes for slower models

    def test_initialization_custom(self):
        """Test initialization with custom values."""
        generator = OutlineGenerator(
            model="ollama/qwen3:30b",
            structure_type="hero-journey",
            max_retries=5,
            timeout=120,
        )
        assert generator.model == "ollama/qwen3:30b"
        assert generator.structure_type == "hero-journey"
        assert generator.max_retries == 5
        assert generator.timeout == 120

    def test_initialization_invalid_structure(self):
        """Test initialization with invalid structure type."""
        from storygen.iterative.exceptions import ConfigError

        with pytest.raises(ConfigError, match="Unknown structure type"):
            OutlineGenerator(structure_type="invalid-structure")


class TestOutlineGeneratorPromptBuilding:
    """Test prompt building."""

    def test_build_prompt(self):
        """Test that prompt includes all necessary context."""
        generator = OutlineGenerator()
        template = get_template("three-act")

        idea = StoryIdea(
            raw_idea="A detective story",
            one_sentence="A detective solves a murder.",
            expanded="A brilliant detective investigates a complex murder case.",
            genres=["mystery", "thriller"],
            tone="dark and suspenseful",
            themes=["justice", "truth"],
            setting="Test setting",
        )

        characters = [
            Character(
                name="Detective Jane",
                role="protagonist",
                bio="A brilliant detective with a troubled past",
                goal="Solve the case",
                flaw="Too obsessive",
            ),
            Character(
                name="The Killer",
                role="antagonist",
                bio="A cunning murderer",
                goal="Escape justice",
                flaw="Overconfident",
            ),
        ]

        locations = [
            Location(
                name="Crime Scene",
                description="A dark alley",
                significance="Where the murder occurred",
                atmosphere="Tense and ominous",
            ),
        ]

        system_prompt, user_prompt = generator._build_prompt(idea, characters, locations, template)

        # Check system prompt explains task
        assert "story_application" in system_prompt
        assert "structure" in system_prompt.lower()

        # Check user prompt includes all context
        assert "A detective solves a murder" in user_prompt
        assert "mystery" in user_prompt
        assert "Detective Jane" in user_prompt
        assert "Crime Scene" in user_prompt

        # Check template structure is included
        assert "Setup" in user_prompt or "Act 1" in user_prompt


class TestOutlineGeneratorResponseParsing:
    """Test response parsing and validation."""

    def test_parse_response_valid(self):
        """Test parsing a valid response with recursive acts."""
        generator = OutlineGenerator()

        response = json.dumps(
            [
                {
                    "title": "Act 1: Setup",
                    "description": "Establish the world",
                    "story_application": "Detective Jane is introduced in her office.",
                    "percentage": 0.25,
                    "order": 1,
                    "sub_acts": [
                        {
                            "title": "Opening Image",
                            "description": "Show normal world",
                            "story_application": "Jane solves a routine case.",
                            "percentage": 0.05,
                            "order": 1,
                            "sub_acts": [],
                            "scenes": [],
                        }
                    ],
                    "scenes": [],
                }
            ]
        )

        result = generator._parse_response(response)

        assert isinstance(result, list)
        assert len(result) >= 1
        assert isinstance(result[0], Act)
        assert result[0].title == "Act 1: Setup"
        assert result[0].story_application == "Detective Jane is introduced in her office."

    def test_parse_response_with_markdown(self):
        """Test parsing response wrapped in markdown code blocks."""
        generator = OutlineGenerator()

        response = """```json
[
  {
    "title": "Act 1",
    "description": "Setup",
    "story_application": "Hero in normal world",
    "percentage": 0.25,
    "order": 1,
    "sub_acts": [],
    "scenes": []
  }
]
```"""

        result = generator._parse_response(response)

        assert isinstance(result, list)
        assert len(result) >= 1
        assert result[0].story_application == "Hero in normal world"

    def test_parse_response_invalid_json(self):
        """Test parsing invalid JSON."""
        generator = OutlineGenerator()

        with pytest.raises(OutlineGenerationError, match="No valid JSON array or objects found"):
            generator._parse_response("{invalid json")

    def test_parse_response_missing_story_application(self):
        """Test parsing response with missing story_application."""
        generator = OutlineGenerator()

        # Missing story_application in first act
        response = json.dumps(
            [
                {
                    "title": "Act 1",
                    "description": "Setup",
                    "story_application": "",  # Empty!
                    "percentage": 0.25,
                    "order": 1,
                    "sub_acts": [],
                    "scenes": [],
                }
            ]
        )

        with pytest.raises(OutlineGenerationError, match="missing story_application"):
            generator._parse_response(response)

    def test_parse_response_nested_missing_story_application(self):
        """Test parsing response with missing story_application in nested act."""
        generator = OutlineGenerator()

        response = json.dumps(
            [
                {
                    "title": "Act 1",
                    "description": "Setup",
                    "story_application": "Hero starts",
                    "percentage": 0.25,
                    "order": 1,
                    "sub_acts": [
                        {
                            "title": "Sub Act",
                            "description": "Detail",
                            "story_application": "",  # Empty in nested!
                            "percentage": 0.25,
                            "order": 1,
                            "sub_acts": [],
                            "scenes": [],
                        }
                    ],
                    "scenes": [],
                }
            ]
        )

        with pytest.raises(OutlineGenerationError, match="missing story_application"):
            generator._parse_response(response)

    def test_parse_response_not_array(self):
        """Test parsing response that is not an array."""
        generator = OutlineGenerator()

        response = json.dumps(
            {
                "title": "Act 1",
                "description": "Setup",
            }
        )

        with pytest.raises(OutlineGenerationError, match="Failed to parse acts"):
            generator._parse_response(response)


class TestOutlineGeneratorGeneration:
    """Test outline generation with mocked AI."""

    def test_generate_success(self):
        """Test successful outline generation."""
        generator = OutlineGenerator(model="gpt-4")

        idea = StoryIdea(
            raw_idea="Test",
            one_sentence="A test story",
            expanded="A detailed test story",
            genres=["test"],
            tone="test",
            themes=["testing"],
            setting="Test setting",
        )

        characters = [
            Character(
                name="Hero",
                role="protagonist",
                bio="The hero",
                goal="Win",
                flaw="Stubborn",
            )
        ]

        locations = [
            Location(
                name="Test Place",
                description="A test location",
                significance="Important",
                atmosphere="Tense",
            )
        ]

        # Mock the AI response with recursive Act structure
        mock_response = Mock()
        mock_choice = Mock()
        mock_message = Mock()
        mock_message.content = json.dumps(
            [
                {
                    "title": "Act 1: Setup",
                    "description": "Establish the world",
                    "story_application": "The hero lives in a normal world.",
                    "percentage": 0.25,
                    "order": 1,
                    "sub_acts": [],
                    "scenes": [],
                },
                {
                    "title": "Act 2: Confrontation",
                    "description": "Rising conflict",
                    "story_application": "The hero faces many trials.",
                    "percentage": 0.50,
                    "order": 2,
                    "sub_acts": [],
                    "scenes": [],
                },
                {
                    "title": "Act 3: Resolution",
                    "description": "Final resolution",
                    "story_application": "Peace is restored to the land.",
                    "percentage": 0.25,
                    "order": 3,
                    "sub_acts": [],
                    "scenes": [],
                },
            ]
        )
        mock_choice.message = mock_message
        mock_response.choices = [mock_choice]

        with patch("litellm.completion", return_value=mock_response):
            outline = generator.generate(idea, characters, locations)

        assert isinstance(outline, Outline)
        assert outline.structure_type == "three-act"
        assert len(outline.acts) == 3
        assert outline.acts[0].title == "Act 1: Setup"
        assert outline.acts[0].story_application == "The hero lives in a normal world."
        assert outline.acts[2].title == "Act 3: Resolution"

    def test_generate_retry_on_timeout(self):
        """Test that generator retries on timeout."""
        generator = OutlineGenerator(model="gpt-4", max_retries=3, timeout=1)

        idea = StoryIdea(
            raw_idea="Test",
            one_sentence="Test",
            expanded="Test",
            genres=["test"],
            tone="test",
            themes=["test"],
            setting="Test setting",
        )
        characters: list[Character] = []
        locations: list[Location] = []

        # Mock timeout on first call, success on second
        mock_success = Mock()
        mock_choice = Mock()
        mock_message = Mock()
        mock_message.content = json.dumps(
            [
                {
                    "title": "Act 1",
                    "description": "Setup",
                    "story_application": "Setup text",
                    "percentage": 0.5,
                    "order": 1,
                    "sub_acts": [],
                    "scenes": [],
                },
                {
                    "title": "Act 2",
                    "description": "Resolution",
                    "story_application": "Resolution text",
                    "percentage": 0.5,
                    "order": 2,
                    "sub_acts": [],
                    "scenes": [],
                },
            ]
        )
        mock_choice.message = mock_message
        mock_success.choices = [mock_choice]

        with patch("litellm.completion", side_effect=[TimeoutError(), mock_success]):
            with patch("time.sleep"):  # Skip actual sleep
                outline = generator.generate(idea, characters, locations)

        assert isinstance(outline, Outline)

    def test_generate_retry_on_malformed_json(self):
        """Test retry on malformed JSON response."""
        generator = OutlineGenerator(model="gpt-4", max_retries=2)

        idea = StoryIdea(
            raw_idea="Test",
            one_sentence="Test",
            expanded="Test",
            genres=["test"],
            tone="test",
            themes=["test"],
            setting="Test setting",
        )
        characters: list[Character] = []
        locations: list[Location] = []

        # Mock malformed JSON on first call, success on second
        mock_bad = Mock()
        mock_bad_choice = Mock()
        mock_bad_message = Mock()
        mock_bad_message.content = "{bad json"
        mock_bad_choice.message = mock_bad_message
        mock_bad.choices = [mock_bad_choice]

        mock_good = Mock()
        mock_good_choice = Mock()
        mock_good_message = Mock()
        mock_good_message.content = json.dumps(
            [
                {
                    "title": "Act 1",
                    "description": "Setup",
                    "story_application": "Setup text",
                    "percentage": 1.0,
                    "order": 1,
                    "sub_acts": [],
                    "scenes": [],
                }
            ]
        )
        mock_good_choice.message = mock_good_message
        mock_good.choices = [mock_good_choice]

        with patch("litellm.completion", side_effect=[mock_bad, mock_good]):
            with patch("time.sleep"):
                outline = generator.generate(idea, characters, locations)

        assert isinstance(outline, Outline)

    def test_generate_exponential_backoff(self):
        """Test that retries use exponential backoff."""
        generator = OutlineGenerator(model="gpt-4", max_retries=3)

        idea = StoryIdea(
            raw_idea="Test",
            one_sentence="Test",
            expanded="Test",
            genres=["test"],
            tone="test",
            themes=["test"],
            setting="Test setting",
        )
        characters: list[Character] = []
        locations: list[Location] = []

        sleep_times = []

        def track_sleep(seconds):
            sleep_times.append(seconds)

        # All attempts fail
        with patch("litellm.completion", side_effect=TimeoutError()):
            with patch("time.sleep", side_effect=track_sleep):
                with pytest.raises(OutlineGenerationError):
                    generator.generate(idea, characters, locations)

        # Should have exponential backoff: 1, 2
        assert sleep_times == [1, 2]
