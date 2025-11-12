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
from storygen.iterative.models import Act, Character, Location, Outline, StoryIdea
from storygen.iterative.outline_templates import list_available_structures
from storygen.iterative.project import ProjectManager

# Load environment variables (for API keys)
load_dotenv()


def resolve_project_or_path(
    name_or_path: str, file_type: str, projects_dir: str = "projects"
) -> tuple[Path | None, bool]:
    """Resolve a project name or file path.

    Args:
        name_or_path: Either a project name or a file path
        file_type: Type of file (idea, characters, locations, etc.)
        projects_dir: Root directory for projects

    Returns:
        Tuple of (resolved_path, is_project_mode)
        If project doesn't exist, returns (None, False) for direct path mode
    """
    manager = ProjectManager(Path(projects_dir))

    # Check if it's a project name
    if manager.project_exists(name_or_path):
        paths = manager.get_project(name_or_path)
        file_map = {
            "idea": paths.idea,
            "characters": paths.characters,
            "locations": paths.locations,
            "outline": paths.outline,
            "breakdown": paths.breakdown,
            "prose": paths.prose,
            "epub": paths.epub,
        }
        return file_map.get(file_type, Path(name_or_path)), True

    # Otherwise treat as direct path
    return Path(name_or_path), False


@click.group()
def cli():
    """Iterative story generation using Scene-Sequel structure."""
    pass


@cli.command()
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
        from datetime import datetime

        from storygen.iterative.models import StoryConfig

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
            defaults = {
                "flash-fiction": 1000,
                "short-story": 5000,
                "novelette": 12000,
                "novella": 30000,
                "novel": 80000,
            }
            words = defaults[story_type]
            click.echo(f"📊 Using default target: {words:,} words for {story_type}")

        # Type checking - at this point all should be set
        assert pitch is not None, "Pitch should be set by now"
        assert story_type is not None, "Story type should be set by now"
        assert words is not None and isinstance(words, int), "Target words should be set by now"

        # Create project
        paths = manager.create_project(name)

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

        click.echo(f"\n✅ Created project: {paths.name}", err=True)
        click.echo(f"📁 Location: {paths.root}", err=True)
        click.echo(f"📏 Type: {config.get_length_category()}", err=True)
        click.echo(f"📊 Target: {words:,} words", err=True)
        click.echo(f"💡 Pitch: {pitch}", err=True)
        click.echo("\n🚀 Next steps:", err=True)
        click.echo(f"  storygen-iter idea {name}", err=True)
        click.echo(f"  storygen-iter characters {name}", err=True)
        click.echo(f"  storygen-iter locations {name}", err=True)

    except FileExistsError as e:
        click.echo(f"❌ Error: {e}", err=True)
        raise click.Abort()
    except Exception as e:
        click.echo(f"❌ Error creating project: {e}", err=True)
        raise


@cli.command(name="projects")
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
                click.echo(f"  ⚠️  {project_name}: Error reading status - {e}")
                click.echo()

    except Exception as e:
        click.echo(f"❌ Error: {e}", err=True)
        raise


@cli.command()
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
        from storygen.iterative.models import StoryConfig

        manager = ProjectManager(Path(projects_dir))
        paths = manager.get_project(name)
        status_dict = manager.get_project_status(name)

        # Load story config if it exists
        try:
            config = StoryConfig.load(paths.root)
            pitch = config.pitch
            story_type = config.story_type
            target_words = config.target_words
        except FileNotFoundError:
            # Fallback to old metadata for backwards compatibility
            pitch = manager.load_pitch(name)
            story_type = None  # type: ignore
            target_words = None  # type: ignore

        click.echo(f"📖 Project: {name}")
        click.echo(f"📁 Location: {paths.root}")

        if story_type:
            click.echo(f"📏 Type: {config.get_length_category()}")
            click.echo(f"📊 Target: {target_words:,} words")

        click.echo()

        if pitch:
            click.echo(f"💡 Pitch: {pitch}\n")

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
        elif not status_dict["epub"]:
            click.echo(f"  storygen-iter epub {name}")
        else:
            click.echo(f"  🎉 Project complete! EPUB at: {paths.epub}")

    except FileNotFoundError as e:
        click.echo(f"❌ Error: {e}", err=True)
        click.echo(f"\n💡 Create the project with: storygen-iter new {name}", err=True)
        raise click.Abort()
    except Exception as e:
        click.echo(f"❌ Error: {e}", err=True)
        raise


