"""Style editor for analyzing POV, voice, and prose rhythm."""

from typing import Any

from ..base import BaseEditor, EditorialFeedback, EditorialIssue, RevisionSuggestion, StoryContext
from ..core.model_manager import ModelManager


class StyleEditor(BaseEditor):
    """Editor that analyzes writing style, POV consistency, and prose quality."""

    def __init__(self, model_manager: ModelManager, config: dict[str, Any]):
        super().__init__(model_manager, config)
        self.batch_size = config.get("batch_size", 2)  # scenes per batch for style analysis
        self.max_concurrent_batches = config.get("max_concurrent_batches", 3)

    async def analyze(self, context: StoryContext) -> EditorialFeedback:
        """Analyze writing style and consistency."""
        feedback = self._create_feedback_container("style")

        if not context.prose:
            feedback.issues.append(
                EditorialIssue(
                    severity="major",
                    category="style",
                    description="No prose content found to analyze",
                    suggestion="Provide story prose content for style analysis",
                )
            )
            return feedback

        try:
            # Analyze POV consistency
            pov_issues = await self._analyze_pov_consistency(context)
            feedback.issues.extend(pov_issues)

            # Analyze voice consistency
            voice_issues = await self._analyze_voice_consistency(context)
            feedback.issues.extend(voice_issues)

            # Analyze prose rhythm and sentence structure
            prose_issues = await self._analyze_prose_rhythm(context)
            feedback.issues.extend(prose_issues)

            # Analyze language level appropriateness
            language_issues = await self._analyze_language_level(context)
            feedback.issues.extend(language_issues)

            # Generate overall style assessment
            feedback.overall_assessment = self._generate_style_assessment(
                pov_issues, voice_issues, prose_issues, language_issues
            )

            # Identify style strengths
            feedback.strengths = self._identify_style_strengths(
                pov_issues, voice_issues, prose_issues, language_issues
            )

            # Create revision suggestions
            feedback.suggested_revisions = self._create_style_revisions(
                pov_issues + voice_issues + prose_issues + language_issues
            )

            feedback.metadata.update(
                {
                    "analysis_type": "style",
                    "style_elements_analyzed": ["pov", "voice", "prose_rhythm", "language_level"],
                }
            )

            # Generate human-readable report
            feedback.human_report = self._generate_human_report(feedback)

        except Exception as e:
            self.logger.error(f"Style analysis failed: {e}")
            return self._handle_analysis_error(e, context)

        return feedback

    def validate_input(self, context: StoryContext) -> list[str]:
        """Validate input for style analysis."""
        errors = []

        if not context.prose:
            errors.append("Prose content required for style analysis")
            return errors

        # Check if content is substantial enough for style analysis
        content_length = self._get_content_length(context)
        if content_length < 500:
            errors.append(
                "Content too short for meaningful style analysis (minimum 500 characters)"
            )

        return errors

    async def _analyze_pov_consistency(self, context: StoryContext) -> list[EditorialIssue]:
        """Analyze point of view consistency."""
        issues = []

        story_text = self._extract_story_text(context)

        prompt = f"""Analyze point of view (POV) consistency in this story. Look for:

1. Consistent narrative perspective throughout
2. No inappropriate head-hopping between characters
3. Consistent access to character thoughts and feelings
4. Appropriate distance from events and characters

Story Content:
{story_text}

Provide specific feedback on any POV consistency issues found."""

        try:
            response = await self.model_manager.call_model(
                prompt=prompt,
                temperature=0.2,  # Low temperature for consistency analysis
                max_tokens=500,
            )

            issues.extend(self._parse_pov_feedback(response))

        except Exception as e:
            self.logger.error(f"POV consistency analysis failed: {e}")

        return issues

    async def _analyze_voice_consistency(self, context: StoryContext) -> list[EditorialIssue]:
        """Analyze narrative voice consistency."""
        issues = []

        story_text = self._extract_story_text(context)

        prompt = f"""Analyze narrative voice consistency in this story. Look for:

1. Consistent authorial tone and attitude
2. Consistent level of formality/informality
3. Consistent use of language and vocabulary
4. Consistent authorial presence/intervention

Story Content:
{story_text}

Provide specific feedback on any voice consistency issues found."""

        try:
            response = await self.model_manager.call_model(
                prompt=prompt,
                temperature=0.2,
                max_tokens=500,
            )

            issues.extend(self._parse_voice_feedback(response))

        except Exception as e:
            self.logger.error(f"Voice consistency analysis failed: {e}")

        return issues

    async def _analyze_prose_rhythm(self, context: StoryContext) -> list[EditorialIssue]:
        """Analyze prose rhythm and sentence structure."""
        issues = []

        story_text = self._extract_story_text(context)

        prompt = f"""Analyze prose rhythm and sentence structure in this story. Look for:

1. Varied sentence lengths for good rhythm
2. Appropriate sentence complexity for the content
3. Good balance between simple, compound, and complex sentences
4. Effective use of punctuation for pacing
5. Avoidance of monotonous sentence patterns

Story Content:
{story_text}

Provide specific feedback on any prose rhythm issues found."""

        try:
            response = await self.model_manager.call_model(
                prompt=prompt,
                temperature=0.3,  # Slightly higher temperature for creative analysis
                max_tokens=600,
            )

            issues.extend(self._parse_prose_feedback(response))

        except Exception as e:
            self.logger.error(f"Prose rhythm analysis failed: {e}")

        return issues

    async def _analyze_language_level(self, context: StoryContext) -> list[EditorialIssue]:
        """Analyze language level appropriateness."""
        issues = []

        story_text = self._extract_story_text(context)

        prompt = f"""Analyze language level appropriateness in this story. Look for:

1. Consistent vocabulary level appropriate for target audience
2. Appropriate use of specialized terminology
3. Consistent register (formal/informal) throughout
4. Age-appropriate language for characters and narrator
5. Cultural and contextual appropriateness of language

Story Content:
{story_text}

Provide specific feedback on any language level issues found."""

        try:
            response = await self.model_manager.call_model(
                prompt=prompt,
                temperature=0.2,
                max_tokens=500,
            )

            issues.extend(self._parse_language_feedback(response))

        except Exception as e:
            self.logger.error(f"Language level analysis failed: {e}")

        return issues

    def _parse_pov_feedback(self, feedback: str) -> list[EditorialIssue]:
        """Parse AI feedback into POV consistency issues."""
        issues = []

        feedback_lower = feedback.lower()

        if "head" in feedback_lower and "hop" in feedback_lower:
            issues.append(
                EditorialIssue(
                    severity="major",
                    category="pov",
                    description="Head-hopping detected",
                    suggestion="Maintain consistent POV throughout scenes and avoid switching between characters' perspectives inappropriately",
                    confidence_score=0.9,
                )
            )

        if "pov" in feedback_lower and (
            "inconsistent" in feedback_lower or "shifts" in feedback_lower
        ):
            issues.append(
                EditorialIssue(
                    severity="major",
                    category="pov",
                    description="Inconsistent point of view",
                    suggestion="Choose and maintain a single POV consistently throughout the story",
                    confidence_score=0.8,
                )
            )

        if "third" in feedback_lower and "person" in feedback_lower and "limited" in feedback_lower:
            if "omniscient" in feedback_lower:
                issues.append(
                    EditorialIssue(
                        severity="minor",
                        category="pov",
                        description="POV distance inconsistency",
                        suggestion="Be consistent with how much access readers have to characters' thoughts and feelings",
                        confidence_score=0.7,
                    )
                )

        return issues

    def _parse_voice_feedback(self, feedback: str) -> list[EditorialIssue]:
        """Parse AI feedback into voice consistency issues."""
        issues = []

        feedback_lower = feedback.lower()

        if "voice" in feedback_lower and (
            "inconsistent" in feedback_lower or "changes" in feedback_lower
        ):
            issues.append(
                EditorialIssue(
                    severity="major",
                    category="voice",
                    description="Inconsistent narrative voice",
                    suggestion="Maintain consistent authorial voice and tone throughout the story",
                    confidence_score=0.8,
                )
            )

        if "tone" in feedback_lower and (
            "shifts" in feedback_lower or "inconsistent" in feedback_lower
        ):
            issues.append(
                EditorialIssue(
                    severity="minor",
                    category="voice",
                    description="Tone inconsistency",
                    suggestion="Ensure the story's tone remains consistent with the established voice",
                    confidence_score=0.7,
                )
            )

        if ("formal" in feedback_lower or "informal" in feedback_lower) and "mix" in feedback_lower:
            issues.append(
                EditorialIssue(
                    severity="minor",
                    category="voice",
                    description="Mixed register inconsistency",
                    suggestion="Maintain consistent level of formality throughout the narrative",
                    confidence_score=0.6,
                )
            )

        return issues

    def _parse_prose_feedback(self, feedback: str) -> list[EditorialIssue]:
        """Parse AI feedback into prose rhythm issues."""
        issues = []

        feedback_lower = feedback.lower()

        if "sentence" in feedback_lower and (
            "monotonous" in feedback_lower or "repetitive" in feedback_lower
        ):
            issues.append(
                EditorialIssue(
                    severity="minor",
                    category="prose",
                    description="Monotonous sentence structure",
                    suggestion="Vary sentence lengths and structures to improve prose rhythm",
                    confidence_score=0.7,
                )
            )

        if "rhythm" in feedback_lower and ("poor" in feedback_lower or "awkward" in feedback_lower):
            issues.append(
                EditorialIssue(
                    severity="minor",
                    category="prose",
                    description="Poor prose rhythm",
                    suggestion="Balance short and long sentences, use varied punctuation for better pacing",
                    confidence_score=0.6,
                )
            )

        if "complex" in feedback_lower and (
            "overly" in feedback_lower or "complicated" in feedback_lower
        ):
            issues.append(
                EditorialIssue(
                    severity="minor",
                    category="prose",
                    description="Overly complex sentence structures",
                    suggestion="Simplify sentence structures where appropriate for better readability",
                    confidence_score=0.6,
                )
            )

        return issues

    def _parse_language_feedback(self, feedback: str) -> list[EditorialIssue]:
        """Parse AI feedback into language level issues."""
        issues = []

        feedback_lower = feedback.lower()

        if "vocabulary" in feedback_lower and (
            "inconsistent" in feedback_lower or "mismatched" in feedback_lower
        ):
            issues.append(
                EditorialIssue(
                    severity="minor",
                    category="language",
                    description="Inconsistent vocabulary level",
                    suggestion="Maintain appropriate vocabulary level for your target audience",
                    confidence_score=0.7,
                )
            )

        if "register" in feedback_lower and (
            "inconsistent" in feedback_lower or "mixed" in feedback_lower
        ):
            issues.append(
                EditorialIssue(
                    severity="minor",
                    category="language",
                    description="Mixed language register",
                    suggestion="Be consistent with formal/informal language throughout",
                    confidence_score=0.6,
                )
            )

        if ("age" in feedback_lower or "audience" in feedback_lower) and (
            "inappropriate" in feedback_lower
        ):
            issues.append(
                EditorialIssue(
                    severity="major",
                    category="language",
                    description="Age-inappropriate language",
                    suggestion="Ensure language is appropriate for the target age group",
                    confidence_score=0.8,
                )
            )

        return issues

    def _generate_style_assessment(
        self, pov_issues: list, voice_issues: list, prose_issues: list, language_issues: list
    ) -> str:
        """Generate overall style assessment."""
        total_issues = (
            len(pov_issues) + len(voice_issues) + len(prose_issues) + len(language_issues)
        )

        if total_issues == 0:
            return "Excellent writing style with consistent POV, voice, and engaging prose rhythm."

        major_issues = sum(
            1
            for issue in pov_issues + voice_issues + prose_issues + language_issues
            if issue.severity == "major"
        )

        if major_issues > 2:
            return f"Significant style issues found ({total_issues} total). Major problems with POV consistency and voice require attention."
        elif major_issues > 0:
            return f"Moderate style issues detected ({total_issues} total). Some inconsistencies in POV, voice, or prose rhythm need fixing."
        else:
            return f"Minor style issues found ({total_issues} total). Writing is generally consistent with only small stylistic improvements needed."

    def _identify_style_strengths(
        self, pov_issues: list, voice_issues: list, prose_issues: list, language_issues: list
    ) -> list[str]:
        """Identify style strengths."""
        strengths = []

        if len(pov_issues) == 0:
            strengths.append("Strong, consistent point of view throughout")

        if len(voice_issues) == 0:
            strengths.append("Consistent and engaging narrative voice")

        if len(prose_issues) == 0:
            strengths.append("Good prose rhythm with varied sentence structures")

        if len(language_issues) == 0:
            strengths.append("Appropriate language level for target audience")

        # Add general strengths
        strengths.extend(
            [
                "Clear and engaging writing style",
                "Appropriate tone for the story genre",
            ]
        )

        return strengths

    def _create_style_revisions(self, issues: list[EditorialIssue]) -> list[RevisionSuggestion]:
        """Create revision suggestions based on style issues."""
        revisions = []

        for issue in issues:
            if issue.category == "pov":
                revisions.append(
                    RevisionSuggestion(
                        revision_type="rewrite",
                        priority="high" if issue.severity == "major" else "medium",
                        reason=f"POV consistency issue: {issue.description}",
                        instruction=f"Fix POV consistency: {issue.suggestion}",
                        scene_id=None,  # Apply to entire story
                        estimated_tokens=400,
                    )
                )
            elif issue.category == "voice":
                revisions.append(
                    RevisionSuggestion(
                        revision_type="rewrite",
                        priority="high" if issue.severity == "major" else "medium",
                        reason=f"Voice consistency issue: {issue.description}",
                        instruction=f"Fix voice consistency: {issue.suggestion}",
                        scene_id=None,
                        estimated_tokens=350,
                    )
                )
            elif issue.category == "prose":
                revisions.append(
                    RevisionSuggestion(
                        revision_type="rewrite",
                        priority="low",
                        reason=f"Prose rhythm issue: {issue.description}",
                        instruction=f"Improve prose rhythm: {issue.suggestion}",
                        scene_id=None,
                        estimated_tokens=200,
                    )
                )
            elif issue.category == "language":
                revisions.append(
                    RevisionSuggestion(
                        revision_type="rewrite",
                        priority="medium",
                        reason=f"Language level issue: {issue.description}",
                        instruction=f"Fix language appropriateness: {issue.suggestion}",
                        scene_id=None,
                        estimated_tokens=250,
                    )
                )

        return revisions

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

    def _generate_human_report(self, feedback: EditorialFeedback) -> str:
        """Generate a human-readable report of the style analysis."""
        report_parts = []

        # Header
        report_parts.append("✍️ Style Analysis Report")
        report_parts.append("=" * 50)

        # Overall assessment
        if feedback.overall_assessment:
            report_parts.append("\n📝 Overall Assessment:")
            report_parts.append(f"   {feedback.overall_assessment}")

        # Analysis summary
        style_elements = feedback.metadata.get("style_elements_analyzed", [])
        report_parts.append(f"\n🎨 Style Elements Analyzed: {', '.join(style_elements)}")

        if feedback.issues:
            # Count issues by severity and category
            major_issues = sum(1 for issue in feedback.issues if issue.severity == "major")
            minor_issues = sum(1 for issue in feedback.issues if issue.severity == "minor")
            info_issues = sum(1 for issue in feedback.issues if issue.severity == "info")

            report_parts.append(f"   • Major Issues: {major_issues}")
            report_parts.append(f"   • Minor Issues: {minor_issues}")
            report_parts.append(f"   • Info Notes: {info_issues}")

        # Strengths
        if feedback.strengths:
            report_parts.append("\n✅ Style Strengths:")
            for strength in feedback.strengths:
                report_parts.append(f"   • {strength}")

        # Issues summary
        if feedback.issues:
            report_parts.append("\n⚠️  Key Issues Found:")

            # Group issues by category
            categories: dict[str, list[EditorialIssue]] = {}
            for issue in feedback.issues:
                if issue.category not in categories:
                    categories[issue.category] = []
                categories[issue.category].append(issue)

            for category, issues in categories.items():
                report_parts.append(f"\n   {category.upper()}:")
                for issue in issues[:3]:  # Limit to top 3 per category
                    severity_icon = {"major": "🔴", "minor": "🟡", "info": "ℹ️"}.get(
                        issue.severity, "❓"
                    )
                    report_parts.append(f"     {severity_icon} {issue.description}")
                    if issue.suggestion:
                        report_parts.append(f"        💡 {issue.suggestion}")

        # Revision recommendations
        if feedback.suggested_revisions:
            report_parts.append(f"\n🔧 Recommended Revisions: {len(feedback.suggested_revisions)}")

            # Group by priority
            priorities: dict[str, list[RevisionSuggestion]] = {"high": [], "medium": [], "low": []}
            for revision in feedback.suggested_revisions:
                priorities[revision.priority].append(revision)

            for priority, revisions in priorities.items():
                if revisions:
                    priority_icon = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(priority, "❓")
                    report_parts.append(
                        f"   {priority_icon} {priority.upper()} Priority: {len(revisions)}"
                    )
                    for revision in revisions[:2]:  # Show top 2 per priority
                        report_parts.append(
                            f"     • {revision.revision_type.title()}: {revision.reason[:80]}..."
                        )

        # Footer with metadata
        report_parts.append("\n" + "=" * 50)
        report_parts.append("✍️ Style Analysis Complete")
        report_parts.append(f"   Model: {feedback.metadata.get('model_used', 'Unknown')}")
        report_parts.append(f"   Timestamp: {feedback.metadata.get('timestamp', 'Unknown')[:19]}")

        return "\n".join(report_parts)
