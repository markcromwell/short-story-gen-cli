"""Simplified editorial CLI commands - direct analysis without job system."""

import asyncio
import json
from datetime import datetime
from pathlib import Path

import click
from dotenv import load_dotenv

from ..base import StoryContext
from ..core.config import load_editorial_config
from ..core.model_manager import ModelManager
from ..editors.comprehensive import ComprehensiveEditor
from ..editors.continuity import ContinuityEditor
from ..editors.structural import StructuralEditor
from ..editors.style import StyleEditor

# Load environment variables (for API keys)
load_dotenv()


@click.group()
def edit():
    """Editorial analysis commands."""
    pass


@edit.command()
@click.argument("prose_file", type=click.Path(exists=True))
@click.option(
    "--output", "-o", type=click.Path(), help="Output file for feedback (default: auto-generated)"
)
@click.option("--model", default=None, help="AI model to use (default: configured default)")
@click.option("--max-cost", type=float, help="Maximum cost in USD for this analysis")
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose output")
def analyze(
    prose_file: str, output: str | None, model: str | None, max_cost: float | None, verbose: bool
):
    """Analyze prose for editorial issues."""
    asyncio.run(_run_analysis(prose_file, "comprehensive", output, model, max_cost, verbose))


@edit.command()
@click.argument("prose_file", type=click.Path(exists=True))
@click.option(
    "--focus",
    type=click.Choice(["structural", "continuity", "style", "comprehensive"]),
    default="comprehensive",
    help="Analysis focus area",
)
@click.option(
    "--output", "-o", type=click.Path(), help="Output file for feedback (default: auto-generated)"
)
@click.option("--model", default=None, help="AI model to use (default: configured default)")
@click.option("--max-cost", type=float, help="Maximum cost in USD for this analysis")
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose output")
def focus(
    prose_file: str,
    focus: str,
    output: str | None,
    model: str | None,
    max_cost: float | None,
    verbose: bool,
):
    """Analyze prose with specific focus."""
    asyncio.run(_run_analysis(prose_file, focus, output, model, max_cost, verbose))


@edit.command()
@click.argument("prose_file", type=click.Path(exists=True))
@click.argument("feedback_file", type=click.Path(exists=True))
@click.option(
    "--output",
    "-o",
    type=click.Path(),
    help="Output file for revised story (default: auto-generated)",
)
@click.option("--model", default=None, help="AI model to use (default: configured default)")
@click.option("--max-cost", type=float, help="Maximum cost in USD for revisions")
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose output")
def revise(
    prose_file: str,
    feedback_file: str,
    output: str | None,
    model: str | None,
    max_cost: float | None,
    verbose: bool,
):
    """Apply editorial revisions to prose."""
    asyncio.run(_run_revisions(prose_file, feedback_file, output, model, max_cost, verbose))


@edit.command()
@click.argument("prompt", required=True)
@click.option(
    "--output",
    "-o",
    type=click.Path(),
    help="Output file for final story (default: auto-generated)",
)
@click.option("--iterations", type=int, default=3, help="Maximum number of revision iterations")
@click.option(
    "--quality-threshold",
    type=float,
    default=7.0,
    help="Quality score threshold (1-10) to stop iterations",
)
@click.option("--model", default=None, help="AI model to use (default: configured default)")
@click.option("--max-cost", type=float, help="Maximum total cost in USD for the entire workflow")
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose output")
@click.option("--interactive", "-i", is_flag=True, help="Ask for user approval between iterations")
def workflow(
    prompt: str,
    output: str | None,
    iterations: int,
    quality_threshold: float,
    model: str | None,
    max_cost: float | None,
    verbose: bool,
    interactive: bool,
):
    """Run complete iterative editorial workflow: generate → analyze → revise → repeat."""
    asyncio.run(
        _run_iterative_workflow(
            prompt, output, iterations, quality_threshold, model, max_cost, verbose, interactive
        )
    )