@cli.command()
@click.argument("project")
@click.option(
    "--model",
    default="gpt-4",
    help="AI model to use for all stages (default: gpt-4)",
)
@click.option(
    "--words",
    type=int,
    default=4000,
    help="Target word count for the story (default: 4000)",
)
@click.option(
    "--structure",
    default="three-act",
    help="Outline structure: three-act, hero-journey, fichtean (default: three-act)",
)
@click.option(
    "--writing-style",
    help="Writing style description (auto-inferred if not provided)",
)
@click.option(
    "--author",
    default="AI Generated",
    help="Author name for EPUB (default: AI Generated)",
)
@click.option(
    "--from-stage",
    type=click.Choice(["idea", "characters", "locations", "outline", "breakdown", "prose", "epub"]),
    help="Resume from specific stage (skips earlier stages)",
)
@click.option(
    "--check-deps",
    is_flag=True,
    help="Check for file changes and regenerate dependencies",
)
@click.option(
    "--backup",
    is_flag=True,
    default=True,
    help="Create backups before overwriting files (default: True)",
)
@click.option(
    "-v",
    "--verbose",
    is_flag=True,
    help="Show detailed progress",
)
@click.option(
    "--projects-dir",
    type=click.Path(),
    default="projects",
    help="Root directory for projects (default: projects)",
)
def generate(
    project: str,
    model: str,
    words: int,
    structure: str,
    writing_style: str | None,
    author: str,
    from_stage: str | None,
    check_deps: bool,
    backup: bool,
    verbose: bool,
    projects_dir: str,
):
    """
    Generate complete story from idea to EPUB.

    Runs the full pipeline or resumes from a specific stage. Can detect
    file changes and regenerate dependencies automatically.

    Examples:
        # Full pipeline from pitch
        storygen-iter generate necromancer-duel --model ollama/qwen3:30b --words 4000

        # Resume from outline stage
        storygen-iter generate necromancer-duel --from-stage outline

        # Check dependencies and regenerate what's needed
        storygen-iter generate necromancer-duel --check-deps -v
    """
    try:
        manager = ProjectManager(Path(projects_dir))
        paths = manager.get_project(project)

        # Check dependencies if requested
        if check_deps:
            needs_regen = manager.check_dependencies(project)
            if needs_regen:
                click.echo("⚠️  Dependency check found changes:\n", err=True)
                for file_type, reasons in needs_regen.items():
                    click.echo(f"  📄 {file_type}:", err=True)
                    for reason in reasons:
                        click.echo(f"     - {reason}", err=True)
                click.echo("\n🔄 Will regenerate affected files with backups\n", err=True)

        # Define pipeline stages
        stages = ["idea", "characters", "locations", "outline", "breakdown", "prose", "epub"]

        # Determine starting stage
        start_idx = 0
        if from_stage:
            start_idx = stages.index(from_stage)
            click.echo(f"▶️  Starting from stage: {from_stage}\n", err=True)

        status_dict = manager.get_project_status(project)
        ctx = click.get_current_context()

        # Run pipeline
        for stage in stages[start_idx:]:
            # Skip if exists and not in needs_regen (unless from_stage specified)
            if status_dict.get(stage) and not check_deps:
                if from_stage is None:
                    click.echo(f"⏭️  Skipping {stage} (already exists)", err=True)
                    continue

            # Check if in needs_regen
            skip_stage = False
            if check_deps and stage not in needs_regen and status_dict.get(stage):
                click.echo(f"⏭️  Skipping {stage} (up to date)", err=True)
                skip_stage = True

            if skip_stage:
                continue

            # Backup if overwriting
            if backup and status_dict.get(stage):
                file_map = {
                    "idea": paths.idea,
                    "characters": paths.characters,
                    "locations": paths.locations,
                    "outline": paths.outline,
                    "breakdown": paths.breakdown,
                    "prose": paths.prose,
                    "epub": paths.epub,
                }
                backup_path = manager.backup_file(file_map[stage])
                if backup_path:
                    click.echo(f"💾 Backed up {stage} to: {backup_path.name}", err=True)

            # Run stage
            click.echo(f"\n{'='*60}", err=True)
            click.echo(f"▶️  Stage: {stage.upper()}", err=True)
            click.echo(f"{'='*60}\n", err=True)

            if stage == "idea":
                ctx.invoke(
                    idea,
                    prompt_or_project=project,
                    model=model,
                    output=None,
                    retries=3,
                    verbose=verbose,
                    projects_dir=projects_dir,
                )
            elif stage == "characters":
                ctx.invoke(
                    characters,
                    project=project,
                    model=model,
                    retries=3,
                    timeout=300,
                    verbose=verbose,
                    projects_dir=projects_dir,
                )
            elif stage == "locations":
                ctx.invoke(
                    locations,
                    project=project,
                    model=model,
                    retries=3,
                    timeout=300,
                    verbose=verbose,
                    projects_dir=projects_dir,
                )
            elif stage == "outline":
                ctx.invoke(
                    outline,
                    project=project,
                    structure=structure,
                    model=model,
                    retries=3,
                    timeout=300,
                    verbose=verbose,
                    projects_dir=projects_dir,
                )
            elif stage == "breakdown":
                ctx.invoke(
                    breakdown,
                    project=project,
                    model=model,
                    target_words=words,
                    retries=3,
                    timeout=600,
                    verbose=verbose,
                    projects_dir=projects_dir,
                )
            elif stage == "prose":
                ctx.invoke(
                    prose,
                    project=project,
                    model=model,
                    temperature=0.7,
                    writing_style=writing_style,
                    context_window=3,
                    retries=3,
                    timeout=300,
                    verbose=verbose,
                    projects_dir=projects_dir,
                )
            elif stage == "epub":
                ctx.invoke(
                    epub,
                    project=project,
                    author=author,
                    title=None,
                    chapters="numbered",
                    chapter_length=3000,
                    force_breaks=None,
                    model=model,
                    verbose=verbose,
                    projects_dir=projects_dir,
                )

            # Update status
            status_dict = manager.get_project_status(project)

        # Final summary
        click.echo(f"\n{'='*60}", err=True)
        click.echo("✨ GENERATION COMPLETE!", err=True)
        click.echo(f"{'='*60}\n", err=True)
        click.echo(f"📖 Project: {project}", err=True)
        click.echo(f"📁 Location: {paths.root}", err=True)
        click.echo(f"📚 EPUB: {paths.epub}", err=True)

    except FileNotFoundError as e:
        click.echo(f"❌ Error: {e}", err=True)
        raise click.Abort()
    except Exception as e:
        click.echo(f"❌ Error during generation: {e}", err=True)
        if verbose:
            import traceback

            traceback.print_exc()
        raise click.Abort()


