"""
Prose generation commands (breakdown, prose).
"""

import json
import logging
from pathlib import Path

import click

from storygen.iterative.cli.commands.utils import format_word_count
from storygen.iterative.constants import DEFAULT_MAX_RETRIES, DEFAULT_TIMEOUT_SECONDS
from storygen.iterative.models import Character, Location, Outline, SceneSequel, StoryIdea
from storygen.iterative.project import ProjectManager

# Configure logger
logger = logging.getLogger(__name__)


@click.command()
@click.argument("project")
@click.option(
    "--model",
    default="gpt-4",
    help='AI model to use (default: gpt-4). Examples: "gpt-4", "ollama/qwen3:30b"',
)
@click.option(
    "--words",
    "target_words",
    type=int,
    default=2000,
    help="Target word count for the story (default: 2000)",
)
@click.option(
    "--retries",
    type=int,
    default=DEFAULT_MAX_RETRIES,
    help=f"Maximum retry attempts (default: {DEFAULT_MAX_RETRIES})",
)
@click.option(
    "--timeout",
    type=int,
    default=DEFAULT_TIMEOUT_SECONDS,
    help=f"Timeout in seconds for AI calls (default: {DEFAULT_TIMEOUT_SECONDS} = 10 minutes)",
)
@click.option(
    "-v",
    "--verbose",
    is_flag=True,
    help="Enable verbose output (show prompts and AI responses)",
)
@click.option(
    "--projects-dir",
    type=click.Path(),
    default="projects",
    help="Root directory for projects (default: projects)",
)
def breakdown(
    project: str,
    model: str,
    target_words: int,
    retries: int,
    timeout: int,
    verbose: bool,
    projects_dir: str,
):
    """Generate scene-sequel breakdown for a project.

    Expands each leaf-level act in the outline into one or more scene-sequel pairs
    with proper goal/conflict/disaster structure (for scenes) and optional
    reaction/dilemma/decision (for sequels).

    Examples:
        storygen-iter breakdown necromancer-duel --words 4000
        storygen-iter breakdown my-story --model ollama/qwen3:30b -v
    """
    try:
        # Get project paths
        manager = ProjectManager(Path(projects_dir))
        paths = manager.get_project(project)
        logger.info(f"Generating breakdown for project: {project}, target: {target_words} words")

        # Check required files
        if not paths.idea.exists():
            logger.error(f"Idea file not found: {paths.idea}")
            click.echo("❌ No idea file found", err=True)
            raise click.Abort()
        if not paths.characters.exists():
            logger.error(f"Characters file not found: {paths.characters}")
            click.echo("❌ No characters file found", err=True)
            raise click.Abort()
        if not paths.locations.exists():
            logger.error(f"Locations file not found: {paths.locations}")
            click.echo("❌ No locations file found", err=True)
            raise click.Abort()
        if not paths.outline.exists():
            logger.error(f"Outline file not found: {paths.outline}")
            click.echo("❌ No outline file found", err=True)
            click.echo(f"💡 Run: storygen-iter outline {project}", err=True)
            raise click.Abort()

        if verbose:
            click.echo(f"📖 Project: {project}", err=True)

        # Load input files
        with open(paths.idea, encoding="utf-8") as f:
            idea_data = json.load(f)
        story_idea = StoryIdea.from_dict(idea_data)
        logger.info(f"Loaded story idea: {story_idea.one_sentence[:50]}...")
        click.echo(f"✅ Loaded idea: {story_idea.one_sentence[:60]}...", err=True)

        with open(paths.characters, encoding="utf-8") as f:
            chars_data = json.load(f)
        # Support both array and object formats
        if isinstance(chars_data, list):
            characters = [Character.from_dict(c) for c in chars_data]
        else:
            characters = [Character.from_dict(c) for c in chars_data["characters"]]
        logger.debug(f"Loaded {len(characters)} characters")
        click.echo(f"✅ Loaded {len(characters)} characters", err=True)

        with open(paths.locations, encoding="utf-8") as f:
            locs_data = json.load(f)
        # Support both array and object formats
        if isinstance(locs_data, list):
            locations = [Location.from_dict(loc) for loc in locs_data]
        else:
            locations = [Location.from_dict(loc) for loc in locs_data["locations"]]
        logger.debug(f"Loaded {len(locations)} locations")
        click.echo(f"✅ Loaded {len(locations)} locations", err=True)

        with open(paths.outline, encoding="utf-8") as f:
            outline_data = json.load(f)
        outline = Outline.from_dict(outline_data)
        logger.debug(f"Loaded outline with {len(outline.acts)} acts")
        click.echo(f"✅ Loaded outline with {len(outline.acts)} acts", err=True)

        # Generate breakdown
        click.echo(f"🤖 Generating scene-sequel breakdown with {model}...", err=True)

        from storygen.iterative.generators.breakdown import BreakdownGenerator

        generator = BreakdownGenerator(
            model=model,
            max_retries=retries,
            timeout=timeout,
            verbose=verbose,
        )

        scene_sequels, usage_info = generator.generate(
            story_idea=story_idea,
            characters=characters,
            locations=locations,
            outline=outline,
            target_words=target_words,
        )

        click.echo(f"✅ Generated {len(scene_sequels)} scene-sequels!", err=True)

        # Save to project
        breakdown_dict = {
            "scene_sequels": [ss.to_dict() for ss in scene_sequels],
            "total_target_words": target_words,
            "story_duration_hours": scene_sequels[-1].end_hours if scene_sequels else 0.0,
        }
        with open(paths.breakdown, "w", encoding="utf-8") as f:
            json.dump(breakdown_dict, f, indent=2, ensure_ascii=False)

        logger.debug(f"Saved breakdown to: {paths.breakdown}")
        click.echo(f"💾 Saved {len(scene_sequels)} scene-sequels to: {paths.breakdown}", err=True)

    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        click.echo(f"❌ Error: File not found: {e.filename}", err=True)
        raise click.Abort()
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON: {e}")
        click.echo(f"❌ Error: Invalid JSON: {e}", err=True)
        raise click.Abort()
    except Exception as e:
        logger.error(f"Failed to generate breakdown: {e}", exc_info=True)
        click.echo(f"❌ Error: {e}", err=True)
        if verbose:
            import traceback

            traceback.print_exc()
        raise click.Abort()


