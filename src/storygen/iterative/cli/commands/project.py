"""
Project management commands (new, status, projects).
"""

import json
import logging
from datetime import datetime
from pathlib import Path

import click

from storygen.iterative.cli.commands.utils import format_word_count, get_default_word_count
from storygen.iterative.models import StoryConfig
from storygen.iterative.project import ProjectManager

# Configure logger
logger = logging.getLogger(__name__)


@click.command()
@click.argument("name")
@click.option(
    "--pitch",
    "-p",
    help="Story pitch/premise (if not provided, will prompt interactively)",
)
@click.option(
    "--type",
    "-t",
    "story_type",
    type=click.Choice(["flash-fiction", "short-story", "novelette", "novella", "novel"]),
    help="Story length type (if not provided, will prompt interactively)",
)
@click.option(
    "--words",
    "-w",
    type=int,
    help="Target word count (if not provided, will use default for story type)",
)
@click.option(
    "--projects-dir",
    type=click.Path(),
    default="projects",
    help="Root directory for projects (default: projects)",
)
def new(name: str, pitch: str | None, story_type: str | None, words: int | None, projects_dir: str):
    """
    Create a new story project directory.

    Creates a project folder with standardized structure for organizing
    all story generation files (idea, characters, locations, outline, etc.).

    Examples:
        storygen-iter new necromancer-duel --pitch "Two necromancers duel" --type short-story
        storygen-iter new detective-mystery  # Will prompt for all options
        storygen-iter new fantasy-epic --type novel --words 80000
    """
    try:
        manager = ProjectManager(Path(projects_dir))

        # Get pitch if not provided
        if not pitch:
            click.echo("📝 Enter your story pitch/premise:")
            pitch = click.prompt("  ", type=str)

        # Get story type if not provided
        if not story_type:
            click.echo("\n📏 Select story type:")
            click.echo("  1. Flash Fiction (<1,500 words)")
            click.echo("  2. Short Story (1,500-7,500 words)")
            click.echo("  3. Novelette (7,500-17,500 words)")
            click.echo("  4. Novella (17,500-40,000 words)")
            click.echo("  5. Novel (40,000+ words)")
            choice = click.prompt("  Choice", type=click.IntRange(1, 5))
            story_type = ["flash-fiction", "short-story", "novelette", "novella", "novel"][
                choice - 1
            ]

        # Get target words if not provided - use defaults based on type
        if not words:
            words = get_default_word_count(story_type)  # type: ignore[arg-type]
            click.echo(
                f"📊 Using default target: {format_word_count(words)} words for {story_type}"
            )

        # Type checking - at this point all should be set
        assert pitch is not None, "Pitch should be set by now"
        assert story_type is not None, "Story type should be set by now"
        assert words is not None and isinstance(words, int), "Target words should be set by now"

        # Create project
        paths = manager.create_project(name)
        logger.info(f"Created project directory: {paths.root}")

        # Save pitch to old metadata for backwards compatibility
        manager.save_pitch(name, pitch)

        # Create story config
        now = datetime.now().isoformat()
        config = StoryConfig(
            story_type=story_type,  # type: ignore[arg-type]
            target_words=words,
            pitch=pitch,
            created_at=now,
            updated_at=now,
        )

        with open(paths.config, "w", encoding="utf-8") as f:
            json.dump(config.to_dict(), f, indent=2, ensure_ascii=False)

        logger.debug(f"Saved config to {paths.config}")

        click.echo(f"\n✅ Created project: {paths.name}", err=True)
        click.echo(f"📁 Location: {paths.root}", err=True)
        click.echo(f"📏 Type: {config.get_length_category()}", err=True)
        click.echo(f"📊 Target: {format_word_count(words)} words", err=True)
        click.echo(f"💡 Pitch: {pitch}", err=True)
        click.echo("\n🚀 Next steps:", err=True)
        click.echo(f"  storygen-iter idea {name}", err=True)
        click.echo(f"  storygen-iter characters {name}", err=True)
        click.echo(f"  storygen-iter locations {name}", err=True)

    except FileExistsError as e:
        logger.error(f"Project already exists: {e}")
        click.echo(f"❌ Error: {e}", err=True)
        raise click.Abort()
    except Exception as e:
        logger.error(f"Failed to create project: {e}", exc_info=True)
        click.echo(f"❌ Error creating project: {e}", err=True)
        raise


@click.command(name="projects")
@click.option(
    "--projects-dir",
    type=click.Path(),
    default="projects",
    help="Root directory for projects (default: projects)",
)
def list_projects_cmd(projects_dir: str):
    """
    List all story projects.

    Shows all projects in the projects directory with their current status.

    Examples:
        storygen-iter projects
        storygen-iter projects --projects-dir ~/my-stories
    """
    try:
        manager = ProjectManager(Path(projects_dir))
        projects = manager.list_projects()

        if not projects:
            click.echo(f"📁 No projects found in {projects_dir}", err=True)
            click.echo("\n💡 Create a new project with: storygen-iter new <name>", err=True)
            return

        click.echo(f"📚 Projects in {projects_dir}:\n")

        for project_name in sorted(projects):
            try:
                status = manager.get_project_status(project_name)
                pitch = manager.load_pitch(project_name)

                # Count completed stages
                completed = sum(1 for v in status.values() if v)
                total = len(status)

                click.echo(f"  📖 {project_name}")
                if pitch:
                    click.echo(f"     💡 {pitch}")
                click.echo(f"     ✅ {completed}/{total} stages complete")

                # Show which stages are done
                stages = []
                if status["idea"]:
                    stages.append("idea")
                if status["characters"]:
                    stages.append("characters")
                if status["locations"]:
                    stages.append("locations")
                if status["outline"]:
                    stages.append("outline")
                if status["breakdown"]:
                    stages.append("breakdown")
                if status["prose"]:
                    stages.append("prose")
                if status["epub"]:
                    stages.append("epub")

                if stages:
                    click.echo(f"     📋 Completed: {', '.join(stages)}")
                click.echo()

            except Exception as e:
                logger.warning(f"Error reading status for {project_name}: {e}")
                click.echo(f"  ⚠️  {project_name}: Error reading status - {e}")
                click.echo()

    except Exception as e:
        logger.error(f"Failed to list projects: {e}", exc_info=True)
        click.echo(f"❌ Error: {e}", err=True)
        raise


