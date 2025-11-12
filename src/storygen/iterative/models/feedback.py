"""
Editorial feedback data models.
"""

from dataclasses import asdict, dataclass, field
from typing import Any, Literal


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
