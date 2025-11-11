"""
Unit tests for IdeaGenerator.

Tests cover:
- Prompt generation
- Successful idea generation with mocked AI
- Retry logic on failures
- Error handling for malformed responses
- JSON parsing edge cases
"""

import json
from unittest.mock import Mock, patch

import pytest

from storygen.iterative.generators.idea import IdeaGenerationError, IdeaGenerator
from storygen.iterative.models import StoryIdea


@pytest.fixture
def valid_ai_response():
    """A valid AI response in expected JSON format."""
    return {
        "raw_idea": "A detective solves her own murder",
        "one_sentence": "A telepath detective must solve her own murder before her consciousness fades.",
        "expanded": "Detective Maya Reeves wakes up as a ghost, discovering she was murdered during her latest investigation. With only 48 hours before her consciousness dissipates, she must use her telepathic abilities to communicate with the living and piece together the clues to her own death.\n\nAs Maya investigates from beyond the grave, she uncovers a conspiracy that goes deeper than she imagined. Her partner, Detective Chen, becomes her unwitting ally as she plants thoughts and guides him toward the truth. But the killer knows she's still watching, and they're determined to ensure Maya's final death is permanent.\n\nWith time running out, Maya must confront the hardest truth of all: someone she trusted betrayed her. The race against her own fading existence becomes a battle not just for justice, but for closure and redemption.",
        "genres": ["mystery", "supernatural", "thriller"],
        "tone": "Dark, tense, emotional",
        "themes": ["mortality", "trust", "justice", "redemption"],
    }


@pytest.fixture
def mock_litellm_response(valid_ai_response):
    """Mock litellm.completion response object."""
    mock_response = Mock()
    mock_response.choices = [Mock()]
    mock_response.choices[0].message = Mock()
    mock_response.choices[0].message.content = json.dumps(valid_ai_response)
    return mock_response


