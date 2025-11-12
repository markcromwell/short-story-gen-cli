# CLI Refactoring Plan

## Current State: Monolithic cli.py (1,699 lines)

**Problem**: Single 1,699-line file containing:
- 10+ Click commands
- Project management
- Status display
- Error handling
- Path resolution utilities
- Mixed concerns

**Why This Matters**:
- Hard to navigate (scrolling through 1,700 lines)
- Difficult to test individual commands
- Merge conflicts likely with multiple developers
- Violates Single Responsibility Principle
- Makes new features harder to add

---

## Proposed Structure

```
src/storygen/iterative/
├── cli/
│   ├── __init__.py           # Re-export main CLI group
│   ├── main.py               # Click group, shared utilities, common options
│   ├── commands/
│   │   ├── __init__.py
│   │   ├── project.py        # new, status, list
│   │   ├── generate.py       # idea, characters, locations, outline
│   │   ├── prose.py          # breakdown, prose
│   │   ├── export.py         # title, epub
│   │   └── utils.py          # resolve_project_or_path, etc.
│   └── formatters/           # Move from parent (or keep as-is)
│       ├── __init__.py
│       └── epub.py
```

---

## File Breakdown

### cli/__init__.py (10 lines)
```python
"""Command-line interface for iterative story generation."""

from storygen.iterative.cli.main import cli

__all__ = ["cli"]
```

### cli/main.py (~50 lines)
```python
"""Main CLI entry point and shared utilities."""

import click
from dotenv import load_dotenv

load_dotenv()


@click.group()
def cli():
    """Iterative story generation using Scene-Sequel structure."""
    pass


# Common options (used by multiple commands)
def model_option():
    return click.option(
        "--model",
        "-m",
        default="gpt-4",
        help="AI model to use (e.g., gpt-4, ollama/qwen3:30b)",
    )


def verbose_option():
    return click.option(
        "--verbose",
        "-v",
        is_flag=True,
        help="Show detailed output including prompts and responses",
    )


def projects_dir_option():
    return click.option(
        "--projects-dir",
        type=click.Path(),
        default="projects",
        help="Root directory for projects (default: projects)",
    )


# Register command groups
from storygen.iterative.cli.commands import project, generate, prose, export

cli.add_command(project.new)
cli.add_command(project.status)
cli.add_command(project.list_projects)
cli.add_command(generate.idea)
cli.add_command(generate.characters)
cli.add_command(generate.locations)
cli.add_command(generate.outline)
cli.add_command(prose.breakdown)
cli.add_command(prose.prose_cmd)
cli.add_command(export.title)
cli.add_command(export.epub)


if __name__ == "__main__":
    cli()
```

### cli/commands/utils.py (~100 lines)
```python
"""Shared utilities for CLI commands."""

from pathlib import Path
from typing import Tuple

from storygen.iterative.project import ProjectManager


def resolve_project_or_path(
    name_or_path: str, file_type: str, projects_dir: str = "projects"
) -> Tuple[Path | None, bool]:
    """
    Resolve a project name or file path.

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


def get_story_type_choices():
    """Get list of valid story types."""
    return ["flash-fiction", "short-story", "novelette", "novella", "novel"]


def format_file_size(size: int) -> str:
    """Format file size in human-readable format."""
    for unit in ["B", "KB", "MB", "GB"]:
        if size < 1024.0:
            return f"{size:.1f} {unit}"
        size /= 1024.0
    return f"{size:.1f} TB"


# ... other shared utilities ...
```

