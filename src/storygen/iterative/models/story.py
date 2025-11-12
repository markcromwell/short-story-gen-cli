"""
Story-related data models (StoryIdea, StoryConfig).
"""

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Literal

from ..exceptions import ConfigError, ValidationError


@dataclass
class StoryConfig:
    """Base configuration for a story project."""

    story_type: Literal["flash-fiction", "short-story", "novelette", "novella", "novel"]
    target_words: int
    pitch: str
    created_at: str
    updated_at: str

    def __post_init__(self):
        """Validate story type and target words."""
        valid_types = ["flash-fiction", "short-story", "novelette", "novella", "novel"]
        if self.story_type not in valid_types:
            raise ConfigError(f"story_type must be one of {valid_types}")

        if self.target_words <= 0:
            raise ConfigError("target_words must be positive")

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "StoryConfig":
        """Deserialize from dictionary."""
        return cls(**data)

    @classmethod
    def load(cls, project_path: Path) -> "StoryConfig":
        """Load config from project directory."""
        import json

        config_path = project_path / "story_config.json"
        if not config_path.exists():
            raise FileNotFoundError(f"Config not found: {config_path}")

        with open(config_path, encoding="utf-8") as f:
            data = json.load(f)

        return cls.from_dict(data)

    def get_length_category(self) -> str:
        """Get human-readable length category."""
        categories = {
            "flash-fiction": "Flash Fiction (<1,500 words)",
            "short-story": "Short Story (1,500-7,500 words)",
            "novelette": "Novelette (7,500-17,500 words)",
            "novella": "Novella (17,500-40,000 words)",
            "novel": "Novel (40,000+ words)",
        }
        return categories.get(self.story_type, self.story_type)


@dataclass
class StoryIdea:
    """A story idea with genre, themes, and expanded description."""

    raw_idea: str
    one_sentence: str
    expanded: str
    genres: list[str]  # e.g., ["sci-fi", "horror"] or ["romantic", "comedy"]
    tone: str
    themes: list[str]
    setting: str  # e.g., "1950s Paris", "Modern NYC", "Hyperborea - ancient sorcerous empire"

    def __post_init__(self):
        """Validate and clean up genres and themes."""
        # Remove duplicates from genres while preserving order
        seen = set()
        unique_genres = []
        for genre in self.genres:
            genre_lower = genre.lower().strip()
            if genre_lower not in seen:
                seen.add(genre_lower)
                unique_genres.append(genre_lower)
        self.genres = unique_genres

        # Remove duplicates from themes while preserving order
        seen_themes = set()
        unique_themes = []
        for theme in self.themes:
            theme_lower = theme.lower().strip()
            if theme_lower not in seen_themes:
                seen_themes.add(theme_lower)
                unique_themes.append(theme_lower)
        self.themes = unique_themes

        # Validate at least one genre
        if not self.genres:
            raise ValidationError("StoryIdea must have at least one genre")

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "StoryIdea":
        """Deserialize from dictionary."""
        return cls(**data)


@dataclass
class WorldBuilding:
    """Optional world-building for speculative fiction."""

    magic_system: str | None = None
    technology_level: str | None = None
    social_structure: str | None = None
    key_rules: list[str] = field(default_factory=list)
    constraints: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "WorldBuilding":
        """Deserialize from dictionary."""
        return cls(**data)
