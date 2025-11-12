"""
Project management data models (ProjectConfig, WorkingDoc, Project).
"""

from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Literal

from .characters import Character
from .feedback import EditorialFeedback
from .locations import Location
from .story import StoryIdea, WorldBuilding
from .structure import ActStructure, SceneSequel


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
