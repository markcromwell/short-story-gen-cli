"""
Character-related data models.
"""

from dataclasses import asdict, dataclass
from typing import Any, Literal


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
