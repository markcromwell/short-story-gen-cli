"""
Generation commands (idea, characters, locations, outline).
"""

import json
import logging
from pathlib import Path

import click

from storygen.iterative.constants import DEFAULT_MAX_RETRIES, DEFAULT_TIMEOUT_SECONDS
from storygen.iterative.generators.character import CharacterGenerator
from storygen.iterative.generators.idea import IdeaGenerator
from storygen.iterative.generators.location import LocationGenerator
from storygen.iterative.generators.outline import OutlineGenerator
from storygen.iterative.models import Act, Character, Location, StoryIdea
from storygen.iterative.outline_templates import list_available_structures
from storygen.iterative.project import ProjectManager

# Configure logger
logger = logging.getLogger(__name__)


@click.command()
@click.argument("prompt_or_project")
@click.option(
    "--model",
    default="gpt-4",
    help="AI model to use (e.g., gpt-4, claude-3-sonnet, ollama/qwen3:30b)",
)
@click.option(
    "--output",
    "-o",
    type=click.Path(),
    help="Save idea to JSON file (default: uses project path or stdout)",
)
@click.option(
    "--retries",
    default=3,
    help="Maximum retry attempts on failure (default: 3)",
)
@click.option(
    "--verbose",
    "-v",
    is_flag=True,
    help="Show detailed generation process",
)
@click.option(
    "--projects-dir",
    type=click.Path(),
    default="projects",
    help="Root directory for projects (default: projects)",
)
def idea(
    prompt_or_project: str,
    model: str,
    output: str | None,
    retries: int,
    verbose: bool,
    projects_dir: str,
):
    """
    Generate a story idea from a PROMPT or for a PROJECT.

    The AI will expand your prompt into a complete story idea with:
    - One-sentence hook
    - Expanded description (2-3 paragraphs)
    - Genres
    - Tone
    - Major themes
    - Setting (time and place)

    Examples:
        # Project mode (uses saved pitch)
        storygen-iter idea necromancer-duel

        # Direct prompt mode
        storygen-iter idea "A detective solves her own murder"
        storygen-iter idea "A robot learns to love" --model ollama/qwen3:30b
        storygen-iter idea "A wizard after the apocalypse" -o my_idea.json
        storygen-iter idea "Space station horror" --verbose
    """
    try:
        # Check if prompt_or_project is a project name
        manager = ProjectManager(Path(projects_dir))
        is_project = manager.project_exists(prompt_or_project)

        story_type = "short-story"  # Default for direct prompt mode

        if is_project:
            # Project mode - load config and pitch
            from storygen.iterative.models import StoryConfig

            paths = manager.get_project(prompt_or_project)
            logger.info(f"Operating in project mode: {prompt_or_project}")

            # Load story config
            try:
                config = StoryConfig.load(paths.root)
                story_type = config.story_type
                prompt = config.pitch
                logger.debug(f"Loaded config: story_type={story_type}")
            except FileNotFoundError:
                # Fallback to old metadata.json for backwards compatibility
                logger.warning("No story_config.json found, falling back to metadata.json")
                loaded_prompt = manager.load_pitch(prompt_or_project)
                if not loaded_prompt:
                    logger.error(f"No pitch found for project: {prompt_or_project}")
                    click.echo(f"❌ No pitch found for project '{prompt_or_project}'", err=True)
                    click.echo(
                        "💡 Add a pitch to metadata.json or use direct prompt mode", err=True
                    )
                    raise click.Abort()
                prompt = loaded_prompt

            # Use project idea path if no output specified
            if not output:
                output = str(paths.idea)

            if verbose:
                click.echo(f"📖 Project: {prompt_or_project}", err=True)
                click.echo(f"📏 Story type: {story_type}", err=True)
                click.echo(f"💡 Pitch: {prompt}", err=True)
        else:
            # Direct prompt mode
            logger.info("Operating in direct prompt mode")
            prompt = prompt_or_project

        logger.info(f"Generating idea with model: {model}")
        if verbose:
            click.echo(f"🎨 Generating story idea with {model}...", err=True)
            click.echo(f"📝 Prompt: {prompt}", err=True)

        # Generate idea
        generator = IdeaGenerator(model=model, max_retries=retries, verbose=verbose)
        click.echo(f"🤖 Generating story idea with {model}...", err=True)
        story_idea, usage_info = generator.generate(prompt, story_type=story_type)
        click.echo("✅ Story idea generated successfully!", err=True)

        logger.info(f"Successfully generated story idea: {story_idea.one_sentence[:50]}...")
        if verbose:
            click.echo(f"📚 Genres: {', '.join(story_idea.genres)}", err=True)
            click.echo(f"🎭 Themes: {', '.join(story_idea.themes)}", err=True)
            click.echo(f"🌍 Setting: {story_idea.setting}", err=True)

        # Output
        if output:
            output_path = Path(output)
            output_path.parent.mkdir(parents=True, exist_ok=True)

            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(story_idea.to_dict(), f, indent=2, ensure_ascii=False)

            logger.debug(f"Saved idea to: {output_path}")
            click.echo(f"💾 Saved to: {output_path}", err=True)
        else:
            # Pretty print to stdout
            click.echo("\n" + "=" * 70)
            click.echo("📖 ONE-SENTENCE HOOK")
            click.echo("=" * 70)
            click.echo(story_idea.one_sentence)

            click.echo("\n" + "=" * 70)
            click.echo("📝 EXPANDED DESCRIPTION")
            click.echo("=" * 70)
            click.echo(story_idea.expanded)

            click.echo("\n" + "=" * 70)
            click.echo("📊 METADATA")
            click.echo("=" * 70)
            click.echo(f"Genres: {', '.join(story_idea.genres)}")
            click.echo(f"Tone: {story_idea.tone}")
            click.echo(f"Themes: {', '.join(story_idea.themes)}")
            click.echo(f"Setting: {story_idea.setting}")
            click.echo("=" * 70 + "\n")

    except Exception as e:
        logger.error(f"Failed to generate idea: {e}", exc_info=True)
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
    help="AI model to use (e.g., gpt-4, claude-3-sonnet, ollama/qwen3:30b)",
)
@click.option(
    "--retries",
    default=DEFAULT_MAX_RETRIES,
    help=f"Maximum retry attempts on failure (default: {DEFAULT_MAX_RETRIES})",
)
@click.option(
    "--timeout",
    default=DEFAULT_TIMEOUT_SECONDS,
    help=f"Timeout in seconds for AI generation (default: {DEFAULT_TIMEOUT_SECONDS} = 10 minutes)",
)
@click.option(
    "--verbose",
    "-v",
    is_flag=True,
    help="Show detailed generation process",
)
@click.option(
    "--projects-dir",
    type=click.Path(),
    default="projects",
    help="Root directory for projects (default: projects)",
)
def characters(
    project: str, model: str, retries: int, timeout: int, verbose: bool, projects_dir: str
):
    """
    Generate characters for a project.

    Generates 1-3 core characters with genre-appropriate names:
    - 1 protagonist (required)
    - Optional antagonist (if central to story)
    - Supporting characters as needed

    Each character has: name, role, bio, goal, flaw, and optional arc.

    Examples:
        storygen-iter characters necromancer-duel
        storygen-iter characters my-story --model ollama/qwen3:30b
        storygen-iter characters fantasy-epic --verbose
    """
    try:
        # Get project paths
        from storygen.iterative.models import StoryConfig

        manager = ProjectManager(Path(projects_dir))
        paths = manager.get_project(project)
        logger.info(f"Generating characters for project: {project}")

        # Load story config
        try:
            config = StoryConfig.load(paths.root)
            story_type = config.story_type
            logger.debug(f"Loaded config: story_type={story_type}")
        except FileNotFoundError:
            story_type = "short-story"  # Fallback for old projects
            logger.warning("No story_config.json found, using default: short-story")
            if verbose:
                click.echo("⚠️  No story_config.json found, using default: short-story", err=True)

        # Check if idea exists
        if not paths.idea.exists():
            logger.error(f"Idea file not found: {paths.idea}")
            click.echo(f"❌ No idea file found for project '{project}'", err=True)
            click.echo(f"💡 Run: storygen-iter idea {project}", err=True)
            raise click.Abort()

        # Load story idea
        if verbose:
            click.echo(f"📖 Project: {project}", err=True)
            click.echo(f"📏 Story type: {story_type}", err=True)
            click.echo(f"📄 Loading story idea from {paths.idea}...", err=True)

        with open(paths.idea, encoding="utf-8") as f:
            idea_data = json.load(f)
        story_idea = StoryIdea.from_dict(idea_data)

        logger.info(f"Loaded story idea: {story_idea.one_sentence[:50]}...")
        if verbose:
            click.echo(f"✅ Loaded: {story_idea.one_sentence[:60]}...", err=True)
            click.echo(f"🎨 Generating characters with {model}...", err=True)

        # Generate characters
        generator = CharacterGenerator(
            model=model, max_retries=retries, timeout=timeout, verbose=verbose
        )
        click.echo(f"🤖 Generating characters with {model}...", err=True)
        characters_list, usage_info = generator.generate(story_idea, story_type=story_type)
        click.echo(f"✅ Generated {len(characters_list)} characters!", err=True)

        # Save to project
        characters_data = [char.to_dict() for char in characters_list]
        with open(paths.characters, "w", encoding="utf-8") as f:
            json.dump(characters_data, f, indent=2, ensure_ascii=False)

        logger.debug(f"Saved characters to: {paths.characters}")
        click.echo(f"💾 Saved {len(characters_list)} characters to: {paths.characters}", err=True)

    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        click.echo(f"❌ Error: {e}", err=True)
        raise click.Abort()
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON: {e}")
        click.echo(f"❌ Error: Invalid JSON: {e}", err=True)
        raise click.Abort()
    except Exception as e:
        logger.error(f"Failed to generate characters: {e}", exc_info=True)
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
    help="AI model to use (default: gpt-4)",
)
@click.option(
    "--retries",
    default=DEFAULT_MAX_RETRIES,
    help=f"Maximum retry attempts on failure (default: {DEFAULT_MAX_RETRIES})",
)
@click.option(
    "--timeout",
    default=DEFAULT_TIMEOUT_SECONDS,
    help=f"Timeout in seconds for AI generation (default: {DEFAULT_TIMEOUT_SECONDS} = 10 minutes)",
)
@click.option(
    "--verbose",
    "-v",
    is_flag=True,
    help="Show detailed generation process",
)
@click.option(
    "--projects-dir",
    type=click.Path(),
    default="projects",
    help="Root directory for projects (default: projects)",
)
def locations(
    project: str, model: str, retries: int, timeout: int, verbose: bool, projects_dir: str
):
    """
    Generate locations for a project.

    Generates 3-7 key locations including:
    - Name and physical description
    - Significance to the story
    - Atmosphere and mood

    Each location is vivid, atmospheric, and serves narrative needs.

    Examples:
        storygen-iter locations necromancer-duel
        storygen-iter locations my-story --model ollama/qwen3:30b
        storygen-iter locations fantasy-epic --timeout 300 --verbose
    """
    try:
        # Get project paths
        from storygen.iterative.models import StoryConfig

        manager = ProjectManager(Path(projects_dir))
        paths = manager.get_project(project)
        logger.info(f"Generating locations for project: {project}")

        # Load story config
        try:
            config = StoryConfig.load(paths.root)
            story_type = config.story_type
            logger.debug(f"Loaded config: story_type={story_type}")
        except FileNotFoundError:
            story_type = "short-story"  # Fallback for old projects
            logger.warning("No story_config.json found, using default: short-story")
            if verbose:
                click.echo("⚠️  No story_config.json found, using default: short-story", err=True)

        # Check if idea exists
        if not paths.idea.exists():
            logger.error(f"Idea file not found: {paths.idea}")
            click.echo(f"❌ No idea file found for project '{project}'", err=True)
            click.echo(f"💡 Run: storygen-iter idea {project}", err=True)
            raise click.Abort()

        # Load story idea
        if verbose:
            click.echo(f"📖 Project: {project}", err=True)
            click.echo(f"📏 Story type: {story_type}", err=True)
            click.echo(f"📄 Loading story idea from {paths.idea}...", err=True)

        with open(paths.idea, encoding="utf-8") as f:
            idea_data = json.load(f)
        story_idea = StoryIdea.from_dict(idea_data)

        logger.info(f"Loaded story idea: {story_idea.one_sentence[:50]}...")
        if verbose:
            click.echo(f"✅ Loaded: {story_idea.one_sentence[:60]}...", err=True)
            click.echo(f"🗺️  Generating locations with {model}...", err=True)

        # Generate locations
        generator = LocationGenerator(
            model=model, max_retries=retries, timeout=timeout, verbose=verbose
        )
        click.echo(f"🤖 Generating locations with {model}...", err=True)
        locations_list, usage_info = generator.generate(story_idea, story_type=story_type)
        click.echo(f"✅ Generated {len(locations_list)} locations!", err=True)

        # Save to project
        locations_dicts = [loc.to_dict() for loc in locations_list]
        with open(paths.locations, "w", encoding="utf-8") as f:
            json.dump(locations_dicts, f, indent=2, ensure_ascii=False)

        logger.debug(f"Saved locations to: {paths.locations}")
        click.echo(f"💾 Saved {len(locations_list)} locations to: {paths.locations}", err=True)

    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        click.echo(f"❌ Error: {e}", err=True)
        raise click.Abort()
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON: {e}")
        click.echo(f"❌ Error: Invalid JSON: {e}", err=True)
        raise click.Abort()
    except Exception as e:
        logger.error(f"Failed to generate locations: {e}", exc_info=True)
        click.echo(f"❌ Error: {e}", err=True)
        if verbose:
            import traceback

            traceback.print_exc()
        raise click.Abort()


