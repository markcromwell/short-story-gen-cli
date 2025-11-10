"""
Data models for structured story output.
"""

import json
from dataclasses import dataclass


@dataclass
class Scene:
    """A single scene in a story."""

    number: int
    title: str
    content: str
    pov_character: str | None = None
    location: str | None = None
    time_hours: float | None = None  # Hours since story start

    def to_dict(self) -> dict:
        """Convert scene to dictionary."""
        return {
            "number": self.number,
            "title": self.title,
            "content": self.content,
            "pov_character": self.pov_character,
            "location": self.location,
            "time_hours": self.time_hours,
        }


@dataclass
class Story:
    """A structured story with title, scenes, and metadata."""

    title: str
    scenes: list[Scene]
    genre: str | None = None
    summary: str | None = None
    word_count: int | None = None
    characters: list[str] | None = None

    def to_dict(self) -> dict:
        """Convert story to dictionary."""
        return {
            "title": self.title,
            "genre": self.genre,
            "summary": self.summary,
            "word_count": self.word_count or self._calculate_word_count(),
            "characters": self.characters,
            "scenes": [scene.to_dict() for scene in self.scenes],
        }

    def get_characters(self) -> list[str]:
        """
        Get sorted list of unique characters (Dramatis Personae).
        Returns characters sorted by last name.
        """
        if self.characters:
            # Sort by last name (last word in the name)
            return sorted(self.characters, key=lambda name: name.split()[-1])
        return []

    def to_json(self, indent: int = 2) -> str:
        """Convert story to JSON string."""
        return json.dumps(self.to_dict(), indent=indent)

    def to_text(self) -> str:
        """Convert story to plain text format with smart scene breaks."""
        lines = [f"# {self.title}", ""]

        if self.genre:
            lines.append(f"**Genre:** {self.genre}")
        if self.summary:
            lines.append(f"**Summary:** {self.summary}")

        if lines[-1]:  # Add blank line after metadata
            lines.append("")

        # Process scenes with intelligent breaks
        for i, scene in enumerate(self.scenes):
            if i > 0:
                prev_scene = self.scenes[i - 1]

                # Determine what kind of separator to add
                pov_changed = (
                    scene.pov_character != prev_scene.pov_character
                    and scene.pov_character is not None
                    and prev_scene.pov_character is not None
                )

                time_gap = False
                if scene.time_hours is not None and prev_scene.time_hours is not None:
                    time_gap = abs(scene.time_hours - prev_scene.time_hours) > 2.0

                location_changed = (
                    scene.location != prev_scene.location
                    and scene.location is not None
                    and prev_scene.location is not None
                )

                if pov_changed:
                    # Scene break for POV change
                    lines.append("")
                    lines.append("— • —")
                    lines.append("")
                elif time_gap or location_changed:
                    # Blank line for time gap or location change
                    lines.append("")
                # Otherwise just continue as new paragraph (no extra separator)

            # Add scene content (no title or POV display)
            lines.append(scene.content)

        # Add Dramatis Personae at the end if characters are defined
        characters = self.get_characters()
        if characters:
            lines.append("")
            lines.append("")
            lines.append("**Dramatis Personae:**")
            for character in characters:
                lines.append(f"- {character}")

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
        return cls.from_dict(data)

    @classmethod
    def from_dict(cls, data: dict) -> "Story":
        """Create Story from dictionary."""
        scenes = [Scene(**scene_data) for scene_data in data.get("scenes", [])]
        return cls(
            title=data["title"],
            scenes=scenes,
            genre=data.get("genre"),
            summary=data.get("summary"),
            word_count=data.get("word_count"),
            characters=data.get("characters"),
        )
