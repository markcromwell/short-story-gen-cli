"""Unit tests for editorial workflow core components."""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from pathlib import Path
import tempfile

from storygen.editorial.base import (
    EditorialIssue, EditorialFeedback, RevisionSuggestion,
    StoryContext, BaseEditor, ValidationError
)
from storygen.editorial.core.model_manager import ModelManager, CostTracker
from storygen.editorial.core.job_manager import JobManager, JobStatus, JobMetadata
from storygen.editorial.core.config import ConfigManager


class TestEditorialFeedback:
    """Test editorial feedback data structures."""

    def test_editorial_issue_creation(self):
        """Test creating an editorial issue."""
        issue = EditorialIssue(
            severity="major",
            category="structure",
            description="Plot hole detected",
            suggestion="Add transition scene",
            scene_ids=["scene_3"],
            confidence_score=0.85
        )

        assert issue.severity == "major"
        assert issue.category == "structure"
        assert issue.confidence_score == 0.85

    def test_editorial_feedback_creation(self):
        """Test creating editorial feedback."""
        feedback = EditorialFeedback(
            editor_type="TestEditor",
            overall_assessment="Good story with minor issues",
            issues=[],
            suggested_revisions=[],
            strengths=["Strong characters"]
        )

        assert feedback.editor_type == "TestEditor"
        assert feedback.overall_assessment == "Good story with minor issues"
        assert len(feedback.strengths) == 1


class TestBaseEditor:
    """Test the base editor class."""

    @pytest.fixture
    def mock_model_manager(self):
        """Create a mock model manager."""
        manager = MagicMock()
        manager.call_model = AsyncMock(return_value="Mock analysis response")
        return manager

    @pytest.fixture
    def base_editor(self, mock_model_manager):
        """Create a test base editor."""
        class TestEditor(BaseEditor):
            async def analyze(self, context):
                return self._create_feedback_container("TestEditor")

            def validate_input(self, context):
                return []

        config = {"version": "1.0.0"}
        return TestEditor(mock_model_manager, config)

    def test_create_feedback_container(self, base_editor):
        """Test creating a feedback container."""
        feedback = base_editor._create_feedback_container("TestEditor")

        assert feedback.editor_type == "TestEditor"
        assert feedback.overall_assessment == ""
        assert len(feedback.issues) == 0
        assert "timestamp" in feedback.metadata

    def test_handle_analysis_error(self, base_editor):
        """Test error handling."""
        error = Exception("Test error")
        context = StoryContext()

        feedback = base_editor._handle_analysis_error(error, context)

        assert feedback.editor_type == "TestEditor"  # Uses the concrete class name
        assert "technical issues" in feedback.overall_assessment
        assert len(feedback.issues) == 1
        assert feedback.issues[0].category == "technical"


class TestModelManager:
    """Test the model manager."""

    @pytest.fixture
    def config(self):
        """Test configuration."""
        return {
            "default_model": "ollama/qwen3:30b",
            "models": {
                "ollama": {
                    "base_url": "http://localhost:11434",
                    "timeout": 120
                }
            }
        }

    @pytest.fixture
    def model_manager(self, config):
        """Create a model manager for testing."""
        return ModelManager(config)

    @pytest.mark.asyncio
    async def test_call_model_success(self, model_manager):
        """Test successful model call."""
        with patch.object(model_manager, '_call_ollama', new_callable=AsyncMock) as mock_call:
            mock_call.return_value = "Test response"

            response = await model_manager.call_model("Test prompt")

            assert response == "Test response"
            mock_call.assert_called_once()

    def test_cost_tracking(self, model_manager):
        """Test cost tracking."""
        model_manager.cost_tracker.record_usage("test_model", "prompt", "response", 1.0)

        assert len(model_manager.cost_tracker.usage_log) == 1
        entry = model_manager.cost_tracker.usage_log[0]
        assert entry["model"] == "test_model"
        assert entry["duration_seconds"] == 1.0


class TestJobManager:
    """Test the job manager."""

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for testing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def job_manager(self, temp_dir):
        """Create a job manager for testing."""
        return JobManager(temp_dir / "jobs", max_concurrent_jobs=2)

    @pytest.mark.asyncio
    async def test_start_job(self, job_manager):
        """Test starting a job."""
        context = StoryContext()
        config = {"model": "test_model"}

        job_id = await job_manager.start_job("test_editor", context, config)

        assert job_id is not None
        assert len(job_id) > 0

        # Check job was created
        metadata = await job_manager.get_job_status(job_id)
        assert metadata is not None
        assert metadata.editor_type == "test_editor"
        assert metadata.status == JobStatus.PENDING

    @pytest.mark.asyncio
    async def test_list_jobs(self, job_manager):
        """Test listing jobs."""
        # Start a job
        context = StoryContext()
        config = {"model": "test_model"}
        job_id = await job_manager.start_job("test_editor", context, config)

        # List jobs
        jobs = await job_manager.list_jobs()
        assert len(jobs) >= 1

        # Find our job
        job = next((j for j in jobs if j.job_id == job_id), None)
        assert job is not None
        assert job.editor_type == "test_editor"


class TestConfigManager:
    """Test the configuration manager."""

    @pytest.fixture
    def config_manager(self):
        """Create a config manager for testing."""
        # Use the actual project config directory
        import os
        project_root = Path(__file__).parent.parent.parent
        config_dir = project_root / "config"
        return ConfigManager(config_dir)

    def test_default_config(self, config_manager):
        """Test loading default configuration."""
        config = config_manager.load_main_config()

        assert "models" in config
        assert "editorial" in config
        assert config["models"]["default"] == "ollama/qwen3:30b"

    def test_editorial_config(self, config_manager):
        """Test loading editorial configuration."""
        editorial_config = config_manager.get_editorial_config()

        assert "enabled" in editorial_config
        assert "job_storage_dir" in editorial_config
        assert "editors" in editorial_config


class TestCostTracker:
    """Test the cost tracker."""

    @pytest.fixture
    def cost_tracker(self):
        """Create a cost tracker for testing."""
        return CostTracker()

    def test_cost_calculation(self, cost_tracker):
        """Test cost calculation."""
        # Test free model
        cost = cost_tracker._calculate_cost("ollama/qwen3:30b", 100, 50)
        assert cost == 0.0

        # Test paid model
        cost = cost_tracker._calculate_cost("openai/gpt-4o", 100, 50)
        expected_cost = (100 * 0.000005) + (50 * 0.000015)
        assert cost == expected_cost

    def test_usage_recording(self, cost_tracker):
        """Test recording usage."""
        cost_tracker.record_usage("test_model", "prompt", "response", 2.5)

        assert len(cost_tracker.usage_log) == 1
        entry = cost_tracker.usage_log[0]
        assert entry["model"] == "test_model"
        assert entry["duration_seconds"] == 2.5

    def test_total_cost_calculation(self, cost_tracker):
        """Test calculating total cost."""
        # Add some usage with known token counts
        cost_tracker.record_usage("openai/gpt-4o", "short prompt", "short response", 1.0)
        cost_tracker.record_usage("openai/gpt-4o", "short prompt", "short response", 1.0)

        total_cost = cost_tracker.get_total_cost()
        # Each call should cost something > 0
        assert total_cost > 0
        assert len(cost_tracker.usage_log) == 2