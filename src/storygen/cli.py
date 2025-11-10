"""
Command-line interface for story generation
"""

import click
from dotenv import load_dotenv

from storygen.generator import StoryGenerator

# Load environment variables (for API keys)
load_dotenv()


@click.command()
@click.argument("prompt")
@click.option(
    "--provider",
    default="gpt-3.5-turbo",
    help="AI provider to use (e.g., gpt-4, claude-3-sonnet, ollama/llama2)",
)
@click.option("--max-tokens", default=1000, help="Maximum length of the generated story")
@click.option(
    "--structured",
    is_flag=True,
    help="Generate structured story with title, scenes, and metadata (JSON format)",
)
@click.option(
    "--format",
    type=click.Choice(["text", "json"], case_sensitive=False),
    default="text",
    help="Output format for structured stories (default: text)",
)
@click.option(
    "--epub",
    type=str,
    metavar="FILENAME",
    help="Generate EPUB file from structured story (implies --structured)",
)
@click.option(
    "--author",
    type=str,
    default="AI Generated",
    help="Author name for EPUB metadata (default: 'AI Generated')",
)
@click.option(
    "--min-words",
    type=int,
    help="Minimum word count to request from AI (e.g., 1000, 2000, 5000)",
)
@click.option(
    "--pov",
    type=click.Choice(
        [
            "first_person",
            "first_person_plural",
            "second_person",
            "third_person_limited",
            "third_person_deep",
            "third_person_omniscient",
            "third_person_objective",
            "multiple_pov",
            "epistolary",
            "free_indirect",
            "stream_of_consciousness",
        ],
        case_sensitive=False,
    ),
    default="third_person_deep",
    help="Point of view/narrative perspective (default: third_person_deep)",
)
@click.option(
    "--structure",
    type=click.Choice(
        [
            "three_act",
            "freytag",
            "heros_journey",
            "fichtean",
            "seven_point",
            "ai_choice",
        ],
        case_sensitive=False,
    ),
    default="three_act",
    help="Story structure to follow (default: three_act)",
)
@click.option(
    "--verbose",
    is_flag=True,
    help="Show detailed debug information (prompts, responses, token usage)",
)
def main(
    prompt: str,
    provider: str,
    max_tokens: int,
    structured: bool,
    min_words: int | None,
    format: str,
    epub: str | None,
    author: str,
    pov: str,
    structure: str,
    verbose: bool,
):
    """
    Generate a short story from a PROMPT using AI.

    Examples:
        storygen "A robot learns to paint"
        storygen --provider xai/grok-2-1212 "A space adventure"
        storygen --structured "A mystery story"
        storygen --structured --format json "A time travel tale" > story.json
        storygen --epub my_story.epub "A magical adventure"
        storygen --epub story.epub --author "John Doe" "A sci-fi tale"
        storygen --structured --min-words 2000 "A detailed fantasy epic"
        storygen --structured --pov first_person "A detective's case"
        storygen --epub story.epub --pov multiple_pov "A thriller with shifting perspectives"
        storygen --epub heist.epub --structure fichtean "A bank heist gone wrong"
        storygen --structure heros_journey --min-words 3000 "A reluctant hero's quest"
        storygen --structure ai_choice "A mysterious disappearance" (AI picks best structure)

    Free/Local providers:
        - ollama/llama2 (requires local Ollama installation)
        - ollama/mistral

    Premium providers:
        - xai/grok-2-1212, xai/grok-beta (requires XAI_API_KEY - fast & cheap!)
        - gpt-4, gpt-3.5-turbo (requires OPENAI_API_KEY)
        - claude-3-sonnet, claude-3-opus (requires ANTHROPIC_API_KEY)
    """
    try:
        # EPUB generation implies structured mode
        if epub:
            structured = True

        mode = "structured" if structured else "plain"
        if not verbose:
            click.echo(f"🎨 Generating {mode} story with {provider}...", err=True)
            click.echo(err=True)

        generator = StoryGenerator(provider=provider, verbose=verbose)

        if structured:
            # Let generate_structured auto-scale max_tokens based on min_words
            # Default is 4000 tokens, scales up if min_words is specified
            story_obj = generator.generate_structured(
                prompt, min_words=min_words, pov=pov, structure=structure
            )

            # Generate EPUB if requested
            if epub:
                from pathlib import Path

                from storygen.epub import generate_epub

                # Ensure output directory exists
                output_dir = Path("output")
                output_dir.mkdir(exist_ok=True)

                # Determine output path - prepend output/ if not already a path
                epub_path_obj = Path(epub)
                if len(epub_path_obj.parts) == 1:  # Just a filename, no directory
                    epub_path_obj = output_dir / epub

                # Check if file exists and create unique name if needed
                if epub_path_obj.exists():
                    stem = epub_path_obj.stem
                    suffix = epub_path_obj.suffix
                    counter = 1
                    while epub_path_obj.exists():
                        epub_path_obj = epub_path_obj.parent / f"{stem}_{counter}{suffix}"
                        counter += 1
                    click.echo(f"⚠️  File exists, using: {epub_path_obj.name}", err=True)

                epub_path = generate_epub(story_obj, str(epub_path_obj), author=author)
                click.echo(f"📚 EPUB generated: {epub_path}", err=True)

            # Also output the story (unless only EPUB was requested)
            if format == "json":
                click.echo(story_obj.to_json())
            else:
                click.echo(story_obj.to_text())
        else:
            story = generator.generate(prompt, max_tokens=max_tokens, pov=pov, structure=structure)
            click.echo(story)

        if not verbose:
            click.echo(err=True)
            click.echo("✅ Story generated successfully!", err=True)

    except Exception as e:
        click.echo(f"❌ Error: {e}", err=True)
        raise click.Abort()


if __name__ == "__main__":
    main()
