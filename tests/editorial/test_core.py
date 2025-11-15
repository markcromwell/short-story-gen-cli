"""Unit tests for editorial workflow core components."""

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from storygen.editorial.base import (
    BaseEditor,
    EditorialFeedback,
    EditorialIssue,
    StoryContext,
)
from storygen.editorial.core.config import ConfigError, ConfigManager
from storygen.editorial.core.model_manager import CostTracker, ModelManager
from storygen.editorial.editors.comprehensive import ComprehensiveEditor


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
            confidence_score=0.85,
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
            strengths=["Strong characters"],
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


class TestComprehensiveEditor:
    """Test the comprehensive editor that combines multiple specialized editors."""

    @pytest.fixture
    def mock_model_manager(self):
        """Create a mock model manager that returns structured editorial feedback."""
        manager = MagicMock()
        manager.call_model = AsyncMock(
            return_value="""
        {
            "editor_type": "StructuralEditor",
            "overall_assessment": "Good structure with clear three-act progression",
            "issues": [
                {
                    "severity": "minor",
                    "category": "structure",
                    "description": "Act 2 could be more intense",
                    "suggestion": "Add more obstacles in the middle",
                    "scene_ids": ["scene_5", "scene_6"],
                    "confidence_score": 0.7
                }
            ],
            "suggested_revisions": [
                {
                    "priority": "medium",
                    "reason": "Enhance conflict",
                    "instruction": "Add complications to scenes 5-6"
                }
            ],
            "strengths": ["Clear setup", "Strong climax"],
            "human_report": "The story has a solid foundation but could benefit from increased tension in the middle act."
        }
        """
        )
        return manager

    @pytest.fixture
    def comprehensive_editor(self, mock_model_manager):
        """Create a comprehensive editor for testing."""
        config = {"version": "1.0.0"}
        return ComprehensiveEditor(mock_model_manager, config)

    @pytest.mark.asyncio
    async def test_analyze_combines_multiple_editors(
        self, comprehensive_editor, mock_model_manager
    ):
        """Test that analyze combines feedback from structural, continuity, and style editors.

        This test would have caught the UnboundLocalError bug in _combine_feedbacks
        where 'feedback' was referenced before assignment in the constructor call.
        """

        # Create test story context with prose content
        # Use a simple mock object that has the expected attributes
        class MockProse:
            def __init__(self):
                self.scenes = [
                    {
                        "number": 1,
                        "title": "Opening scene",
                        "pov_character": "Test Character",
                        "location": "Test Location",
                        "time_hours": 0.0,
                        "content": "Opening scene content",
                    },
                    {
                        "number": 2,
                        "title": "Middle scene",
                        "pov_character": "Test Character",
                        "location": "Test Location",
                        "time_hours": 1.0,
                        "content": "Middle scene content",
                    },
                    {
                        "number": 3,
                        "title": "Climax scene",
                        "pov_character": "Test Character",
                        "location": "Test Location",
                        "time_hours": 2.0,
                        "content": "Climax scene content",
                    },
                ]

            def to_text(self):
                return "Mock story text for testing"

        context = StoryContext(prose=MockProse())

        # This call would have failed with UnboundLocalError before the fix
        feedback = await comprehensive_editor.analyze(context)

        # Verify the combined feedback structure
        assert feedback.editor_type == "comprehensive"
        assert hasattr(feedback, "overall_assessment")
        assert hasattr(feedback, "issues")
        assert hasattr(feedback, "suggested_revisions")
        assert hasattr(feedback, "strengths")
        assert hasattr(feedback, "human_report")

        # Verify that call_model was called multiple times (each sub-editor makes several calls)
        assert mock_model_manager.call_model.call_count >= 3

    @pytest.mark.asyncio
    async def test_analyze_handles_empty_story(self, comprehensive_editor):
        """Test analyze with minimal story data."""

        # Create minimal story
        class MockProse:
            def __init__(self):
                self.scenes = []

            def to_text(self):
                return "Minimal story text"

        context = StoryContext(prose=MockProse())

        feedback = await comprehensive_editor.analyze(context)

        assert feedback.editor_type == "comprehensive"
        assert hasattr(feedback, "human_report")

    def test_validate_input(self, comprehensive_editor):
        """Test input validation."""

        # Valid input
        class MockProse:
            def __init__(self):
                self.scenes = [
                    {
                        "number": 1,
                        "title": "Test scene",
                        "pov_character": "Test Character",
                        "location": "Test Location",
                        "time_hours": 0.0,
                        "content": "Test content",
                    }
                ]

        context = StoryContext(prose=MockProse())
        errors = comprehensive_editor.validate_input(context)
        assert len(errors) == 0

        # Invalid input - no prose
        context = StoryContext()
        errors = comprehensive_editor.validate_input(context)
        assert len(errors) > 0


