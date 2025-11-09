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
def main(prompt: str, provider: str, max_tokens: int, structured: bool, format: str):
    """
    Generate a short story from a PROMPT using AI.

    Examples:
        storygen "A robot learns to paint"
        storygen --provider xai/grok-2-1212 "A space adventure"
        storygen --structured "A mystery story"
        storygen --structured --format json "A time travel tale" > story.json

    Free/Local providers:
        - ollama/llama2 (requires local Ollama installation)
        - ollama/mistral

    Premium providers:
        - xai/grok-2-1212, xai/grok-beta (requires XAI_API_KEY - fast & cheap!)
        - gpt-4, gpt-3.5-turbo (requires OPENAI_API_KEY)
        - claude-3-sonnet, claude-3-opus (requires ANTHROPIC_API_KEY)
    """
    try:
        mode = "structured" if structured else "plain"
        click.echo(f"🎨 Generating {mode} story with {provider}...", err=True)
        click.echo(err=True)

        generator = StoryGenerator(provider=provider)

        if structured:
            # Use higher token limit for structured stories
            story_obj = generator.generate_structured(prompt, max_tokens=max(max_tokens, 2000))

            if format == "json":
                click.echo(story_obj.to_json())
            else:
                click.echo(story_obj.to_text())
        else:
            story = generator.generate(prompt, max_tokens=max_tokens)
            click.echo(story)

        click.echo(err=True)
        click.echo("✅ Story generated successfully!", err=True)

    except Exception as e:
        click.echo(f"❌ Error: {e}", err=True)
        raise click.Abort()


if __name__ == "__main__":
    main()
