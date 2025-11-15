"""Core data models and base classes for the editorial workflow system."""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import TYPE_CHECKING, Any, Literal

if TYPE_CHECKING:
    from .core.model_manager import ModelManager


@dataclass
class EditorialIssue:
    """Represents a single editorial issue or suggestion."""

    severity: Literal["major", "minor", "info"]
    category: str  # structure, character, pacing, continuity, pov, etc.
    description: str
    suggestion: str
    scene_ids: list[str] | None = None
    line_numbers: list[int] | None = None
    confidence_score: float | None = None  # 0.0 to 1.0


@dataclass
class EditorialFeedback:
    """Container for all feedback from an editor."""

    editor_type: str
    overall_assessment: str
    issues: list[EditorialIssue] = field(default_factory=list)
    suggested_revisions: list["RevisionSuggestion"] = field(default_factory=list)
    strengths: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    human_report: str = ""  # Human-readable summary of what the editor did


@dataclass
class RevisionSuggestion:
    """Specific revision recommendation."""

    revision_type: Literal["rewrite", "expand", "cut", "reorder", "add"]
    priority: Literal["high", "medium", "low"]
    reason: str
    instruction: str  # Detailed guidance for AI regeneration
    scene_id: str | None = None  # None for "add new scene"
    target_word_count: int | None = None
    insert_after: str | None = None  # For "add" type
    estimated_tokens: int | None = None


@dataclass
class StoryContext:
    """Complete context for editorial analysis."""

    story_idea: Any | None = None  # StoryIdea from existing codebase
    characters: list[Any] = field(default_factory=list)  # List[Character]
    locations: list[Any] = field(default_factory=list)  # List[Location]
    outline: Any | None = None  # Outline from existing codebase
    prose: Any | None = None  # Prose from existing codebase
    previous_feedback: list[EditorialFeedback] = field(default_factory=list)


class EditorialError(Exception):
    """Base exception for editorial workflow errors."""

    pass


class ValidationError(EditorialError):
    """Raised when input validation fails."""

    pass


class ModelError(EditorialError):
    """Raised when AI model calls fail."""

    pass


class BudgetExceededError(EditorialError):
    """Raised when cost limits are exceeded."""

    pass


class BaseEditor(ABC):
    """Abstract base class for all editors."""

    def __init__(self, model_manager: "ModelManager", config: dict[str, Any]):
        self.model_manager = model_manager
        self.config = config
        self.logger = logging.getLogger(self.__class__.__name__)

    @abstractmethod
    async def analyze(self, context: StoryContext) -> EditorialFeedback:
        """Perform editorial analysis."""
        pass

    @abstractmethod
    def validate_input(self, context: StoryContext) -> list[str]:
        """Validate input data and return error messages."""
        pass

    def _create_feedback_container(self, editor_type: str) -> EditorialFeedback:
        """Create standardized feedback container."""
        return EditorialFeedback(
            editor_type=editor_type,
            overall_assessment="",
            issues=[],
            suggested_revisions=[],
            strengths=[],
            metadata={
                "timestamp": datetime.now().isoformat(),
                "editor_version": self.config.get("version", "1.0.0"),
                "model_used": getattr(self.model_manager, "current_model", "unknown"),
            },
        )

    def _handle_analysis_error(self, error: Exception, context: StoryContext) -> EditorialFeedback:
        """Standardized error handling."""
        self.logger.error(f"Analysis failed: {error}")
        feedback = self._create_feedback_container(self.__class__.__name__)
        feedback.overall_assessment = "Analysis could not be completed due to technical issues"
        feedback.issues = [
            EditorialIssue(
                severity="info",
                category="technical",
                description=f"Analysis failed: {str(error)}",
                suggestion="Please try again or proceed with manual review",
            )
        ]
        return feedback
