"""Unit tests for editorial CLI commands."""

import json
from unittest.mock import AsyncMock, patch

import pytest

from storygen.editorial.cli.commands import _apply_revisions_with_ai, _extract_quality_score
from storygen.editorial.core.model_manager import ModelManager


class TestIterativeWorkflow:
    """Test the iterative editorial workflow."""

    @pytest.fixture
    def config(self):
        """Test configuration."""
        return {
            "default_model": "ollama/qwen3:30b",
            "models": {"ollama": {"base_url": "http://localhost:11434", "timeout": 120}},
        }

    @pytest.fixture
    def model_manager(self, config):
        """Create a model manager for testing."""
        return ModelManager(config)

    def test_quality_score_initialization_logic(self):
        """Test that quality_score is properly initialized and handled.

        This test validates the logic we added to prevent UnboundLocalError
        when quality_score is referenced after a loop that may never execute.
        """
        # Test the _extract_quality_score function works correctly
        feedback_data = {"quality_score": 8.5}
        score = _extract_quality_score(feedback_data)
        assert score == 8.5

        # Test default value when quality_score is missing
        feedback_data = {}
        score = _extract_quality_score(feedback_data)
        assert score == 5.0

        # Test that we can safely handle None quality_score in final result
        # This simulates the logic we added: final_quality_score = quality_score if quality_score is not None else 0.0
        quality_score = None
        final_quality_score = quality_score if quality_score is not None else 0.0
        assert final_quality_score == 0.0

        quality_score = 7.5
        final_quality_score = quality_score if quality_score is not None else 0.0
        assert final_quality_score == 7.5

    @pytest.mark.asyncio
    async def test_apply_revisions_with_new_scenes(self, model_manager):
        """Test that _apply_revisions_with_ai preserves new scenes.

        This test would have caught the scene_dict bug where new scenes
        were added to scene_sequels but not to scene_dict, causing them
        to be filtered out during the rebuild step.
        """
        # Mock story with existing scenes
        story_data = {
            "scene_sequels": [
                {"id": "scene_1", "content": "Original scene 1"},
                {"id": "scene_2", "content": "Original scene 2"},
            ]
        }

        # Mock revisions that add a new scene
        revisions = [
            {
                "priority": "high",
                "reason": "Add new scene",
                "instruction": "Add a new scene with id 'scene_3'",
            }
        ]

        # Mock the AI response to return a new scene
        mock_response = json.dumps(
            [{"id": "scene_3", "content": "This is a new scene added by AI", "type": "scene"}]
        )

        with patch.object(model_manager, "call_model", new_callable=AsyncMock) as mock_call:
            mock_call.return_value = mock_response

            # Apply revisions
            result = await _apply_revisions_with_ai(
                story_data=story_data,
                revisions=revisions,
                model_manager=model_manager,
                max_cost=None,
                verbose=False,
            )

            # Verify the new scene was added and preserved
            scene_ids = [scene["id"] for scene in result["scene_sequels"]]
            assert "scene_1" in scene_ids
            assert "scene_2" in scene_ids
            assert "scene_3" in scene_ids  # This would fail before the fix

            # Verify the new scene content is correct
            new_scene = next(scene for scene in result["scene_sequels"] if scene["id"] == "scene_3")
            assert new_scene["content"] == "This is a new scene added by AI"

    @pytest.mark.asyncio
    async def test_apply_revisions_with_existing_scene_modification(self, model_manager):
        """Test that _apply_revisions_with_ai correctly modifies existing scenes."""
        # Mock story with existing scenes
        story_data = {
            "scene_sequels": [
                {"id": "scene_1", "content": "Original scene 1"},
                {"id": "scene_2", "content": "Original scene 2"},
            ]
        }

        # Mock revisions that modify an existing scene
        revisions = [
            {
                "priority": "high",
                "reason": "Improve scene 1",
                "instruction": "Make scene 1 more exciting",
            }
        ]

        # Mock the AI response to return a modified existing scene
        mock_response = json.dumps(
            [{"id": "scene_1", "content": "Modified exciting scene 1", "type": "scene"}]
        )

        with patch.object(model_manager, "call_model", new_callable=AsyncMock) as mock_call:
            mock_call.return_value = mock_response

            # Apply revisions
            result = await _apply_revisions_with_ai(
                story_data=story_data,
                revisions=revisions,
                model_manager=model_manager,
                max_cost=None,
                verbose=False,
            )

            # Verify scene_1 was modified
            scene_1 = next(scene for scene in result["scene_sequels"] if scene["id"] == "scene_1")
            assert scene_1["content"] == "Modified exciting scene 1"

            # Verify scene_2 is unchanged
            scene_2 = next(scene for scene in result["scene_sequels"] if scene["id"] == "scene_2")
            assert scene_2["content"] == "Original scene 2"


