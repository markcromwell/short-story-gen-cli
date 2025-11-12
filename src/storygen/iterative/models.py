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
class Act:
    """
    Recursive act structure for story outlines.

    Can represent any level of story structure from high-level acts down to
    individual scenes. Non-terminal acts have sub_acts, terminal acts have scenes.
    """

    title: str  # e.g., "Act 1: Setup", "Crossing the Threshold", "The Journey Begins"
    description: str  # Generic description of what happens in this act (template)
    story_application: str  # How this act applies to the specific story (AI-generated)
    percentage: float  # Percentage of total story length (0.0 to 1.0)
    order: int = 0  # Position within parent (0-indexed, auto-assigned if not provided)

    # Recursive structure: either has sub-acts OR scenes, never both
    sub_acts: list["Act"] = field(default_factory=list)  # Non-terminal nodes
    scenes: list[str] = field(default_factory=list)  # Terminal: scene/sequel IDs

    def is_terminal(self) -> bool:
        """Check if this is a leaf act (has scenes, not sub-acts)."""
        return len(self.sub_acts) == 0

    def get_total_percentage(self) -> float:
        """Calculate total percentage including all descendants."""
        if self.is_terminal():
            return self.percentage
        return sum(act.get_total_percentage() for act in self.sub_acts)

    def get_depth(self) -> int:
        """Get the maximum depth of the tree from this node."""
        if self.is_terminal():
            return 1
        return 1 + max((act.get_depth() for act in self.sub_acts), default=0)

    def validate(self) -> list[str]:
        """
        Validate act structure and return list of errors.

        Returns:
            List of error messages (empty if valid)
        """
        errors = []

        # Check percentage is valid
        if not 0.0 <= self.percentage <= 1.0:
            errors.append(f"Act '{self.title}': percentage {self.percentage} not in range [0, 1]")

        # Check mutually exclusive: can't have both sub_acts and scenes
        if len(self.sub_acts) > 0 and len(self.scenes) > 0:
            errors.append(
                f"Act '{self.title}': cannot have both sub_acts and scenes (must be one or the other)"
            )

        # If non-terminal, validate sub-acts sum to parent percentage
        if not self.is_terminal():
            if len(self.sub_acts) == 0:
                errors.append(f"Act '{self.title}': non-terminal act must have sub_acts")

            sub_total = sum(act.percentage for act in self.sub_acts)
            if abs(sub_total - self.percentage) > 0.01:  # Allow small floating point error
                errors.append(
                    f"Act '{self.title}': sub-acts total {sub_total:.2%} "
                    f"but parent is {self.percentage:.2%}"
                )

            # Recursively validate children
            for sub_act in self.sub_acts:
                errors.extend(sub_act.validate())

        return errors

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Act":
        """Deserialize from dictionary."""
        data_copy = data.copy()

        # Recursively deserialize sub_acts and auto-assign order if not present
        if data_copy.get("sub_acts"):
            data_copy["sub_acts"] = [
                cls.from_dict({**act, "order": i} if "order" not in act else act)
                for i, act in enumerate(data_copy["sub_acts"])
            ]

        # Auto-assign order if not present (will use default 0)
        if "order" not in data_copy:
            data_copy["order"] = 0

        return cls(**data_copy)


@dataclass
class Outline:
    """
    Story outline with recursive act structure.

    Supports multiple structure types (three-act, hero's journey, fichtean, custom)
    with flexible hierarchical organization.
    """

    structure_type: str  # "three-act", "hero-journey", "fichtean", "custom"
    acts: list[Act]  # Top-level acts

    def validate(self) -> list[str]:
        """
        Validate outline structure.

        Returns:
            List of error messages (empty if valid)
        """
        errors = []

        # Check acts exist
        if not self.acts:
            errors.append("Outline must have at least one act")
            return errors

        # Validate total percentage sums to ~100%
        total = sum(act.get_total_percentage() for act in self.acts)
        if abs(total - 1.0) > 0.01:
            errors.append(f"Acts total {total:.2%} but should be 100%")

        # Validate each act
        for act in self.acts:
            errors.extend(act.validate())

        return errors

    def get_all_terminal_acts(self) -> list[Act]:
        """Get all leaf acts (those that will contain scenes)."""
        terminals = []

        def collect_terminals(act: Act):
            if act.is_terminal():
                terminals.append(act)
            else:
                for sub_act in act.sub_acts:
                    collect_terminals(sub_act)

        for act in self.acts:
            collect_terminals(act)

        return terminals

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Outline":
        """Deserialize from dictionary."""
        data_copy = data.copy()

        # Deserialize acts
        if data_copy.get("acts"):
            data_copy["acts"] = [Act.from_dict(act) for act in data_copy["acts"]]

        return cls(**data_copy)


