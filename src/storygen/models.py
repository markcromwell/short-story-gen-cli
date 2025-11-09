"""
Data models for structured story output.
"""

import json
from dataclasses import dataclass
from typing import Optional


@dataclass
class Scene:
    """A single scene in a story."""

    number: int
    title: str
    content: str
    setting: Optional[str] = None
    characters: Optional[list[str]] = None

    def to_dict(self) -> dict:
        """Convert scene to dictionary."""
        return {
            "number": self.number,
            "title": self.title,
            "content": self.content,
            "setting": self.setting,
            "characters": self.characters,
        }


@dataclass
class Story:
    """A structured story with title, scenes, and metadata."""

    title: str
    scenes: list[Scene]
    genre: Optional[str] = None
    summary: Optional[str] = None
    word_count: Optional[int] = None

    def to_dict(self) -> dict:
        """Convert story to dictionary."""
        return {
            "title": self.title,
            "genre": self.genre,
            "summary": self.summary,
            "word_count": self.word_count or self._calculate_word_count(),
            "scenes": [scene.to_dict() for scene in self.scenes],
        }

    def to_json(self, indent: int = 2) -> str:
        """Convert story to JSON string."""
        return json.dumps(self.to_dict(), indent=indent)

    def to_text(self) -> str:
        """Convert story to plain text format."""
        lines = [f"# {self.title}", ""]

        if self.genre:
            lines.append(f"**Genre:** {self.genre}")
        if self.summary:
            lines.append(f"**Summary:** {self.summary}")
        if lines[-1]:  # Add blank line after metadata
            lines.append("")

        for scene in self.scenes:
            lines.append(f"## Scene {scene.number}: {scene.title}")
            if scene.setting:
                lines.append(f"*Setting: {scene.setting}*")
            if scene.characters:
                lines.append(f"*Characters: {', '.join(scene.characters)}*")
            lines.append("")
            lines.append(scene.content)
            lines.append("")

        return "\n".join(lines)

    def _calculate_word_count(self) -> int:
        """Calculate total word count across all scenes."""
        total = 0
        for scene in self.scenes:
            total += len(scene.content.split())
        return total

    @classmethod
    def from_json(cls, json_str: str) -> "Story":
        """Create Story from JSON string."""
        data = json.loads(json_str)
        scenes = [Scene(**scene_data) for scene_data in data.get("scenes", [])]
        return cls(
            title=data["title"],
            scenes=scenes,
            genre=data.get("genre"),
            summary=data.get("summary"),
            word_count=data.get("word_count"),
        )