@click.command()
@click.argument("name")
@click.option(
    "--projects-dir",
    type=click.Path(),
    default="projects",
    help="Root directory for projects (default: projects)",
)
def status(name: str, projects_dir: str):
    """
    Show detailed status of a story project.

    Displays which files exist and next steps for the project.

    Examples:
        storygen-iter status necromancer-duel
        storygen-iter status fantasy-epic --projects-dir ~/my-stories
    """
    try:
        manager = ProjectManager(Path(projects_dir))
        paths = manager.get_project(name)
        status_dict = manager.get_project_status(name)

        # Load story config if it exists
        pitch: str | None
        story_type: str
        target_words: int
        length_category: str

        try:
            config = StoryConfig.load(paths.root)
            pitch = config.pitch
            story_type = config.story_type
            target_words = config.target_words
            length_category = config.get_length_category()
        except FileNotFoundError:
            # Fallback to old metadata for backwards compatibility
            logger.debug("Config file not found, using fallback metadata")
            pitch = manager.load_pitch(name)
            story_type = "short-story"  # Default fallback
            target_words = 5000  # Default fallback
            length_category = "Short Story (1,500-7,500 words)"  # Default

        click.echo(f"📖 Project: {name}")
        click.echo(f"📁 Location: {paths.root}")

        if story_type:
            click.echo(f"📏 Type: {length_category}")
            click.echo(f"📊 Target: {format_word_count(target_words)} words")

        click.echo()

        if pitch:
            click.echo(f"💡 Pitch: {pitch}\n")

        # Show title if generated
        try:
            with open(paths.config, encoding="utf-8") as f:
                config_data = json.load(f)
                if config_data.get("title"):
                    click.echo(f"📖 Title: {config_data['title']}\n")
        except (FileNotFoundError, json.JSONDecodeError, KeyError):
            pass

        # Show setting if idea exists
        if status_dict["idea"]:
            try:
                with open(paths.idea, encoding="utf-8") as f:
                    idea_data = json.load(f)
                    if "setting" in idea_data:
                        click.echo(f"🌍 Setting: {idea_data['setting']}\n")
            except (FileNotFoundError, json.JSONDecodeError, KeyError):
                pass

        click.echo("📋 Pipeline Status:")
        stages = [
            ("idea", "Story Idea", paths.idea),
            ("characters", "Characters", paths.characters),
            ("locations", "Locations", paths.locations),
            ("outline", "Outline", paths.outline),
            ("breakdown", "Breakdown", paths.breakdown),
            ("prose", "Prose", paths.prose),
            ("epub", "EPUB", paths.epub),
        ]

        for key, label, path in stages:
            exists = status_dict[key]
            icon = "✅" if exists else "⬜"

            # Special handling for prose to show progress
            if key == "prose" and exists:
                try:
                    with open(paths.prose, encoding="utf-8") as f:
                        prose_data = json.load(f)
                        total = len(prose_data.get("scene_sequels", []))
                        completed = sum(
                            1
                            for ss in prose_data.get("scene_sequels", [])
                            if ss.get("content") and ss["content"].strip()
                        )
                        if completed < total:
                            icon = "🔄"
                            click.echo(
                                f"  {icon} {label:<15} {path.name} ({completed}/{total} scenes)"
                            )
                            continue
                except (FileNotFoundError, json.JSONDecodeError, KeyError):
                    pass

            click.echo(f"  {icon} {label:<15} {path.name}")

        # Suggest next step
        click.echo("\n🚀 Next step:")
        if not status_dict["idea"]:
            click.echo(f"  storygen-iter idea {name}")
        elif not status_dict["characters"]:
            click.echo(f"  storygen-iter characters {name}")
        elif not status_dict["locations"]:
            click.echo(f"  storygen-iter locations {name}")
        elif not status_dict["outline"]:
            click.echo(f"  storygen-iter outline {name}")
        elif not status_dict["breakdown"]:
            click.echo(f"  storygen-iter breakdown {name} --words 4000")
        elif not status_dict["prose"]:
            click.echo(f"  storygen-iter prose {name}")
        elif status_dict["prose"]:
            # Check if prose is partially complete
            try:
                with open(paths.prose, encoding="utf-8") as f:
                    prose_data = json.load(f)
                    total = len(prose_data.get("scene_sequels", []))
                    completed = sum(
                        1
                        for ss in prose_data.get("scene_sequels", [])
                        if ss.get("content") and ss["content"].strip()
                    )
                    if completed < total:
                        click.echo(
                            f"  storygen-iter prose {name}  # Resume: {completed}/{total} scenes complete"
                        )
                        return
            except (FileNotFoundError, json.JSONDecodeError, KeyError):
                pass
            # Prose is complete, check EPUB
            if not status_dict["epub"]:
                click.echo(f"  storygen-iter epub {name}")
            else:
                click.echo(f"  🎉 Project complete! EPUB at: {paths.epub}")

    except FileNotFoundError as e:
        logger.error(f"Project not found: {e}")
        click.echo(f"❌ Error: {e}", err=True)
        click.echo(f"\n💡 Create the project with: storygen-iter new {name}", err=True)
        raise click.Abort()
