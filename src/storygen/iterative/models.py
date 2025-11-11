"""
Data models for iterative story generation.

All models support JSON serialization via to_dict() and from_dict() methods.
"""

from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Literal


@dataclass
class StoryIdea:
    """A story idea with genre, themes, and expanded description."""

    raw_idea: str
    one_sentence: str
    expanded: str
    genres: list[str]  # e.g., ["sci-fi", "horror"] or ["romantic", "comedy"]
    tone: str
    themes: list[str]

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
            raise ValueError("StoryIdea must have at least one genre")

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "StoryIdea":
        """Deserialize from dictionary."""
        return cls(**data)


@dataclass
class Character:
    """A character with role, goals, flaws, and arc."""

    name: str
    role: Literal["protagonist", "antagonist", "mentor", "ally", "foil", "supporting"]
    bio: str
    goal: str
    flaw: str
    arc: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Character":
        """Deserialize from dictionary."""
        return cls(**data)


@dataclass
class Location:
    """A story location with description and atmosphere."""

    name: str
    description: str
    atmosphere: str
    significance: str

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Location":
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


@dataclass
class ActStructure:
    """Three-act structure outline."""

    act: int
    summary: str
    hook: str | None = None
    midpoint: str | None = None
    climax: str | None = None
    resolution: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ActStructure":
        """Deserialize from dictionary."""
        return cls(**data)


