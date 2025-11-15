"""
Integration tests for editorial workflow that use real API calls.

These tests verify that the editorial system works end-to-end with actual AI models.
They should only be run when explicitly requested due to API costs and requirements.

Run with:
  pytest tests/editorial/test_integration.py --integration -v

Requirements:
- Valid API keys for configured models (XAI_API_KEY, OPENAI_API_KEY, etc.)
- Network access to AI providers
- Acceptance of API costs (~$0.01-0.05 per test)
"""

import os

import pytest

from storygen.editorial.base import StoryContext
from storygen.editorial.core.model_manager import ModelManager
from storygen.editorial.editors.comprehensive import ComprehensiveEditor

# Mark all tests in this file as integration tests
pytestmark = pytest.mark.integration


class TestModelManagerIntegration:
    """Integration tests for ModelManager with real API calls."""

    @pytest.fixture
    def config(self):
        """Test configuration with real models."""
        return {
            "default_model": "xai/grok-4-fast-reasoning",  # Free tier
            "models": {
                "xai": {"timeout": 120},
                "openai": {"timeout": 120},
                "ollama": {"base_url": "http://localhost:11434", "timeout": 120},
            },
        }

    @pytest.fixture
    def model_manager(self, config):
        """Create a model manager for integration testing."""
        return ModelManager(config)

    @pytest.mark.asyncio
    async def test_call_model_real_xai(self, model_manager):
        """Test real XAI API call (would have caught mock implementation)."""
        # This test would fail with the old mock implementation
        response = await model_manager.call_model(
            "Say 'Hello from real XAI API' in exactly those words.",
            model="xai/grok-4-fast-reasoning",
        )

        # Verify it's not a mock response
        assert "Mock response" not in response
        assert "Hello from real XAI API" in response
        assert len(response.strip()) > 0

    @pytest.mark.asyncio
    @pytest.mark.skipif(not os.getenv("OPENAI_API_KEY"), reason="OPENAI_API_KEY not set")
    async def test_call_model_real_openai(self, model_manager):
        """Test real OpenAI API call (would have caught mock implementation)."""
        response = await model_manager.call_model(
            "Say 'Hello from real OpenAI API' in exactly those words.", model="openai/gpt-4o-mini"
        )

        # Verify it's not a mock response
        assert "Mock response" not in response
        assert "Hello from real OpenAI API" in response
        assert len(response.strip()) > 0

    @pytest.mark.asyncio
    async def test_call_model_sync_wrapper(self, model_manager):
        """Test the synchronous wrapper for model calls."""
        response = model_manager.call_model_sync(
            "Say 'Sync response' in exactly those words.", model="xai/grok-4-fast-reasoning"
        )

        assert "Mock response" not in response
        assert "Sync response" in response
        assert len(response.strip()) > 0

    def test_cost_tracking_real_calls(self, model_manager):
        """Test that cost tracking works with real calls."""
        initial_cost = model_manager.cost_tracker.get_total_cost()

        # Make a sync call to ensure cost is tracked
        model_manager.call_model_sync(
            "Say 'Cost tracking test' in exactly those words.", model="xai/grok-4-fast-reasoning"
        )

        final_cost = model_manager.cost_tracker.get_total_cost()

        # XAI calls should be free (cost = 0)
        assert final_cost == initial_cost
        assert len(model_manager.cost_tracker.usage_log) >= 1


class TestComprehensiveEditorIntegration:
    """Integration tests for ComprehensiveEditor with real API calls."""

    @pytest.fixture
    def config(self):
        """Test configuration."""
        return {
            "default_model": "xai/grok-4-fast-reasoning",
            "models": {"xai": {"timeout": 120}},
        }

    @pytest.fixture
    def model_manager(self, config):
        """Create a model manager for integration testing."""
        return ModelManager(config)

    @pytest.fixture
    def comprehensive_editor(self, model_manager, config):
        """Create a comprehensive editor for integration testing."""
        return ComprehensiveEditor(model_manager, config)

    @pytest.mark.asyncio
    async def test_full_editorial_analysis_real_api(self, comprehensive_editor):
        """Test complete editorial analysis with real API calls.

        This integration test would have caught both:
        1. The UnboundLocalError in _combine_feedbacks
        2. Mock implementations in ModelManager
        """

        # Create realistic test story data
        class MockProse:
            def __init__(self):
                self.title = "The Detective's Dilemma"
                self.genre = "Mystery"
                self.summary = (
                    "A detective investigates a murder but discovers the victim is still alive."
                )
                self.characters = [
                    "Detective Maya Reeves",
                    "Victim Alex Chen",
                    "Suspect Jordan Blake",
                ]
                self.scenes = [
                    {
                        "number": 1,
                        "title": "The Crime Scene",
                        "pov_character": "Detective Maya Reeves",
                        "location": "Abandoned Warehouse",
                        "time_hours": 0.0,
                        "content": "Detective Maya Reeves arrived at the warehouse, her flashlight cutting through the darkness. The body lay still, a single gunshot wound to the chest. But something felt wrong about this case.",
                    },
                    {
                        "number": 2,
                        "title": "The Interrogation",
                        "pov_character": "Detective Maya Reeves",
                        "location": "Police Precinct",
                        "time_hours": 2.0,
                        "content": "Maya questioned Jordan Blake in the interrogation room. 'I didn't do it,' he insisted. But his eyes told a different story. Maya activated her telepathy, diving into his mind.",
                    },
                    {
                        "number": 3,
                        "title": "The Revelation",
                        "pov_character": "Detective Maya Reeves",
                        "location": "Hospital Room",
                        "time_hours": 4.0,
                        "content": "Maya burst into the hospital room where Alex Chen waited. 'You're alive!' she exclaimed. The 'victim' smiled weakly. 'It was the only way to catch the real killer.'",
                    },
                ]

            def to_text(self):
                return "\n\n".join([str(scene["content"]) for scene in self.scenes])

        context = StoryContext(prose=MockProse())

        # This would have failed with UnboundLocalError before the fix
        # And would have returned mock responses before the ModelManager fix
        feedback = await comprehensive_editor.analyze(context)

        # Verify real analysis was performed (not mock responses)
        assert feedback.editor_type == "comprehensive"
        assert "Mock response" not in feedback.overall_assessment
        assert "Mock response" not in feedback.human_report

        # Verify comprehensive analysis structure
        assert isinstance(feedback.issues, list)
        assert isinstance(feedback.suggested_revisions, list)
        assert isinstance(feedback.strengths, list)
        assert len(feedback.human_report) > 50  # Real analysis should be substantial

        # Verify cost was tracked
        total_cost = comprehensive_editor.model_manager.cost_tracker.get_total_cost()
        assert total_cost >= 0  # Should be 0 for XAI, but properly tracked
