"""
Command-line interface for iterative story generation.
"""

import json
from pathlib import Path

import click
from dotenv import load_dotenv

from storygen.iterative.generators.character import CharacterGenerator
from storygen.iterative.generators.idea import IdeaGenerator
from storygen.iterative.models import StoryIdea

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
    "--verbose",
    "-v",
    is_flag=True,
    help="Show detailed generation process",
)
def characters(idea_file: str, model: str, output: str | None, retries: int, verbose: bool):
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
        generator = CharacterGenerator(model=model, max_retries=retries)
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


if __name__ == "__main__":
    cli()