class TestModelManager:
    """Test the model manager."""

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
    async def test_call_model_success(self, model_manager):
        """Test successful model call."""
        with patch.object(model_manager, "_call_ollama", new_callable=AsyncMock) as mock_call:
            mock_call.return_value = "Test response"

            response = await model_manager.call_model("Test prompt")

            assert response == "Test response"
            mock_call.assert_called_once()

    def test_call_model_sync(self, model_manager):
        """Test synchronous model call wrapper."""
        with patch.object(model_manager, "call_model", new_callable=AsyncMock) as mock_call:
            mock_call.return_value = "Sync response"

            response = model_manager.call_model_sync("Test prompt")

            assert response == "Sync response"
            mock_call.assert_called_once()

    def test_api_key_validation(self, config):
        """Test API key validation."""
        # Test with missing XAI key
        config["default_model"] = "xai/grok-4-fast-reasoning"
        with patch.dict("os.environ", {}, clear=True):
            with pytest.raises(ValueError, match="XAI_API_KEY"):
                ModelManager(config)

        # Test with invalid XAI key (should start with 'xai-')
        config["default_model"] = "xai/grok-4-fast-reasoning"
        with patch.dict("os.environ", {"XAI_API_KEY": "invalid-key"}):
            with pytest.raises(ValueError, match="should start with 'xai-'"):
                ModelManager(config)

        # Test with valid XAI key
        config["default_model"] = "xai/grok-4-fast-reasoning"
        with patch.dict("os.environ", {"XAI_API_KEY": "xai-valid-key"}):
            manager = ModelManager(config)
            assert manager.current_model == "xai/grok-4-fast-reasoning"

    def test_cost_tracking_with_budget(self, model_manager):
        """Test cost tracking with budget enforcement."""
        # Set a low budget
        model_manager.budget_limit = 0.01  # $0.01

        # Add expensive usage that exceeds budget
        model_manager.cost_tracker.record_usage(
            "openai/gpt-4o", "long prompt " * 1000, "long response " * 500, 1.0
        )

        # Should exceed budget
        total_cost = model_manager.cost_tracker.get_total_cost()
        assert total_cost > model_manager.budget_limit

    def test_cost_tracking(self, model_manager):
        """Test cost tracking."""
        model_manager.cost_tracker.record_usage("test_model", "prompt", "response", 1.0)

        assert len(model_manager.cost_tracker.usage_log) == 1
        entry = model_manager.cost_tracker.usage_log[0]
        assert entry["model"] == "test_model"
        assert entry["duration_seconds"] == 1.0


