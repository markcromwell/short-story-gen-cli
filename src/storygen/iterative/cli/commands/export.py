"""
Export commands (epub).
"""

import json
import logging
from pathlib import Path

import click

from storygen.iterative.cli.commands.utils import format_word_count
from storygen.iterative.models import Character, Location, SceneSequel, StoryIdea
from storygen.iterative.project import ProjectManager

# Configure logger
logger = logging.getLogger(__name__)


@click.command()
@click.argument("project")
@click.option(
    "--author",
    default="AI Generated",
    help="Author name for EPUB metadata (default: AI Generated)",
)
@click.option(
    "--publisher",
    help="Publisher name for EPUB metadata",
)
@click.option(
    "--rights",
    help="Copyright/rights text for EPUB metadata",
)
@click.option(
    "--series",
    help="Series name for collection metadata",
)
@click.option(
    "--series-number",
    type=int,
    help="Position in series (requires --series)",
)
@click.option(
    "--include-copyright",
    is_flag=True,
    help="Generate copyright page",
)
@click.option(
    "--isbn",
    help="ISBN for copyright page",
)
@click.option(
    "--edition",
    help="Edition info for copyright page",
)
@click.option(
    "--nav-in-spine/--no-nav-in-spine",
    default=True,
    help="Include nav.xhtml in reading order (default: yes)",
)
@click.option(
    "--style-nav",
    is_flag=True,
    help="Apply CSS styling to navigation",
)
@click.option(
    "--accessible",
    is_flag=True,
    help="Include accessibility metadata",
)
@click.option(
    "--retail-mode",
    type=click.Choice(["none", "kindle", "apple", "kobo"]),
    default="none",
    help="Optimize for specific retailer",
)
@click.option(
    "--title",
    help="Override story title (AI-generated from content if not provided)",
)
@click.option(
    "--chapters",
    type=click.Choice(["numbered", "titled", "sections", "none"]),
    default="numbered",
    help="Chapter style: numbered (Chapter 1), titled (Chapter 1: Title), sections (no chapters), none (single chapter)",
)
@click.option(
    "--chapter-length",
    type=int,
    default=3000,
    help="Target words per chapter for auto-break logic (default: 3000)",
)
@click.option(
    "--force-breaks",
    help="Comma-separated scene-sequel IDs to force chapter breaks (e.g., ss_005,ss_012)",
)
@click.option(
    "--model",
    default="gpt-4",
    help="AI model for title generation (default: gpt-4)",
)
@click.option(
    "-v",
    "--verbose",
    is_flag=True,
    help="Enable verbose output (show chapter decisions)",
)
@click.option(
    "--projects-dir",
    type=click.Path(),
    default="projects",
    help="Root directory for projects (default: projects)",
)
def epub(
    project: str,
    author: str,
    title: str | None,
    chapters: str,
    chapter_length: int,
    force_breaks: str | None,
    model: str,
    verbose: bool,
    projects_dir: str,
    publisher: str | None,
    rights: str | None,
    series: str | None,
    series_number: int | None,
    include_copyright: bool,
    isbn: str | None,
    edition: str | None,
    nav_in_spine: bool,
    style_nav: bool,
    accessible: bool,
    retail_mode: str,
):
    """Generate EPUB for a project with intelligent chapter breaks.

    Takes completed prose and formats it into a polished EPUB file with:
    - AI-generated title (analyzes story content for resonant title)
    - Intelligent chapter break placement (act boundaries, time gaps, POV changes)
    - Scene break formatting (major/minor based on context)
    - Markdown to HTML conversion
    - Table of contents
    - Dramatis personae

    Examples:
        storygen-iter epub necromancer-duel --author "Mark Cromwell"
        storygen-iter epub my-story --chapters titled --chapter-length 2500 -v
        storygen-iter epub fantasy-epic --force-breaks ss_005,ss_012 --title "My Title"
    """
    try:
        # Get project paths
        manager = ProjectManager(Path(projects_dir))
        paths = manager.get_project(project)
        logger.info(f"Generating EPUB for project: {project}")

        # Check required files
        if not paths.prose.exists():
            logger.error(f"Prose file not found: {paths.prose}")
            click.echo("❌ No prose file found", err=True)
            click.echo(f"💡 Run: storygen-iter prose {project}", err=True)
            raise click.Abort()

        if verbose:
            click.echo(f"📖 Project: {project}", err=True)

        # Load input files
        with open(paths.idea, encoding="utf-8") as f:
            idea_data = json.load(f)
        story_idea = StoryIdea.from_dict(idea_data)
        logger.debug(f"Loaded story idea: {story_idea.one_sentence[:50]}...")

        with open(paths.characters, encoding="utf-8") as f:
            chars_data = json.load(f)
        if isinstance(chars_data, list):
            characters = [Character.from_dict(c) for c in chars_data]
        else:
            characters = [Character.from_dict(c) for c in chars_data["characters"]]
        logger.debug(f"Loaded {len(characters)} characters")

        with open(paths.locations, encoding="utf-8") as f:
            locs_data = json.load(f)
        if isinstance(locs_data, list):
            locations = [Location.from_dict(loc) for loc in locs_data]
        else:
            locations = [Location.from_dict(loc) for loc in locs_data["locations"]]
        logger.debug(f"Loaded {len(locations)} locations")

        with open(paths.prose, encoding="utf-8") as f:
            prose_data = json.load(f)

        scene_sequels = [SceneSequel.from_dict(ss) for ss in prose_data["scene_sequels"]]
        total_words = sum(ss.actual_word_count or 0 for ss in scene_sequels)
        logger.info(f"Loaded {len(scene_sequels)} scene-sequels ({total_words} words)")
        click.echo(
            f"✅ Loaded {len(scene_sequels)} scene-sequels ({format_word_count(total_words)} words)",
            err=True,
        )

        # Parse force breaks
        force_break_list = None
        if force_breaks:
            force_break_list = [s.strip() for s in force_breaks.split(",")]
            logger.debug(f"Forcing chapter breaks at: {force_break_list}")
            click.echo(f"🔖 Forcing chapter breaks at: {', '.join(force_break_list)}", err=True)

        # Format EPUB
        click.echo(f"📚 Formatting EPUB with {chapters} chapters...", err=True)

        from storygen.iterative.formatters.epub import EpubFormatter

        formatter = EpubFormatter(
            author=author,
            chapter_style=chapters,  # type: ignore
            target_chapter_length=chapter_length,
            model=model,
            verbose=verbose,
            publisher=publisher,
            rights=rights,
            series=series,
            series_number=series_number,
            include_copyright=include_copyright,
            isbn=isbn,
            edition=edition,
            nav_in_spine=nav_in_spine,
            style_nav=style_nav,
            include_accessibility=accessible,
            retail_mode=retail_mode,  # type: ignore
        )

        epub_path = formatter.format(
            story_idea=story_idea,
            characters=characters,
            locations=locations,
            scene_sequels=scene_sequels,
            output_path=str(paths.epub),
            config_path=paths.config,
            title_override=title,
            force_chapter_breaks=force_break_list,
        )

        logger.info(f"Successfully generated EPUB: {epub_path}")
        click.echo(f"✅ EPUB generated: {epub_path}", err=True)
        click.echo(
            f"📊 {len(scene_sequels)} scenes, {format_word_count(total_words)} words", err=True
        )

    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        click.echo(f"❌ Error: File not found: {e.filename}", err=True)
        raise click.Abort()
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON: {e}")
        click.echo(f"❌ Error: Invalid JSON: {e}", err=True)
        raise click.Abort()
    except Exception as e:
        logger.error(f"Failed to generate EPUB: {e}", exc_info=True)
        click.echo(f"❌ Error: {e}", err=True)
        if verbose:
            import traceback

            traceback.print_exc()
        raise click.Abort()
