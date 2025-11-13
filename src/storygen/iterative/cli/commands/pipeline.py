"""
Pipeline command for running full story generation in one go.
"""

import logging
from pathlib import Path
from typing import Any

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
    "--max-cost",
    type=float,
    default=None,
    help="Maximum cost in USD to allow before stopping (default: no limit)",
)
def generate_all(
    name: str,
    pitch: str,
    words: int,
    story_type: str,
    model: str,
    timeout: int,
    retries: int,
    projects_dir: str = "projects",
    max_cost: float | None = None,
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
    8. Export to polished EPUB

    Cost tracking: Shows real-time costs and stops if --max-cost limit is exceeded.

    Examples:
        storygen-iter all bank-heist --pitch "A sophisticated bank robbery" --words 10000 --model ollama/qwen3:30b
        storygen-iter all fantasy-quest --pitch "A quest for the lost crown" --words 8000 --max-cost 2.50
    """
    try:
        import click

        from storygen.iterative.cli.commands import export, project

        click.echo(f"\n🚀 Starting full story generation: {name}")
        click.echo(f"📝 Pitch: {pitch}")
        click.echo(f"📊 Target: {words} words")
        click.echo(f"🤖 Model: {model}")
        click.echo(f"⏱️  Timeout: {timeout}s per step")
        if max_cost is not None:
            click.echo(f"💰 Max cost: ${max_cost:.2f}")
        click.echo()

        def check_cost_limit(current_cost: float, step_name: str) -> None:
            """Check if current cost exceeds the maximum allowed cost."""
            if max_cost is not None and current_cost > max_cost:
                click.echo("\n❌ COST LIMIT EXCEEDED!")
                click.echo(f"   Step: {step_name}")
                click.echo(f"   Current cost: ${current_cost:.4f}")
                click.echo(f"   Max allowed: ${max_cost:.2f}")
                click.echo("   Stopping generation to prevent overspending.")
                raise click.Abort()

        manager = ProjectManager(Path(projects_dir))

        # Track usage across all steps
        total_usage: dict[str, Any] = {
            "total_tokens": 0,
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_cost": 0.0,
            "steps": [],
        }

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
        import json

        from storygen.iterative.generators.idea import IdeaGenerator
        from storygen.iterative.models import StoryConfig

        paths = manager.get_project(name)

        # Load story config
        config = StoryConfig.load(paths.root)
        prompt = config.pitch

        idea_generator = IdeaGenerator(model=model, max_retries=retries, verbose=False)
        click.echo(f"🤖 Calling AI with {model}...", err=True)
        story_idea, usage_info = idea_generator.generate(prompt, story_type=story_type)
        click.echo("✅ Story idea generated!", err=True)

        # Save the generated idea
        with open(paths.idea, "w", encoding="utf-8") as f:
            json.dump(story_idea.to_dict(), f, indent=2, ensure_ascii=False)

        # Track usage
        total_usage["steps"].append({"step": "idea", "usage": usage_info})
        if usage_info:
            total_usage["total_tokens"] += usage_info.get("total_tokens", 0)
            total_usage["prompt_tokens"] += usage_info.get("prompt_tokens", 0)
            total_usage["completion_tokens"] += usage_info.get("completion_tokens", 0)
            total_usage["total_cost"] += usage_info.get("total_cost", 0.0)

        check_cost_limit(total_usage["total_cost"], "idea generation")

        # Step 3: Generate characters
        click.echo("\n" + "=" * 70)
        click.echo("Step 3/8: Generating characters...")
        click.echo("=" * 70)
        import json

        from storygen.iterative.generators.character import CharacterGenerator
        from storygen.iterative.models import Character, StoryIdea

        # Load story idea for character generation
        with open(paths.idea, encoding="utf-8") as f:
            idea_data = json.load(f)
        story_idea = StoryIdea.from_dict(idea_data)

        character_generator = CharacterGenerator(
            model=model, max_retries=retries, timeout=timeout, verbose=False
        )
        click.echo(f"🤖 Calling AI with {model}...", err=True)
        characters_list, usage_info = character_generator.generate(
            story_idea, story_type=story_type
        )
        click.echo(f"✅ Generated {len(characters_list)} characters!", err=True)

        # Save characters
        characters_data = [char.to_dict() for char in characters_list]
        with open(paths.characters, "w", encoding="utf-8") as f:
            json.dump(characters_data, f, indent=2, ensure_ascii=False)
        click.echo(f"💾 Saved {len(characters_list)} characters to: {paths.characters}", err=True)

        # Track usage
        total_usage["steps"].append({"step": "characters", "usage": usage_info})
        if usage_info:
            total_usage["total_tokens"] += usage_info.get("total_tokens", 0)
            total_usage["prompt_tokens"] += usage_info.get("prompt_tokens", 0)
            total_usage["completion_tokens"] += usage_info.get("completion_tokens", 0)
            total_usage["total_cost"] += usage_info.get("total_cost", 0.0)

        check_cost_limit(total_usage["total_cost"], "character generation")

        # Step 4: Generate locations
        click.echo("\n" + "=" * 70)
        click.echo("Step 4/8: Generating locations...")
        click.echo("=" * 70)
        import json

        from storygen.iterative.generators.location import LocationGenerator
        from storygen.iterative.models import Location

        # Load story idea for location generation
        with open(paths.idea, encoding="utf-8") as f:
            idea_data = json.load(f)
        story_idea = StoryIdea.from_dict(idea_data)

        location_generator = LocationGenerator(
            model=model, max_retries=retries, timeout=timeout, verbose=False
        )
        click.echo(f"🤖 Calling AI with {model}...", err=True)
        locations_list, usage_info = location_generator.generate(story_idea, story_type=story_type)
        click.echo(f"✅ Generated {len(locations_list)} locations!", err=True)

        # Save locations
        locations_data = [loc.to_dict() for loc in locations_list]
        with open(paths.locations, "w", encoding="utf-8") as f:
            json.dump(locations_data, f, indent=2, ensure_ascii=False)
        click.echo(f"💾 Saved {len(locations_list)} locations to: {paths.locations}", err=True)

        # Track usage
        total_usage["steps"].append({"step": "locations", "usage": usage_info})
        if usage_info:
            total_usage["total_tokens"] += usage_info.get("total_tokens", 0)
            total_usage["prompt_tokens"] += usage_info.get("prompt_tokens", 0)
            total_usage["completion_tokens"] += usage_info.get("completion_tokens", 0)
            total_usage["total_cost"] += usage_info.get("total_cost", 0.0)

        check_cost_limit(total_usage["total_cost"], "location generation")

        # Step 5: Generate outline
        click.echo("\n" + "=" * 70)
        click.echo("Step 5/8: Generating outline...")
        click.echo("=" * 70)
        import json

        from storygen.iterative.generators.outline import OutlineGenerator
        from storygen.iterative.models import Outline

        # Load required data for outline generation
        with open(paths.idea, encoding="utf-8") as f:
            idea_data = json.load(f)
        story_idea = StoryIdea.from_dict(idea_data)

        with open(paths.characters, encoding="utf-8") as f:
            chars_data = json.load(f)
        characters_list = [Character.from_dict(c) for c in chars_data]

        with open(paths.locations, encoding="utf-8") as f:
            locs_data = json.load(f)
        locations_list = [Location.from_dict(loc) for loc in locs_data]

        outline_generator = OutlineGenerator(
            model=model, max_retries=retries, timeout=timeout, verbose=False
        )
        click.echo(f"🤖 Calling AI with {model}...", err=True)
        story_outline, usage_info = outline_generator.generate(
            story_idea, characters_list, locations_list
        )
        click.echo("✅ Generated three-act outline!", err=True)

        # Save outline
        outline_dict = story_outline.to_dict()
        with open(paths.outline, "w", encoding="utf-8") as f:
            json.dump(outline_dict, f, indent=2, ensure_ascii=False)
        click.echo(f"💾 Saved outline to: {paths.outline}", err=True)

        # Track usage
        total_usage["steps"].append({"step": "outline", "usage": usage_info})
        if usage_info:
            total_usage["total_tokens"] += usage_info.get("total_tokens", 0)
            total_usage["prompt_tokens"] += usage_info.get("prompt_tokens", 0)
            total_usage["completion_tokens"] += usage_info.get("completion_tokens", 0)
            total_usage["total_cost"] += usage_info.get("total_cost", 0.0)

        check_cost_limit(total_usage["total_cost"], "outline generation")

        # Step 6: Generate breakdown
        click.echo("\n" + "=" * 70)
        click.echo("Step 6/8: Generating scene-sequel breakdown...")
        click.echo("=" * 70)
        import json

        from storygen.iterative.generators.breakdown import BreakdownGenerator
        from storygen.iterative.models import Character, Location, StoryIdea

        # Load required data
        with open(paths.idea, encoding="utf-8") as f:
            idea_data = json.load(f)
        story_idea = StoryIdea.from_dict(idea_data)

        with open(paths.characters, encoding="utf-8") as f:
            chars_data = json.load(f)
        characters_list = [Character.from_dict(c) for c in chars_data]

        with open(paths.locations, encoding="utf-8") as f:
            locs_data = json.load(f)
        locations_list = [Location.from_dict(loc) for loc in locs_data]

        with open(paths.outline, encoding="utf-8") as f:
            outline_data = json.load(f)
        story_outline = Outline.from_dict(outline_data)

        breakdown_generator = BreakdownGenerator(
            model=model, max_retries=retries, timeout=timeout, verbose=False
        )
        click.echo(f"🤖 Calling AI with {model}...", err=True)
        scene_sequels, usage_info = breakdown_generator.generate(
            story_idea=story_idea,
            characters=characters_list,
            locations=locations_list,
            outline=story_outline,
            target_words=words,
        )
        click.echo("✅ Scene-sequel breakdown generated!", err=True)

        # Save the breakdown
        breakdown_dict = {
            "scene_sequels": [ss.to_dict() for ss in scene_sequels],
            "total_target_words": words,
            "story_duration_hours": scene_sequels[-1].end_hours if scene_sequels else 0.0,
        }
        with open(paths.breakdown, "w", encoding="utf-8") as f:
            json.dump(breakdown_dict, f, indent=2, ensure_ascii=False)

        # Track usage
        total_usage["steps"].append({"step": "breakdown", "usage": usage_info})
        if usage_info:
            total_usage["total_tokens"] += usage_info.get("total_tokens", 0)
            total_usage["prompt_tokens"] += usage_info.get("prompt_tokens", 0)
            total_usage["completion_tokens"] += usage_info.get("completion_tokens", 0)
            total_usage["total_cost"] += usage_info.get("total_cost", 0.0)

        check_cost_limit(total_usage["total_cost"], "scene breakdown generation")

        # Step 7: Generate prose
        click.echo("\n" + "=" * 70)
        click.echo("Step 7/8: Generating prose (this may take a while)...")
        click.echo("=" * 70)
        import json

        from storygen.iterative.cli.commands.utils import format_word_count
        from storygen.iterative.generators.prose import ProseGenerator
        from storygen.iterative.models import SceneSequel

        # Load required data for prose generation
        with open(paths.idea, encoding="utf-8") as f:
            idea_data = json.load(f)
        story_idea = StoryIdea.from_dict(idea_data)

        with open(paths.characters, encoding="utf-8") as f:
            chars_data = json.load(f)
        characters_list = [Character.from_dict(c) for c in chars_data]

        with open(paths.locations, encoding="utf-8") as f:
            locs_data = json.load(f)
        locations_list = [Location.from_dict(loc) for loc in locs_data]

        with open(paths.breakdown, encoding="utf-8") as f:
            breakdown_data = json.load(f)
        scene_sequels = [SceneSequel.from_dict(ss) for ss in breakdown_data["scene_sequels"]]

        prose_generator = ProseGenerator(
            model=model, max_retries=retries, timeout=timeout, verbose=False
        )
        click.echo(f"🤖 Calling AI with {model} for each scene...")
        updated_scene_sequels, usage_info = prose_generator.generate(
            story_idea=story_idea,
            characters=characters_list,
            locations=locations_list,
            scene_sequels=scene_sequels,
            writing_style=None,  # Auto-infer from tone/genre
            output_path=str(paths.prose),
        )

        # Calculate total words
        total_words = sum(ss.actual_word_count or 0 for ss in updated_scene_sequels)
        click.echo(f"✅ Generated {format_word_count(total_words)} words of prose!")

        # Save to project
        prose_dict = {
            "scene_sequels": [ss.to_dict() for ss in updated_scene_sequels],
            "total_actual_words": total_words,
        }
        with open(paths.prose, "w", encoding="utf-8") as f:
            json.dump(prose_dict, f, indent=2, ensure_ascii=False)
        click.echo(f"💾 Saved {format_word_count(total_words)} words to: {paths.prose}", err=True)

        # Track usage
        total_usage["steps"].append({"step": "prose", "usage": usage_info})
        if usage_info:
            total_usage["total_tokens"] += usage_info.get("total_tokens", 0)
            total_usage["prompt_tokens"] += usage_info.get("prompt_tokens", 0)
            total_usage["completion_tokens"] += usage_info.get("completion_tokens", 0)
            total_usage["total_cost"] += usage_info.get("total_cost", 0.0)

        check_cost_limit(total_usage["total_cost"], "prose generation")

        # Step 8: Generate EPUB
        click.echo("\n" + "=" * 70)
        click.echo("Step 8/8: Generating EPUB...")
        click.echo("=" * 70)
        click.echo("📚 Formatting and generating EPUB file...", err=True)
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
        click.echo("✅ EPUB generated!", err=True)

        # Success!
        click.echo("\n" + "=" * 70)
        click.echo("🎉 COMPLETE! Story generation finished successfully!")
        click.echo("=" * 70)

        # Display usage summary
        if total_usage["total_tokens"] > 0:
            click.echo("\n💰 COST & USAGE SUMMARY:")
            click.echo("-" * 50)
            click.echo(f"   Total tokens: {total_usage['total_tokens']:,}")
            click.echo(f"   Prompt tokens: {total_usage['prompt_tokens']:,}")
            click.echo(f"   Completion tokens: {total_usage['completion_tokens']:,}")
            click.echo(f"   💵 Total cost: ${total_usage['total_cost']:.4f}")
            click.echo(f"   Steps completed: {len(total_usage['steps'])}")

            # Show cost breakdown by step
            click.echo("\n   Cost breakdown by step:")
            for step_info in total_usage["steps"]:
                step_name = step_info["step"]
                usage = step_info["usage"]
                if usage and usage.get("total_cost", 0) > 0:
                    cost = usage.get("total_cost", 0)
                    click.echo(f"     • {step_name}: ${cost:.4f}")

            if max_cost is not None:
                remaining = max_cost - total_usage["total_cost"]
                click.echo(f"\n   Budget remaining: ${remaining:.4f} (of ${max_cost:.2f} limit)")

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
