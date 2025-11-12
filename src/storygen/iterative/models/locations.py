"""
Location-related data models.
"""

from dataclasses import asdict, dataclass
from typing import Any


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