### cli/commands/project.py (~200 lines)
```python
"""Project management commands: new, status, list."""

import json
from datetime import datetime
from pathlib import Path

import click

from storygen.iterative.models import StoryConfig
from storygen.iterative.project import ProjectManager


@click.command("new")
@click.argument("name")
@click.option("--pitch", "-p", help="Story pitch/premise")
@click.option("--type", "-t", "story_type",
              type=click.Choice(["flash-fiction", "short-story", "novelette", "novella", "novel"]))
@click.option("--words", "-w", type=int, help="Target word count")
@click.option("--projects-dir", type=click.Path(), default="projects")
def new(name: str, pitch: str | None, story_type: str | None,
        words: int | None, projects_dir: str):
    """
    Create a new story project directory.

    Examples:
        storygen-iter new necromancer-duel --pitch "Two necromancers duel" --type short-story
        storygen-iter new detective-mystery  # Will prompt for all options
    """
    try:
        from storygen.iterative.models import StoryConfig

        manager = ProjectManager(Path(projects_dir))

        # Interactive prompts if not provided
        if not pitch:
            pitch = click.prompt("📝 Story pitch (one sentence)")

        if not story_type:
            click.echo("\n📏 Story length:")
            types = [
                "flash-fiction (<1,500 words)",
                "short-story (1,500-7,500 words)",
                "novelette (7,500-17,500 words)",
                "novella (17,500-40,000 words)",
                "novel (40,000+ words)",
            ]
            for i, t in enumerate(types, 1):
                click.echo(f"  {i}. {t}")
            choice = click.prompt("Choose", type=int, default=2)
            story_type = ["flash-fiction", "short-story", "novelette", "novella", "novel"][choice - 1]

        # Get target words with defaults
        if not words:
            defaults = {
                "flash-fiction": 1000,
                "short-story": 5000,
                "novelette": 12000,
                "novella": 30000,
                "novel": 80000,
            }
            if story_type and story_type in defaults:
                words = defaults[story_type]
            else:
                words = 5000
            click.echo(f"📊 Using default target: {words:,} words for {story_type}")

        # Type assertions
        assert pitch is not None
        assert story_type is not None
        assert words is not None

        # Create project
        paths = manager.create_project(name)

        # Save config
        now = datetime.now().isoformat()
        config = StoryConfig(
            story_type=story_type,
            target_words=words,
            pitch=pitch,
            created_at=now,
            updated_at=now,
        )

        config_path = paths.root / "story_config.json"
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(config.to_dict(), f, indent=2)

        click.echo(f"\n✅ Created project: {name}")
        click.echo(f"📁 Location: {paths.root}")
        click.echo(f"📖 Type: {config.get_length_category()}")
        click.echo(f"🎯 Target: {words:,} words")
        click.echo(f"\n💡 Next step: storygen-iter idea {name}")

    except Exception as e:
        click.echo(f"❌ Error: {str(e)}", err=True)
        raise click.Abort()


@click.command("status")
@click.argument("name")
@click.option("--projects-dir", type=click.Path(), default="projects")
def status(name: str, projects_dir: str):
    """
    Show project status and progress.

    Examples:
        storygen-iter status necromancer-duel
    """
    try:
        # ... existing status implementation ...
        pass
    except Exception as e:
        click.echo(f"❌ Error: {str(e)}", err=True)
        raise click.Abort()


@click.command("list")
@click.option("--projects-dir", type=click.Path(), default="projects")
def list_projects(projects_dir: str):
    """
    List all story projects.

    Example:
        storygen-iter list
    """
    try:
        # ... existing list implementation ...
        pass
    except Exception as e:
        click.echo(f"❌ Error: {str(e)}", err=True)
        raise click.Abort()
```