def _print_act_tree(act: Act, indent: int = 0, is_last: bool = True, prefix: str = ""):
    """
    Recursively print act tree with indentation.

    Args:
        act: The act to print
        indent: Current indentation level
        is_last: Whether this is the last sibling
        prefix: Accumulated prefix for tree lines
    """
    # Determine tree characters
    if indent == 0:
        connector = ""
        new_prefix = ""
    else:
        connector = "└── " if is_last else "├── "
        new_prefix = prefix + ("    " if is_last else "│   ")

    # Print act title with percentage
    percentage_str = f"{int(act.percentage * 100)}%"
    click.echo(f"{prefix}{connector}{act.title} ({percentage_str})")

    # Print description (generic template description)
    desc_indent = new_prefix if indent > 0 else "    "
    if act.description:
        click.echo(f"{desc_indent}📝 Template: {act.description}")

    # Print story_application (AI-generated specific application)
    if act.story_application:
        # Wrap long text
        story_lines = act.story_application.split("\n")
        for line in story_lines:
            click.echo(f"{desc_indent}💡 Story: {line}")

    click.echo()  # Blank line after each act

    # Recursively print sub-acts
    if act.sub_acts:
        for i, sub_act in enumerate(act.sub_acts):
            _print_act_tree(sub_act, indent + 1, i == len(act.sub_acts) - 1, new_prefix)