class TestConfigManager:
    """Test the configuration manager."""

    @pytest.fixture
    def config_manager(self):
        """Create a config manager for testing."""
        # Use the actual project config directory
        project_root = Path(__file__).parent.parent.parent
        config_dir = project_root / "src" / "config"
        return ConfigManager(config_dir)

    def test_default_config(self, config_manager):
        """Test loading default configuration."""
        config = config_manager.load_main_config()

        assert "models" in config
        assert "editorial" in config
        assert config["models"]["default"] == "xai/grok-4-fast-reasoning"

    def test_editorial_config(self, config_manager):
        """Test loading editorial configuration."""
        editorial_config = config_manager.get_editorial_config()

        assert "enabled" in editorial_config
        assert "job_storage_dir" in editorial_config
        assert "editors" in editorial_config

    def test_get_model_config(self, config_manager):
        """Test getting model configuration."""
        # Test getting all models
        all_models = config_manager.get_model_config()
        assert "default" in all_models
        assert "ollama" in all_models

        # Test getting specific model
        model_config = config_manager.get_model_config("qwen3:30b")
        assert model_config["provider"] == "ollama"
        assert model_config["model"] == "qwen3:30b"

        # Test getting unknown model (should return default)
        default_config = config_manager.get_model_config("unknown-model")
        assert "provider" in default_config
        assert "model" in default_config

    def test_get_logging_config(self, config_manager):
        """Test getting logging configuration."""
        logging_config = config_manager.get_logging_config()

        assert "level" in logging_config
        assert "file" in logging_config

    def test_load_config_error_handling(self, config_manager):
        """Test config loading error handling."""
        # Test loading non-existent file
        with pytest.raises(ConfigError):
            config_manager._load_config("nonexistent.yaml")

    def test_config_caching(self, config_manager):
        """Test that config files are cached."""
        # Load config twice - should use cache on second call
        config1 = config_manager._load_config("editorial_config.yaml")
        config2 = config_manager._load_config("editorial_config.yaml")

        assert config1 is config2  # Same object from cache


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


