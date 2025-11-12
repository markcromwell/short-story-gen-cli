"""
Shared utility functions for CLI commands.
"""

import logging
from pathlib import Path

from storygen.iterative.project import ProjectManager

# Configure logger
logger = logging.getLogger(__name__)


def resolve_project_or_path(
    name_or_path: str, file_type: str, projects_dir: str = "projects"
) -> tuple[Path | None, bool]:
    """Resolve a project name or file path.

    Args:
        name_or_path: Either a project name or a file path
        file_type: Type of file (idea, characters, locations, etc.)
        projects_dir: Root directory for projects

    Returns:
        Tuple of (resolved_path, is_project_mode)
        If project doesn't exist, returns (None, False) for direct path mode
    """
    manager = ProjectManager(Path(projects_dir))

    # Check if it's a project name
    if manager.project_exists(name_or_path):
        paths = manager.get_project(name_or_path)
        file_map = {
            "idea": paths.idea,
            "characters": paths.characters,
            "locations": paths.locations,
            "outline": paths.outline,
            "breakdown": paths.breakdown,
            "prose": paths.prose,
            "epub": paths.epub,
        }
        return file_map.get(file_type, Path(name_or_path)), True

    # Otherwise treat as direct path
    return Path(name_or_path), False


def get_default_word_count(story_type: str) -> int:
    """Get default word count for a story type.

    Args:
        story_type: Story type (flash-fiction, short-story, etc.)

    Returns:
        Default word count for that story type
    """
    defaults: dict[str, int] = {
        "flash-fiction": 1000,
        "short-story": 5000,
        "novelette": 12000,
        "novella": 30000,
        "novel": 80000,
    }
    return defaults.get(story_type, 5000)


def format_word_count(count: int) -> str:
    """Format word count with thousands separator.

    Args:
        count: Word count number

    Returns:
        Formatted string like "5,000"
    """
    return f"{count:,}"


def format_list(items: list[str], max_items: int = 3) -> str:
    """Format a list of items for display, truncating if too long.

    Args:
        items: List of items to format
        max_items: Maximum items to show before truncating

    Returns:
        Formatted string like "item1, item2, item3" or "item1, item2, +3 more"
    """
    if len(items) <= max_items:
        return ", ".join(items)
    else:
        shown = ", ".join(items[:max_items])
        remaining = len(items) - max_items
        return f"{shown}, +{remaining} more"


def setup_logging(verbose: bool = False) -> None:
    """Configure logging for CLI commands.

    Args:
        verbose: If True, set DEBUG level; otherwise INFO
    """
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
