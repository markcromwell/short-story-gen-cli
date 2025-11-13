"""Continuity editor for analyzing character and plot consistency."""

from typing import Any

from ..base import BaseEditor, EditorialFeedback, EditorialIssue, RevisionSuggestion, StoryContext
from ..core.model_manager import ModelManager


class ContinuityEditor(BaseEditor):
    """Editor that analyzes story continuity and consistency."""

    def __init__(self, model_manager: ModelManager, config: dict[str, Any]):
        super().__init__(model_manager, config)
        self.batch_size = config.get("batch_size", 3)  # scenes per batch for continuity
        self.max_concurrent_batches = config.get("max_concurrent_batches", 2)

    async def analyze(self, context: StoryContext) -> EditorialFeedback:
        """Analyze story continuity and consistency."""
        feedback = self._create_feedback_container("continuity")

        if not context.prose:
            feedback.issues.append(
                EditorialIssue(
                    severity="major",
                    category="continuity",
                    description="No prose content found to analyze",
                    suggestion="Provide story prose content for continuity analysis",
                )
            )
            return feedback

        try:
            # Extract characters and timeline
            characters = self._extract_characters(context)
            timeline = self._extract_timeline(context)

            # Analyze character consistency
            character_issues = await self._analyze_character_consistency(context, characters)
            feedback.issues.extend(character_issues)

            # Analyze plot continuity
            plot_issues = await self._analyze_plot_continuity(context, timeline)
            feedback.issues.extend(plot_issues)

            # Analyze world-building consistency
            world_issues = await self._analyze_world_consistency(context)
            feedback.issues.extend(world_issues)

            # Generate overall assessment
            feedback.overall_assessment = self._generate_continuity_assessment(
                character_issues, plot_issues, world_issues
            )

            # Identify continuity strengths
            feedback.strengths = self._identify_continuity_strengths(
                character_issues, plot_issues, world_issues
            )

            # Create revision suggestions
            feedback.suggested_revisions = self._create_continuity_revisions(
                character_issues + plot_issues + world_issues
            )

            feedback.metadata.update(
                {
                    "characters_identified": len(characters),
                    "timeline_events": len(timeline),
                    "analysis_type": "continuity",
                }
            )

        except Exception as e:
            self.logger.error(f"Continuity analysis failed: {e}")
            return self._handle_analysis_error(e, context)

        return feedback

    def validate_input(self, context: StoryContext) -> list[str]:
        """Validate input for continuity analysis."""
        errors = []

        if not context.prose:
            errors.append("Prose content required for continuity analysis")
            return errors

        # Check if content is substantial enough for continuity analysis
        content_length = self._get_content_length(context)
        if content_length < 1000:
            errors.append(
                "Content too short for meaningful continuity analysis (minimum 1000 characters)"
            )

        return errors

    def _extract_characters(self, context: StoryContext) -> list[dict[str, Any]]:
        """Extract character information from the story."""
        # This is a simplified extraction - in practice, this could be more sophisticated
        story_text = self._extract_story_text(context)

        # Look for common character indicators
        characters = []

        # Extract potential character names (capitalized words that appear multiple times)
        words = story_text.split()
        capitalized_words = [word.strip('.,!?;:') for word in words if word[0].isupper() and len(word) > 2]

        # Count frequency
        from collections import Counter
        word_counts = Counter(capitalized_words)

        # Consider words that appear multiple times as potential characters
        potential_characters = [word for word, count in word_counts.items() if count >= 2]

        for name in potential_characters[:10]:  # Limit to top 10
            characters.append({
                "name": name,
                "mentions": word_counts[name],
                "traits": [],  # Would be populated by AI analysis
                "relationships": [],  # Would be populated by AI analysis
            })

        return characters

    def _extract_timeline(self, context: StoryContext) -> list[dict[str, Any]]:
        """Extract timeline events from the story."""
        scenes = self._extract_scenes(context)
        timeline = []

        for i, scene in enumerate(scenes):
            timeline.append({
                "scene_id": f"scene_{i+1}",
                "title": scene.get("title", f"Scene {i+1}"),
                "events": [],  # Would be populated by AI analysis
                "sequence": i,
            })

        return timeline

    async def _analyze_character_consistency(
        self, context: StoryContext, characters: list[dict[str, Any]]
    ) -> list[EditorialIssue]:
        """Analyze character consistency throughout the story."""
        issues: list[EditorialIssue] = []

        if not characters:
            return issues

        story_text = self._extract_story_text(context)

        prompt = f"""Analyze character consistency in this story. Look for:

1. Character names used consistently
2. Character traits and personalities maintained
3. Character relationships consistent throughout
4. Character development logical and coherent

Story Content:
{story_text}

Characters identified: {', '.join([c['name'] for c in characters])}

Provide specific feedback on any continuity issues found."""

        try:
            response = await self.model_manager.call_model(
                prompt=prompt,
                temperature=0.2,  # Low temperature for consistency analysis
                max_tokens=600,
            )

            # Parse response for specific issues
            issues.extend(self._parse_character_feedback(response))

        except Exception as e:
            self.logger.error(f"Character consistency analysis failed: {e}")

        return issues

    async def _analyze_plot_continuity(
        self, context: StoryContext, timeline: list[dict[str, Any]]
    ) -> list[EditorialIssue]:
        """Analyze plot continuity and timeline consistency."""
        issues = []

        story_text = self._extract_story_text(context)

        prompt = f"""Analyze plot continuity and timeline consistency in this story. Look for:

1. Chronological consistency of events
2. Cause and effect relationships logical
3. Plot threads resolved appropriately
4. Timeline gaps or contradictions
5. Foreshadowing and payoff alignment

Story Content:
{story_text}

Provide specific feedback on any plot continuity issues found."""

        try:
            response = await self.model_manager.call_model(
                prompt=prompt,
                temperature=0.2,
                max_tokens=600,
            )

            issues.extend(self._parse_plot_feedback(response))

        except Exception as e:
            self.logger.error(f"Plot continuity analysis failed: {e}")

        return issues

    async def _analyze_world_consistency(self, context: StoryContext) -> list[EditorialIssue]:
        """Analyze world-building and setting consistency."""
        issues = []

        story_text = self._extract_story_text(context)

        prompt = f"""Analyze world-building and setting consistency in this story. Look for:

1. Consistent rules of the world/universe
2. Location descriptions consistent throughout
3. Technology/magic systems coherent
4. Cultural/social norms maintained
5. Object and place consistency

Story Content:
{story_text}

Provide specific feedback on any world-building continuity issues found."""

        try:
            response = await self.model_manager.call_model(
                prompt=prompt,
                temperature=0.2,
                max_tokens=500,
            )

            issues.extend(self._parse_world_feedback(response))

        except Exception as e:
            self.logger.error(f"World consistency analysis failed: {e}")

        return issues

    def _parse_character_feedback(self, feedback: str) -> list[EditorialIssue]:
        """Parse AI feedback into character continuity issues."""
        issues = []

        feedback_lower = feedback.lower()

        # Look for common character continuity problems
        if "inconsistent" in feedback_lower or "contradiction" in feedback_lower:
            issues.append(
                EditorialIssue(
                    severity="major",
                    category="character",
                    description="Character inconsistency detected",
                    suggestion="Review character traits and ensure consistency throughout the story",
                    confidence_score=0.8,
                )
            )

        if "name" in feedback_lower and ("wrong" in feedback_lower or "different" in feedback_lower):
            issues.append(
                EditorialIssue(
                    severity="major",
                    category="character",
                    description="Character name inconsistency",
                    suggestion="Ensure character names are used consistently throughout",
                    confidence_score=0.9,
                )
            )

        if "relationship" in feedback_lower and ("confusing" in feedback_lower or "inconsistent" in feedback_lower):
            issues.append(
                EditorialIssue(
                    severity="minor",
                    category="character",
                    description="Character relationship inconsistency",
                    suggestion="Clarify and maintain consistent character relationships",
                    confidence_score=0.7,
                )
            )

        return issues

    def _parse_plot_feedback(self, feedback: str) -> list[EditorialIssue]:
        """Parse AI feedback into plot continuity issues."""
        issues = []

        feedback_lower = feedback.lower()

        if "timeline" in feedback_lower and ("gap" in feedback_lower or "missing" in feedback_lower):
            issues.append(
                EditorialIssue(
                    severity="major",
                    category="plot",
                    description="Timeline gap or inconsistency",
                    suggestion="Fill timeline gaps and ensure chronological consistency",
                    confidence_score=0.8,
                )
            )

        if "cause" in feedback_lower and "effect" in feedback_lower:
            if "illogical" in feedback_lower or "doesn't make sense" in feedback_lower:
                issues.append(
                    EditorialIssue(
                        severity="major",
                        category="plot",
                        description="Illogical cause-effect relationship",
                        suggestion="Ensure plot events have logical cause-effect connections",
                        confidence_score=0.8,
                    )
                )

        if "foreshadowing" in feedback_lower and ("missing" in feedback_lower or "unresolved" in feedback_lower):
            issues.append(
                EditorialIssue(
                    severity="minor",
                    category="plot",
                    description="Unresolved foreshadowing",
                    suggestion="Ensure foreshadowed elements are properly resolved",
                    confidence_score=0.7,
                )
            )

        return issues

    def _parse_world_feedback(self, feedback: str) -> list[EditorialIssue]:
        """Parse AI feedback into world-building continuity issues."""
        issues = []

        feedback_lower = feedback.lower()

        if "world" in feedback_lower and ("inconsistent" in feedback_lower or "contradiction" in feedback_lower):
            issues.append(
                EditorialIssue(
                    severity="major",
                    category="world",
                    description="World-building inconsistency",
                    suggestion="Maintain consistent world rules and setting details",
                    confidence_score=0.8,
                )
            )

        if "location" in feedback_lower and ("wrong" in feedback_lower or "different" in feedback_lower):
            issues.append(
                EditorialIssue(
                    severity="minor",
                    category="world",
                    description="Location description inconsistency",
                    suggestion="Ensure location details remain consistent throughout",
                    confidence_score=0.7,
                )
            )

        if ("magic" in feedback_lower or "technology" in feedback_lower) and "inconsistent" in feedback_lower:
            issues.append(
                EditorialIssue(
                    severity="major",
                    category="world",
                    description="Magic/technology system inconsistency",
                    suggestion="Maintain consistent rules for supernatural/technological elements",
                    confidence_score=0.8,
                )
            )

        return issues

    def _generate_continuity_assessment(
        self, character_issues: list, plot_issues: list, world_issues: list
    ) -> str:
        """Generate overall continuity assessment."""
        total_issues = len(character_issues) + len(plot_issues) + len(world_issues)

        if total_issues == 0:
            return "Excellent continuity throughout the story. Characters, plot, and world elements are consistent and well-maintained."

        major_issues = sum(1 for issue in character_issues + plot_issues + world_issues
                          if issue.severity == "major")

        if major_issues > 3:
            return f"Significant continuity issues found ({total_issues} total). Major problems with character, plot, and world consistency require attention."
        elif major_issues > 0:
            return f"Moderate continuity issues detected ({total_issues} total). Some inconsistencies in characters, plot, or world-building need fixing."
        else:
            return f"Minor continuity issues found ({total_issues} total). Story is generally consistent with only small details needing attention."

    def _identify_continuity_strengths(
        self, character_issues: list, plot_issues: list, world_issues: list
    ) -> list[str]:
        """Identify continuity strengths."""
        strengths = []

        if len(character_issues) == 0:
            strengths.append("Strong character consistency throughout the story")

        if len(plot_issues) == 0:
            strengths.append("Logical and coherent plot progression")

        if len(world_issues) == 0:
            strengths.append("Consistent world-building and setting details")

        # Add general strengths
        strengths.extend([
            "Clear narrative timeline",
            "Well-established character relationships",
        ])

        return strengths

    def _create_continuity_revisions(self, issues: list[EditorialIssue]) -> list[RevisionSuggestion]:
        """Create revision suggestions based on continuity issues."""
        revisions = []

        for issue in issues:
            if issue.category == "character":
                revisions.append(
                    RevisionSuggestion(
                        revision_type="rewrite",
                        priority="high" if issue.severity == "major" else "medium",
                        reason=f"Character continuity issue: {issue.description}",
                        instruction=f"Fix character inconsistency: {issue.suggestion}",
                        scene_id=None,  # Apply to entire story
                        estimated_tokens=300,
                    )
                )
            elif issue.category == "plot":
                revisions.append(
                    RevisionSuggestion(
                        revision_type="rewrite",
                        priority="high" if issue.severity == "major" else "medium",
                        reason=f"Plot continuity issue: {issue.description}",
                        instruction=f"Fix plot continuity: {issue.suggestion}",
                        scene_id=None,
                        estimated_tokens=400,
                    )
                )
            elif issue.category == "world":
                revisions.append(
                    RevisionSuggestion(
                        revision_type="rewrite",
                        priority="medium",
                        reason=f"World-building continuity issue: {issue.description}",
                        instruction=f"Fix world consistency: {issue.suggestion}",
                        scene_id=None,
                        estimated_tokens=250,
                    )
                )

        return revisions

    def _extract_scenes(self, context: StoryContext) -> list[dict[str, Any]]:
        """Extract scenes from the story context."""
        if not context.prose:
            return []

        if hasattr(context.prose, "scenes") and context.prose.scenes:
            scenes = context.prose.scenes
            return list(scenes) if scenes else []
        elif hasattr(context.prose, "content"):
            content = str(context.prose.content)
            # Simple scene splitting - in practice this could be more sophisticated
            scenes = [{"title": "Main Content", "content": content}]
            return scenes

        return []

    def _extract_story_text(self, context: StoryContext) -> str:
        """Extract readable text from story context."""
        if not context.prose:
            return ""

        if hasattr(context.prose, "to_text"):
            text = context.prose.to_text()
            return str(text) if text is not None else ""
        elif hasattr(context.prose, "content"):
            return str(context.prose.content)
        else:
            return str(context.prose)

    def _get_content_length(self, context: StoryContext) -> int:
        """Get the total content length."""
        story_text = self._extract_story_text(context)
        return len(story_text)