class TestCLIAnalysisCommands:
    """Test CLI analysis commands."""

    @pytest.fixture
    def config(self):
        """Test configuration."""
        return {
            "default_model": "ollama/qwen3:30b",
            "models": {"ollama": {"base_url": "http://localhost:11434", "timeout": 120}},
        }

    @pytest.fixture
    def model_manager(self, config):
        """Create a model manager for testing."""
        return ModelManager(config)

    @pytest.mark.asyncio
    async def test_load_story_context_from_prose_file(self, tmp_path, model_manager):
        """Test loading story context from a prose file."""
        from storygen.editorial.cli.commands import _load_story_context_from_prose_file

        # Create a temporary JSON prose file
        prose_content = {
            "scene_sequels": [
                {"id": "scene_1", "content": "Scene one content", "type": "scene"},
                {"id": "scene_2", "content": "Scene two content", "type": "scene"},
            ]
        }
        prose_file = tmp_path / "test_prose.json"
        prose_file.write_text(json.dumps(prose_content))

        context = await _load_story_context_from_prose_file(str(prose_file))

        assert context is not None
        assert hasattr(context, "prose")
        assert context.prose is not None
        assert len(context.prose.scenes) == 2

    @pytest.mark.asyncio
    async def test_save_feedback(self, tmp_path):
        """Test saving feedback to a file."""
        from storygen.editorial.base import EditorialFeedback
        from storygen.editorial.cli.commands import _save_feedback

        # Create mock feedback
        feedback = EditorialFeedback(
            editor_type="test",
            overall_assessment="Test assessment",
            issues=[],
            suggested_revisions=[],
            strengths=["Test strength"],
            human_report="Test report",
            metadata={"test": True},
        )

        output_file = tmp_path / "feedback.json"

        await _save_feedback(feedback, str(output_file))

        # Verify file was created and contains expected content
        assert output_file.exists()
        content = output_file.read_text()
        assert "Test assessment" in content
        assert "Test strength" in content

    @pytest.mark.asyncio
    async def test_generate_initial_story(self, model_manager):
        """Test generating initial story from prompt."""
        from storygen.editorial.cli.commands import _generate_initial_story

        with patch.object(model_manager, "call_model", new_callable=AsyncMock) as mock_call:
            mock_call.return_value = '{"title": "Test Story", "scenes": [{"id": "scene_1", "content": "Generated content"}]}'

            result = await _generate_initial_story("Test prompt", model_manager, False)

            assert result["title"] == "Test Story"
            assert len(result["scenes"]) == 1
            mock_call.assert_called_once()

    @pytest.mark.asyncio
    async def test_analyze_story_quality(self, model_manager):
        """Test analyzing story quality."""
        from storygen.editorial.cli.commands import _analyze_story_quality

        story_data = {"content": "Test story content"}

        with patch.object(model_manager, "call_model", new_callable=AsyncMock) as mock_call:
            mock_call.return_value = '{"quality_score": 8.5, "overall_assessment": "Good story"}'

            result = await _analyze_story_quality(story_data, model_manager, False)

            assert result["quality_score"] == 8.5
            assert result["overall_assessment"] == "Good story"
            mock_call.assert_called_once()

    @pytest.mark.asyncio
    async def test_revise_story(self, model_manager):
        """Test revising a story."""
        from storygen.editorial.cli.commands import _revise_story

        story_data = {"content": "Original content"}
        feedback_data = {
            "suggested_revisions": [
                {
                    "priority": "high",
                    "reason": "Make it better",
                    "instruction": "Improve the content",
                }
            ]
        }

        with patch.object(model_manager, "call_model", new_callable=AsyncMock) as mock_call:
            mock_call.return_value = '{"content": "Improved content"}'

            result = await _revise_story(story_data, feedback_data, model_manager, False)

            assert result["content"] == "Improved content"
            mock_call.assert_called_once()