@dataclass
class SceneSequel:
    """A scene or sequel with goals, conflicts, and outcomes."""

    id: str
    type: Literal["scene", "sequel"]
    act: int
    pov_character: str
    location: str
    goal: str
    outcome: str
    conflict: str | None = None
    disaster: str | None = None
    reaction: str | None = None
    dilemma: str | None = None
    decision: str | None = None
    prose: str | None = None

    # Pacing control
    pacing: Literal["very_fast", "fast", "medium", "slow", "very_slow"] = "medium"
    target_word_count: int = 600

    # Time tracking
    start_hours: float = 0.0
    duration_hours: float = 0.5
    end_hours: float = field(init=False)
    time_of_day: str = field(init=False)
    day_number: int = field(init=False)
    timestamp_description: str | None = None

    # Chapter support
    chapter: int | None = None
    chapter_title: str | None = None
    chapter_start: bool = False
    chapter_end: bool = False

    def __post_init__(self):
        """Calculate derived time fields."""
        self.end_hours = self.start_hours + self.duration_hours
        self.day_number = int(self.start_hours // 24) + 1
        self.time_of_day = self._calculate_time_of_day()

    def _calculate_time_of_day(self) -> str:
        """Calculate time of day from start_hours."""
        hour_of_day = self.start_hours % 24

        if 0 <= hour_of_day < 4:
            return "dead of night"
        elif 4 <= hour_of_day < 6:
            return "pre-dawn"
        elif 6 <= hour_of_day < 9:
            return "early morning"
        elif 9 <= hour_of_day < 12:
            return "late morning"
        elif 12 <= hour_of_day < 14:
            return "midday"
        elif 14 <= hour_of_day < 17:
            return "afternoon"
        elif 17 <= hour_of_day < 20:
            return "evening"
        elif 20 <= hour_of_day < 22:
            return "night"
        else:
            return "late night"

    def get_time_gap_from(self, previous: "SceneSequel") -> float:
        """Calculate time gap from previous scene/sequel in hours."""
        return self.start_hours - previous.end_hours

    def get_time_summary(self) -> str:
        """Get human-readable time summary."""
        return f"Day {self.day_number}, {self.time_of_day} ({self.start_hours:.1f}h - {self.end_hours:.1f}h)"

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SceneSequel":
        """Deserialize from dictionary."""
        # Remove calculated fields if present (they'll be recalculated in __post_init__)
        data_copy = data.copy()
        data_copy.pop("end_hours", None)
        data_copy.pop("time_of_day", None)
        data_copy.pop("day_number", None)
        return cls(**data_copy)


@dataclass
class EditorialFeedback:
    """Feedback from Editor AI."""

    step: str
    rating: Literal["failure", "acceptable", "good", "excellent"]
    issues: list[str]
    suggestions: list[str]
    praise: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "EditorialFeedback":
        """Deserialize from dictionary."""
        return cls(**data)


@dataclass
class ProjectConfig:
    """Configuration for a story project."""

    # Story metadata
    target_length: Literal["flash", "short", "novelette", "novella", "novel"] = "short"
    structure: Literal["three_act", "five_act", "hero_journey", "fichtean"] = "three_act"

    # AI configuration
    writer_model: str = "gpt-4"
    editor_model: str = "gpt-4"
    use_editor: bool = True
    max_revision_cycles: int = 2

    # Pacing configuration
    default_pacing: Literal["very_fast", "fast", "medium", "slow", "very_slow"] = "medium"
    pacing_profile: Literal["thriller", "literary", "balanced", "mystery"] = "balanced"

    # Time tracking
    start_timestamp: str | None = None
    story_duration_hours: float | None = None
    validate_travel_times: bool = True
    track_human_needs: bool = True
    allow_time_gaps: bool = True
    max_time_gap_hours: float = 24.0
    location_distances: dict[str, dict[str, float]] = field(default_factory=dict)

    # Chapter configuration
    use_chapters: bool = False
    chapter_style: Literal["numbered", "titled", "epigraphs", "sections"] = "numbered"
    target_chapter_length: int = 3000

    # Output configuration
    output_format: Literal["epub", "html", "markdown"] = "epub"

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ProjectConfig":
        """Deserialize from dictionary."""
        return cls(**data)


@dataclass
class WorkingDoc:
    """The complete working document for a story project."""

    id: str
    created_at: datetime
    updated_at: datetime = field(default_factory=datetime.now)

    # Story components (filled in during generation)
    idea: StoryIdea | None = None
    characters: list[Character] = field(default_factory=list)
    locations: list[Location] = field(default_factory=list)
    world_building: WorldBuilding | None = None
    outline: list[ActStructure] = field(default_factory=list)
    scene_sequel_breakdown: list[SceneSequel] = field(default_factory=list)

    # Editorial history
    editorial_feedback: list[EditorialFeedback] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        data = asdict(self)
        # Convert datetime to ISO string
        data["created_at"] = self.created_at.isoformat()
        data["updated_at"] = self.updated_at.isoformat()
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "WorkingDoc":
        """Deserialize from dictionary."""
        data_copy = data.copy()

        # Convert ISO strings to datetime
        data_copy["created_at"] = datetime.fromisoformat(data["created_at"])
        data_copy["updated_at"] = datetime.fromisoformat(data["updated_at"])

        # Convert nested objects
        if data_copy.get("idea"):
            data_copy["idea"] = StoryIdea.from_dict(data_copy["idea"])

        if data_copy.get("characters"):
            data_copy["characters"] = [Character.from_dict(c) for c in data_copy["characters"]]

        if data_copy.get("locations"):
            data_copy["locations"] = [Location.from_dict(loc) for loc in data_copy["locations"]]

        if data_copy.get("world_building"):
            data_copy["world_building"] = WorldBuilding.from_dict(data_copy["world_building"])

        if data_copy.get("outline"):
            data_copy["outline"] = [ActStructure.from_dict(act) for act in data_copy["outline"]]

        if data_copy.get("scene_sequel_breakdown"):
            data_copy["scene_sequel_breakdown"] = [
                SceneSequel.from_dict(ss) for ss in data_copy["scene_sequel_breakdown"]
            ]

        if data_copy.get("editorial_feedback"):
            data_copy["editorial_feedback"] = [
                EditorialFeedback.from_dict(ef) for ef in data_copy["editorial_feedback"]
            ]

        return cls(**data_copy)


@dataclass
class Project:
    """A story generation project with metadata and file paths."""

    id: str
    title: str
    created_at: datetime
    updated_at: datetime = field(default_factory=datetime.now)
    current_step: Literal[
        "created",
        "idea",
        "characters",
        "locations",
        "world_building",
        "outline",
        "breakdown",
        "prose",
        "complete",
    ] = "created"

    config: ProjectConfig = field(default_factory=ProjectConfig)

    # File paths (set by ProjectManager, optional for serialization)
    project_dir: Path | None = None
    working_doc_path: Path | None = None
    versions_dir: Path | None = None
    output_dir: Path | None = None

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        data = asdict(self)
        data["created_at"] = self.created_at.isoformat()
        data["updated_at"] = self.updated_at.isoformat()
        # Convert Path objects to strings
        if self.project_dir is not None:
            data["project_dir"] = str(self.project_dir)
        if self.working_doc_path is not None:
            data["working_doc_path"] = str(self.working_doc_path)
        if self.versions_dir is not None:
            data["versions_dir"] = str(self.versions_dir)
        if self.output_dir is not None:
            data["output_dir"] = str(self.output_dir)
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Project":
        """Deserialize from dictionary."""
        data_copy = data.copy()

        # Convert ISO strings to datetime
        data_copy["created_at"] = datetime.fromisoformat(data["created_at"])
        data_copy["updated_at"] = datetime.fromisoformat(data["updated_at"])

        # Convert config
        if data_copy.get("config"):
            data_copy["config"] = ProjectConfig.from_dict(data_copy["config"])

        # Remove Path fields (they'll be set by ProjectManager)
        data_copy.pop("project_dir", None)
        data_copy.pop("working_doc_path", None)
        data_copy.pop("versions_dir", None)
        data_copy.pop("output_dir", None)

        return cls(**data_copy)