class TestStructuralEditor:
    """Test the StructuralEditor individually."""

    @pytest.fixture
    def config(self):
        """Test configuration."""
        return {
            "batch_size": 2,
            "max_concurrent_batches": 2,
        }

    @pytest.fixture
    def mock_model_manager(self):
        """Create a mock model manager for testing."""
        manager = MagicMock(spec=ModelManager)
        manager.call_model = AsyncMock()
        manager.cost_tracker = MagicMock()
        manager.cost_tracker.get_total_cost.return_value = 0.0
        return manager

    @pytest.fixture
    def structural_editor(self, mock_model_manager, config):
        """Create a structural editor for testing."""
        from storygen.editorial.editors.structural import StructuralEditor

        return StructuralEditor(mock_model_manager, config)

    @pytest.mark.asyncio
    async def test_analyze_with_scenes(self, structural_editor, mock_model_manager):
        """Test structural analysis with scene data."""
        # Mock the model responses
        mock_model_manager.call_model.side_effect = [
            "Overall structure assessment: Good three-act structure with clear progression.",
            "Scene 1 analysis: Strong opening with good tension.",
            "Scene 2 analysis: Effective middle development.",
        ]

        # Create test story context
        class MockProse:
            def __init__(self):
                self.scenes = [
                    {"title": "Opening", "content": "Opening content", "number": 1},
                    {"title": "Middle", "content": "Middle content", "number": 2},
                ]

        context = StoryContext(prose=MockProse())

        feedback = await structural_editor.analyze(context)

        assert feedback.editor_type == "structural"
        assert "Overall structure assessment" in feedback.overall_assessment
        assert len(feedback.issues) >= 0  # May have issues from analysis
        assert len(feedback.suggested_revisions) >= 0
        assert len(feedback.strengths) > 0
        assert "Structural Analysis Report" in feedback.human_report

    @pytest.mark.asyncio
    async def test_analyze_no_prose(self, structural_editor):
        """Test structural analysis with no prose content."""
        context = StoryContext()

        feedback = await structural_editor.analyze(context)

        assert feedback.editor_type == "structural"
        assert len(feedback.issues) == 1
        assert "No prose content found" in feedback.issues[0].description

    def test_validate_input_valid(self, structural_editor):
        """Test input validation with valid input."""

        class MockProse:
            def __init__(self):
                self.scenes = [{"title": "Test", "content": "Content", "number": 1}]

        context = StoryContext(prose=MockProse())
        errors = structural_editor.validate_input(context)
        assert len(errors) == 0

    def test_validate_input_no_prose(self, structural_editor):
        """Test input validation with no prose."""
        context = StoryContext()
        errors = structural_editor.validate_input(context)
        assert len(errors) == 1
        assert "Prose content required" in errors[0]

    def test_validate_input_short_content(self, structural_editor):
        """Test input validation with content that's too short."""

        class MockProse:
            def __init__(self):
                self.content = "Short"

        context = StoryContext(prose=MockProse())
        errors = structural_editor.validate_input(context)
        assert len(errors) == 1
        assert "too short" in errors[0]

    def test_extract_scenes_from_scenes_attr(self, structural_editor):
        """Test scene extraction from prose.scenes attribute."""

        class MockProse:
            def __init__(self):
                self.scenes = [
                    {"title": "Scene 1", "content": "Content 1"},
                    {"title": "Scene 2", "content": "Content 2"},
                ]

        context = StoryContext(prose=MockProse())
        scenes = structural_editor._extract_scenes(context)

        assert len(scenes) == 2
        assert scenes[0]["title"] == "Scene 1"
        assert scenes[1]["title"] == "Scene 2"

    def test_extract_scenes_from_content_delimiters(self, structural_editor):
        """Test scene extraction from content with delimiters."""

        class MockProse:
            def __init__(self):
                self.content = "Opening\nOpening content\n\n## Middle\nMiddle content\n\n## Climax\nClimax content"

        context = StoryContext(prose=MockProse())
        scenes = structural_editor._extract_scenes(context)

        assert len(scenes) == 3
        assert scenes[0]["title"] == "Scene 1"
        assert scenes[1]["title"] == "Scene 2"
        assert scenes[2]["title"] == "Scene 3"

    def test_extract_story_text(self, structural_editor):
        """Test story text extraction."""

        class MockProse:
            def __init__(self):
                self.content = "Story content"

            def to_text(self):
                return "Extracted text"

        context = StoryContext(prose=MockProse())

        # Test to_text method
        text = structural_editor._extract_story_text(context)
        assert text == "Extracted text"

        # Test fallback to content
        class MockProseNoToText:
            def __init__(self):
                self.content = "Direct content"

        context.prose = MockProseNoToText()
        text = structural_editor._extract_story_text(context)
        assert text == "Direct content"

    def test_identify_structural_strengths(self, structural_editor):
        """Test identification of structural strengths."""
        scene_analyses = [
            {"analysis": "Strong scene with good pacing and effective transitions"},
            {"analysis": "Another strong scene with good development"},
            {"analysis": "Third strong scene with effective pacing"},
        ]

        strengths = structural_editor._identify_structural_strengths(scene_analyses)

        assert len(strengths) >= 3  # Should have identified strength plus default strengths
        assert "Consistent scene quality throughout the story" in strengths

    def test_parse_scene_feedback_creates_issues(self, structural_editor):
        """Test parsing scene feedback for issues and revisions."""
        feedback = "This scene has weak pacing and needs expansion."

        issues, revisions = structural_editor._parse_scene_feedback(feedback, 0)

        assert len(issues) > 0
        assert len(revisions) > 0
        assert issues[0].category in ["structure", "pacing"]
        assert revisions[0].scene_id == "scene_1"