@click.command()
@click.argument("project")
@click.option(
    "--model",
    default="gpt-4",
    help='AI model to use (default: gpt-4). Examples: "gpt-4", "ollama/qwen3:30b"',
)
@click.option(
    "--temperature",
    type=float,
    default=0.7,
    help="Sampling temperature for generation (0.0-1.0, default: 0.7)",
)
@click.option(
    "--writing-style",
    help="Writing style description (auto-inferred from tone/genre if not provided)",
)
@click.option(
    "--context-window",
    type=int,
    default=3,
    help="Number of previous scenes to include in context (default: 3)",
)
@click.option(
    "--retries",
    type=int,
    default=DEFAULT_MAX_RETRIES,
    help=f"Maximum retry attempts (default: {DEFAULT_MAX_RETRIES})",
)
@click.option(
    "--timeout",
    type=int,
    default=DEFAULT_TIMEOUT_SECONDS,
    help=f"Timeout in seconds per scene-sequel (default: {DEFAULT_TIMEOUT_SECONDS}s)",
)
@click.option(
    "-v",
    "--verbose",
    is_flag=True,
    help="Enable verbose output (show prompts and AI responses)",
)
@click.option(
    "--projects-dir",
    type=click.Path(),
    default="projects",
    help="Root directory for projects (default: projects)",
)
def prose(
    project: str,
    model: str,
    temperature: float,
    writing_style: str | None,
    context_window: int,
    retries: int,
    timeout: int,
    verbose: bool,
    projects_dir: str,
):
    """Generate prose for a project with markdown formatting.

    Takes a breakdown of scene-sequels and generates markdown prose for each one,
    maintaining continuity through summaries and key points. Automatically infers
    writing style from the story's tone and genre unless explicitly provided.

    Supports incremental save - if generation fails, you can resume from where it stopped.

    Examples:
        storygen-iter prose necromancer-duel --model ollama/qwen3:30b
        storygen-iter prose my-story --temperature 0.8 --writing-style "Hemingway: terse, direct" -v
    """
    try:
        # Get project paths
        manager = ProjectManager(Path(projects_dir))
        paths = manager.get_project(project)
        logger.info(f"Generating prose for project: {project}")

        # Check required files
        if not paths.breakdown.exists():
            logger.error(f"Breakdown file not found: {paths.breakdown}")
            click.echo("❌ No breakdown file found", err=True)
            click.echo(f"💡 Run: storygen-iter breakdown {project} --words 4000", err=True)
            raise click.Abort()

        if verbose:
            click.echo(f"📖 Project: {project}", err=True)

        # Load input files
        with open(paths.idea, encoding="utf-8") as f:
            idea_data = json.load(f)
        story_idea = StoryIdea.from_dict(idea_data)
        logger.info(f"Loaded story idea: {story_idea.one_sentence[:50]}...")
        click.echo(f"✅ Loaded idea: {story_idea.one_sentence[:60]}...", err=True)

        with open(paths.characters, encoding="utf-8") as f:
            chars_data = json.load(f)
        if isinstance(chars_data, list):
            characters = [Character.from_dict(c) for c in chars_data]
        else:
            characters = [Character.from_dict(c) for c in chars_data["characters"]]
        logger.debug(f"Loaded {len(characters)} characters")
        click.echo(f"✅ Loaded {len(characters)} characters", err=True)

        with open(paths.locations, encoding="utf-8") as f:
            locs_data = json.load(f)
        if isinstance(locs_data, list):
            locations = [Location.from_dict(loc) for loc in locs_data]
        else:
            locations = [Location.from_dict(loc) for loc in locs_data["locations"]]
        logger.debug(f"Loaded {len(locations)} locations")
        click.echo(f"✅ Loaded {len(locations)} locations", err=True)

        # Check if prose file already exists (resume capability)
        if paths.prose.exists():
            logger.info("Found existing prose file, checking for resume capability")
            click.echo("🔄 Found existing prose file, checking for resume...", err=True)
            with open(paths.prose, encoding="utf-8") as f:
                existing_data = json.load(f)
            scene_sequels = [SceneSequel.from_dict(ss) for ss in existing_data["scene_sequels"]]
            completed = sum(1 for ss in scene_sequels if ss.content)
            if completed > 0:
                logger.info(f"Resuming from {completed}/{len(scene_sequels)} completed scenes")
                click.echo(
                    f"✅ Resuming from {completed}/{len(scene_sequels)} completed scenes", err=True
                )
            else:
                # File exists but empty, load from breakdown
                with open(paths.breakdown, encoding="utf-8") as f:
                    breakdown_data = json.load(f)
                scene_sequels = [
                    SceneSequel.from_dict(ss) for ss in breakdown_data["scene_sequels"]
                ]
                logger.debug(f"Loaded {len(scene_sequels)} scene-sequels from breakdown")
                click.echo(f"✅ Loaded {len(scene_sequels)} scene-sequels", err=True)
        else:
            with open(paths.breakdown, encoding="utf-8") as f:
                breakdown_data = json.load(f)
            scene_sequels = [SceneSequel.from_dict(ss) for ss in breakdown_data["scene_sequels"]]
            logger.debug(f"Loaded {len(scene_sequels)} scene-sequels")
            click.echo(f"✅ Loaded {len(scene_sequels)} scene-sequels", err=True)

        # Generate prose
        click.echo(f"🤖 Generating prose with {model} (this may take a while)...", err=True)

        from storygen.iterative.generators.prose import ProseGenerator

        generator = ProseGenerator(
            model=model,
            max_retries=retries,
            timeout=timeout,
            temperature=temperature,
            context_window=context_window,
            verbose=verbose,
        )

        updated_scene_sequels, usage_info = generator.generate(
            story_idea=story_idea,
            characters=characters,
            locations=locations,
            scene_sequels=scene_sequels,
            writing_style=writing_style,
            output_path=str(paths.prose),  # Enable incremental saving
        )

        # Calculate total words
        total_words = sum(ss.actual_word_count or 0 for ss in updated_scene_sequels)
        click.echo(f"✅ Generated {format_word_count(total_words)} words of prose!", err=True)

        # Save to project
        prose_dict = {
            "scene_sequels": [ss.to_dict() for ss in updated_scene_sequels],
            "total_actual_words": total_words,
        }
        with open(paths.prose, "w", encoding="utf-8") as f:
            json.dump(prose_dict, f, indent=2, ensure_ascii=False)

        logger.debug(f"Saved prose to: {paths.prose}")
        click.echo(f"💾 Saved {format_word_count(total_words)} words to: {paths.prose}", err=True)

    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        click.echo(f"❌ Error: File not found: {e.filename}", err=True)
        raise click.Abort()
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON: {e}")
        click.echo(f"❌ Error: Invalid JSON: {e}", err=True)
        raise click.Abort()
    except Exception as e:
        logger.error(f"Failed to generate prose: {e}", exc_info=True)
        click.echo(f"❌ Error: {e}", err=True)
        if verbose:
            import traceback

            traceback.print_exc()
        raise click.Abort()