### cli/commands/generate.py (~400 lines)
```python
"""Content generation commands: idea, characters, locations, outline."""

import json
from pathlib import Path

import click

from storygen.iterative.generators.idea import IdeaGenerator
from storygen.iterative.generators.character import CharacterGenerator
from storygen.iterative.generators.location import LocationGenerator
from storygen.iterative.generators.outline import OutlineGenerator
from storygen.iterative.project import ProjectManager
from storygen.iterative.cli.commands.utils import resolve_project_or_path


@click.command("idea")
@click.argument("name")
@click.option("--model", "-m", default="gpt-4")
@click.option("--verbose", "-v", is_flag=True)
@click.option("--projects-dir", type=click.Path(), default="projects")
def idea(name: str, model: str, verbose: bool, projects_dir: str):
    """
    Generate story idea from project pitch.

    Example:
        storygen-iter idea necromancer-duel
    """
    try:
        # ... existing idea implementation ...
        pass
    except Exception as e:
        click.echo(f"❌ Error: {str(e)}", err=True)
        raise click.Abort()


@click.command("characters")
@click.argument("name")
@click.option("--model", "-m", default="gpt-4")
@click.option("--verbose", "-v", is_flag=True)
@click.option("--projects-dir", type=click.Path(), default="projects")
def characters(name: str, model: str, verbose: bool, projects_dir: str):
    """
    Generate characters for story.

    Example:
        storygen-iter characters necromancer-duel
    """
    try:
        # ... existing characters implementation ...
        pass
    except Exception as e:
        click.echo(f"❌ Error: {str(e)}", err=True)
        raise click.Abort()


@click.command("locations")
@click.argument("name")
@click.option("--model", "-m", default="gpt-4")
@click.option("--verbose", "-v", is_flag=True)
@click.option("--projects-dir", type=click.Path(), default="projects")
def locations(name: str, model: str, verbose: bool, projects_dir: str):
    """
    Generate locations for story.

    Example:
        storygen-iter locations necromancer-duel
    """
    try:
        # ... existing locations implementation ...
        pass
    except Exception as e:
        click.echo(f"❌ Error: {str(e)}", err=True)
        raise click.Abort()


@click.command("outline")
@click.argument("name")
@click.option("--structure", type=click.Choice([...]))
@click.option("--model", "-m", default="gpt-4")
@click.option("--verbose", "-v", is_flag=True)
@click.option("--projects-dir", type=click.Path(), default="projects")
def outline(name: str, structure: str | None, model: str, verbose: bool, projects_dir: str):
    """
    Generate story outline.

    Example:
        storygen-iter outline necromancer-duel --structure three-act
    """
    try:
        # ... existing outline implementation ...
        pass
    except Exception as e:
        click.echo(f"❌ Error: {str(e)}", err=True)
        raise click.Abort()
```

### cli/commands/prose.py (~400 lines)
```python
"""Prose generation commands: breakdown, prose."""

import click

from storygen.iterative.generators.breakdown import BreakdownGenerator
from storygen.iterative.generators.prose import ProseGenerator


@click.command("breakdown")
@click.argument("name")
@click.option("--model", "-m", default="gpt-4")
@click.option("--verbose", "-v", is_flag=True)
@click.option("--projects-dir", type=click.Path(), default="projects")
def breakdown(name: str, model: str, verbose: bool, projects_dir: str):
    """
    Break outline into scene-sequel beats.

    Example:
        storygen-iter breakdown necromancer-duel
    """
    try:
        # ... existing breakdown implementation ...
        pass
    except Exception as e:
        click.echo(f"❌ Error: {str(e)}", err=True)
        raise click.Abort()


@click.command("prose")
@click.argument("name")
@click.option("--model", "-m", default="gpt-4")
@click.option("--verbose", "-v", is_flag=True)
@click.option("--editorial/--no-editorial", default=True)
@click.option("--projects-dir", type=click.Path(), default="projects")
def prose_cmd(name: str, model: str, verbose: bool, editorial: bool, projects_dir: str):
    """
    Generate prose from breakdown.

    Example:
        storygen-iter prose necromancer-duel
    """
    try:
        # ... existing prose implementation ...
        pass
    except Exception as e:
        click.echo(f"❌ Error: {str(e)}", err=True)
        raise click.Abort()
```

### cli/commands/export.py (~200 lines)
```python
"""Export commands: title, epub."""

import click

from storygen.iterative.generators.title import TitleGenerator
from storygen.iterative.formatters.epub import create_epub


@click.command("title")
@click.argument("name")
@click.option("--model", "-m", default="gpt-4")
@click.option("--verbose", "-v", is_flag=True)
@click.option("--projects-dir", type=click.Path(), default="projects")
def title(name: str, model: str, verbose: bool, projects_dir: str):
    """
    Generate story title.

    Example:
        storygen-iter title necromancer-duel
    """
    try:
        # ... existing title implementation ...
        pass
    except Exception as e:
        click.echo(f"❌ Error: {str(e)}", err=True)
        raise click.Abort()


@click.command("epub")
@click.argument("name")
@click.option("--author", default="Anonymous")
@click.option("--output", "-o", type=click.Path())
@click.option("--projects-dir", type=click.Path(), default="projects")
def epub(name: str, author: str, output: str | None, projects_dir: str):
    """
    Generate EPUB from story.

    Example:
        storygen-iter epub necromancer-duel --author "Mark Cromwell"
    """
    try:
        # ... existing epub implementation ...
        pass
    except Exception as e:
        click.echo(f"❌ Error: {str(e)}", err=True)
        raise click.Abort()
```

