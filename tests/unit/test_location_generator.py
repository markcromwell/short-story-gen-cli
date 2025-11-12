"""Unit tests for LocationGenerator."""

from unittest.mock import MagicMock, patch

import pytest

from storygen.iterative.generators.location import LocationGenerationError, LocationGenerator
from storygen.iterative.models import Location, StoryIdea


class TestLocationGenerator:
    """Test suite for LocationGenerator class."""

    def test_initialization_defaults(self):
        """Test LocationGenerator with default parameters."""
        generator = LocationGenerator()
        assert generator.model == "gpt-4"
        assert generator.max_retries == 3
        assert generator.timeout == 600  # Updated to 10 minutes for slower models

    def test_initialization_custom(self):
        """Test LocationGenerator with custom parameters."""
        generator = LocationGenerator(model="ollama/llama2", max_retries=5, timeout=120)
        assert generator.model == "ollama/llama2"
        assert generator.max_retries == 5
        assert generator.timeout == 120

    def test_build_prompt(self):
        """Test prompt building includes story context."""
        generator = LocationGenerator()
        story_idea = StoryIdea(
            raw_idea="A space station mystery",
            one_sentence="A detective investigates a murder on a remote space station.",
            expanded="In the far reaches of space...",
            genres=["sci-fi", "mystery"],
            tone="tense and claustrophobic",
            themes=["isolation", "paranoia"],
            setting="Test setting",
        )

        system_prompt, user_prompt = generator._build_prompt(story_idea, story_type="short-story")

        # System prompt should have instructions
        assert "2-4" in system_prompt  # short-story range
        assert "locations" in system_prompt.lower()
        assert "JSON" in system_prompt

        # User prompt should include story details
        assert "detective investigates" in user_prompt
        assert "sci-fi" in user_prompt
        assert "tense and claustrophobic" in user_prompt
        assert "isolation" in user_prompt

    def test_parse_response_valid(self):
        """Test parsing a valid AI response."""
        generator = LocationGenerator()
        response = """{
  "locations": [
    {
      "name": "Command Center",
      "description": "A sleek control room with holographic displays.",
      "significance": "Where the murder was discovered.",
      "atmosphere": "Cold and sterile."
    },
    {
      "name": "Living Quarters",
      "description": "Cramped personal spaces.",
      "significance": "Where suspects hide secrets.",
      "atmosphere": "Claustrophobic."
    },
    {
      "name": "Airlock Bay",
      "description": "Industrial loading dock.",
      "significance": "Potential escape route.",
      "atmosphere": "Dangerous and exposed."
    }
  ]
}"""
        locations = generator._parse_response(response)
        assert len(locations) == 3
        assert locations[0]["name"] == "Command Center"
        assert "murder" in locations[0]["significance"]

    def test_parse_response_with_markdown(self):
        """Test parsing response wrapped in markdown code blocks."""
        generator = LocationGenerator()
        response = """```json
{
  "locations": [
    {"name": "Lab", "description": "Scientific lab.", "significance": "Crime scene.", "atmosphere": "Eerie."},
    {"name": "Hallway", "description": "Long corridor.", "significance": "Connect areas.", "atmosphere": "Echoing."},
    {"name": "Reactor", "description": "Power core.", "significance": "Sabotage point.", "atmosphere": "Humming."}
  ]
}
```"""
        locations = generator._parse_response(response)
        assert len(locations) == 3
        assert locations[0]["name"] == "Lab"

    def test_parse_response_invalid_json(self):
        """Test error on invalid JSON."""
        generator = LocationGenerator()
        with pytest.raises(LocationGenerationError, match="Invalid JSON"):
            generator._parse_response("not valid json")

    def test_parse_response_missing_locations_field(self):
        """Test error when 'locations' field is missing."""
        generator = LocationGenerator()
        with pytest.raises(LocationGenerationError, match="missing 'locations'"):
            generator._parse_response('{"items": []}')

    def test_parse_response_locations_not_list(self):
        """Test error when 'locations' is not a list."""
        generator = LocationGenerator()
        with pytest.raises(LocationGenerationError, match="must be a list"):
            generator._parse_response('{"locations": "not a list"}')

    def test_parse_response_too_few_locations(self):
        """Test error when zero locations generated."""
        generator = LocationGenerator()
        response = """{
  "locations": []
}"""
        with pytest.raises(LocationGenerationError, match="Must generate at least 1 location, got"):
            generator._parse_response(response)

    def test_parse_response_too_many_locations(self):
        """Test error when more than 12 locations generated."""
        generator = LocationGenerator()
        locations_list = [
            {
                "name": f"Location {i}",
                "description": f"Description {i}",
                "significance": f"Significance {i}",
                "atmosphere": f"Atmosphere {i}",
            }
            for i in range(13)
        ]
        response = json_dumps({"locations": locations_list})
        with pytest.raises(LocationGenerationError, match="Must generate at most 12 locations"):
            generator._parse_response(response)

    def test_parse_response_missing_required_field(self):
        """Test error when a location is missing required fields."""
        generator = LocationGenerator()
        response = """{
  "locations": [
    {"name": "Lab", "description": "Scientific lab.", "significance": "Crime scene."},
    {"name": "Hallway", "description": "Long corridor.", "significance": "Connect areas.", "atmosphere": "Echoing."},
    {"name": "Reactor", "description": "Power core.", "significance": "Sabotage point.", "atmosphere": "Humming."}
  ]
}"""
        with pytest.raises(LocationGenerationError, match="missing required fields.*atmosphere"):
            generator._parse_response(response)

    @patch("storygen.iterative.generators.base.litellm.completion")
    def test_generate_success(self, mock_completion):
        """Test successful location generation."""
        # Mock AI response
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(
                message=MagicMock(
                    content="""{
  "locations": [
    {"name": "Lab", "description": "High-tech laboratory.", "significance": "Murder location.", "atmosphere": "Cold."},
    {"name": "Quarters", "description": "Living spaces.", "significance": "Suspect hideouts.", "atmosphere": "Tense."},
    {"name": "Bridge", "description": "Command center.", "significance": "Control point.", "atmosphere": "Busy."}
  ]
}"""
                )
            )
        ]
        mock_completion.return_value = mock_response

        generator = LocationGenerator(model="test-model")
        story_idea = StoryIdea(
            raw_idea="test",
            one_sentence="test story",
            expanded="test expanded",
            genres=["sci-fi"],
            tone="tense",
            themes=["isolation"],
            setting="Test setting",
        )

        locations = generator.generate(story_idea)

        assert len(locations) == 3
        assert all(isinstance(loc, Location) for loc in locations)
        assert locations[0].name == "Lab"
        assert "Murder" in locations[0].significance

    @patch("storygen.iterative.generators.base.litellm.completion")
    @patch("storygen.iterative.generators.base.time.sleep")
    def test_generate_retry_on_timeout(self, mock_sleep, mock_completion):
        """Test retry on timeout error."""
        # First call times out, second succeeds
        mock_completion.side_effect = [
            Exception("Timeout"),
            MagicMock(
                choices=[
                    MagicMock(
                        message=MagicMock(
                            content='{"locations": [{"name": "Lab", "description": "Desc", "significance": "Sig", "atmosphere": "Atm"}, {"name": "Hall", "description": "Desc2", "significance": "Sig2", "atmosphere": "Atm2"}, {"name": "Bay", "description": "Desc3", "significance": "Sig3", "atmosphere": "Atm3"}]}'
                        )
                    )
                ]
            ),
        ]

        generator = LocationGenerator(model="test-model", max_retries=2)
        story_idea = StoryIdea(
            raw_idea="test",
            one_sentence="test",
            expanded="test",
            genres=["sci-fi"],
            tone="tense",
            themes=["isolation"],
            setting="Test setting",
        )

        locations = generator.generate(story_idea)
        assert len(locations) == 3
        assert mock_sleep.called

    @patch("storygen.iterative.generators.base.litellm.completion")
    @patch("storygen.iterative.generators.base.time.sleep")
    def test_generate_retry_on_malformed_json(self, mock_sleep, mock_completion):
        """Test retry on malformed JSON."""
        # First call returns bad JSON, second succeeds
        mock_completion.side_effect = [
            MagicMock(choices=[MagicMock(message=MagicMock(content="not json"))]),
            MagicMock(
                choices=[
                    MagicMock(
                        message=MagicMock(
                            content='{"locations": [{"name": "Lab", "description": "Desc", "significance": "Sig", "atmosphere": "Atm"}, {"name": "Hall", "description": "Desc2", "significance": "Sig2", "atmosphere": "Atm2"}, {"name": "Bay", "description": "Desc3", "significance": "Sig3", "atmosphere": "Atm3"}]}'
                        )
                    )
                ]
            ),
        ]

        generator = LocationGenerator(model="test-model", max_retries=2)
        story_idea = StoryIdea(
            raw_idea="test",
            one_sentence="test",
            expanded="test",
            genres=["sci-fi"],
            tone="tense",
            themes=["isolation"],
            setting="Test setting",
        )

        locations = generator.generate(story_idea)
        assert len(locations) == 3

    @patch("storygen.iterative.generators.base.litellm.completion")
    def test_generate_fails_after_max_retries(self, mock_completion):
        """Test failure after exhausting retries."""
        mock_completion.side_effect = Exception("Persistent error")

        generator = LocationGenerator(model="test-model", max_retries=2)
        story_idea = StoryIdea(
            raw_idea="test",
            one_sentence="test",
            expanded="test",
            genres=["sci-fi"],
            tone="tense",
            themes=["isolation"],
            setting="Test setting",
        )

        with pytest.raises(LocationGenerationError, match="Failed to generate"):
            generator.generate(story_idea)

    @patch("storygen.iterative.generators.base.litellm.completion")
    @patch("storygen.iterative.generators.base.time.sleep")
    def test_generate_exponential_backoff(self, mock_sleep, mock_completion):
        """Test exponential backoff between retries."""
        mock_completion.side_effect = [
            Exception("Error 1"),
            Exception("Error 2"),
            MagicMock(
                choices=[
                    MagicMock(
                        message=MagicMock(
                            content='{"locations": [{"name": "Lab", "description": "Desc", "significance": "Sig", "atmosphere": "Atm"}, {"name": "Hall", "description": "Desc2", "significance": "Sig2", "atmosphere": "Atm2"}, {"name": "Bay", "description": "Desc3", "significance": "Sig3", "atmosphere": "Atm3"}]}'
                        )
                    )
                ]
            ),
        ]

        generator = LocationGenerator(model="test-model", max_retries=3)
        story_idea = StoryIdea(
            raw_idea="test",
            one_sentence="test",
            expanded="test",
            genres=["sci-fi"],
            tone="tense",
            themes=["isolation"],
            setting="Test setting",
        )

        generator.generate(story_idea)

        # Check exponential backoff: 1s, 2s
        assert mock_sleep.call_count == 2
        assert mock_sleep.call_args_list[0][0][0] == 1  # 2^0
        assert mock_sleep.call_args_list[1][0][0] == 2  # 2^1

    @patch("storygen.iterative.generators.base.litellm.completion")
    def test_generate_with_different_model(self, mock_completion):
        """Test generation with custom model."""
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(
                message=MagicMock(
                    content='{"locations": [{"name": "Lab", "description": "Desc", "significance": "Sig", "atmosphere": "Atm"}, {"name": "Hall", "description": "Desc2", "significance": "Sig2", "atmosphere": "Atm2"}, {"name": "Bay", "description": "Desc3", "significance": "Sig3", "atmosphere": "Atm3"}]}'
                )
            )
        ]
        mock_completion.return_value = mock_response

        generator = LocationGenerator(model="ollama/qwen3:30b")
        story_idea = StoryIdea(
            raw_idea="test",
            one_sentence="test",
            expanded="test",
            genres=["sci-fi"],
            tone="tense",
            themes=["isolation"],
            setting="Test setting",
        )

        generator.generate(story_idea)

        # Verify the custom model was used
        assert mock_completion.call_args[1]["model"] == "ollama/qwen3:30b"


def json_dumps(obj):
    """Helper to serialize JSON for tests."""
    import json

    return json.dumps(obj)
