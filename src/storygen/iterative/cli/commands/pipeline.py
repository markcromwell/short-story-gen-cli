"""
Pipeline command for running full story generation in one go.
"""

import logging
from pathlib import Path

import click

from storygen.iterative.constants import DEFAULT_MAX_RETRIES, DEFAULT_MODEL, DEFAULT_TIMEOUT_SECONDS
from storygen.iterative.project import ProjectManager

logger = logging.getLogger(__name__)


@click.command()
@click.argument("name")
@click.option("--pitch", required=True, help="Story pitch/concept")
@click.option(
    "--words",
    type=int,
    default=5000,
    help="Target word count (default: 5000)",
)
@click.option(
    "--type",
    "story_type",
    type=click.Choice(["flash-fiction", "short-story", "novelette", "novella", "novel"]),
    default="short-story",
    help="Story length category (default: short-story)",
)
@click.option(
    "--model",
    default=DEFAULT_MODEL,
    help=f"AI model to use (default: {DEFAULT_MODEL})",
)
@click.option(
    "--timeout",
    type=int,
    default=DEFAULT_TIMEOUT_SECONDS,
    help=f"Timeout in seconds per generation step (default: {DEFAULT_TIMEOUT_SECONDS}s)",
)
@click.option(
    "--retries",
    type=int,
    default=DEFAULT_MAX_RETRIES,
    help=f"Maximum retry attempts (default: {DEFAULT_MAX_RETRIES})",
)
@click.option(
    "--projects-dir",
    type=click.Path(),
    default="projects",
    help="Root directory for projects (default: projects)",
)
def generate_all(
    name: str,
    pitch: str,
    words: int,
    story_type: str,
    model: str,
    timeout: int,
    retries: int,
    projects_dir: str,
):
    """
    Generate a complete story from pitch to EPUB in one command.

    Runs the entire pipeline automatically:
    1. Create project
    2. Generate idea
    3. Generate characters
    4. Generate locations
    5. Generate outline
    6. Generate scene-sequel breakdown
    7. Generate prose
    8. Generate EPUB

    Examples:
        storygen-iter all bank-heist --pitch "A sophisticated bank robbery" --words 10000 --model ollama/qwen3:30b
        storygen-iter all fantasy-quest --pitch "A quest for the lost crown" --words 8000
    """
    try:
        import click

        from storygen.iterative.cli.commands import export, generate, project, prose

        click.echo(f"\n🚀 Starting full story generation: {name}")
        click.echo(f"📝 Pitch: {pitch}")
        click.echo(f"📊 Target: {words} words")
        click.echo(f"🤖 Model: {model}")
        click.echo(f"⏱️  Timeout: {timeout}s per step")
        click.echo()

        manager = ProjectManager(Path(projects_dir))

        # Step 1: Create project
        click.echo("=" * 70)
        click.echo("Step 1/8: Creating project...")
        click.echo("=" * 70)
        ctx = click.get_current_context()
        ctx.invoke(
            project.new,
            name=name,
            pitch=pitch,
            words=words,
            story_type=story_type,
            projects_dir=projects_dir,
        )

        # Step 2: Generate idea
        click.echo("\n" + "=" * 70)
        click.echo("Step 2/8: Generating story idea...")
        click.echo("=" * 70)
        ctx.invoke(
            generate.idea,
            prompt_or_project=name,
            model=model,
            output=None,
            retries=retries,
            verbose=False,
            projects_dir=projects_dir,
        )

        # Step 3: Generate characters
        click.echo("\n" + "=" * 70)
        click.echo("Step 3/8: Generating characters...")
        click.echo("=" * 70)
        ctx.invoke(
            generate.characters,
            project=name,
            model=model,
            retries=retries,
            timeout=timeout,
            verbose=False,
            projects_dir=projects_dir,
        )

        # Step 4: Generate locations
        click.echo("\n" + "=" * 70)
        click.echo("Step 4/8: Generating locations...")
        click.echo("=" * 70)
        ctx.invoke(
            generate.locations,
            project=name,
            model=model,
            retries=retries,
            timeout=timeout,
            verbose=False,
            projects_dir=projects_dir,
        )

        # Step 5: Generate outline
        click.echo("\n" + "=" * 70)
        click.echo("Step 5/8: Generating outline...")
        click.echo("=" * 70)
        ctx.invoke(
            generate.outline,
            project=name,
            model=model,
            retries=retries,
            timeout=timeout,
            verbose=False,
            projects_dir=projects_dir,
        )

        # Step 6: Generate breakdown
        click.echo("\n" + "=" * 70)
        click.echo("Step 6/8: Generating scene-sequel breakdown...")
        click.echo("=" * 70)
        ctx.invoke(
            prose.breakdown,
            project=name,
            model=model,
            target_words=words,
            retries=retries,
            timeout=timeout,
            verbose=False,
            projects_dir=projects_dir,
        )

        # Step 7: Generate prose
        click.echo("\n" + "=" * 70)
        click.echo("Step 7/8: Generating prose (this may take a while)...")
        click.echo("=" * 70)
        ctx.invoke(
            prose.prose,
            project=name,
            model=model,
            temperature=0.7,
            writing_style=None,
            context_window=4000,
            retries=retries,
            timeout=timeout,
            verbose=False,
            projects_dir=projects_dir,
        )

        # Step 8: Generate EPUB
        click.echo("\n" + "=" * 70)
        click.echo("Step 8/8: Generating EPUB...")
        click.echo("=" * 70)
        ctx.invoke(
            export.epub,
            project=name,
            author="AI Generated",
            title=None,
            chapters="act",
            chapter_length=2000,
            force_breaks=None,
            model=model,
            verbose=False,
            projects_dir=projects_dir,
        )

        # Success!
        click.echo("\n" + "=" * 70)
        click.echo("🎉 COMPLETE! Story generation finished successfully!")
        click.echo("=" * 70)

        paths = manager.get_project(name)
        epub_path = manager.get_epub_path(name)
        if epub_path:
            click.echo(f"\n📖 EPUB: {epub_path}")
        else:
            click.echo(f"\n📖 EPUB: {paths.root / 'story.epub'}")

        click.echo(f"📁 Project: {paths.root}")
        click.echo(f"\n✅ Run 'storygen-iter status {name}' to see details")

    except click.Abort:
        click.echo("\n❌ Generation aborted by user", err=True)
        raise
    except Exception as e:
        logger.error(f"Pipeline failed: {e}", exc_info=True)
        click.echo(f"\n❌ Pipeline failed at current step: {e}", err=True)
        click.echo("\n💡 You can resume with individual commands:", err=True)
        click.echo(f"   storygen-iter status {name}", err=True)
        raise click.Abort()