---

## Migration Strategy

### Phase 1: Setup Structure (30 minutes)
1. Create `cli/` directory
2. Create `cli/__init__.py`, `main.py`
3. Create `cli/commands/` directory
4. Create empty command files

### Phase 2: Extract Utilities (30 minutes)
5. Move `resolve_project_or_path()` to `utils.py`
6. Add other shared utilities
7. Test imports work

### Phase 3: Migrate Commands (2 hours)
8. Start with simplest: `new`, `status`, `list` → `project.py`
9. Test: `storygen-iter new test-proj`
10. Migrate: `idea`, `characters`, `locations`, `outline` → `generate.py`
11. Test each command
12. Migrate: `breakdown`, `prose` → `prose.py`
13. Test
14. Migrate: `title`, `epub` → `export.py`
15. Test

### Phase 4: Wire Up Main (30 minutes)
16. Update `main.py` to import and register all commands
17. Update `cli/__init__.py` to export main cli group
18. Test entire CLI works: `storygen-iter --help`

### Phase 5: Update Imports (30 minutes)
19. Update `setup.py` or `pyproject.toml` entry point if needed
20. Search for any imports of old `cli.py` in tests
21. Update tests to use new structure
22. Run full test suite

### Phase 6: Cleanup (15 minutes)
23. Delete old `cli.py`
24. Commit changes
25. Update documentation

**Total Time**: ~4-6 hours

---

## Benefits

### Before
```
cli.py (1,699 lines)
├── Commands mixed with utilities
├── Hard to navigate
├── Merge conflicts likely
└── Testing individual commands difficult
```

### After
```
cli/
├── main.py (50 lines) - Entry point
├── commands/
│   ├── project.py (200 lines) - Project management
│   ├── generate.py (400 lines) - Content generation
│   ├── prose.py (400 lines) - Prose generation
│   ├── export.py (200 lines) - Export commands
│   └── utils.py (100 lines) - Shared utilities
└── formatters/ (unchanged)
```

✅ **Each file has single responsibility**
✅ **Easy to find specific commands**
✅ **Easy to test individual command groups**
✅ **Reduce merge conflicts**
✅ **New commands go in appropriate file**
✅ **Shared utilities centralized**

---

## Testing Strategy

### Unit Tests (New)
```python
# tests/unit/cli/test_project_commands.py
def test_new_command_creates_project():
    runner = CliRunner()
    result = runner.invoke(new, ["test-proj", "--pitch", "Test", "--type", "short-story"])
    assert result.exit_code == 0
    assert "Created project" in result.output

# tests/unit/cli/test_generate_commands.py
def test_idea_command_generates_idea():
    # ... test idea command ...

# tests/unit/cli/test_utils.py
def test_resolve_project_or_path():
    # ... test utility functions ...
```

### Integration Tests (Existing)
- Keep existing integration tests in `tests/integration/`
- They should continue working without changes
- Just update imports if needed

---

## Rollback Plan

If something goes wrong:
1. Git has full history - easy to revert
2. Tests will catch any issues immediately
3. Can merge files back together if needed (but shouldn't be necessary)

---

## Conclusion

This refactor will make the CLI codebase **significantly more maintainable** while keeping all functionality intact. The modular structure makes it easy to:
- Find specific commands
- Add new commands
- Test individual components
- Onboard new developers
- Reduce merge conflicts

**Recommended**: Do this refactor before adding research/worldbuilding commands from TODO.md