@dataclass
class OutlineLegacy:
    """
    DEPRECATED: Legacy 3-act outline with 7 fixed plot points.

    Use the new recursive Outline/Act structure instead.
    Kept for backward compatibility with existing code.
    """

    # Act 1: Setup (25%)
    act1_setup: str  # Introduce protagonist, world, and status quo
    act1_inciting_incident: str  # Event that disrupts the status quo

    # Act 2: Confrontation (50%)
    act2_rising_action: str  # Protagonist pursues goal, faces obstacles
    act2_midpoint: str  # Major revelation or turning point
    act2_crisis: str  # All seems lost, darkest moment

    # Act 3: Resolution (25%)
    act3_climax: str  # Final confrontation with antagonist
    act3_resolution: str  # New status quo, aftermath

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "OutlineLegacy":
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
    """A scene or sequel with goals, conflicts, and outcomes.

    Scene-Sequel structure based on Dwight Swain's method:
    - Scene: goal/conflict/disaster (REQUIRED for type="scene")
    - Sequel: reaction/dilemma/decision (OPTIONAL for type="sequel")
    """

    id: str
    type: Literal["scene", "sequel"]

    # Context (REQUIRED)
    source_act: str  # Which outline act this came from
    pov_character: str  # Whose eyes we see through (REQUIRED)
    location: str  # Where this takes place (can be new or from location list)

    # Time tracking (REQUIRED)
    start_hours: float  # Hours since story start (t=0.0)
    duration_hours: float  # How long this scene-sequel lasts
    end_hours: float = field(init=False)  # Calculated: start + duration
    time_of_day: str = field(init=False)  # Calculated: "morning", "night", etc.
    day_number: int = field(init=False)  # Calculated: which story day
    timestamp_description: str | None = None  # Optional: "Monday 3:00 AM"

    # Scene elements (REQUIRED if type="scene")
    goal: str | None = None  # What POV character wants
    conflict: str | None = None  # Opposition to goal
    disaster: str | None = None  # How it goes wrong

    # Sequel elements (OPTIONAL if type="sequel")
    reaction: str | None = None  # Emotional response
    dilemma: str | None = None  # Weighing options
    decision: str | None = None  # Choice leading to next scene

    # Pacing control
    target_word_count: int = 600

    # Content (generated in prose step)
    content: str = ""  # The actual prose in markdown format
    actual_word_count: int = 0
    summary: str = ""  # 2-3 sentence summary for continuity
    key_points: list[str] = field(default_factory=list)  # Critical details for next scenes

    # Chapter support (optional)
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

    def validate(self) -> list[str]:
        """Validate scene-sequel structure.

        Returns:
            List of validation error messages (empty if valid)
        """
        issues = []

        # Check required fields
        if not self.pov_character:
            issues.append(f"{self.id}: Missing POV character")
        if not self.location:
            issues.append(f"{self.id}: Missing location")
        if not self.source_act:
            issues.append(f"{self.id}: Missing source_act")

        # Check time values
        if self.start_hours < 0:
            issues.append(f"{self.id}: Invalid start_hours ({self.start_hours})")
        if self.duration_hours <= 0:
            issues.append(f"{self.id}: Invalid duration_hours ({self.duration_hours})")

        # Check scene-specific requirements
        if self.type == "scene":
            if not self.goal:
                issues.append(f"{self.id}: Scene missing 'goal' (what POV character wants)")
            if not self.conflict:
                issues.append(f"{self.id}: Scene missing 'conflict' (opposition to goal)")
            if not self.disaster:
                issues.append(f"{self.id}: Scene missing 'disaster' (how goal fails/complicates)")

        # Sequels are more flexible - reaction/dilemma/decision are optional
        # but at least one should be present
        if self.type == "sequel":
            if not any([self.reaction, self.dilemma, self.decision]):
                issues.append(
                    f"{self.id}: Sequel should have at least one of: reaction, dilemma, or decision"
                )

        return issues

    def get_plain_text(self) -> str:
        """Convert markdown content to plain text.

        Returns:
            Plain text version of content (strips markdown formatting)
        """
        import re

        if not self.content:
            return ""

        text = self.content
        # Remove bold/italic
        text = re.sub(r"\*\*\*(.+?)\*\*\*", r"\1", text)  # bold+italic
        text = re.sub(r"\*\*(.+?)\*\*", r"\1", text)  # bold
        text = re.sub(r"\*(.+?)\*", r"\1", text)  # italic
        text = re.sub(r"_(.+?)_", r"\1", text)  # italic underscore
        # Remove horizontal rules
        text = re.sub(r"^---+\s*$", "", text, flags=re.MULTILINE)
        # Remove headers (keep text)
        text = re.sub(r"^#+\s+", "", text, flags=re.MULTILINE)

        return text.strip()

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