def _print_outline_tree(outline):
    """Print an outline in a tree structure to the console."""
    click.echo("\n" + "=" * 70)
    click.echo(f"📝 STORY OUTLINE: {outline.structure_type.upper()}")
    click.echo("=" * 70 + "\n")

    for i, act in enumerate(outline.acts):
        _print_act_tree(act, indent=0, is_last=i == len(outline.acts) - 1)

    click.echo("=" * 70 + "\n")


@click.command()
@click.argument("project")
@click.option(
    "--structure",
    "-s",
    default="three-act",
    help="Outline structure type: three-act, hero-journey, fichtean (default: three-act)",
)
@click.option(
    "--model",
    default="gpt-4",
    help="AI model to use (default: gpt-4)",
)
@click.option(
    "--retries",
    default=DEFAULT_MAX_RETRIES,
    help=f"Maximum retry attempts on failure (default: {DEFAULT_MAX_RETRIES})",
)
@click.option(
    "--timeout",
    default=DEFAULT_TIMEOUT_SECONDS,
    help=f"Timeout in seconds for AI generation (default: {DEFAULT_TIMEOUT_SECONDS} = 10 minutes)",
)
@click.option(
    "--verbose",
    "-v",
    is_flag=True,
    help="Show detailed generation process",
)
@click.option(
    "--projects-dir",
    type=click.Path(),
    default="projects",
    help="Root directory for projects (default: projects)",
)
def outline(
    project: str,
    structure: str,
    model: str,
    retries: int,
    timeout: int,
    verbose: bool,
    projects_dir: str,
):
    """
    Generate a story outline for a project.

    Creates a structured outline from idea, characters, and locations.
    Supports multiple templates:
    - three-act: Traditional 3-act structure with 7 beats
    - hero-journey: Hero's Journey with 12 stages
    - fichtean: Fichtean Curve with 6 crisis-driven beats

    The AI fills in story_application for each act based on your specific story.

    Examples:
        storygen-iter outline necromancer-duel
        storygen-iter outline my-story --structure hero-journey
        storygen-iter outline fantasy-epic --model ollama/qwen3:30b -v
    """
    try:
        # Get project paths
        manager = ProjectManager(Path(projects_dir))
        paths = manager.get_project(project)
        logger.info(f"Generating outline for project: {project}, structure: {structure}")

        # Check required files exist
        if not paths.idea.exists():
            logger.error(f"Idea file not found: {paths.idea}")
            click.echo("❌ No idea file found", err=True)
            click.echo(f"💡 Run: storygen-iter idea {project}", err=True)
            raise click.Abort()
        if not paths.characters.exists():
            logger.error(f"Characters file not found: {paths.characters}")
            click.echo("❌ No characters file found", err=True)
            click.echo(f"💡 Run: storygen-iter characters {project}", err=True)
            raise click.Abort()
        if not paths.locations.exists():
            logger.error(f"Locations file not found: {paths.locations}")
            click.echo("❌ No locations file found", err=True)
            click.echo(f"💡 Run: storygen-iter locations {project}", err=True)
            raise click.Abort()

        # Validate structure type
        available = list_available_structures()
        if structure not in available:
            logger.error(f"Invalid structure type: {structure}")
            click.echo(
                f"❌ Error: Unknown structure type '{structure}'. "
                f"Available: {', '.join(available)}",
                err=True,
            )
            raise click.Abort()

        if verbose:
            click.echo(f"📖 Project: {project}", err=True)

        # Load story idea
        with open(paths.idea, encoding="utf-8") as f:
            idea_data = json.load(f)
        story_idea = StoryIdea.from_dict(idea_data)

        logger.info(f"Loaded story idea: {story_idea.one_sentence[:50]}...")
        if verbose:
            click.echo(f"✅ Loaded idea: {story_idea.one_sentence[:60]}...", err=True)

        # Load characters
        with open(paths.characters, encoding="utf-8") as f:
            characters_data = json.load(f)
        characters = [Character.from_dict(char) for char in characters_data]

        logger.debug(f"Loaded {len(characters)} characters")
        if verbose:
            click.echo(f"✅ Loaded {len(characters)} characters", err=True)

        # Load locations
        with open(paths.locations, encoding="utf-8") as f:
            locations_data = json.load(f)
        locations = [Location.from_dict(loc) for loc in locations_data]

        logger.debug(f"Loaded {len(locations)} locations")
        if verbose:
            click.echo(f"✅ Loaded {len(locations)} locations", err=True)
            click.echo(f"📝 Generating {structure} outline with {model}...", err=True)

        # Generate outline
        generator = OutlineGenerator(
            model=model,
            structure_type=structure,
            max_retries=retries,
            timeout=timeout,
            verbose=verbose,
        )
        click.echo(f"🤖 Generating {structure} outline with {model}...", err=True)
        story_outline, usage_info = generator.generate(story_idea, characters, locations)
        click.echo(f"✅ Generated {structure} outline!", err=True)

        # Save to project
        outline_dict = story_outline.to_dict()
        with open(paths.outline, "w", encoding="utf-8") as f:
            json.dump(outline_dict, f, indent=2, ensure_ascii=False)

        logger.debug(f"Saved outline to: {paths.outline}")
        click.echo(f"💾 Saved outline to: {paths.outline}", err=True)

        # Print outline tree
        _print_outline_tree(story_outline)

    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        click.echo(f"❌ Error: {e}", err=True)
        raise click.Abort()
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON: {e}")
        click.echo(f"❌ Error: Invalid JSON: {e}", err=True)
        raise click.Abort()
    except Exception as e:
        logger.error(f"Failed to generate outline: {e}", exc_info=True)
        click.echo(f"❌ Error: {e}", err=True)
        if verbose:
            import traceback

            traceback.print_exc()
        raise click.Abort()
