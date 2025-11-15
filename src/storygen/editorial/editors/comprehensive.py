"""Comprehensive editor that combines structural, continuity, and style analysis."""

import asyncio
from datetime import datetime
from typing import Any

from ..base import BaseEditor, EditorialFeedback, EditorialIssue, RevisionSuggestion, StoryContext


class ComprehensiveEditor(BaseEditor):
    """Editor that performs comprehensive analysis combining structural, continuity, and style analysis."""

    def __init__(self, model_manager, config: dict[str, Any]):
        """Initialize the comprehensive editor."""
        super().__init__(model_manager, config)

    async def analyze(self, context: StoryContext) -> EditorialFeedback:
        """Perform comprehensive analysis combining all specialized editors."""
        # Import specialized editors here to avoid circular imports
        from .continuity import ContinuityEditor
        from .structural import StructuralEditor
        from .style import StyleEditor

        # Create specialized editors
        structural_editor = StructuralEditor(self.model_manager, self.config)
        continuity_editor = ContinuityEditor(self.model_manager, self.config)
        style_editor = StyleEditor(self.model_manager, self.config)

        # Run all analyses concurrently
        tasks = [
            structural_editor.analyze(context),
            continuity_editor.analyze(context),
            style_editor.analyze(context),
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Handle any exceptions
        feedbacks: list[EditorialFeedback] = []
        for i, result in enumerate(results):
            editor_names = ["structural", "continuity", "style"]
            if isinstance(result, Exception):
                # Create error feedback for failed analysis
                error_feedback = EditorialFeedback(
                    editor_type=f"content-{editor_names[i]}",
                    overall_assessment=f"Analysis failed: {str(result)}",
                    issues=[
                        EditorialIssue(
                            severity="major",
                            category="analysis_error",
                            description=f"{editor_names[i].title()} analysis failed: {str(result)}",
                            suggestion="Retry the analysis or check system configuration",
                            confidence_score=1.0,
                        )
                    ],
                    suggested_revisions=[],
                    strengths=[],
                    metadata={
                        "timestamp": datetime.now().isoformat(),
                        "editor_version": "1.0.0",
                        "model_used": self.model_manager.current_model,
                        "analysis_type": f"content-{editor_names[i]}",
                        "error": str(result),
                    },
                )
                feedbacks.append(error_feedback)
            else:
                # Type is guaranteed to be EditorialFeedback here
                feedbacks.append(result)  # type: ignore

        # Combine results from all editors
        return self._combine_feedbacks(feedbacks)

    def _combine_feedbacks(self, feedbacks: list[EditorialFeedback]) -> EditorialFeedback:
        """Combine feedback from multiple specialized editors into comprehensive feedback."""
        # Aggregate all issues, revisions, and strengths
        all_issues = []
        all_revisions = []
        all_strengths = []

        # Track analysis types and metadata
        analysis_types = []
        total_cost = 0.0

        for feedback in feedbacks:
            all_issues.extend(feedback.issues)
            all_revisions.extend(feedback.suggested_revisions)
            all_strengths.extend(feedback.strengths)
            analysis_types.append(feedback.metadata.get("analysis_type", feedback.editor_type))

            # Sum up costs
            cost = feedback.metadata.get("cost_usd", 0.0)
            if isinstance(cost, int | float):
                total_cost += cost

        # Create comprehensive assessment
        overall_assessment = self._generate_comprehensive_assessment(feedbacks, all_issues)

        # Remove duplicates from strengths
        unique_strengths = list(set(all_strengths))

        # Sort issues by severity (major first, then minor, then info)
        severity_order = {"major": 0, "minor": 1, "info": 2}
        all_issues.sort(key=lambda x: severity_order.get(x.severity, 3))

        # Sort revisions by priority (high first, then medium, then low)
        priority_order = {"high": 0, "medium": 1, "low": 2}
        all_revisions.sort(key=lambda x: priority_order.get(x.priority, 3))

        # Create combined metadata
        combined_metadata = {
            "timestamp": datetime.now().isoformat(),
            "editor_version": "1.0.0",
            "model_used": self.model_manager.current_model,
            "analysis_types": analysis_types,
            "total_cost_usd": total_cost,
            "analysis_type": "comprehensive",
            "editors_combined": len(feedbacks),
            "total_issues": len(all_issues),
            "total_revisions": len(all_revisions),
            "total_strengths": len(unique_strengths),
        }

        # Create the feedback object first
        feedback = EditorialFeedback(
            editor_type="comprehensive",
            overall_assessment=overall_assessment,
            issues=all_issues,
            suggested_revisions=all_revisions,
            strengths=unique_strengths,
            metadata=combined_metadata,
        )

        # Now generate the human report with the created feedback object
        feedback.human_report = self._generate_human_report(feedback, feedbacks)

        return feedback

    def _generate_human_report(
        self, feedback: EditorialFeedback, feedbacks: list[EditorialFeedback]
    ) -> str:
        """Generate a human-readable comprehensive report."""
        report_parts = []

        # Header
        report_parts.append("📊 Comprehensive Editorial Analysis Report")
        report_parts.append("=" * 60)

        # Overall assessment
        if feedback.overall_assessment:
            report_parts.append("\n📝 Overall Assessment:")
            report_parts.append(f"   {feedback.overall_assessment}")

        # Analysis summary
        editors_combined = feedback.metadata.get("editors_combined", 0)
        total_issues = feedback.metadata.get("total_issues", 0)
        total_revisions = feedback.metadata.get("total_revisions", 0)
        total_strengths = feedback.metadata.get("total_strengths", 0)

        report_parts.append(f"\n🔍 Analysis Components: {editors_combined}")
        report_parts.append(f"📋 Total Issues Found: {total_issues}")
        report_parts.append(f"🔧 Revision Suggestions: {total_revisions}")
        report_parts.append(f"✅ Strengths Identified: {total_strengths}")

        if total_issues > 0:
            # Count issues by severity
            major_issues = sum(1 for issue in feedback.issues if issue.severity == "major")
            minor_issues = sum(1 for issue in feedback.issues if issue.severity == "minor")
            info_issues = sum(1 for issue in feedback.issues if issue.severity == "info")

            report_parts.append(f"   • Major Issues: {major_issues}")
            report_parts.append(f"   • Minor Issues: {minor_issues}")
            report_parts.append(f"   • Info Notes: {info_issues}")

        # Component analysis summary
        successful_analyses = sum(
            1 for f in feedbacks if not any(i.category == "analysis_error" for i in f.issues)
        )
        failed_analyses = editors_combined - successful_analyses

        if failed_analyses > 0:
            report_parts.append(
                f"\n⚠️ Analysis Status: {successful_analyses}/{editors_combined} components completed"
            )
        else:
            report_parts.append(
                f"\n✅ Analysis Status: All {editors_combined} components completed successfully"
            )

        # Strengths
        if feedback.strengths:
            report_parts.append("\n✅ Overall Strengths:")
            for strength in feedback.strengths[:8]:  # Limit to top 8
                report_parts.append(f"   • {strength}")

        # Issues summary by category
        if feedback.issues:
            report_parts.append("\n⚠️ Issues by Category:")

            # Group issues by category
            categories: dict[str, list[EditorialIssue]] = {}
            for issue in feedback.issues:
                if issue.category not in categories:
                    categories[issue.category] = []
                categories[issue.category].append(issue)

            for category, issues in sorted(categories.items())[:6]:  # Top 6 categories
                major_count = sum(1 for i in issues if i.severity == "major")
                minor_count = sum(1 for i in issues if i.severity == "minor")
                info_count = sum(1 for i in issues if i.severity == "info")

                status = "🔴" if major_count > 0 else "🟡" if minor_count > 0 else "ℹ️"
                report_parts.append(
                    f"   {status} {category.upper()}: {len(issues)} issues ({major_count} major, {minor_count} minor, {info_count} info)"
                )

        # Top issues
        if feedback.issues:
            report_parts.append("\n🚨 Top Priority Issues:")
            top_issues = sorted(
                feedback.issues,
                key=lambda x: {"major": 0, "minor": 1, "info": 2}.get(x.severity, 3),
            )[:5]

            for i, issue in enumerate(top_issues, 1):
                severity_icon = {"major": "🔴", "minor": "🟡", "info": "ℹ️"}.get(
                    issue.severity, "❓"
                )
                report_parts.append(f"   {i}. {severity_icon} {issue.description}")
                if issue.suggestion:
                    report_parts.append(f"      💡 {issue.suggestion}")

        # Revision recommendations summary
        if feedback.suggested_revisions:
            report_parts.append(
                f"\n🔧 Revision Recommendations: {len(feedback.suggested_revisions)}"
            )

            # Group by priority
            priorities: dict[str, list[RevisionSuggestion]] = {"high": [], "medium": [], "low": []}
            for revision in feedback.suggested_revisions:
                priorities[revision.priority].append(revision)

            for priority in ["high", "medium", "low"]:
                revisions = priorities[priority]
                if revisions:
                    priority_icon = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(priority, "❓")
                    report_parts.append(
                        f"   {priority_icon} {priority.upper()} Priority: {len(revisions)} actions"
                    )

                    # Show top 2 examples
                    for revision in revisions[:2]:
                        scene_info = f" (Scene {revision.scene_id})" if revision.scene_id else ""
                        report_parts.append(
                            f"     • {revision.revision_type.title()}{scene_info}: {revision.reason[:60]}..."
                        )

        # Component details
        report_parts.append("\n📈 Component Analysis Details:")
        for fb in feedbacks:
            analysis_type = fb.metadata.get("analysis_type", fb.editor_type)
            issue_count = len(fb.issues)
            revision_count = len(fb.suggested_revisions)
            strength_count = len(fb.strengths)

            # Check if this component had errors
            has_errors = any(i.category == "analysis_error" for i in fb.issues)
            status = "❌" if has_errors else "✅"

            report_parts.append(
                f"   {status} {analysis_type.title()}: {issue_count} issues, {revision_count} revisions, {strength_count} strengths"
            )

        # Footer with metadata
        report_parts.append("\n" + "=" * 60)
        report_parts.append("📊 Comprehensive Analysis Complete")
        report_parts.append(f"   Model: {feedback.metadata.get('model_used', 'Unknown')}")
        report_parts.append(f"   Total Cost: ${feedback.metadata.get('total_cost_usd', 0):.4f}")
        report_parts.append(f"   Timestamp: {feedback.metadata.get('timestamp', 'Unknown')[:19]}")

        return "\n".join(report_parts)

    def _generate_comprehensive_assessment(
        self, feedbacks: list[EditorialFeedback], all_issues: list[EditorialIssue]
    ) -> str:
        """Generate a comprehensive overall assessment from all feedback."""
        # Count issues by severity
        major_issues = [i for i in all_issues if i.severity == "major"]
        minor_issues = [i for i in all_issues if i.severity == "minor"]
        info_issues = [i for i in all_issues if i.severity == "info"]

        # Analyze feedback quality
        successful_analyses = [
            f
            for f in feedbacks
            if not f.issues or not any(i.category == "analysis_error" for i in f.issues)
        ]
        failed_analyses = len(feedbacks) - len(successful_analyses)

        if failed_analyses > 0:
            return f"Comprehensive analysis partially completed. {failed_analyses} analysis components failed. {len(major_issues)} major issues, {len(minor_issues)} minor issues found across successful analyses."

        if not all_issues:
            return "Excellent comprehensive analysis results. No issues found across structural, continuity, and style analysis. The story demonstrates strong writing quality in all evaluated areas."

        # Generate assessment based on issue distribution
        if len(major_issues) > 5:
            quality_level = "significant concerns"
        elif len(major_issues) > 2:
            quality_level = "moderate issues"
        elif len(major_issues) > 0:
            quality_level = "minor issues"
        else:
            quality_level = "strong foundation"

        assessment = f"Comprehensive editorial analysis completed. Story shows {quality_level} with {len(major_issues)} major issues, {len(minor_issues)} minor issues, and {len(info_issues)} informational notes across structural, continuity, and style dimensions."

        # Add specific insights
        if major_issues:
            categories = list(set(i.category for i in major_issues))
            if len(categories) <= 3:
                assessment += f" Key areas needing attention: {', '.join(categories)}."
            else:
                assessment += f" Issues span {len(categories)} different categories."

        return assessment

    def validate_input(self, context: StoryContext) -> list[str]:
        """Validate input for comprehensive analysis."""
        errors = []

        if not context.prose:
            errors.append("Prose content required for comprehensive analysis")
            return errors

        # Check if prose has scenes (required for structural analysis)
        if hasattr(context.prose, "scenes") and context.prose.scenes:
            if len(context.prose.scenes) == 0:
                errors.append("At least one scene required for structural analysis")
        elif hasattr(context.prose, "content") and not context.prose.content:
            errors.append("Prose content cannot be empty")
        else:
            errors.append("Prose must have either scenes or content for analysis")

        return errors
