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
def main(prompt: str, provider: str, max_tokens: int):
    """
    Generate a short story from a PROMPT using AI.

    Examples:
        storygen "A robot learns to paint"
        storygen --provider xai/grok-2-1212 "A space adventure"
        storygen --provider claude-3-sonnet "A mystery story"
        storygen --provider ollama/llama2 "A time travel tale"

    Free/Local providers:
        - ollama/llama2 (requires local Ollama installation)
        - ollama/mistral

    Premium providers:
        - xai/grok-2-1212, xai/grok-beta (requires XAI_API_KEY - fast & cheap!)
        - gpt-4, gpt-3.5-turbo (requires OPENAI_API_KEY)
        - claude-3-sonnet, claude-3-opus (requires ANTHROPIC_API_KEY)
    """
    try:
        click.echo(f"🎨 Generating story with {provider}...")
        click.echo()

        generator = StoryGenerator(provider=provider)
        story = generator.generate(prompt, max_tokens=max_tokens)

        click.echo(story)
        click.echo()
        click.echo("✅ Story generated successfully!")

    except Exception as e:
        click.echo(f"❌ Error: {e}", err=True)
        raise click.Abort()


if __name__ == "__main__":
    main()
