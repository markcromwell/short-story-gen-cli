"""CLI commands for editorial workflow."""

import asyncio
import json
from pathlib import Path
from typing import Optional, Dict, Any
import click
import logging

from ..core.model_manager import ModelManager
from ..core.job_manager import JobManager, JobStatus
from ..core.config import load_editorial_config
from ..base import StoryContext, ValidationError


@click.group()
def edit():
    """Editorial analysis commands."""
    pass


@edit.command()
@click.option("--idea", "idea_file", type=click.Path(exists=True), required=True,
              help="Path to story idea JSON file")
@click.option("--output", "-o", type=click.Path(), required=True,
              help="Output file for feedback")
@click.option("--model", default=None,
              help="AI model to use (default: configured default)")
@click.option("--max-cost", type=float,
              help="Maximum cost in USD for this analysis")
@click.option("--verbose", "-v", is_flag=True,
              help="Enable verbose output")
def idea(idea_file: str, output: str, model: Optional[str], max_cost: Optional[float], verbose: bool):
    """Analyze story idea for conceptual strength."""
    asyncio.run(_run_idea_editor(idea_file, output, model, max_cost, verbose))


@edit.command()
@click.option("--prose", "prose_file", type=click.Path(exists=True), required=True,
              help="Path to prose JSON file")
@click.option("--focus", type=click.Choice(["structural", "continuity", "style", "comprehensive"]),
              default="comprehensive", help="Analysis focus area")
@click.option("--output", "-o", type=click.Path(), required=True,
              help="Output file for feedback")
@click.option("--model", default=None,
              help="AI model to use (default: configured default)")
@click.option("--max-cost", type=float,
              help="Maximum cost in USD for this analysis")
@click.option("--batch-size", type=int, default=5,
              help="Scenes per batch for analysis")
@click.option("--verbose", "-v", is_flag=True,
              help="Enable verbose output")
def content(prose_file: str, focus: str, output: str, model: Optional[str],
           max_cost: Optional[float], batch_size: int, verbose: bool):
    """Analyze prose content (structural, continuity, or style)."""
    asyncio.run(_run_content_editor(prose_file, focus, output, model, max_cost, batch_size, verbose))


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
@click.option("--status", type=click.Choice(["pending", "running", "paused", "completed", "failed", "cancelled"]))
def list(status: Optional[str]):
    """List jobs."""
    status_filter = JobStatus(status) if status else None
    asyncio.run(_list_jobs(status_filter))


async def _run_idea_editor(
    idea_file: str,
    output: str,
    model: Optional[str],
    max_cost: Optional[float],
    verbose: bool
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


async def _run_content_editor(
    prose_file: str,
    focus: str,
    output: str,
    model: Optional[str],
    max_cost: Optional[float],
    batch_size: int,
    verbose: bool
):
    """Run content editor analysis."""
    try:
        # Load configuration
        config = load_editorial_config()

        # Initialize components
        model_manager = ModelManager(config)
        if model:
            model_manager.current_model = model

        # Load input data
        context = await _load_story_context_from_prose_file(prose_file)

        # Create mock editor for Stage 1
        editor = await _create_mock_editor(f"content-{focus}", model_manager, config)

        # Validate input
        validation_errors = editor.validate_input(context)
        if validation_errors:
            click.echo("Input validation errors:", err=True)
            for error in validation_errors:
                click.echo(f"  - {error}", err=True)
            return

        # Run analysis
        if verbose:
            click.echo(f"Running {focus} content analysis...")

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


async def _list_jobs(status_filter: Optional[JobStatus]):
    """List jobs."""
    try:
        config = load_editorial_config()
        job_manager = JobManager(Path(config.get("job_storage_dir", "./jobs")))

        jobs = await job_manager.list_jobs(status_filter)

        if not jobs:
            click.echo("No jobs found")
            return

        click.echo(f"{'Job ID':<36} {'Status':<10} {'Editor':<12} {'Progress':<10} {'Created':<19}")
        click.echo("-" * 90)

        for job in jobs:
            progress = f"{job.progress:.0%}"
            created = job.created_at.strftime("%Y-%m-%d %H:%M:%S")
            click.echo(f"{job.job_id:<36} {job.status.value:<10} {job.editor_type:<12} {progress:<10} {created:<19}")

    except Exception as e:
        click.echo(f"Error: {e}", err=True)


async def _create_mock_editor(editor_type: str, model_manager: ModelManager, config: Dict[str, Any]):
    """Create mock editor for Stage 1 testing."""
    class MockEditor:
        def __init__(self, editor_type, model_manager, config):
            self.editor_type = editor_type
            self.model_manager = model_manager
            self.config = config

        async def analyze(self, context):
            # Simulate analysis work
            await asyncio.sleep(0.1)
            return await self.model_manager.call_model(
                prompt=f"Analyze this content for {self.editor_type}",
                temperature=0.3,
                max_tokens=500
            )

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
    # Placeholder - will implement proper loading
    return StoryContext()


async def _load_story_context_from_prose_file(prose_file: str) -> StoryContext:
    """Load story context from prose file."""
    # Placeholder - will implement proper loading
    return StoryContext()


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
        "metadata": feedback.metadata
    }

    output_path.write_text(json.dumps(data, indent=2))