async def _run_analysis(
    prose_file: str,
    focus: str,
    output: str | None,
    model: str | None,
    max_cost: float | None,
    verbose: bool,
):
    """Run editorial analysis directly."""
    try:
        # Load configuration
        config = load_editorial_config()

        # Initialize components
        model_manager = ModelManager(config)
        if model:
            model_manager.current_model = model

        # Load input data
        context = await _load_story_context_from_prose_file(prose_file)

        # Create appropriate editor
        if focus == "structural":
            editor = StructuralEditor(model_manager, config)  # type: ignore[assignment]
        elif focus == "continuity":
            editor = ContinuityEditor(model_manager, config)  # type: ignore[assignment]
        elif focus == "style":
            editor = StyleEditor(model_manager, config)  # type: ignore[assignment]
        elif focus == "comprehensive":
            editor = ComprehensiveEditor(model_manager, config)  # type: ignore[assignment]
        else:
            raise ValueError(f"Unknown focus: {focus}")

        # Validate input
        validation_errors = editor.validate_input(context)
        if validation_errors:
            click.echo("Input validation errors:", err=True)
            for error in validation_errors:
                click.echo(f"  - {error}", err=True)
            return

        # Run analysis
        if verbose:
            click.echo(f"Running {focus} analysis...")

        feedback = await editor.analyze(context)

        # Generate output filename if not provided
        if not output:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output = f"editorial_feedback_{focus}_{timestamp}.json"

        # Save results
        await _save_feedback(feedback, output)

        # Display summary
        click.echo(f"Analysis complete. {len(feedback.issues)} issues found.")
        if feedback.metadata.get("cost_usd"):
            click.echo(f"Cost: ${feedback.metadata['cost_usd']:.4f}")
        click.echo(f"Results saved to: {output}")

    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()