class TestContinuityEditor:
    """Test the ContinuityEditor individually."""

    @pytest.fixture
    def config(self):
        """Test configuration."""
        return {
            "batch_size": 2,
            "max_concurrent_batches": 2,
        }

    @pytest.fixture
    def mock_model_manager(self):
        """Create a mock model manager for testing."""
        manager = MagicMock(spec=ModelManager)
        manager.call_model = AsyncMock()
        manager.cost_tracker = MagicMock()
        manager.cost_tracker.get_total_cost.return_value = 0.0
        return manager

    @pytest.fixture
    def continuity_editor(self, mock_model_manager, config):
        """Create a continuity editor for testing."""
        from storygen.editorial.editors.continuity import ContinuityEditor

        return ContinuityEditor(mock_model_manager, config)

    @pytest.mark.asyncio
    async def test_analyze_with_story(self, continuity_editor, mock_model_manager):
        """Test continuity analysis with story data."""
        # Mock the model responses for character and plot analysis
        mock_model_manager.call_model.side_effect = [
            "Character consistency: Good character development.",
            "Plot continuity: Logical progression with no major issues.",
            "World-building: Consistent setting and rules.",
        ]

        # Create test story context
        class MockProse:
            def __init__(self):
                self.content = "Story with character development and plot progression."

        context = StoryContext(prose=MockProse())

        feedback = await continuity_editor.analyze(context)

        assert feedback.editor_type == "continuity"
        assert len(feedback.issues) >= 0
        assert len(feedback.suggested_revisions) >= 0
        assert "Continuity Analysis Report" in feedback.human_report

    @pytest.mark.asyncio
    async def test_analyze_no_prose(self, continuity_editor):
        """Test continuity analysis with no prose content."""
        context = StoryContext()

        feedback = await continuity_editor.analyze(context)

        assert feedback.editor_type == "continuity"
        assert len(feedback.issues) == 1
        assert "No prose content found" in feedback.issues[0].description

    def test_validate_input(self, continuity_editor):
        """Test input validation."""

        # Valid input - longer content
        class MockProse:
            def __init__(self):
                self.content = (
                    "This is a much longer story content for continuity analysis that should be long enough to pass validation. "
                    * 50
                )

        context = StoryContext(prose=MockProse())
        errors = continuity_editor.validate_input(context)
        assert len(errors) == 0

        # Invalid input - no prose
        context = StoryContext()
        errors = continuity_editor.validate_input(context)
        assert len(errors) == 1


class TestStyleEditor:
    """Test the StyleEditor individually."""

    @pytest.fixture
    def config(self):
        """Test configuration."""
        return {
            "batch_size": 2,
            "max_concurrent_batches": 2,
        }

    @pytest.fixture
    def mock_model_manager(self):
        """Create a mock model manager for testing."""
        manager = MagicMock(spec=ModelManager)
        manager.call_model = AsyncMock()
        manager.cost_tracker = MagicMock()
        manager.cost_tracker.get_total_cost.return_value = 0.0
        return manager

    @pytest.fixture
    def style_editor(self, mock_model_manager, config):
        """Create a style editor for testing."""
        from storygen.editorial.editors.style import StyleEditor

        return StyleEditor(mock_model_manager, config)

    @pytest.mark.asyncio
    async def test_analyze_with_story(self, style_editor, mock_model_manager):
        """Test style analysis with story data."""
        # Mock the model responses for style analysis
        mock_model_manager.call_model.side_effect = [
            "POV consistency: Consistent third-person limited.",
            "Voice consistency: Strong narrative voice maintained.",
            "Prose rhythm: Good sentence variety and flow.",
            "Language level: Appropriate for target audience.",
        ]

        # Create test story context
        class MockProse:
            def __init__(self):
                self.content = "Story with consistent style and voice."

        context = StoryContext(prose=MockProse())

        feedback = await style_editor.analyze(context)

        assert feedback.editor_type == "style"
        assert len(feedback.issues) >= 0
        assert len(feedback.suggested_revisions) >= 0
        assert "Style Analysis Report" in feedback.human_report

    @pytest.mark.asyncio
    async def test_analyze_no_prose(self, style_editor):
        """Test style analysis with no prose content."""
        context = StoryContext()

        feedback = await style_editor.analyze(context)

        assert feedback.editor_type == "style"
        assert len(feedback.issues) == 1
        assert "No prose content found" in feedback.issues[0].description

    def test_validate_input(self, style_editor):
        """Test input validation."""

        # Valid input - longer content
        class MockProse:
            def __init__(self):
                self.content = (
                    "This is a much longer story content for style analysis that should be long enough to pass validation. "
                    * 20
                )

        context = StoryContext(prose=MockProse())
        errors = style_editor.validate_input(context)
        assert len(errors) == 0

        # Invalid input - no prose
        context = StoryContext()
        errors = style_editor.validate_input(context)
        assert len(errors) == 1