class TestIdeaGenerator:
    """Tests for IdeaGenerator class."""

    def test_initialization_defaults(self):
        """Test IdeaGenerator initializes with default values."""
        generator = IdeaGenerator()

        assert generator.model == "gpt-4"
        assert generator.max_retries == 3
        assert generator.timeout == 60

    def test_initialization_custom(self):
        """Test IdeaGenerator with custom parameters."""
        generator = IdeaGenerator(model="ollama/qwen3:30b", max_retries=5, timeout=120)

        assert generator.model == "ollama/qwen3:30b"
        assert generator.max_retries == 5
        assert generator.timeout == 120

    def test_build_prompt(self):
        """Test prompt building includes required instructions."""
        generator = IdeaGenerator()
        prompt = generator._build_prompt("A detective solves crimes")

        # Check for key requirements
        assert "JSON" in prompt
        assert "one_sentence" in prompt
        assert "expanded" in prompt
        assert "genres" in prompt
        assert "themes" in prompt
        assert "2-3" in prompt  # Paragraph requirement

    def test_parse_response_valid(self, valid_ai_response):
        """Test parsing a valid JSON response."""
        generator = IdeaGenerator()
        response_text = json.dumps(valid_ai_response)

        data = generator._parse_response(response_text)

        assert data["one_sentence"] == valid_ai_response["one_sentence"]
        assert data["genres"] == ["mystery", "supernatural", "thriller"]
        assert len(data["themes"]) == 4

    def test_parse_response_with_markdown(self, valid_ai_response):
        """Test parsing JSON wrapped in markdown code blocks."""
        generator = IdeaGenerator()

        # Wrapped in ```json
        response_text = f"```json\n{json.dumps(valid_ai_response)}\n```"
        data = generator._parse_response(response_text)
        assert data["one_sentence"] == valid_ai_response["one_sentence"]

        # Wrapped in ```
        response_text = f"```\n{json.dumps(valid_ai_response)}\n```"
        data = generator._parse_response(response_text)
        assert data["one_sentence"] == valid_ai_response["one_sentence"]

    def test_parse_response_invalid_json(self):
        """Test parsing invalid JSON raises error."""
        generator = IdeaGenerator()

        with pytest.raises(IdeaGenerationError, match="Failed to parse JSON"):
            generator._parse_response("This is not JSON")

    def test_parse_response_missing_fields(self, valid_ai_response):
        """Test parsing JSON with missing required fields."""
        generator = IdeaGenerator()

        # Remove required field
        invalid_data = valid_ai_response.copy()
        del invalid_data["one_sentence"]

        with pytest.raises(IdeaGenerationError, match="Missing required fields"):
            generator._parse_response(json.dumps(invalid_data))

    def test_parse_response_invalid_genres_type(self, valid_ai_response):
        """Test parsing with genres as string instead of list."""
        generator = IdeaGenerator()

        invalid_data = valid_ai_response.copy()
        invalid_data["genres"] = "mystery"  # Should be list

        with pytest.raises(IdeaGenerationError, match="genres must be a non-empty list"):
            generator._parse_response(json.dumps(invalid_data))

    def test_parse_response_empty_genres(self, valid_ai_response):
        """Test parsing with empty genres list."""
        generator = IdeaGenerator()

        invalid_data = valid_ai_response.copy()
        invalid_data["genres"] = []

        with pytest.raises(IdeaGenerationError, match="genres must be a non-empty list"):
            generator._parse_response(json.dumps(invalid_data))

    @patch("litellm.completion")
    def test_generate_success(self, mock_completion, mock_litellm_response):
        """Test successful idea generation."""
        mock_completion.return_value = mock_litellm_response

        generator = IdeaGenerator(model="gpt-4")
        idea = generator.generate("A detective solves her own murder")

        # Verify litellm called correctly
        mock_completion.assert_called_once()
        call_kwargs = mock_completion.call_args[1]
        assert call_kwargs["model"] == "gpt-4"
        assert call_kwargs["temperature"] == 0.8
        assert len(call_kwargs["messages"]) == 2

        # Verify returned StoryIdea
        assert isinstance(idea, StoryIdea)
        assert "telepath detective" in idea.one_sentence.lower()
        assert "mystery" in idea.genres
        assert len(idea.themes) == 4

    @patch("litellm.completion")
    def test_generate_retry_on_timeout(self, mock_completion, mock_litellm_response):
        """Test retry logic when AI times out."""
        # First call fails, second succeeds
        mock_completion.side_effect = [Exception("Timeout"), mock_litellm_response]

        generator = IdeaGenerator(model="gpt-4", max_retries=3)

        with patch("time.sleep"):  # Don't actually sleep in tests
            idea = generator.generate("A detective solves crimes")

        # Should have retried once
        assert mock_completion.call_count == 2
        assert isinstance(idea, StoryIdea)

    @patch("litellm.completion")
    def test_generate_retry_on_malformed_json(self, mock_completion, mock_litellm_response):
        """Test retry when AI returns malformed JSON."""
        # First response is bad JSON, second is good
        bad_response = Mock()
        bad_response.choices = [Mock()]
        bad_response.choices[0].message = Mock()
        bad_response.choices[0].message.content = "Not JSON"

        mock_completion.side_effect = [bad_response, mock_litellm_response]

        generator = IdeaGenerator(model="gpt-4", max_retries=3)

        with patch("time.sleep"):
            idea = generator.generate("A detective solves crimes")

        # Should have retried
        assert mock_completion.call_count == 2
        assert isinstance(idea, StoryIdea)

    @patch("litellm.completion")
    def test_generate_fails_after_max_retries(self, mock_completion):
        """Test generation fails after exhausting retries."""
        mock_completion.side_effect = Exception("Network error")

        generator = IdeaGenerator(model="gpt-4", max_retries=3)

        with patch("time.sleep"):
            with pytest.raises(
                IdeaGenerationError, match="Failed to generate idea after 3 attempts"
            ):
                generator.generate("A detective solves crimes")

        # Should have tried 3 times
        assert mock_completion.call_count == 3

    @patch("litellm.completion")
    def test_generate_exponential_backoff(self, mock_completion, mock_litellm_response):
        """Test exponential backoff between retries."""
        # Fail twice, then succeed
        mock_completion.side_effect = [
            Exception("Timeout"),
            Exception("Timeout"),
            mock_litellm_response,
        ]

        generator = IdeaGenerator(model="gpt-4", max_retries=3)

        with patch("time.sleep") as mock_sleep:
            result = generator.generate("A detective solves crimes")

        # Should have succeeded after retries
        assert isinstance(result, StoryIdea)

        # Should have slept with exponential backoff: 1s, 2s
        assert mock_sleep.call_count == 2
        assert mock_sleep.call_args_list[0][0][0] == 1  # 2^0 = 1
        assert mock_sleep.call_args_list[1][0][0] == 2  # 2^1 = 2

    @patch("litellm.completion")
    def test_generate_normalizes_genres(self, mock_completion, valid_ai_response):
        """Test that genres are normalized (lowercase, deduplicated)."""
        # AI returns genres with mixed case and duplicates
        response_data = valid_ai_response.copy()
        response_data["genres"] = ["Mystery", "MYSTERY", "Thriller", "mystery"]

        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message = Mock()
        mock_response.choices[0].message.content = json.dumps(response_data)

        mock_completion.return_value = mock_response

        generator = IdeaGenerator()
        idea = generator.generate("A detective story")

        # StoryIdea should normalize and deduplicate
        assert idea.genres == ["mystery", "thriller"]
        assert len(idea.genres) == 2

    @patch("litellm.completion")
    def test_generate_with_different_model(self, mock_completion, mock_litellm_response):
        """Test generation with different model."""
        mock_completion.return_value = mock_litellm_response

        generator = IdeaGenerator(model="ollama/qwen3:30b")
        idea = generator.generate("A space adventure")

        # Verify correct model used
        call_kwargs = mock_completion.call_args[1]
        assert call_kwargs["model"] == "ollama/qwen3:30b"
        assert isinstance(idea, StoryIdea)