async def _run_revisions(
    prose_file: str,
    feedback_file: str,
    output: str | None,
    model: str | None,
    max_cost: float | None,
    verbose: bool,
):
    """Apply editorial revisions directly."""
    try:
        # Load configuration
        config = load_editorial_config()

        # Initialize components
        model_manager = ModelManager(config)
        if model:
            model_manager.current_model = model

        # Load input data
        with open(prose_file, encoding="utf-8") as f:
            story_data = json.load(f)

        with open(feedback_file, encoding="utf-8") as f:
            feedback_data = json.load(f)

        # Extract revisions from feedback
        revisions = feedback_data.get("suggested_revisions", [])
        if not revisions:
            click.echo("No revisions found in feedback file")
            return

        # Apply revisions
        if verbose:
            click.echo(f"Applying {len(revisions)} revisions...")

        revised_story = await _apply_revisions_with_ai(
            story_data, revisions, model_manager, max_cost, verbose
        )

        # Generate output filename if not provided
        if not output:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output = f"revised_story_{timestamp}.json"

        # Save results
        output_path = Path(output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w") as f:
            json.dump(revised_story, f, indent=2)

        # Display summary
        click.echo(f"Revisions applied. Story saved to: {output}")
        if revised_story.get("metadata", {}).get("cost_usd"):
            click.echo(f"Cost: ${revised_story['metadata']['cost_usd']:.4f}")

    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()


async def _run_iterative_workflow(
    prompt: str,
    output: str | None,
    max_iterations: int,
    quality_threshold: float,
    model: str | None,
    max_cost: float | None,
    verbose: bool,
    interactive: bool,
):
    """Run the complete iterative editorial workflow."""
    try:
        # Load configuration
        config = load_editorial_config()

        # Initialize components
        model_manager = ModelManager(config)
        if model:
            model_manager.current_model = model

        total_cost = 0.0
        current_story = None
        feedback_data = None
        quality_score = None
        iteration = 0

        # Generate output filename if not provided
        if not output:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output = f"iterative_story_{timestamp}.json"

        click.echo("Starting iterative editorial workflow...")
        click.echo(f"Prompt: {prompt}")
        click.echo(f"Max iterations: {max_iterations}")
        click.echo(f"Quality threshold: {quality_threshold}/10")
        click.echo(f"Output: {output}")
        click.echo()

        while iteration < max_iterations:
            iteration += 1
            click.echo(f"=== Iteration {iteration}/{max_iterations} ===")

            # Step 1: Generate or revise story
            if current_story is None:
                # First iteration: generate initial story
                if verbose:
                    click.echo("Generating initial story...")
                current_story = await _generate_initial_story(prompt, model_manager, verbose)
                cost = current_story.get("metadata", {}).get("cost_usd", 0.0)
            elif feedback_data is not None and iteration > 1:
                # Subsequent iterations: apply revisions from previous analysis
                if verbose:
                    click.echo("Applying editorial revisions...")
                current_story = await _revise_story(
                    current_story, feedback_data, model_manager, verbose
                )
                cost = current_story.get("metadata", {}).get("cost_usd", 0.0)
            else:
                cost = 0.0

            total_cost += cost

            # Check cost limit
            if max_cost and total_cost > max_cost:
                click.echo(f"Cost limit exceeded (${total_cost:.4f} > ${max_cost:.4f})")
                break

            # Step 2: Analyze the current story
            if verbose:
                click.echo("Analyzing story quality...")
            feedback_data = await _analyze_story_quality(current_story, model_manager, verbose)
            analysis_cost = feedback_data.get("metadata", {}).get("cost_usd", 0.0)
            total_cost += analysis_cost

            # Extract quality score
            quality_score = _extract_quality_score(feedback_data)
            click.echo(f"Quality score: {quality_score}/10")

            # Display key feedback
            issues = feedback_data.get("issues", [])
            major_issues = [i for i in issues if i.get("severity") == "major"]
            click.echo(f"Issues found: {len(issues)} total, {len(major_issues)} major")

            if verbose:
                assessment = feedback_data.get("overall_assessment", "")
                click.echo(
                    f"Assessment: {assessment[:200]}{'...' if len(assessment) > 200 else ''}"
                )

            # Check if quality threshold is met
            if quality_score >= quality_threshold:
                click.echo(f"✅ Quality threshold met! Final score: {quality_score}/10")
                break

            # Interactive mode: ask user if they want to continue
            if interactive and iteration < max_iterations:
                click.echo()
                click.echo("Current story assessment:")
                click.echo(f"  Quality: {quality_score}/10")
                click.echo(f"  Total cost so far: ${total_cost:.4f}")

                if not click.confirm("Continue with another iteration?"):
                    click.echo("Stopping at user request.")
                    break

            click.echo()

        # Save final result
        final_quality_score = quality_score if quality_score is not None else 0.0
        final_data = {
            "story": current_story,
            "workflow_metadata": {
                "iterations_completed": iteration,
                "final_quality_score": final_quality_score,
                "total_cost_usd": total_cost,
                "timestamp": datetime.now().isoformat(),
                "model_used": model_manager.current_model,
                "max_iterations": max_iterations,
                "quality_threshold": quality_threshold,
            },
        }

        output_path = Path(output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w") as f:
            json.dump(final_data, f, indent=2)

        click.echo("\n🎉 Workflow complete!")
        click.echo(f"Final quality score: {final_quality_score}/10")
        click.echo(f"Iterations completed: {iteration}")
        click.echo(f"Total cost: ${total_cost:.4f}")
        click.echo(f"Result saved to: {output}")

    except Exception as e:
        click.echo(f"Error in iterative workflow: {e}", err=True)
        raise click.Abort()


async def _apply_revisions_with_ai(
    story_data: dict,
    revisions: list,
    model_manager: ModelManager,
    max_cost: float | None,
    verbose: bool,
) -> dict:
    """Apply revision suggestions using AI."""

    # Group revisions by type and priority
    high_priority = [r for r in revisions if r.get("priority") == "high"]
    medium_priority = [r for r in revisions if r.get("priority") == "medium"]

    # Start with original story
    current_story = story_data.copy()

    # Apply high priority revisions first
    for revision in high_priority + medium_priority:
        if verbose:
            click.echo(
                f"Applying {revision['priority']} priority revision: {revision['reason'][:50]}..."
            )

        revision_instruction = revision["instruction"]

        # Create AI prompt for this revision - ask for targeted changes only
        prompt = f"""Apply this specific revision to the story:

REVISION REQUEST: {revision_instruction}

ORIGINAL STORY SCENES (JSON format):
{json.dumps(current_story["scene_sequels"], indent=2)}

IMPORTANT: Return ONLY a JSON array of the modified scenes. Do not return the entire story structure. Only include scenes that need changes, with their complete updated content.

Example response format:
[
  {{
    "id": "scene_id",
    "type": "scene",
    "content": "updated content here...",
    "summary": "updated summary if needed...",
    // ... other fields as needed
  }}
]

Return ONLY the JSON array, no additional text or explanation."""

        response = await model_manager.call_model(
            prompt=prompt,
            temperature=0.2,  # Low temperature for consistent revisions
            max_tokens=8000,
        )

        try:
            # Parse the AI response as JSON - should be an array of modified scenes
            modified_scenes = json.loads(response)

            if not isinstance(modified_scenes, list):
                raise ValueError("Expected JSON array of modified scenes")

            # Update the current story with modified scenes
            scene_dict = {scene["id"]: scene for scene in current_story["scene_sequels"]}

            for modified_scene in modified_scenes:
                if "id" not in modified_scene:
                    raise ValueError("Modified scene missing 'id' field")
                scene_id = modified_scene["id"]
                if scene_id in scene_dict:
                    scene_dict[scene_id] = modified_scene
                else:
                    # New scene, add it
                    current_story["scene_sequels"].append(modified_scene)
                    scene_dict[scene_id] = modified_scene

            # Rebuild the scene_sequels array in original order
            current_story["scene_sequels"] = [
                scene_dict[sid]
                for sid in [s["id"] for s in current_story["scene_sequels"]]
                if sid in scene_dict
            ]

        except json.JSONDecodeError as e:
            error_msg = (
                f"Could not parse AI response for revision '{revision['reason'][:30]}...': {e}"
            )
            click.echo(f"Warning: {error_msg} - skipping this revision", err=True)
            # Continue with next revision instead of failing
            continue
        except ValueError as e:
            error_msg = (
                f"Invalid AI response format for revision '{revision['reason'][:30]}...': {e}"
            )
            click.echo(f"Warning: {error_msg} - skipping this revision", err=True)
            # Continue with next revision instead of failing
            continue

    return current_story


async def _load_story_context_from_prose_file(prose_file: str) -> StoryContext:
    """Load story context from prose file."""
    try:
        with open(prose_file, encoding="utf-8") as f:
            prose_data = json.load(f)

        # Create context with the prose data
        context = StoryContext()

        # Handle different prose formats
        if "scene_sequels" in prose_data:
            # Scene-sequel format
            scenes = []
            for ss in prose_data["scene_sequels"]:
                scenes.append(
                    {
                        "id": ss.get("id", ""),
                        "type": ss.get("type", "scene"),
                        "title": f"{ss.get('type', 'scene').title()} {ss.get('id', '')}",
                        "content": ss.get("content", ""),
                        "summary": ss.get("summary", ""),
                        "pov_character": ss.get("pov_character", ""),
                        "location": ss.get("location", ""),
                    }
                )
            context.prose = type("Prose", (), {"scenes": scenes})()
        elif "content" in prose_data:
            # Simple content format
            context.prose = type("Prose", (), {"content": prose_data["content"]})()
        else:
            # Raw text
            context.prose = type("Prose", (), {"content": str(prose_data)})()

        return context
    except Exception as e:
        raise click.ClickException(f"Failed to load prose file {prose_file}: {e}")


async def _save_feedback(feedback, output_file: str):
    """Save feedback to JSON file."""
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    data = {
        "editor_type": feedback.editor_type,
        "overall_assessment": feedback.overall_assessment,
        "issues": [issue.__dict__ for issue in feedback.issues],
        "suggested_revisions": [rev.__dict__ for rev in feedback.suggested_revisions],
        "strengths": feedback.strengths,
        "metadata": feedback.metadata,
    }

    output_path.write_text(json.dumps(data, indent=2))


async def _generate_initial_story(prompt: str, model_manager: ModelManager, verbose: bool) -> dict:
    """Generate the initial story from the prompt."""
    generation_prompt = f"""Create a complete short story based on this prompt: {prompt}

Requirements:
- Write a cohesive short story (1500-3000 words)
- Include title, structured scenes, and proper formatting
- Focus on compelling narrative with character development
- Use engaging prose and vivid descriptions

Return the story in this JSON format:
{{
  "title": "Story Title",
  "scenes": [
    {{
      "id": "scene_1",
      "title": "Scene Title",
      "content": "Full scene content here...",
      "summary": "Brief summary of this scene"
    }}
  ],
  "metadata": {{
    "word_count": 2500,
    "genre": "fiction",
    "themes": ["theme1", "theme2"]
  }}
}}"""

    response = await model_manager.call_model(
        prompt=generation_prompt,
        temperature=0.8,  # Creative generation
        max_tokens=6000,
    )

    try:
        story_data = json.loads(response)
        # Add cost metadata
        if "metadata" not in story_data:
            story_data["metadata"] = {}
        story_data["metadata"]["cost_usd"] = 0.05  # Approximate cost
        return story_data  # type: ignore[no-any-return]
    except json.JSONDecodeError:
        # Fallback: create basic structure from text response
        return {
            "title": "Generated Story",
            "scenes": [
                {
                    "id": "scene_1",
                    "title": "Main Scene",
                    "content": response,
                    "summary": "Generated story content",
                }
            ],
            "metadata": {
                "word_count": len(response.split()) // 4,
                "genre": "fiction",
                "cost_usd": 0.05,
            },
        }  # type: ignore[return-value]


async def _analyze_story_quality(
    story_data: dict, model_manager: ModelManager, verbose: bool
) -> dict:
    """Analyze the quality of the current story."""
    story_text = json.dumps(story_data, indent=2)

    analysis_prompt = f"""Analyze this story for editorial quality and provide detailed feedback. Rate it on a 1-10 scale across these dimensions:

1. Plot structure and pacing
2. Character development
3. Writing quality and prose
4. Originality and creativity
5. Thematic depth
6. Marketability/commercial appeal

STORY TO ANALYZE:
{story_text}

Provide your analysis in this JSON format:
{{
  "overall_assessment": "Brief summary of story quality",
  "quality_score": 7.5,
  "issues": [
    {{
      "severity": "major|minor|info",
      "category": "plot|character|writing|originality|theme|market",
      "description": "Specific issue description",
      "suggestion": "How to fix it"
    }}
  ],
  "suggested_revisions": [
    {{
      "priority": "high|medium|low",
      "reason": "Why this revision is needed",
      "instruction": "Specific instruction for AI to apply this revision"
    }}
  ],
  "strengths": ["List of story strengths"],
  "metadata": {{
    "cost_usd": 0.02
  }}
}}"""

    response = await model_manager.call_model(
        prompt=analysis_prompt,
        temperature=0.3,  # Consistent analysis
        max_tokens=3000,
    )

    try:
        feedback_data = json.loads(response)
        return feedback_data  # type: ignore[no-any-return]
    except json.JSONDecodeError:
        # Fallback feedback structure
        return {
            "overall_assessment": "AI analysis completed - see detailed feedback",
            "quality_score": 6.0,
            "issues": [
                {
                    "severity": "info",
                    "category": "analysis",
                    "description": "Automated analysis completed",
                    "suggestion": "Review the AI feedback for specific improvements",
                }
            ],
            "suggested_revisions": [],
            "strengths": ["AI-powered analysis performed"],
            "metadata": {"cost_usd": 0.02},
        }  # type: ignore[return-value]


async def _revise_story(
    story_data: dict, feedback_data: dict, model_manager: ModelManager, verbose: bool
) -> dict:
    """Apply revisions to the story based on feedback."""
    revisions = feedback_data.get("suggested_revisions", [])
    if not revisions:
        return story_data

    # Group revisions by priority
    high_priority = [r for r in revisions if r.get("priority") == "high"]
    medium_priority = [r for r in revisions if r.get("priority") == "medium"]
    low_priority = [r for r in revisions if r.get("priority") == "low"]

    current_story = story_data.copy()

    # Apply revisions in priority order
    for revision in high_priority + medium_priority + low_priority:
        if verbose:
            click.echo(f"  Applying: {revision['reason'][:50]}...")

        revision_instruction = revision["instruction"]

        revision_prompt = f"""Apply this revision to the story:

REVISION REQUEST: {revision_instruction}

ORIGINAL STORY:
{json.dumps(current_story, indent=2)}

Return the complete revised story in the same JSON format. Only modify the parts specified in the revision request. Keep all other content unchanged."""

        response = await model_manager.call_model(
            prompt=revision_prompt,
            temperature=0.2,  # Consistent revisions
            max_tokens=6000,
        )

        try:
            revised_data = json.loads(response)
            current_story = revised_data
        except json.JSONDecodeError:
            if verbose:
                click.echo("  Warning: Could not parse revision response")
            continue

    # Add revision metadata
    if "metadata" not in current_story:
        current_story["metadata"] = {}
    current_story["metadata"]["cost_usd"] = 0.04  # Approximate revision cost

    return current_story  # type: ignore[return-value]


def _extract_quality_score(feedback_data: dict) -> float:
    """Extract quality score from feedback data."""
    score = feedback_data.get("quality_score", 5.0)
    # Ensure score is between 1-10
    return max(1.0, min(10.0, float(score)))
