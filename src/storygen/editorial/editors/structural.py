"""Structural editor for analyzing story prose content."""

import asyncio
from typing import Any

from ..base import BaseEditor, EditorialFeedback, EditorialIssue, StoryContext
from ..core.model_manager import ModelManager


class StructuralEditor(BaseEditor):
    """Editor that analyzes story structure and pacing."""

    def __init__(self, model_manager: ModelManager, config: dict[str, Any]):
        super().__init__(model_manager, config)
        self.batch_size = config.get("batch_size", 5)  # scenes per batch
        self.max_concurrent_batches = config.get("max_concurrent_batches", 3)

    async def analyze(self, context: StoryContext) -> EditorialFeedback:
        """Analyze story structure and pacing."""
        feedback = self._create_feedback_container("structural")

        if not context.prose:
            feedback.issues.append(
                EditorialIssue(
                    severity="major",
                    category="structure",
                    description="No prose content found to analyze",
                    suggestion="Provide story prose content for structural analysis",
                )
            )
            return feedback

        try:
            # Analyze overall structure
            overall_feedback = await self._analyze_overall_structure(context)
            feedback.overall_assessment = overall_feedback

            # Analyze scenes in batches
            scene_analyses = await self._analyze_scenes_batch(context)

            # Compile issues and suggestions
            for scene_analysis in scene_analyses:
                feedback.issues.extend(scene_analysis.get("issues", []))
                feedback.suggested_revisions.extend(scene_analysis.get("revisions", []))

            # Add structural strengths
            feedback.strengths = self._identify_structural_strengths(scene_analyses)

            feedback.metadata.update(
                {
                    "scenes_analyzed": len(scene_analyses),
                    "analysis_type": "structural",
                    "batch_size": self.batch_size,
                }
            )

        except Exception as e:
            self.logger.error(f"Structural analysis failed: {e}")
            return self._handle_analysis_error(e, context)

        return feedback

    def validate_input(self, context: StoryContext) -> list[str]:
        """Validate input for structural analysis."""
        errors = []

        if not context.prose:
            errors.append("Prose content required for structural analysis")
            return errors

        # Check if prose has scenes or can be divided into analyzable units
        if hasattr(context.prose, "scenes") and context.prose.scenes:
            if len(context.prose.scenes) == 0:
                errors.append("Prose must contain at least one scene")
        elif hasattr(context.prose, "content") and context.prose.content:
            # Check if content is long enough for meaningful analysis
            content_length = len(str(context.prose.content))
            if content_length < 500:
                errors.append(
                    "Prose content too short for structural analysis (minimum 500 characters)"
                )
        else:
            errors.append("Prose content not in expected format")

        return errors

    async def _analyze_overall_structure(self, context: StoryContext) -> str:
        """Analyze the overall story structure."""
        prompt = f"""Analyze the overall structure and pacing of this story. Focus on:

1. Three-act structure adherence (setup, confrontation, resolution)
2. Pacing and tension building
3. Plot arc development
4. Scene transitions and flow
5. Overall narrative coherence

Story Content:
{self._extract_story_text(context)}

Provide a comprehensive assessment of the story's structural strengths and weaknesses."""

        response = await self.model_manager.call_model(
            prompt=prompt,
            temperature=0.3,
            max_tokens=800,
        )

        return response

    async def _analyze_scenes_batch(self, context: StoryContext) -> list[dict[str, Any]]:
        """Analyze scenes in batches with concurrency control."""
        scenes = self._extract_scenes(context)
        if not scenes:
            return []

        # Process scenes in batches
        semaphore = asyncio.Semaphore(self.max_concurrent_batches)
        results = []

        for i in range(0, len(scenes), self.batch_size):
            batch = scenes[i : i + self.batch_size]

            # Process batch concurrently with semaphore
            batch_tasks = [
                self._analyze_scene(scene, idx + i, semaphore) for idx, scene in enumerate(batch)
            ]

            batch_results = await asyncio.gather(*batch_tasks)
            results.extend(batch_results)

        return results

    async def _analyze_scene(
        self, scene: dict[str, Any], scene_index: int, semaphore: asyncio.Semaphore
    ) -> dict[str, Any]:
        """Analyze a single scene."""
        async with semaphore:
            scene_text = scene.get("content", "")
            scene_title = scene.get("title", f"Scene {scene_index + 1}")

            prompt = f"""Analyze this scene for structural elements:

Scene: {scene_title}

Content:
{scene_text}

Evaluate:
1. Scene purpose and function in the overall plot
2. Conflict and tension level
3. Character development contribution
4. Pacing and length appropriateness
5. Transition effectiveness

Provide specific feedback on strengths and areas for improvement."""

            try:
                response = await self.model_manager.call_model(
                    prompt=prompt,
                    temperature=0.3,
                    max_tokens=400,
                )

                # Parse response for issues and revisions
                issues, revisions = self._parse_scene_feedback(response, scene_index)

                return {
                    "scene_index": scene_index,
                    "scene_title": scene_title,
                    "analysis": response,
                    "issues": issues,
                    "revisions": revisions,
                }

            except Exception as e:
                self.logger.error(f"Failed to analyze scene {scene_index}: {e}")
                return {
                    "scene_index": scene_index,
                    "scene_title": scene_title,
                    "analysis": f"Analysis failed: {e}",
                    "issues": [],
                    "revisions": [],
                }

    def _parse_scene_feedback(
        self, feedback: str, scene_index: int
    ) -> tuple[list[EditorialIssue], list[Any]]:
        """Parse AI feedback into structured issues and revisions."""
        from ..base import RevisionSuggestion

        issues = []
        revisions = []

        feedback_lower = feedback.lower()

        # Create specific revision suggestions based on feedback content
        if "weak" in feedback_lower or "problem" in feedback_lower:
            issues.append(
                EditorialIssue(
                    severity="minor",
                    category="structure",
                    description=f"Scene {scene_index + 1} structural concerns",
                    suggestion="Review scene analysis for specific improvements",
                    scene_ids=[f"scene_{scene_index + 1}"],
                )
            )
            # Create actionable revision
            revisions.append(
                RevisionSuggestion(
                    revision_type="rewrite",
                    priority="medium",
                    reason="Structural weaknesses identified in scene analysis",
                    instruction=f"Rewrite scene {scene_index + 1} to address: {feedback[:200]}...",
                    scene_id=f"scene_{scene_index + 1}",
                    target_word_count=None,  # Keep similar length
                    estimated_tokens=500,
                )
            )

        if "pacing" in feedback_lower and ("slow" in feedback_lower or "fast" in feedback_lower):
            issues.append(
                EditorialIssue(
                    severity="minor",
                    category="pacing",
                    description=f"Scene {scene_index + 1} pacing issues",
                    suggestion="Adjust scene length or tension for better pacing",
                    scene_ids=[f"scene_{scene_index + 1}"],
                )
            )
            # Create pacing revision
            if "slow" in feedback_lower:
                revision_instruction = f"Add tension and urgency to scene {scene_index + 1} by introducing immediate conflict or stakes"
            else:
                revision_instruction = f"Slow down scene {scene_index + 1} by adding descriptive details and character introspection"

            revisions.append(
                RevisionSuggestion(
                    revision_type="rewrite",
                    priority="medium",
                    reason="Pacing issues affecting scene rhythm",
                    instruction=revision_instruction,
                    scene_id=f"scene_{scene_index + 1}",
                    target_word_count=None,
                    estimated_tokens=400,
                )
            )

        # Add expansion suggestions for underdeveloped scenes
        if "expand" in feedback_lower or "more detail" in feedback_lower:
            revisions.append(
                RevisionSuggestion(
                    revision_type="expand",
                    priority="low",
                    reason="Scene needs more development",
                    instruction=f"Expand scene {scene_index + 1} with additional sensory details and character development",
                    scene_id=f"scene_{scene_index + 1}",
                    target_word_count=300,  # Suggest expansion
                    estimated_tokens=600,
                )
            )

        return issues, revisions

    def _extract_scenes(self, context: StoryContext) -> list[dict[str, Any]]:
        """Extract scenes from the story context."""
        if not context.prose:
            return []

        # Try different ways to extract scenes
        if hasattr(context.prose, "scenes") and context.prose.scenes:
            return context.prose.scenes
        elif hasattr(context.prose, "content"):
            # Split content into scenes by common delimiters
            content = str(context.prose.content)
            scene_delimiters = ["## ", "Scene ", "\n\n---\n\n", "\n\n***\n\n"]

            scenes = []
            current_content = content

            for delimiter in scene_delimiters:
                if delimiter in current_content:
                    parts = current_content.split(delimiter)
                    if len(parts) > 1:
                        scenes = [
                            {"title": f"Scene {i+1}", "content": part.strip()}
                            for i, part in enumerate(parts)
                            if part.strip()
                        ]
                        break

            if not scenes:
                # Fallback: treat entire content as one scene
                scenes = [{"title": "Main Scene", "content": content}]

            return scenes

        return []

    def _extract_story_text(self, context: StoryContext) -> str:
        """Extract readable text from story context."""
        if not context.prose:
            return ""

        if hasattr(context.prose, "to_text"):
            return context.prose.to_text()
        elif hasattr(context.prose, "content"):
            return str(context.prose.content)
        else:
            return str(context.prose)

    def _identify_structural_strengths(self, scene_analyses: list[dict[str, Any]]) -> list[str]:
        """Identify overall structural strengths from scene analyses."""
        strengths = []

        # Look for common positive patterns
        strong_scenes = sum(
            1
            for analysis in scene_analyses
            if "strong" in analysis.get("analysis", "").lower()
            or "effective" in analysis.get("analysis", "").lower()
        )

        if strong_scenes > len(scene_analyses) * 0.7:
            strengths.append("Consistent scene quality throughout the story")

        if len(scene_analyses) >= 3:
            strengths.append("Well-developed multi-scene structure")

        # Add default strengths
        strengths.extend(
            [
                "Clear narrative progression",
                "Effective scene transitions",
            ]
        )

        return strengths
