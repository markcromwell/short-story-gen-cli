"""Project management for organizing story generation files."""

import json
from dataclasses import dataclass
from pathlib import Path


@dataclass
class ProjectPaths:
    """Standard file paths for a story project."""

    root: Path
    config: Path
    idea: Path
    characters: Path
    locations: Path
    outline: Path
    breakdown: Path
    prose: Path
    epub: Path

    @property
    def name(self) -> str:
        """Get project name from root directory."""
        return self.root.name


class ProjectManager:
    """Manages story project directory structure and file paths."""

    def __init__(self, projects_dir: Path = Path("projects")):
        """Initialize project manager.

        Args:
            projects_dir: Root directory for all projects (default: "projects")
        """
        self.projects_dir = projects_dir

    def create_project(self, name: str) -> ProjectPaths:
        """Create a new project directory structure.

        Args:
            name: Project name (will be used as directory name)

        Returns:
            ProjectPaths with all standard file paths

        Raises:
            FileExistsError: If project directory already exists
        """
        project_root = self.projects_dir / name

        if project_root.exists():
            raise FileExistsError(f"Project '{name}' already exists at {project_root}")

        # Create project directory
        project_root.mkdir(parents=True, exist_ok=False)

        return self.get_project(name)

    def get_project(self, name: str) -> ProjectPaths:
        """Get file paths for an existing project.

        Args:
            name: Project name

        Returns:
            ProjectPaths with all standard file paths

        Raises:
            FileNotFoundError: If project directory doesn't exist
        """
        project_root = self.projects_dir / name

        if not project_root.exists():
            raise FileNotFoundError(f"Project '{name}' not found at {project_root}")

        return ProjectPaths(
            root=project_root,
            config=project_root / "story_config.json",
            idea=project_root / "idea.json",
            characters=project_root / "characters.json",
            locations=project_root / "locations.json",
            outline=project_root / "outline.json",
            breakdown=project_root / "breakdown.json",
            prose=project_root / "prose.json",
            epub=project_root / "story.epub",
        )

    def list_projects(self) -> list[str]:
        """List all existing projects.

        Returns:
            List of project names
        """
        if not self.projects_dir.exists():
            return []

        return [
            d.name for d in self.projects_dir.iterdir() if d.is_dir() and not d.name.startswith(".")
        ]

    def project_exists(self, name: str) -> bool:
        """Check if a project exists.

        Args:
            name: Project name

        Returns:
            True if project directory exists
        """
        return (self.projects_dir / name).exists()

    def get_project_status(self, name: str) -> dict[str, bool]:
        """Check which files exist in a project.

        Args:
            name: Project name

        Returns:
            Dictionary mapping file type to existence status

        Raises:
            FileNotFoundError: If project doesn't exist
        """
        paths = self.get_project(name)

        return {
            "idea": paths.idea.exists(),
            "characters": paths.characters.exists(),
            "locations": paths.locations.exists(),
            "outline": paths.outline.exists(),
            "breakdown": paths.breakdown.exists(),
            "prose": paths.prose.exists(),
            "epub": paths.epub.exists(),
        }

    def save_pitch(self, name: str, pitch: str) -> None:
        """Save a pitch to project metadata.

        Args:
            name: Project name
            pitch: Story pitch text

        Raises:
            FileNotFoundError: If project doesn't exist
        """
        paths = self.get_project(name)
        metadata_path = paths.root / "metadata.json"

        metadata = {"pitch": pitch}

        with metadata_path.open("w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2)

    def load_pitch(self, name: str) -> str | None:
        """Load pitch from project metadata.

        Args:
            name: Project name

        Returns:
            Pitch text if it exists, None otherwise

        Raises:
            FileNotFoundError: If project doesn't exist
        """
        paths = self.get_project(name)
        metadata_path = paths.root / "metadata.json"

        if not metadata_path.exists():
            return None

        with metadata_path.open("r", encoding="utf-8") as f:
            metadata = json.load(f)
            pitch = metadata.get("pitch")
            return str(pitch) if pitch is not None else None

    def backup_file(self, file_path: Path) -> Path | None:
        """Create a timestamped backup of a file before overwriting.

        Args:
            file_path: Path to file to backup

        Returns:
            Path to backup file, or None if original doesn't exist
        """
        if not file_path.exists():
            return None

        from datetime import datetime

        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        backup_path = file_path.with_suffix(f".backup-{timestamp}{file_path.suffix}")

        # Copy the file
        import shutil

        shutil.copy2(file_path, backup_path)
        return backup_path

    def get_file_mtime(self, file_path: Path) -> float | None:
        """Get modification time of a file.

        Args:
            file_path: Path to file

        Returns:
            Modification timestamp, or None if file doesn't exist
        """
        if not file_path.exists():
            return None
        return file_path.stat().st_mtime

    def check_dependencies(self, name: str) -> dict[str, list[str]]:
        """Check which files need regeneration based on modification times.

        Dependency chain:
        - idea -> characters, locations, outline
        - characters, locations -> outline
        - outline -> breakdown
        - breakdown -> prose
        - prose -> epub

        Args:
            name: Project name

        Returns:
            Dictionary mapping file type to list of reasons it needs regeneration
        """
        paths = self.get_project(name)
        needs_regen: dict[str, list[str]] = {}

        # Get modification times
        idea_time = self.get_file_mtime(paths.idea)
        chars_time = self.get_file_mtime(paths.characters)
        locs_time = self.get_file_mtime(paths.locations)
        outline_time = self.get_file_mtime(paths.outline)
        breakdown_time = self.get_file_mtime(paths.breakdown)
        prose_time = self.get_file_mtime(paths.prose)

        # Check idea -> characters/locations
        if idea_time:
            if chars_time and idea_time > chars_time:
                needs_regen.setdefault("characters", []).append("idea.json was modified")
            if locs_time and idea_time > locs_time:
                needs_regen.setdefault("locations", []).append("idea.json was modified")

        # Check characters/locations -> outline
        if chars_time and outline_time and chars_time > outline_time:
            needs_regen.setdefault("outline", []).append("characters.json was modified")
        if locs_time and outline_time and locs_time > outline_time:
            needs_regen.setdefault("outline", []).append("locations.json was modified")
        if idea_time and outline_time and idea_time > outline_time:
            needs_regen.setdefault("outline", []).append("idea.json was modified")

        # Check outline -> breakdown
        if outline_time and breakdown_time and outline_time > breakdown_time:
            needs_regen.setdefault("breakdown", []).append("outline.json was modified")

        # Check breakdown -> prose
        if breakdown_time and prose_time and breakdown_time > prose_time:
            needs_regen.setdefault("prose", []).append("breakdown.json was modified")

        # Cascade: if outline needs regen, so do breakdown and prose
        if "outline" in needs_regen:
            if breakdown_time:
                needs_regen.setdefault("breakdown", []).append("outline needs regeneration")
            if prose_time:
                needs_regen.setdefault("prose", []).append("outline needs regeneration")

        # If breakdown needs regen, so does prose
        if "breakdown" in needs_regen:
            if prose_time:
                needs_regen.setdefault("prose", []).append("breakdown needs regeneration")

        return needs_regen
