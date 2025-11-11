"""Unit tests for OutlineGenerator."""

import json
from unittest.mock import Mock, patch

import pytest

from storygen.iterative.generators.outline import OutlineGenerationError, OutlineGenerator
from storygen.iterative.models import Character, Location, Outline, StoryIdea


class TestOutlineGeneratorInitialization:
    """Test OutlineGenerator initialization."""

    def test_initialization_defaults(self):
        """Test initialization with default values."""
        generator = OutlineGenerator()
        assert generator.model == "gpt-4"
        assert generator.max_retries == 3
        assert generator.timeout == 60

    def test_initialization_custom(self):
        """Test initialization with custom values."""
        generator = OutlineGenerator(
            model="ollama/qwen3:30b",
            max_retries=5,
            timeout=120,
        )
        assert generator.model == "ollama/qwen3:30b"
        assert generator.max_retries == 5
        assert generator.timeout == 120


class TestOutlineGeneratorPromptBuilding:
    """Test prompt building."""

    def test_build_prompt(self):
        """Test that prompt includes all necessary context."""
        generator = OutlineGenerator()

        idea = StoryIdea(
            raw_idea="A detective story",
            one_sentence="A detective solves a murder.",
            expanded="A brilliant detective investigates a complex murder case.",
            genres=["mystery", "thriller"],
            tone="dark and suspenseful",
            themes=["justice", "truth"],
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

        system_prompt, user_prompt = generator._build_prompt(idea, characters, locations)

        # Check system prompt
        assert "3-act" in system_prompt.lower()
        assert "7" in system_prompt
        assert "act1_setup" in system_prompt
        assert "act3_resolution" in system_prompt

        # Check user prompt includes all context
        assert "A detective solves a murder" in user_prompt
        assert "mystery" in user_prompt
        assert "Detective Jane" in user_prompt
        assert "Crime Scene" in user_prompt


class TestOutlineGeneratorResponseParsing:
    """Test response parsing and validation."""

    def test_parse_response_valid(self):
        """Test parsing a valid response."""
        generator = OutlineGenerator()

        response = json.dumps(
            {
                "act1_setup": "The protagonist is introduced in their normal world.",
                "act1_inciting_incident": "An event disrupts their life.",
                "act2_rising_action": "They pursue a goal but face obstacles.",
                "act2_midpoint": "A major revelation changes everything.",
                "act2_crisis": "All seems lost at the darkest moment.",
                "act3_climax": "The final confrontation occurs.",
                "act3_resolution": "A new normal is established.",
            }
        )

        result = generator._parse_response(response)

        assert isinstance(result, dict)
        assert result["act1_setup"] == "The protagonist is introduced in their normal world."
        assert result["act3_resolution"] == "A new normal is established."

    def test_parse_response_with_markdown(self):
        """Test parsing response wrapped in markdown code blocks."""
        generator = OutlineGenerator()

        response = """```json
{
  "act1_setup": "Setup text",
  "act1_inciting_incident": "Incident text",
  "act2_rising_action": "Rising action text",
  "act2_midpoint": "Midpoint text",
  "act2_crisis": "Crisis text",
  "act3_climax": "Climax text",
  "act3_resolution": "Resolution text"
}
```"""

        result = generator._parse_response(response)

        assert isinstance(result, dict)
        assert result["act1_setup"] == "Setup text"
        assert result["act3_climax"] == "Climax text"

    def test_parse_response_invalid_json(self):
        """Test parsing invalid JSON."""
        generator = OutlineGenerator()

        with pytest.raises(OutlineGenerationError, match="Invalid JSON"):
            generator._parse_response("{invalid json")

    def test_parse_response_missing_field(self):
        """Test parsing response with missing required field."""
        generator = OutlineGenerator()

        # Missing act2_midpoint
        response = json.dumps(
            {
                "act1_setup": "Setup",
                "act1_inciting_incident": "Incident",
                "act2_rising_action": "Rising",
                "act2_crisis": "Crisis",
                "act3_climax": "Climax",
                "act3_resolution": "Resolution",
            }
        )

        with pytest.raises(OutlineGenerationError, match="missing required fields"):
            generator._parse_response(response)

    def test_parse_response_empty_field(self):
        """Test parsing response with empty field value."""
        generator = OutlineGenerator()

        response = json.dumps(
            {
                "act1_setup": "Setup text",
                "act1_inciting_incident": "",  # Empty!
                "act2_rising_action": "Rising action",
                "act2_midpoint": "Midpoint",
                "act2_crisis": "Crisis",
                "act3_climax": "Climax",
                "act3_resolution": "Resolution",
            }
        )

        with pytest.raises(OutlineGenerationError, match="must be a non-empty string"):
            generator._parse_response(response)

    def test_parse_response_wrong_type(self):
        """Test parsing response with wrong type for field."""
        generator = OutlineGenerator()

        response = json.dumps(
            {
                "act1_setup": "Setup",
                "act1_inciting_incident": 123,  # Should be string!
                "act2_rising_action": "Rising",
                "act2_midpoint": "Midpoint",
                "act2_crisis": "Crisis",
                "act3_climax": "Climax",
                "act3_resolution": "Resolution",
            }
        )

        with pytest.raises(OutlineGenerationError, match="must be a non-empty string"):
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

        # Mock the AI response
        mock_response = Mock()
        mock_choice = Mock()
        mock_message = Mock()
        mock_message.content = json.dumps(
            {
                "act1_setup": "The hero lives in a normal world.",
                "act1_inciting_incident": "A call to adventure arrives.",
                "act2_rising_action": "The hero faces many trials.",
                "act2_midpoint": "A revelation changes everything.",
                "act2_crisis": "The hero faces their greatest fear.",
                "act3_climax": "The final battle is fought.",
                "act3_resolution": "Peace is restored to the land.",
            }
        )
        mock_choice.message = mock_message
        mock_response.choices = [mock_choice]

        with patch("litellm.completion", return_value=mock_response):
            outline = generator.generate(idea, characters, locations)

        assert isinstance(outline, Outline)
        assert outline.act1_setup == "The hero lives in a normal world."
        assert outline.act1_inciting_incident == "A call to adventure arrives."
        assert outline.act2_rising_action == "The hero faces many trials."
        assert outline.act2_midpoint == "A revelation changes everything."
        assert outline.act2_crisis == "The hero faces their greatest fear."
        assert outline.act3_climax == "The final battle is fought."
        assert outline.act3_resolution == "Peace is restored to the land."

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
        )
        characters: list[Character] = []
        locations: list[Location] = []

        # Mock timeout on first call, success on second
        mock_success = Mock()
        mock_choice = Mock()
        mock_message = Mock()
        mock_message.content = json.dumps(
            {
                "act1_setup": "Setup",
                "act1_inciting_incident": "Incident",
                "act2_rising_action": "Rising",
                "act2_midpoint": "Midpoint",
                "act2_crisis": "Crisis",
                "act3_climax": "Climax",
                "act3_resolution": "Resolution",
            }
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
            {
                "act1_setup": "Setup",
                "act1_inciting_incident": "Incident",
                "act2_rising_action": "Rising",
                "act2_midpoint": "Midpoint",
                "act2_crisis": "Crisis",
                "act3_climax": "Climax",
                "act3_resolution": "Resolution",
            }
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
