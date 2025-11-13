"""Job management for long-running editorial analyses."""

import asyncio
import json
import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

from ..base import EditorialFeedback, StoryContext


class JobStatus(Enum):
    """Job execution states."""

    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class JobMetadata:
    """Metadata for tracking job execution."""

    job_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    status: JobStatus = JobStatus.PENDING
    created_at: datetime = field(default_factory=datetime.now)
    started_at: datetime | None = None
    completed_at: datetime | None = None
    progress: float = 0.0  # 0.0 to 1.0
    estimated_completion: datetime | None = None
    current_stage: str = ""
    error_message: str | None = None
    retry_count: int = 0
    max_retries: int = 3

    # Cost and resource tracking
    total_cost_usd: float = 0.0
    tokens_used: int = 0
    duration_seconds: float = 0.0

    # Configuration
    editor_type: str = ""
    model_used: str = ""
    batch_size: int = 5
    max_concurrent_batches: int = 3


@dataclass
class CheckpointData:
    """Data saved at checkpoints for resume capability."""

    job_id: str
    stage: str
    progress: float
    completed_items: list[str] = field(default_factory=list)
    partial_results: dict[str, Any] = field(default_factory=dict)
    context_state: dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)


class JobManager:
    """Manages long-running editorial analysis jobs."""

    def __init__(self, storage_dir: Path, max_concurrent_jobs: int = 5):
        self.storage_dir = storage_dir
        self.jobs_dir = storage_dir / "jobs"
        self.checkpoints_dir = storage_dir / "checkpoints"
        self.jobs_dir.mkdir(parents=True, exist_ok=True)
        self.checkpoints_dir.mkdir(parents=True, exist_ok=True)

        self.active_jobs: dict[str, asyncio.Task] = {}
        self.job_metadata: dict[str, JobMetadata] = {}
        self.semaphore = asyncio.Semaphore(max_concurrent_jobs)
        self.logger = logging.getLogger(__name__)

    async def start_job(
        self, editor_type: str, context: StoryContext, config: dict[str, Any]
    ) -> str:
        """Start a new editorial analysis job."""
        job_id = str(uuid.uuid4())

        # Create job metadata
        metadata = JobMetadata(
            job_id=job_id,
            editor_type=editor_type,
            model_used=config.get("model", "ollama/qwen3:30b"),
            batch_size=config.get("batch_size", 5),
            max_concurrent_batches=config.get("max_concurrent_batches", 3),
        )

        # Save initial metadata
        await self._save_job_metadata(metadata)

        # Start the job task
        task = asyncio.create_task(self._run_job(job_id, editor_type, context, config))

        self.active_jobs[job_id] = task
        self.job_metadata[job_id] = metadata

        return job_id

    async def pause_job(self, job_id: str) -> bool:
        """Pause a running job."""
        if job_id not in self.active_jobs:
            return False

        metadata = await self._load_job_metadata(job_id)
        if metadata.status != JobStatus.RUNNING:
            return False

        # Signal pause (implementation depends on editor)
        metadata.status = JobStatus.PAUSED
        await self._save_job_metadata(metadata)

        return True

    async def resume_job(self, job_id: str) -> bool:
        """Resume a paused job."""
        metadata = await self._load_job_metadata(job_id)
        if metadata.status != JobStatus.PAUSED:
            return False

        # Load checkpoint
        checkpoint = await self._load_checkpoint(job_id)
        if not checkpoint:
            return False

        # Resume from checkpoint
        metadata.status = JobStatus.RUNNING
        metadata.started_at = datetime.now()
        await self._save_job_metadata(metadata)

        # Restart the job task from checkpoint
        context = await self._restore_context_from_checkpoint(checkpoint)
        config = await self._load_job_config(job_id)

        task = asyncio.create_task(
            self._resume_job_from_checkpoint(job_id, checkpoint, context, config)
        )

        self.active_jobs[job_id] = task
        return True

    async def cancel_job(self, job_id: str) -> bool:
        """Cancel a job."""
        if job_id not in self.active_jobs:
            return False

        # Cancel the task
        task = self.active_jobs[job_id]
        task.cancel()

        # Update metadata
        metadata = await self._load_job_metadata(job_id)
        metadata.status = JobStatus.CANCELLED
        metadata.completed_at = datetime.now()
        await self._save_job_metadata(metadata)

        # Clean up
        del self.active_jobs[job_id]
        del self.job_metadata[job_id]

        return True

    async def get_job_status(self, job_id: str) -> JobMetadata | None:
        """Get current job status."""
        return await self._load_job_metadata(job_id)

    async def list_jobs(self, status_filter: JobStatus | None = None) -> list[JobMetadata]:
        """List all jobs, optionally filtered by status."""
        all_jobs = []

        for job_file in self.jobs_dir.glob("*.json"):
            try:
                metadata = await self._load_job_metadata(job_file.stem)
                if not status_filter or metadata.status == status_filter:
                    all_jobs.append(metadata)
            except Exception:
                continue  # Skip corrupted job files

        return sorted(all_jobs, key=lambda j: j.created_at, reverse=True)

    async def _run_job(
        self, job_id: str, editor_type: str, context: StoryContext, config: dict[str, Any]
    ):
        """Execute a job with basic error handling."""
        metadata = await self._load_job_metadata(job_id)
        metadata.status = JobStatus.RUNNING
        metadata.started_at = datetime.now()
        await self._save_job_metadata(metadata)

        try:
            async with self.semaphore:
                # Initialize editor (placeholder for now)
                editor = await self._create_editor(editor_type, config)

                # Run analysis
                metadata.current_stage = "analyzing"
                await self._save_job_metadata(metadata)

                feedback = await editor.analyze(context)

                # Save final result
                await self._save_job_result(job_id, feedback)

                # Save to user-specified output file if provided
                output_file = config.get("output_file")
                if output_file:
                    await self._save_user_result(output_file, feedback)

                # Update metadata
                metadata.status = JobStatus.COMPLETED
                metadata.completed_at = datetime.now()
                metadata.progress = 1.0
                metadata.duration_seconds = (
                    metadata.completed_at - metadata.started_at
                ).total_seconds()
                await self._save_job_metadata(metadata)

        except asyncio.CancelledError:
            metadata.status = JobStatus.CANCELLED
            await self._save_job_metadata(metadata)
            raise

        except Exception as e:
            metadata.status = JobStatus.FAILED
            metadata.error_message = str(e)
            metadata.completed_at = datetime.now()
            await self._save_job_metadata(metadata)

            # Auto-retry if under retry limit
            if metadata.retry_count < metadata.max_retries:
                await self._schedule_retry(job_id, editor_type, context, config)

        finally:
            # Clean up active job tracking
            if job_id in self.active_jobs:
                del self.active_jobs[job_id]
            if job_id in self.job_metadata:
                del self.job_metadata[job_id]

    async def _create_editor(self, editor_type: str, config: dict[str, Any]):
        """Create editor instance based on type."""
        from ..core.model_manager import ModelManager

        # Initialize model manager from config
        model_manager = ModelManager(config)
        model_manager.current_model = config.get("model", model_manager.current_model)

        if editor_type.startswith("content"):
            # Use StructuralEditor for content analysis
            from ..editors.structural import StructuralEditor

            return StructuralEditor(model_manager, config)
        else:
            # Use mock editor for idea analysis (for now)
            class MockEditor:
                def __init__(self, editor_type, model_manager, config):
                    self.editor_type = editor_type
                    self.model_manager = model_manager
                    self.config = config

                async def analyze(self, context):
                    import json
                    from datetime import datetime

                    from ..base import EditorialFeedback, EditorialIssue

                    # Perform actual AI analysis for idea
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
                        overall_assessment=response[:500] + "..."
                        if len(response) > 500
                        else response,
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

    async def _save_job_result(self, job_id: str, feedback: EditorialFeedback):
        """Save job result to file."""
        # Save to job-specific result file
        result_file = self.jobs_dir / f"{job_id}_result.json"
        result_data = {
            "job_id": job_id,
            "feedback": {
                "editor_type": feedback.editor_type,
                "overall_assessment": feedback.overall_assessment,
                "issues": [issue.__dict__ for issue in feedback.issues],
                "suggested_revisions": [rev.__dict__ for rev in feedback.suggested_revisions],
                "strengths": feedback.strengths,
                "metadata": feedback.metadata,
            },
        }
        result_file.write_text(json.dumps(result_data, indent=2))

        # Also save to user-specified output file if provided
        # This will be loaded from config in the job
        # For now, we'll handle this in the CLI when checking job completion

    async def _save_user_result(self, output_file: str, feedback: EditorialFeedback):
        """Save result to user-specified output file."""
        from pathlib import Path

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

    async def _save_job_metadata(self, metadata: JobMetadata):
        """Save job metadata to disk."""
        job_file = self.jobs_dir / f"{metadata.job_id}.json"
        job_file.write_text(
            json.dumps(
                {
                    "job_id": metadata.job_id,
                    "status": metadata.status.value,
                    "created_at": metadata.created_at.isoformat(),
                    "started_at": metadata.started_at.isoformat() if metadata.started_at else None,
                    "completed_at": metadata.completed_at.isoformat()
                    if metadata.completed_at
                    else None,
                    "progress": metadata.progress,
                    "estimated_completion": metadata.estimated_completion.isoformat()
                    if metadata.estimated_completion
                    else None,
                    "current_stage": metadata.current_stage,
                    "error_message": metadata.error_message,
                    "retry_count": metadata.retry_count,
                    "max_retries": metadata.max_retries,
                    "total_cost_usd": metadata.total_cost_usd,
                    "tokens_used": metadata.tokens_used,
                    "duration_seconds": metadata.duration_seconds,
                    "editor_type": metadata.editor_type,
                    "model_used": metadata.model_used,
                    "batch_size": metadata.batch_size,
                    "max_concurrent_batches": metadata.max_concurrent_batches,
                },
                indent=2,
            )
        )

    async def _load_job_metadata(self, job_id: str) -> JobMetadata:
        """Load job metadata from disk."""
        job_file = self.jobs_dir / f"{job_id}.json"
        data = json.loads(job_file.read_text())

        return JobMetadata(
            job_id=data["job_id"],
            status=JobStatus(data["status"]),
            created_at=datetime.fromisoformat(data["created_at"]),
            started_at=datetime.fromisoformat(data["started_at"]) if data["started_at"] else None,
            completed_at=datetime.fromisoformat(data["completed_at"])
            if data["completed_at"]
            else None,
            progress=data["progress"],
            estimated_completion=datetime.fromisoformat(data["estimated_completion"])
            if data["estimated_completion"]
            else None,
            current_stage=data["current_stage"],
            error_message=data["error_message"],
            retry_count=data["retry_count"],
            max_retries=data["max_retries"],
            total_cost_usd=data["total_cost_usd"],
            tokens_used=data["tokens_used"],
            duration_seconds=data["duration_seconds"],
            editor_type=data["editor_type"],
            model_used=data["model_used"],
            batch_size=data["batch_size"],
            max_concurrent_batches=data["max_concurrent_batches"],
        )

    async def _load_checkpoint(self, job_id: str) -> CheckpointData | None:
        """Load the most recent checkpoint for a job."""
        checkpoint_dir = self.checkpoints_dir / job_id
        if not checkpoint_dir.exists():
            return None

        # Find most recent checkpoint
        checkpoint_files = list(checkpoint_dir.glob("*.json"))
        if not checkpoint_files:
            return None

        latest_file = max(checkpoint_files, key=lambda f: f.stat().st_mtime)

        try:
            data = json.loads(latest_file.read_text())
            return CheckpointData(
                job_id=data["job_id"],
                stage=data["stage"],
                progress=data["progress"],
                completed_items=data["completed_items"],
                partial_results=data["partial_results"],
                context_state=data["context_state"],
                timestamp=datetime.fromisoformat(data["timestamp"]),
            )
        except Exception:
            return None

    async def _resume_job_from_checkpoint(
        self, job_id: str, checkpoint: CheckpointData, context: StoryContext, config: dict[str, Any]
    ):
        """Resume job execution from checkpoint."""
        # For Stage 1, just restart the job
        await self._run_job(job_id, config.get("editor_type", "unknown"), context, config)

    async def _schedule_retry(
        self, job_id: str, editor_type: str, context: StoryContext, config: dict[str, Any]
    ):
        """Schedule a retry for a failed job."""
        # For Stage 1, just mark for manual retry
        self.logger.info(f"Job {job_id} failed, manual retry needed")

    async def _load_job_config(self, job_id: str) -> dict[str, Any]:
        """Load job configuration (placeholder)."""
        return {"editor_type": "mock"}

    def _serialize_context(self, context: StoryContext) -> dict[str, Any]:
        """Serialize context for checkpointing."""
        # Placeholder implementation
        return {}

    async def _restore_context_from_checkpoint(self, checkpoint: CheckpointData) -> StoryContext:
        """Restore context from checkpoint."""
        # Placeholder implementation
        return StoryContext()
