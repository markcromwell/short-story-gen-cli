"""
Command-line interface for iterative story generation.
"""

import json
from pathlib import Path

import click
from dotenv import load_dotenv

from storygen.iterative.generators.character import CharacterGenerator
from storygen.iterative.generators.idea import IdeaGenerator
from storygen.iterative.generators.location import LocationGenerator
from storygen.iterative.generators.outline import OutlineGenerator
from storygen.iterative.models import Act, Character, Location, StoryIdea
from storygen.iterative.outline_templates import list_available_structures

# Load environment variables (for API keys)
load_dotenv()


@click.group()
def cli():
    """Iterative story generation using Scene-Sequel structure."""
    pass


@cli.command()
@click.argument("prompt")
@click.option(
    "--model",
    default="gpt-4",
    help="AI model to use (e.g., gpt-4, claude-3-sonnet, ollama/qwen3:30b)",
)
@click.option(
    "--output",
    "-o",
    type=click.Path(),
    help="Save idea to JSON file (default: print to stdout)",
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
def idea(prompt: str, model: str, output: str | None, retries: int, verbose: bool):
    """
    Generate a story idea from a PROMPT.

    The AI will expand your prompt into a complete story idea with:
    - One-sentence hook
    - Expanded description (2-3 paragraphs)
    - Genres
    - Tone
    - Major themes

    Examples:
        storygen-iter idea "A detective solves her own murder"
        storygen-iter idea "A robot learns to love" --model ollama/qwen3:30b
        storygen-iter idea "A wizard after the apocalypse" -o my_idea.json
        storygen-iter idea "Space station horror" --verbose
    """
    try:
        if verbose:
            click.echo(f"🎨 Generating story idea with {model}...", err=True)
            click.echo(f"📝 Prompt: {prompt}", err=True)

        # Generate idea
        generator = IdeaGenerator(model=model, max_retries=retries)
        story_idea = generator.generate(prompt)

        if verbose:
            click.echo("✅ Story idea generated successfully!", err=True)
            click.echo(f"📚 Genres: {', '.join(story_idea.genres)}", err=True)
            click.echo(f"🎭 Themes: {', '.join(story_idea.themes)}", err=True)

        # Output
        if output:
            output_path = Path(output)
            output_path.parent.mkdir(parents=True, exist_ok=True)

            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(story_idea.to_dict(), f, indent=2, ensure_ascii=False)

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
            click.echo("=" * 70 + "\n")

    except Exception as e:
        click.echo(f"❌ Error: {e}", err=True)
        if verbose:
            import traceback

            traceback.print_exc()
        raise click.Abort()


@cli.command()
@click.option(
    "--idea-file",
    "-i",
    type=click.Path(exists=True),
    required=True,
    help="JSON file with story idea (from 'idea' command)",
)
@click.option(
    "--model",
    default="gpt-4",
    help="AI model to use (e.g., gpt-4, claude-3-sonnet, ollama/qwen3:30b)",
)
@click.option(
    "--output",
    "-o",
    type=click.Path(),
    help="Save characters to JSON file (default: print to stdout)",
)
@click.option(
    "--retries",
    default=3,
    help="Maximum retry attempts on failure (default: 3)",
)
@click.option(
    "--timeout",
    default=60,
    help="Timeout in seconds for AI generation (default: 60)",
)
@click.option(
    "--verbose",
    "-v",
    is_flag=True,
    help="Show detailed generation process",
)
def characters(
    idea_file: str, model: str, output: str | None, retries: int, timeout: int, verbose: bool
):
    """
    Generate characters based on a story idea.

    Takes a story idea JSON file and generates 3-5 characters including:
    - 1 protagonist
    - 1 antagonist
    - Supporting characters (mentor, ally, foil, etc.)

    Each character has: name, role, bio, goal, flaw, and optional arc.

    Examples:
        storygen-iter characters --idea-file my_idea.json
        storygen-iter characters -i idea.json --model ollama/qwen3:30b
        storygen-iter characters -i idea.json -o characters.json
        storygen-iter characters -i idea.json --verbose
    """
    try:
        # Load story idea
        if verbose:
            click.echo(f"📖 Loading story idea from {idea_file}...", err=True)

        with open(idea_file, encoding="utf-8") as f:
            idea_data = json.load(f)
        story_idea = StoryIdea.from_dict(idea_data)

        if verbose:
            click.echo(f"✅ Loaded: {story_idea.one_sentence[:60]}...", err=True)
            click.echo(f"🎨 Generating characters with {model}...", err=True)

        # Generate characters
        generator = CharacterGenerator(model=model, max_retries=retries, timeout=timeout)
        characters_list = generator.generate(story_idea)

        if verbose:
            click.echo(f"✅ Generated {len(characters_list)} characters!", err=True)

        # Output
        if output:
            output_path = Path(output)
            output_path.parent.mkdir(parents=True, exist_ok=True)

            characters_data = [char.to_dict() for char in characters_list]
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(characters_data, f, indent=2, ensure_ascii=False)

            click.echo(f"💾 Saved {len(characters_list)} characters to: {output_path}", err=True)
        else:
            # Pretty print to stdout
            click.echo("\n" + "=" * 70)
            click.echo(f"👥 CHARACTERS ({len(characters_list)} generated)")
            click.echo("=" * 70)

            for i, char in enumerate(characters_list, 1):
                click.echo(f"\n{i}. {char.name} ({char.role.upper()})")
                click.echo("-" * 70)
                click.echo(f"Bio: {char.bio}")
                click.echo(f"Goal: {char.goal}")
                click.echo(f"Flaw: {char.flaw}")
                if char.arc:
                    click.echo(f"Arc: {char.arc}")

            click.echo("\n" + "=" * 70 + "\n")

    except FileNotFoundError:
        click.echo(f"❌ Error: File not found: {idea_file}", err=True)
        raise click.Abort()
    except json.JSONDecodeError as e:
        click.echo(f"❌ Error: Invalid JSON in {idea_file}: {e}", err=True)
        raise click.Abort()
    except Exception as e:
        click.echo(f"❌ Error: {e}", err=True)
        if verbose:
            import traceback

            traceback.print_exc()
        raise click.Abort()


@cli.command()
@click.option(
    "--idea-file",
    "-i",
    required=True,
    help="Path to story idea JSON file",
)
@click.option(
    "--model",
    default="gpt-4",
    help="AI model to use (default: gpt-4)",
)
@click.option(
    "--output",
    "-o",
    default=None,
    help="Output JSON file path (default: print to console)",
)
@click.option(
    "--retries",
    default=3,
    help="Maximum retry attempts on failure (default: 3)",
)
@click.option(
    "--timeout",
    default=60,
    help="Timeout in seconds for AI generation (default: 60)",
)
@click.option(
    "--verbose",
    "-v",
    is_flag=True,
    help="Show detailed generation process",
)
def locations(
    idea_file: str, model: str, output: str | None, retries: int, timeout: int, verbose: bool
):
    """
    Generate locations based on a story idea.

    Takes a story idea JSON file and generates 3-7 key locations including:
    - Name and physical description
    - Significance to the story
    - Atmosphere and mood

    Each location is vivid, atmospheric, and serves narrative needs.

    Examples:
        storygen-iter locations --idea-file my_idea.json
        storygen-iter locations -i idea.json --model ollama/qwen3:30b
        storygen-iter locations -i idea.json -o locations.json
        storygen-iter locations -i idea.json --timeout 300 --verbose
    """
    try:
        # Load story idea
        if verbose:
            click.echo(f"📖 Loading story idea from {idea_file}...", err=True)

        with open(idea_file, encoding="utf-8") as f:
            idea_data = json.load(f)
        story_idea = StoryIdea.from_dict(idea_data)

        if verbose:
            click.echo(f"✅ Loaded: {story_idea.one_sentence[:60]}...", err=True)
            click.echo(f"🗺️  Generating locations with {model}...", err=True)

        # Generate locations
        generator = LocationGenerator(model=model, max_retries=retries, timeout=timeout)
        locations_list = generator.generate(story_idea)

        if verbose:
            click.echo(f"✅ Generated {len(locations_list)} locations!", err=True)

        # Output results
        if output:
            # Save to JSON file
            locations_dicts = [loc.to_dict() for loc in locations_list]
            output_path = Path(output)
            output_path.parent.mkdir(parents=True, exist_ok=True)

            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(locations_dicts, f, indent=2, ensure_ascii=False)

            click.echo(f"💾 Saved to: {output}")
        else:
            # Pretty print to console
            click.echo("\n" + "=" * 70)
            click.echo(f"🗺️  LOCATIONS ({len(locations_list)} generated)")
            click.echo("=" * 70 + "\n")

            for i, loc in enumerate(locations_list, 1):
                click.echo(f"{i}. {loc.name}")
                click.echo("-" * 70)
                click.echo(f"Description: {loc.description}")
                click.echo(f"Significance: {loc.significance}")
                click.echo(f"Atmosphere: {loc.atmosphere}")
                click.echo()

            click.echo("=" * 70 + "\n")

    except FileNotFoundError:
        click.echo(f"❌ Error: File not found: {idea_file}", err=True)
        raise click.Abort()
    except json.JSONDecodeError as e:
        click.echo(f"❌ Error: Invalid JSON in {idea_file}: {e}", err=True)
        raise click.Abort()
    except Exception as e:
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


@cli.command()
@click.option(
    "--idea-file",
    "-i",
    required=True,
    help="Path to story idea JSON file",
)
@click.option(
    "--characters-file",
    "-c",
    required=True,
    help="Path to characters JSON file",
)
@click.option(
    "--locations-file",
    "-l",
    required=True,
    help="Path to locations JSON file",
)
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
    "--output",
    "-o",
    default=None,
    help="Output JSON file path (default: print to console)",
)
@click.option(
    "--retries",
    default=3,
    help="Maximum retry attempts on failure (default: 3)",
)
@click.option(
    "--timeout",
    default=60,
    help="Timeout in seconds for AI generation (default: 60)",
)
@click.option(
    "--verbose",
    "-v",
    is_flag=True,
    help="Show detailed generation process",
)
def outline(
    idea_file: str,
    characters_file: str,
    locations_file: str,
    structure: str,
    model: str,
    output: str | None,
    retries: int,
    timeout: int,
    verbose: bool,
):
    """
    Generate a story outline with flexible structure types.

    Takes a story idea, characters, and locations to create a structured
    outline. Supports multiple templates:
    - three-act: Traditional 3-act structure with 7 beats
    - hero-journey: Hero's Journey with 12 stages
    - fichtean: Fichtean Curve with 6 crisis-driven beats

    The AI fills in story_application for each act based on your specific story.

    Examples:
        storygen-iter outline -i idea.json -c chars.json -l locs.json
        storygen-iter outline -i idea.json -c chars.json -l locs.json --structure hero-journey
        storygen-iter outline -i idea.json -c chars.json -l locs.json --model ollama/qwen3:30b
        storygen-iter outline -i idea.json -c chars.json -l locs.json -o outline.json -v
    """
    try:
        # Validate structure type
        available = list_available_structures()
        if structure not in available:
            click.echo(
                f"❌ Error: Unknown structure type '{structure}'. "
                f"Available: {', '.join(available)}",
                err=True,
            )
            raise click.Abort()

        # Load story idea
        if verbose:
            click.echo(f"📖 Loading story idea from {idea_file}...", err=True)

        with open(idea_file, encoding="utf-8") as f:
            idea_data = json.load(f)
        story_idea = StoryIdea.from_dict(idea_data)

        if verbose:
            click.echo(f"✅ Loaded idea: {story_idea.one_sentence[:60]}...", err=True)

        # Load characters
        if verbose:
            click.echo(f"👥 Loading characters from {characters_file}...", err=True)

        with open(characters_file, encoding="utf-8") as f:
            characters_data = json.load(f)
        characters = [Character.from_dict(char) for char in characters_data]

        if verbose:
            click.echo(f"✅ Loaded {len(characters)} characters", err=True)

        # Load locations
        if verbose:
            click.echo(f"🗺️  Loading locations from {locations_file}...", err=True)

        with open(locations_file, encoding="utf-8") as f:
            locations_data = json.load(f)
        locations = [Location.from_dict(loc) for loc in locations_data]

        if verbose:
            click.echo(f"✅ Loaded {len(locations)} locations", err=True)
            click.echo(f"📝 Generating {structure} outline with {model}...", err=True)

        # Generate outline
        generator = OutlineGenerator(
            model=model, structure_type=structure, max_retries=retries, timeout=timeout
        )
        story_outline = generator.generate(story_idea, characters, locations)

        if verbose:
            click.echo(f"✅ Generated {structure} outline!", err=True)

        # Output results
        if output:
            # Save to JSON file
            outline_dict = story_outline.to_dict()
            output_path = Path(output)
            output_path.parent.mkdir(parents=True, exist_ok=True)

            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(outline_dict, f, indent=2, ensure_ascii=False)

            click.echo(f"💾 Saved to: {output}")
        else:
            # Pretty print to console with tree structure
            _print_outline_tree(story_outline)

    except FileNotFoundError as e:
        click.echo(f"❌ Error: File not found: {e.filename}", err=True)
        raise click.Abort()
    except json.JSONDecodeError as e:
        click.echo(f"❌ Error: Invalid JSON: {e}", err=True)
        raise click.Abort()
    except Exception as e:
        click.echo(f"❌ Error: {e}", err=True)
        if verbose:
            import traceback

            traceback.print_exc()
        raise click.Abort()


if __name__ == "__main__":
    cli()
