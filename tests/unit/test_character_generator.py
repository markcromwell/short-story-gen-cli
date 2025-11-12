"""
Unit tests for CharacterGenerator.

All tests use mocked AI responses to avoid real API calls.
"""

import json
from unittest.mock import Mock, patch

import pytest

from storygen.iterative.generators.character import CharacterGenerationError, CharacterGenerator
from storygen.iterative.models import Character, StoryIdea


class TestCharacterGenerator:
    """Tests for CharacterGenerator class."""

    @pytest.fixture
    def story_idea(self):
        """Sample story idea for testing."""
        return StoryIdea(
            raw_idea="A detective with telepathy",
            one_sentence="A telepathic detective must solve her own murder.",
            expanded="Detective Maya dies and must solve her murder as a ghost...",
            genres=["mystery", "supernatural"],
            tone="Dark, tense",
            themes=["mortality", "justice"],
            setting="Modern-day Seattle",
        )

    @pytest.fixture
    def valid_characters_response(self):
        """Valid AI response with character list."""
        return {
            "characters": [
                {
                    "name": "Maya Reeves",
                    "role": "protagonist",
                    "bio": "A telepathic detective with trust issues.",
                    "goal": "Solve her own murder and find peace",
                    "flaw": "Struggles to trust others",
                    "arc": "Learns to accept help and let go",
                },
                {
                    "name": "Victor Kane",
                    "role": "antagonist",
                    "bio": "A corrupt politician who fears exposure.",
                    "goal": "Cover up his crimes at any cost",
                    "flaw": "Arrogance and overconfidence",
                    "arc": None,
                },
                {
                    "name": "Sam Chen",
                    "role": "ally",
                    "bio": "Maya's former partner, haunted by her death.",
                    "goal": "Find Maya's killer and honor her memory",
                    "flaw": "Guilt over not protecting her",
                    "arc": "Finds redemption through justice",
                },
            ]
        }

    @pytest.fixture
    def mock_litellm_response(self, valid_characters_response):
        """Mock litellm response object."""
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message = Mock()
        mock_response.choices[0].message.content = json.dumps(valid_characters_response)
        return mock_response

    def test_initialization_defaults(self):
        """Test CharacterGenerator initializes with default values."""
        generator = CharacterGenerator()

        assert generator.model == "gpt-4"
        assert generator.max_retries == 3
        assert generator.timeout == 600  # Updated to 10 minutes for slower models

    def test_initialization_custom(self):
        """Test CharacterGenerator with custom parameters."""
        generator = CharacterGenerator(model="ollama/qwen3:30b", max_retries=5, timeout=120)

        assert generator.model == "ollama/qwen3:30b"
        assert generator.max_retries == 5
        assert generator.timeout == 120

    def test_build_prompt(self, story_idea):
        """Test prompt building includes story context."""
        generator = CharacterGenerator()

        system_prompt, user_prompt = generator._build_prompt(story_idea, story_type="short-story")

        # System prompt should request JSON and specify character requirements
        assert "JSON" in system_prompt
        assert "protagonist" in system_prompt
        assert "1-3" in system_prompt  # short-story range

        # User prompt should include story details
        assert story_idea.one_sentence in user_prompt
        assert story_idea.expanded in user_prompt
        assert "mystery" in user_prompt
        assert "supernatural" in user_prompt

    def test_parse_response_valid(self, valid_characters_response):
        """Test parsing valid character response."""
        generator = CharacterGenerator()
        response_text = json.dumps(valid_characters_response)

        characters = generator._parse_response(response_text)

        assert len(characters) == 3
        assert characters[0]["name"] == "Maya Reeves"
        assert characters[0]["role"] == "protagonist"
        assert characters[1]["role"] == "antagonist"

    def test_parse_response_with_markdown(self, valid_characters_response):
        """Test parsing response wrapped in markdown code blocks."""
        generator = CharacterGenerator()
        response_text = f"```json\n{json.dumps(valid_characters_response)}\n```"

        characters = generator._parse_response(response_text)

        assert len(characters) == 3
        assert characters[0]["name"] == "Maya Reeves"

    def test_parse_response_invalid_json(self):
        """Test parsing invalid JSON raises error."""
        generator = CharacterGenerator()

        with pytest.raises(CharacterGenerationError, match="Failed to parse JSON"):
            generator._parse_response("not valid json {]")

    def test_parse_response_missing_characters_field(self):
        """Test response without 'characters' field raises error."""
        generator = CharacterGenerator()
        response_text = json.dumps({"wrong_field": []})

        with pytest.raises(CharacterGenerationError, match="missing 'characters' field"):
            generator._parse_response(response_text)

    def test_parse_response_characters_not_list(self):
        """Test 'characters' field not being a list raises error."""
        generator = CharacterGenerator()
        response_text = json.dumps({"characters": "not a list"})

        with pytest.raises(CharacterGenerationError, match="must be a list"):
            generator._parse_response(response_text)

    def test_parse_response_too_few_characters(self):
        """Test fewer than 1 character raises error."""
        generator = CharacterGenerator()
        response_text = json.dumps(
            {
                "characters": []  # Empty list - should fail validation
            }
        )

        with pytest.raises(
            CharacterGenerationError, match="Must generate 1-8 core characters, got 0"
        ):
            generator._parse_response(response_text)

    def test_parse_response_too_many_characters(self):
        """Test more than 8 characters raises error."""
        generator = CharacterGenerator()
        characters_list = [
            {
                "name": f"Character {i}",
                "role": "protagonist" if i == 0 else "ally",
                "bio": "Bio",
                "goal": "Goal",
                "flaw": "Flaw",
            }
            for i in range(9)
        ]
        response_text = json.dumps({"characters": characters_list})

        with pytest.raises(
            CharacterGenerationError, match="Must generate 1-8 core characters, got"
        ):
            generator._parse_response(response_text)

    def test_parse_response_missing_required_field(self):
        """Test character missing required field raises error."""
        generator = CharacterGenerator()
        # Include 3 characters so we pass the count check
        response_text = json.dumps(
            {
                "characters": [
                    {
                        "name": "Maya",
                        "role": "protagonist",
                        "bio": "Detective",
                        # Missing 'goal' and 'flaw'
                    },
                    {
                        "name": "Victor",
                        "role": "antagonist",
                        "bio": "Villain",
                        "goal": "Cover up",
                        "flaw": "Arrogance",
                    },
                    {
                        "name": "Sam",
                        "role": "ally",
                        "bio": "Helper",
                        "goal": "Help",
                        "flaw": "Guilt",
                    },
                ]
            }
        )

        with pytest.raises(CharacterGenerationError, match="missing required fields.*goal.*flaw"):
            generator._parse_response(response_text)

    def test_parse_response_missing_protagonist(self):
        """Test response without protagonist raises error."""
        generator = CharacterGenerator()
        response_text = json.dumps(
            {
                "characters": [
                    {
                        "name": "Victor",
                        "role": "antagonist",
                        "bio": "Villain",
                        "goal": "Cover up",
                        "flaw": "Arrogance",
                    },
                    {
                        "name": "Sam",
                        "role": "ally",
                        "bio": "Helper",
                        "goal": "Help",
                        "flaw": "Guilt",
                    },
                    {
                        "name": "Anna",
                        "role": "mentor",
                        "bio": "Guide",
                        "goal": "Guide",
                        "flaw": "Old age",
                    },
                ]
            }
        )

        with pytest.raises(CharacterGenerationError, match="Must have.*protagonist"):
            generator._parse_response(response_text)

    def test_parse_response_missing_antagonist(self):
        """Test response without antagonist succeeds (antagonist optional now)."""
        generator = CharacterGenerator()
        response_text = json.dumps(
            {
                "characters": [
                    {
                        "name": "Maya",
                        "role": "protagonist",
                        "bio": "Detective",
                        "goal": "Solve case",
                        "flaw": "Trust issues",
                    },
                    {
                        "name": "Sam",
                        "role": "ally",
                        "bio": "Helper",
                        "goal": "Help",
                        "flaw": "Guilt",
                    },
                    {
                        "name": "Anna",
                        "role": "mentor",
                        "bio": "Guide",
                        "goal": "Guide",
                        "flaw": "Old age",
                    },
                ]
            }
        )

        # Should succeed - antagonist is optional with new story type system
        char_dicts = generator._parse_response(response_text)
        assert len(char_dicts) == 3
        assert char_dicts[0]["role"] == "protagonist"

    @patch("litellm.completion")
    def test_generate_success(self, mock_completion, story_idea, mock_litellm_response):
        """Test successful character generation."""
        mock_completion.return_value = mock_litellm_response

        generator = CharacterGenerator(model="gpt-4")
        characters = generator.generate(story_idea)

        # Should return Character objects
        assert len(characters) == 3
        assert all(isinstance(c, Character) for c in characters)
        assert characters[0].name == "Maya Reeves"
        assert characters[0].role == "protagonist"
        assert characters[1].role == "antagonist"

        # Verify API was called correctly
        mock_completion.assert_called_once()
        call_args = mock_completion.call_args
        assert call_args.kwargs["model"] == "gpt-4"
        assert call_args.kwargs["temperature"] == 0.8
        assert call_args.kwargs["stream"] is False

    @patch("litellm.completion")
    def test_generate_retry_on_timeout(self, mock_completion, story_idea, mock_litellm_response):
        """Test retry logic on timeout."""
        # Fail once, then succeed
        mock_completion.side_effect = [
            Exception("Timeout"),
            mock_litellm_response,
        ]

        generator = CharacterGenerator(model="gpt-4", max_retries=2)

        with patch("time.sleep"):  # Don't actually sleep in tests
            characters = generator.generate(story_idea)

        assert len(characters) == 3
        assert mock_completion.call_count == 2

    @patch("litellm.completion")
    def test_generate_retry_on_malformed_json(
        self, mock_completion, story_idea, valid_characters_response
    ):
        """Test retry on malformed JSON response."""
        # First response is bad JSON, second is good
        bad_response = Mock()
        bad_response.choices = [Mock()]
        bad_response.choices[0].message = Mock()
        bad_response.choices[0].message.content = "not valid json"

        good_response = Mock()
        good_response.choices = [Mock()]
        good_response.choices[0].message = Mock()
        good_response.choices[0].message.content = json.dumps(valid_characters_response)

        mock_completion.side_effect = [bad_response, good_response]

        generator = CharacterGenerator(max_retries=2)

        with patch("time.sleep"):
            characters = generator.generate(story_idea)

        assert len(characters) == 3
        assert mock_completion.call_count == 2

    @patch("litellm.completion")
    def test_generate_fails_after_max_retries(self, mock_completion, story_idea):
        """Test generation fails after exhausting retries."""
        mock_completion.side_effect = Exception("Network error")

        generator = CharacterGenerator(max_retries=2)

        with patch("time.sleep"):
            with pytest.raises(CharacterGenerationError, match="Failed to generate.*2 attempts"):
                generator.generate(story_idea)

        assert mock_completion.call_count == 2

    @patch("litellm.completion")
    def test_generate_exponential_backoff(self, mock_completion, story_idea, mock_litellm_response):
        """Test exponential backoff between retries."""
        mock_completion.side_effect = [
            Exception("Error 1"),
            Exception("Error 2"),
            mock_litellm_response,
        ]

        generator = CharacterGenerator(max_retries=3)

        with patch("time.sleep") as mock_sleep:
            result = generator.generate(story_idea)

        # Should have succeeded after retries
        assert isinstance(result, list)
        assert len(result) == 3

        # Should have slept with exponential backoff: 1s, 2s
        assert mock_sleep.call_count == 2
        assert mock_sleep.call_args_list[0][0][0] == 1  # 2^0 = 1
        assert mock_sleep.call_args_list[1][0][0] == 2  # 2^1 = 2

    @patch("litellm.completion")
    def test_generate_with_different_model(
        self, mock_completion, story_idea, mock_litellm_response
    ):
        """Test generation with Ollama model."""
        mock_completion.return_value = mock_litellm_response

        generator = CharacterGenerator(model="ollama/qwen3:30b")
        characters = generator.generate(story_idea)

        assert len(characters) == 3
        # Verify correct model was used
        call_args = mock_completion.call_args
        assert call_args.kwargs["model"] == "ollama/qwen3:30b"
