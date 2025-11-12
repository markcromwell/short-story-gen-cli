"""
Story structure data models (Act, Outline, SceneSequel, legacy structures).
"""

import re
from dataclasses import asdict, dataclass, field
from typing import Any, Literal


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
