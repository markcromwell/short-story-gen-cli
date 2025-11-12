"""
Exception hierarchy for story generation system.

Provides consistent, semantic exceptions across all generators and components.
"""


class StoryGenError(Exception):
    """Base exception for all story generation errors."""

    pass


class GenerationError(StoryGenError):
    """Raised when content generation fails."""

    pass


class ValidationError(StoryGenError):
    """Raised when model validation fails."""

    pass


class ModelError(StoryGenError):
    """Raised when there are issues with data models."""

    pass


class ConfigError(StoryGenError):
    """Raised when there are configuration issues."""

    pass


class APIError(StoryGenError):
    """Raised when AI API calls fail."""

    pass


class ProjectError(StoryGenError):
    """Raised when project operations fail."""

    pass