@cli.command()
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

            # Load story config
            try:
                config = StoryConfig.load(paths.root)
                story_type = config.story_type
                prompt = config.pitch
            except FileNotFoundError:
                # Fallback to old metadata.json for backwards compatibility
                loaded_prompt = manager.load_pitch(prompt_or_project)
                if not loaded_prompt:
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
            prompt = prompt_or_project

        if verbose:
            click.echo(f"🎨 Generating story idea with {model}...", err=True)
            click.echo(f"📝 Prompt: {prompt}", err=True)

        # Generate idea
        generator = IdeaGenerator(model=model, max_retries=retries, verbose=verbose)
        story_idea = generator.generate(prompt, story_type=story_type)

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
@click.argument("project")
@click.option(
    "--model",
    default="gpt-4",
    help="AI model to use (e.g., gpt-4, claude-3-sonnet, ollama/qwen3:30b)",
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

        # Load story config
        try:
            config = StoryConfig.load(paths.root)
            story_type = config.story_type
        except FileNotFoundError:
            story_type = "short-story"  # Fallback for old projects
            if verbose:
                click.echo("⚠️  No story_config.json found, using default: short-story", err=True)

        # Check if idea exists
        if not paths.idea.exists():
            click.echo(f"❌ No idea file found for project '{project}'", err=True)
            click.echo(f"💡 Run: storygen-iter idea {project}", err=True)
            raise click.Abort()

        # Load story idea
        if verbose:
            click.echo(f"📖 Project: {project}", err=True)
            click.echo(f"� Story type: {story_type}", err=True)
            click.echo(f"�📄 Loading story idea from {paths.idea}...", err=True)

        with open(paths.idea, encoding="utf-8") as f:
            idea_data = json.load(f)
        story_idea = StoryIdea.from_dict(idea_data)

        if verbose:
            click.echo(f"✅ Loaded: {story_idea.one_sentence[:60]}...", err=True)
            click.echo(f"🎨 Generating characters with {model}...", err=True)

        # Generate characters
        generator = CharacterGenerator(
            model=model, max_retries=retries, timeout=timeout, verbose=verbose
        )
        characters_list = generator.generate(story_idea, story_type=story_type)

        if verbose:
            click.echo(f"✅ Generated {len(characters_list)} characters!", err=True)

        # Save to project
        characters_data = [char.to_dict() for char in characters_list]
        with open(paths.characters, "w", encoding="utf-8") as f:
            json.dump(characters_data, f, indent=2, ensure_ascii=False)

        click.echo(f"💾 Saved {len(characters_list)} characters to: {paths.characters}", err=True)

    except FileNotFoundError as e:
        click.echo(f"❌ Error: {e}", err=True)
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


@cli.command()
@click.argument("project")
@click.option(
    "--model",
    default="gpt-4",
    help="AI model to use (default: gpt-4)",
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

        # Load story config
        try:
            config = StoryConfig.load(paths.root)
            story_type = config.story_type
        except FileNotFoundError:
            story_type = "short-story"  # Fallback for old projects
            if verbose:
                click.echo("⚠️  No story_config.json found, using default: short-story", err=True)

        # Check if idea exists
        if not paths.idea.exists():
            click.echo(f"❌ No idea file found for project '{project}'", err=True)
            click.echo(f"💡 Run: storygen-iter idea {project}", err=True)
            raise click.Abort()

        # Load story idea
        if verbose:
            click.echo(f"📖 Project: {project}", err=True)
            click.echo(f"� Story type: {story_type}", err=True)
            click.echo(f"�📄 Loading story idea from {paths.idea}...", err=True)

        with open(paths.idea, encoding="utf-8") as f:
            idea_data = json.load(f)
        story_idea = StoryIdea.from_dict(idea_data)

        if verbose:
            click.echo(f"✅ Loaded: {story_idea.one_sentence[:60]}...", err=True)
            click.echo(f"🗺️  Generating locations with {model}...", err=True)

        # Generate locations
        generator = LocationGenerator(
            model=model, max_retries=retries, timeout=timeout, verbose=verbose
        )
        locations_list = generator.generate(story_idea, story_type=story_type)

        if verbose:
            click.echo(f"✅ Generated {len(locations_list)} locations!", err=True)

        # Save to project
        locations_dicts = [loc.to_dict() for loc in locations_list]
        with open(paths.locations, "w", encoding="utf-8") as f:
            json.dump(locations_dicts, f, indent=2, ensure_ascii=False)

        click.echo(f"💾 Saved {len(locations_list)} locations to: {paths.locations}", err=True)

    except FileNotFoundError as e:
        click.echo(f"❌ Error: {e}", err=True)
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

        # Check required files exist
        if not paths.idea.exists():
            click.echo("❌ No idea file found", err=True)
            click.echo(f"💡 Run: storygen-iter idea {project}", err=True)
            raise click.Abort()
        if not paths.characters.exists():
            click.echo("❌ No characters file found", err=True)
            click.echo(f"💡 Run: storygen-iter characters {project}", err=True)
            raise click.Abort()
        if not paths.locations.exists():
            click.echo("❌ No locations file found", err=True)
            click.echo(f"💡 Run: storygen-iter locations {project}", err=True)
            raise click.Abort()

        # Validate structure type
        available = list_available_structures()
        if structure not in available:
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

        if verbose:
            click.echo(f"✅ Loaded idea: {story_idea.one_sentence[:60]}...", err=True)

        # Load characters
        with open(paths.characters, encoding="utf-8") as f:
            characters_data = json.load(f)
        characters = [Character.from_dict(char) for char in characters_data]

        if verbose:
            click.echo(f"✅ Loaded {len(characters)} characters", err=True)

        # Load locations
        with open(paths.locations, encoding="utf-8") as f:
            locations_data = json.load(f)
        locations = [Location.from_dict(loc) for loc in locations_data]

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
        story_outline = generator.generate(story_idea, characters, locations)

        if verbose:
            click.echo(f"✅ Generated {structure} outline!", err=True)

        # Save to project
        outline_dict = story_outline.to_dict()
        with open(paths.outline, "w", encoding="utf-8") as f:
            json.dump(outline_dict, f, indent=2, ensure_ascii=False)

        click.echo(f"💾 Saved outline to: {paths.outline}", err=True)

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


@cli.command()
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
    default=3,
    help="Maximum retry attempts (default: 3)",
)
@click.option(
    "--timeout",
    type=int,
    default=600,
    help="Timeout in seconds for AI calls (default: 600)",
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

        # Check required files
        if not paths.idea.exists():
            click.echo("❌ No idea file found", err=True)
            raise click.Abort()
        if not paths.characters.exists():
            click.echo("❌ No characters file found", err=True)
            raise click.Abort()
        if not paths.locations.exists():
            click.echo("❌ No locations file found", err=True)
            raise click.Abort()
        if not paths.outline.exists():
            click.echo("❌ No outline file found", err=True)
            click.echo(f"� Run: storygen-iter outline {project}", err=True)
            raise click.Abort()

        if verbose:
            click.echo(f"📖 Project: {project}", err=True)

        # Load input files
        with open(paths.idea, encoding="utf-8") as f:
            idea_data = json.load(f)
        story_idea = StoryIdea.from_dict(idea_data)
        click.echo(f"✅ Loaded idea: {story_idea.one_sentence[:60]}...", err=True)

        with open(paths.characters, encoding="utf-8") as f:
            chars_data = json.load(f)
        # Support both array and object formats
        if isinstance(chars_data, list):
            characters = [Character.from_dict(c) for c in chars_data]
        else:
            characters = [Character.from_dict(c) for c in chars_data["characters"]]
        click.echo(f"✅ Loaded {len(characters)} characters", err=True)

        with open(paths.locations, encoding="utf-8") as f:
            locs_data = json.load(f)
        # Support both array and object formats
        if isinstance(locs_data, list):
            locations = [Location.from_dict(loc) for loc in locs_data]
        else:
            locations = [Location.from_dict(loc) for loc in locs_data["locations"]]
        click.echo(f"✅ Loaded {len(locations)} locations", err=True)

        with open(paths.outline, encoding="utf-8") as f:
            outline_data = json.load(f)
        outline = Outline.from_dict(outline_data)
        click.echo(f"✅ Loaded outline with {len(outline.acts)} acts", err=True)

        # Generate breakdown
        click.echo(f"📝 Generating scene-sequel breakdown with {model}...", err=True)

        from storygen.iterative.generators.breakdown import BreakdownGenerator

        generator = BreakdownGenerator(
            model=model,
            max_retries=retries,
            timeout=timeout,
            verbose=verbose,
        )

        scene_sequels = generator.generate(
            story_idea=story_idea,
            characters=characters,
            locations=locations,
            outline=outline,
            target_words=target_words,
        )

        if verbose:
            click.echo(f"✅ Generated {len(scene_sequels)} scene-sequels!", err=True)

        # Save to project
        breakdown_dict = {
            "scene_sequels": [ss.to_dict() for ss in scene_sequels],
            "total_target_words": target_words,
            "story_duration_hours": scene_sequels[-1].end_hours if scene_sequels else 0.0,
        }
        with open(paths.breakdown, "w", encoding="utf-8") as f:
            json.dump(breakdown_dict, f, indent=2, ensure_ascii=False)

        click.echo(f"💾 Saved {len(scene_sequels)} scene-sequels to: {paths.breakdown}", err=True)

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


@cli.command()
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
    default=3,
    help="Maximum retry attempts (default: 3)",
)
@click.option(
    "--timeout",
    type=int,
    default=120,
    help="Timeout in seconds per scene-sequel (default: 120)",
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

        # Check required files
        if not paths.breakdown.exists():
            click.echo("❌ No breakdown file found", err=True)
            click.echo(f"💡 Run: storygen-iter breakdown {project} --words 4000", err=True)
            raise click.Abort()

        if verbose:
            click.echo(f"📖 Project: {project}", err=True)

        # Load input files
        with open(paths.idea, encoding="utf-8") as f:
            idea_data = json.load(f)
        story_idea = StoryIdea.from_dict(idea_data)
        click.echo(f"✅ Loaded idea: {story_idea.one_sentence[:60]}...", err=True)

        with open(paths.characters, encoding="utf-8") as f:
            chars_data = json.load(f)
        if isinstance(chars_data, list):
            characters = [Character.from_dict(c) for c in chars_data]
        else:
            characters = [Character.from_dict(c) for c in chars_data["characters"]]
        click.echo(f"✅ Loaded {len(characters)} characters", err=True)

        with open(paths.locations, encoding="utf-8") as f:
            locs_data = json.load(f)
        if isinstance(locs_data, list):
            locations = [Location.from_dict(loc) for loc in locs_data]
        else:
            locations = [Location.from_dict(loc) for loc in locs_data["locations"]]
        click.echo(f"✅ Loaded {len(locations)} locations", err=True)

        # Check if prose file already exists (resume capability)
        from storygen.iterative.models import SceneSequel

        if paths.prose.exists():
            click.echo("🔄 Found existing prose file, checking for resume...", err=True)
            with open(paths.prose, encoding="utf-8") as f:
                existing_data = json.load(f)
            scene_sequels = [SceneSequel.from_dict(ss) for ss in existing_data["scene_sequels"]]
            completed = sum(1 for ss in scene_sequels if ss.content)
            if completed > 0:
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
                click.echo(f"✅ Loaded {len(scene_sequels)} scene-sequels", err=True)
        else:
            with open(paths.breakdown, encoding="utf-8") as f:
                breakdown_data = json.load(f)
            scene_sequels = [SceneSequel.from_dict(ss) for ss in breakdown_data["scene_sequels"]]
            click.echo(f"✅ Loaded {len(scene_sequels)} scene-sequels", err=True)

        # Generate prose
        click.echo(f"📝 Generating prose with {model}...", err=True)

        from storygen.iterative.generators.prose import ProseGenerator

        generator = ProseGenerator(
            model=model,
            max_retries=retries,
            timeout=timeout,
            temperature=temperature,
            context_window=context_window,
            verbose=verbose,
        )

        updated_scene_sequels = generator.generate(
            story_idea=story_idea,
            characters=characters,
            locations=locations,
            scene_sequels=scene_sequels,
            writing_style=writing_style,
            output_path=str(paths.prose),  # Enable incremental saving
        )

        # Calculate total words
        total_words = sum(ss.actual_word_count or 0 for ss in updated_scene_sequels)
        click.echo(f"✅ Generated {total_words:,} words of prose!", err=True)

        # Save to project
        prose_dict = {
            "scene_sequels": [ss.to_dict() for ss in updated_scene_sequels],
            "total_actual_words": total_words,
        }
        with open(paths.prose, "w", encoding="utf-8") as f:
            json.dump(prose_dict, f, indent=2, ensure_ascii=False)

        click.echo(f"💾 Saved {total_words:,} words to: {paths.prose}", err=True)

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


@cli.command()
@click.argument("project")
@click.option(
    "--author",
    default="AI Generated",
    help="Author name for EPUB metadata (default: AI Generated)",
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
    """
    try:
        # Get project paths
        manager = ProjectManager(Path(projects_dir))
        paths = manager.get_project(project)

        # Check required files
        if not paths.prose.exists():
            click.echo("❌ No prose file found", err=True)
            click.echo(f"💡 Run: storygen-iter prose {project}", err=True)
            raise click.Abort()

        if verbose:
            click.echo(f"📖 Project: {project}", err=True)

        # Load input files
        with open(paths.idea, encoding="utf-8") as f:
            idea_data = json.load(f)
        story_idea = StoryIdea.from_dict(idea_data)

        with open(paths.characters, encoding="utf-8") as f:
            chars_data = json.load(f)
        if isinstance(chars_data, list):
            characters = [Character.from_dict(c) for c in chars_data]
        else:
            characters = [Character.from_dict(c) for c in chars_data["characters"]]

        with open(paths.locations, encoding="utf-8") as f:
            locs_data = json.load(f)
        if isinstance(locs_data, list):
            locations = [Location.from_dict(loc) for loc in locs_data]
        else:
            locations = [Location.from_dict(loc) for loc in locs_data["locations"]]

        with open(paths.prose, encoding="utf-8") as f:
            prose_data = json.load(f)

        from storygen.iterative.models import SceneSequel

        scene_sequels = [SceneSequel.from_dict(ss) for ss in prose_data["scene_sequels"]]
        total_words = sum(ss.actual_word_count or 0 for ss in scene_sequels)
        click.echo(
            f"✅ Loaded {len(scene_sequels)} scene-sequels ({total_words:,} words)", err=True
        )

        # Parse force breaks
        force_break_list = None
        if force_breaks:
            force_break_list = [s.strip() for s in force_breaks.split(",")]
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
        )

        formatter.format(
            story_idea=story_idea,
            characters=characters,
            locations=locations,
            scene_sequels=scene_sequels,
            output_path=str(paths.epub),
            title_override=title,
            force_chapter_breaks=force_break_list,
        )

        click.echo(f"✅ EPUB generated: {paths.epub}", err=True)
        click.echo(f"📊 {len(scene_sequels)} scenes, {total_words:,} words", err=True)

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
