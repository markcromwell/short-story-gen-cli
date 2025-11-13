"""CLI commands for editorial workflow."""

import asyncio
import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

import click

from ..base import EditorialFeedback, EditorialIssue, StoryContext
from ..core.config import load_editorial_config
from ..core.job_manager import JobManager, JobStatus
from ..core.model_manager import ModelManager
from ..editors.continuity import ContinuityEditor
from ..editors.structural import StructuralEditor
from ..editors.style import StyleEditor


@click.group()
def edit():
    """Editorial analysis commands."""
    pass


@edit.command()
@click.option(
    "--idea",
    "idea_file",
    type=click.Path(exists=True),
    required=True,
    help="Path to story idea JSON file",
)
@click.option("--output", "-o", type=click.Path(), required=True, help="Output file for feedback")
@click.option("--model", default=None, help="AI model to use (default: configured default)")
@click.option("--max-cost", type=float, help="Maximum cost in USD for this analysis")
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose output")
def idea(idea_file: str, output: str, model: str | None, max_cost: float | None, verbose: bool):
    """Analyze story idea for conceptual strength."""
    asyncio.run(_run_idea_editor(idea_file, output, model, max_cost, verbose))


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
def all(
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


@click.group()
def job():
    """Job management commands."""
    pass


@job.command()
@click.argument("job_id")
def status(job_id: str):
    """Check job status."""
    asyncio.run(_show_job_status(job_id))


@job.command()
@click.option(
    "--idea",
    "idea_file",
    type=click.Path(exists=True),
    help="Path to story idea JSON file",
)
@click.option(
    "--prose",
    "prose_file",
    type=click.Path(exists=True),
    help="Path to prose JSON file",
)
@click.option(
    "--focus",
    type=click.Choice(["structural", "continuity", "style", "comprehensive"]),
    default="comprehensive",
    help="Analysis focus area (for prose analysis)",
)
@click.option("--output", "-o", type=click.Path(), required=True, help="Output file for feedback")
@click.option("--model", default=None, help="AI model to use (default: configured default)")
@click.option("--max-cost", type=float, help="Maximum cost in USD for this analysis")
@click.option("--batch-size", type=int, default=5, help="Scenes per batch for analysis")
def start(
    idea_file: str | None,
    prose_file: str | None,
    focus: str,
    output: str,
    model: str | None,
    max_cost: float | None,
    batch_size: int,
):
    """Start a new editorial analysis job."""
    if not idea_file and not prose_file:
        raise click.UsageError("Must specify either --idea or --prose file")
    if idea_file and prose_file:
        raise click.UsageError("Cannot specify both --idea and --prose files")

    if idea_file:
        job_id = asyncio.run(_start_idea_job(idea_file, output, model, max_cost))
    else:
        # prose_file is guaranteed to be not None here due to the earlier check
        assert prose_file is not None
        job_id = asyncio.run(
            _start_content_job(prose_file, focus, output, model, max_cost, batch_size)
        )

    click.echo(f"Started job: {job_id}")


@job.command()
@click.argument("job_id")
def pause(job_id: str):
    """Pause a running job."""
    asyncio.run(_pause_job(job_id))


@job.command()
@click.argument("job_id")
def resume(job_id: str):
    """Resume a paused job."""
    asyncio.run(_resume_job(job_id))


@job.command()
@click.argument("job_id")
def cancel(job_id: str):
    """Cancel a job."""
    asyncio.run(_cancel_job(job_id))


@job.command()
@click.option(
    "--status",
    type=click.Choice(["pending", "running", "paused", "completed", "failed", "cancelled"]),
)
def list_jobs(status: str | None):
    """List jobs."""
    status_filter = JobStatus(status) if status else None
    asyncio.run(_list_jobs(status_filter))


async def _run_idea_editor(
    idea_file: str, output: str, model: str | None, max_cost: float | None, verbose: bool
):
    """Run idea editor analysis."""
    try:
        # Load configuration
        config = load_editorial_config()

        # Initialize components
        model_manager = ModelManager(config)
        if model:
            model_manager.current_model = model

        # Load input data
        context = await _load_story_context_from_idea_file(idea_file)

        # Create mock editor for Stage 1
        editor = await _create_mock_editor("idea", model_manager, config)

        # Validate input
        validation_errors = editor.validate_input(context)
        if validation_errors:
            click.echo("Input validation errors:", err=True)
            for error in validation_errors:
                click.echo(f"  - {error}", err=True)
            return

        # Run analysis
        if verbose:
            click.echo("Running idea analysis...")

        feedback = await editor.analyze(context)

        # Save results
        await _save_feedback(feedback, output)

        # Display summary
        click.echo(f"Analysis complete. {len(feedback.issues)} issues found.")
        if feedback.metadata.get("cost_usd"):
            click.echo(f"Cost: ${feedback.metadata['cost_usd']:.4f}")

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
        final_data = {
            "story": current_story,
            "workflow_metadata": {
                "iterations_completed": iteration,
                "final_quality_score": quality_score,
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
        click.echo(f"Final quality score: {quality_score}/10")
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

        # Create AI prompt for this revision
        prompt = f"""Apply this revision to the story:

REVISION REQUEST: {revision_instruction}

ORIGINAL STORY:
{json.dumps(current_story, indent=2)}

Return the complete revised story in the same JSON format. Only modify the parts specified in the revision request. Keep all other content unchanged."""

        response = await model_manager.call_model(
            prompt=prompt,
            temperature=0.2,  # Low temperature for consistent revisions
            max_tokens=8000,
        )

        try:
            # Parse the AI response as JSON
            revised_data = json.loads(response)
            current_story = revised_data
        except json.JSONDecodeError:
            if verbose:
                click.echo(
                    f"Warning: Could not parse AI response for revision: {revision['reason'][:30]}..."
                )
            continue

    return current_story


async def _start_idea_job(
    idea_file: str, output: str, model: str | None, max_cost: float | None
) -> str:
    """Start an idea analysis job."""
    config = load_editorial_config()

    # Initialize components
    model_manager = ModelManager(config)
    if model:
        model_manager.current_model = model

    job_manager = JobManager(Path(config.get("job_storage_dir", "./jobs")))

    # Load input data
    context = await _load_story_context_from_idea_file(idea_file)

    # Create job config
    job_config = {
        "model": model_manager.current_model,
        "max_cost_usd": max_cost,
        "output_file": output,
        "batch_size": 1,  # Not used for idea analysis
        "max_concurrent_batches": 1,
    }

    # Start the job
    job_id = await job_manager.start_job("idea", context, job_config)
    return job_id


async def _start_content_job(
    prose_file: str,
    focus: str,
    output: str,
    model: str | None,
    max_cost: float | None,
    batch_size: int,
) -> str:
    """Start a content analysis job."""
    config = load_editorial_config()

    # Initialize components
    model_manager = ModelManager(config)
    if model:
        model_manager.current_model = model

    job_manager = JobManager(Path(config.get("job_storage_dir", "./jobs")))

    # Load input data
    context = await _load_story_context_from_prose_file(prose_file)

    # Create job config
    job_config = {
        "model": model_manager.current_model,
        "max_cost_usd": max_cost,
        "output_file": output,
        "focus": focus,
        "batch_size": batch_size,
        "max_concurrent_batches": 3,
    }

    # For now, run synchronously instead of as background job
    # TODO: Implement true background job processing
    job_id = str(uuid.uuid4())

    # Create job metadata
    from datetime import datetime

    from ..core.job_manager import JobMetadata, JobStatus

    metadata = JobMetadata(
        job_id=job_id,
        editor_type=f"content-{focus}",
        model_used=model_manager.current_model,
        batch_size=batch_size,
        max_concurrent_batches=3,
    )

    # Save initial metadata
    await job_manager._save_job_metadata(metadata)

    try:
        # Run the analysis synchronously
        metadata.status = JobStatus.RUNNING
        metadata.started_at = datetime.now()
        await job_manager._save_job_metadata(metadata)

        # Create editor
        editor = await job_manager._create_editor(f"content-{focus}", job_config)

        # Run analysis
        feedback = await editor.analyze(context)

        # Save results
        await job_manager._save_job_result(job_id, feedback)
        if output:
            await job_manager._save_user_result(output, feedback)

        # Update metadata
        metadata.status = JobStatus.COMPLETED
        metadata.completed_at = datetime.now()
        metadata.progress = 1.0
        metadata.duration_seconds = (metadata.completed_at - metadata.started_at).total_seconds()
        await job_manager._save_job_metadata(metadata)

        click.echo(f"Job {job_id} completed successfully")

    except Exception as e:
        metadata.status = JobStatus.FAILED
        metadata.error_message = str(e)
        metadata.completed_at = datetime.now()
        await job_manager._save_job_metadata(metadata)
        click.echo(f"Job {job_id} failed: {e}", err=True)
        raise

    return job_id


async def _show_job_status(job_id: str):
    """Show detailed job status."""
    try:
        config = load_editorial_config()
        job_manager = JobManager(Path(config.get("job_storage_dir", "./jobs")))

        metadata = await job_manager.get_job_status(job_id)
        if not metadata:
            click.echo(f"Job {job_id} not found", err=True)
            return

        click.echo(f"Job ID: {metadata.job_id}")
        click.echo(f"Status: {metadata.status.value}")
        click.echo(f"Editor: {metadata.editor_type}")
        click.echo(f"Model: {metadata.model_used}")
        click.echo(f"Progress: {metadata.progress:.1%}")
        click.echo(f"Stage: {metadata.current_stage}")
        click.echo(f"Created: {metadata.created_at}")
        if metadata.started_at:
            click.echo(f"Started: {metadata.started_at}")
        if metadata.completed_at:
            click.echo(f"Completed: {metadata.completed_at}")
        if metadata.duration_seconds > 0:
            click.echo(f"Duration: {metadata.duration_seconds:.1f}s")
        if metadata.total_cost_usd > 0:
            click.echo(f"Cost: ${metadata.total_cost_usd:.4f}")
        if metadata.error_message:
            click.echo(f"Error: {metadata.error_message}")

    except Exception as e:
        click.echo(f"Error: {e}", err=True)


async def _pause_job(job_id: str):
    """Pause a job."""
    try:
        config = load_editorial_config()
        job_manager = JobManager(Path(config.get("job_storage_dir", "./jobs")))

        success = await job_manager.pause_job(job_id)
        if success:
            click.echo(f"Job {job_id} paused")
        else:
            click.echo(f"Failed to pause job {job_id}", err=True)

    except Exception as e:
        click.echo(f"Error: {e}", err=True)


async def _resume_job(job_id: str):
    """Resume a job."""
    try:
        config = load_editorial_config()
        job_manager = JobManager(Path(config.get("job_storage_dir", "./jobs")))

        success = await job_manager.resume_job(job_id)
        if success:
            click.echo(f"Job {job_id} resumed")
        else:
            click.echo(f"Failed to resume job {job_id}", err=True)

    except Exception as e:
        click.echo(f"Error: {e}", err=True)


async def _cancel_job(job_id: str):
    """Cancel a job."""
    try:
        config = load_editorial_config()
        job_manager = JobManager(Path(config.get("job_storage_dir", "./jobs")))

        success = await job_manager.cancel_job(job_id)
        if success:
            click.echo(f"Job {job_id} cancelled")
        else:
            click.echo(f"Failed to cancel job {job_id}", err=True)

    except Exception as e:
        click.echo(f"Error: {e}", err=True)


async def _list_jobs(status_filter: JobStatus | None):
    """List jobs."""
    try:
        config = load_editorial_config()
        job_manager = JobManager(Path(config.get("job_storage_dir", "./jobs")))

        jobs = await job_manager.list_jobs(status_filter)
        assert jobs is not None  # list_jobs should never return None

        if not jobs:
            click.echo("No jobs found")
            return

        click.echo(f"{'Job ID':<36} {'Status':<10} {'Editor':<12} {'Progress':<10} {'Created':<19}")
        click.echo("-" * 90)

        for job in jobs:
            progress = f"{job.progress:.0%}"
            created = job.created_at.strftime("%Y-%m-%d %H:%M:%S")
            click.echo(
                f"{job.job_id:<36} {job.status.value:<10} {job.editor_type:<12} {progress:<10} {created:<19}"
            )

    except Exception as e:
        click.echo(f"Error: {e}", err=True)


async def _create_mock_editor(
    editor_type: str, model_manager: ModelManager, config: dict[str, Any]
):
    """Create appropriate editor based on type."""

    if editor_type == "structural":
        # Use StructuralEditor for scene and structure analysis
        return StructuralEditor(model_manager, config)
    elif editor_type == "continuity":
        # Use ContinuityEditor for character and plot consistency
        return ContinuityEditor(model_manager, config)
    elif editor_type == "style":
        # Use StyleEditor for POV, voice, and prose analysis
        return StyleEditor(model_manager, config)
    else:
        # Use mock editor for idea analysis (for now)
        class MockEditor:
            def __init__(self, editor_type, model_manager, config):
                self.editor_type = editor_type
                self.model_manager = model_manager
                self.config = config

            async def analyze(self, context):
                # Perform actual AI analysis
                if context.story_idea:
                    prompt = f"""Analyze this story idea for conceptual strength and provide editorial feedback. Focus on:

1. Plot structure and pacing
2. Character development potential
3. Thematic depth
4. Originality and marketability
5. Areas for improvement

Story Idea:
{json.dumps(context.story_idea, indent=2)}

Provide a comprehensive editorial assessment with specific strengths and actionable suggestions."""
                else:
                    prompt = f"Analyze this content for {self.editor_type}"

                response = await self.model_manager.call_model(
                    prompt=prompt,
                    temperature=0.3,
                    max_tokens=1000,
                )

                # Create feedback from AI response
                feedback = EditorialFeedback(
                    editor_type=self.editor_type,
                    overall_assessment=response[:500] + "..." if len(response) > 500 else response,
                    issues=[
                        EditorialIssue(
                            severity="info",
                            category="conceptual",
                            description="AI analysis completed - see overall assessment",
                            suggestion="Review the detailed feedback above",
                            confidence_score=0.9,
                        )
                    ],
                    suggested_revisions=[],
                    strengths=["AI-powered analysis performed", "Detailed feedback provided"],
                    metadata={
                        "timestamp": datetime.now().isoformat(),
                        "model_used": self.model_manager.current_model,
                        "cost_usd": 0.01,  # Will be calculated properly later
                        "ai_response": response,
                        "analysis_type": "idea_editorial_review",
                    },
                )
                return feedback

            def validate_input(self, context):
                # Basic validation
                errors = []
                if not context.story_idea and self.editor_type.startswith("idea"):
                    errors.append("Story idea required for idea editor")
                if not context.prose and self.editor_type.startswith("content"):
                    errors.append("Prose required for content editor")
                return errors

        return MockEditor(editor_type, model_manager, config)


async def _load_story_context_from_idea_file(idea_file: str) -> StoryContext:
    """Load story context from idea file."""
    try:
        with open(idea_file, encoding="utf-8") as f:
            idea_data = json.load(f)

        # Create context with the idea data
        context = StoryContext()
        context.story_idea = idea_data  # Store the raw idea data
        return context
    except Exception as e:
        raise click.ClickException(f"Failed to load idea file {idea_file}: {e}")


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
        return story_data
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
        }


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
        return feedback_data
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
        }


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

    return current_story


def _extract_quality_score(feedback_data: dict) -> float:
    """Extract quality score from feedback data."""
    score = feedback_data.get("quality_score", 5.0)
    # Ensure score is between 1-10
    return max(1.0, min(10.0, float(score)))
