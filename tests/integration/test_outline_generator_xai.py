"""
Integration tests for OutlineGenerator with xAI Grok models.

These tests make REAL API calls to xAI Grok models.
They are skipped by default and only run when:
1. The --integration flag is passed to pytest
2. xAI API key is configured
3. The test model (grok-4-fast-reasoning) is available

Run with: pytest tests/integration/ --integration
Or mark specific: pytest -m integration

Prerequisites:
- xAI API key configured (XAI_API_KEY environment variable)
- xAI account with API access
"""

import pytest

from storygen.iterative.generators.outline import OutlineGenerator
from storygen.iterative.models import Character, Location, StoryIdea

# Mark all tests in this file as integration tests
pytestmark = pytest.mark.integration


class TestOutlineGeneratorXAI:
    """Integration tests for OutlineGenerator with real xAI Grok model calls."""

    @pytest.fixture
    def xai_model(self):
        """Return the xAI model to use for testing."""
        return "xai/grok-4-fast-reasoning"

    @pytest.fixture
    def check_xai_api(self):
        """Check if xAI API is available before running tests."""
        import os

        api_key = os.getenv("XAI_API_KEY")
        if not api_key:
            pytest.skip("XAI_API_KEY environment variable not set")

        # Try a simple API call to check if key is valid
        try:
            import litellm

            # Quick test call
            response = litellm.completion(
                model="xai/grok-4-fast-reasoning",
                messages=[{"role": "user", "content": "Hello"}],
                max_tokens=10,
                api_key=api_key,
            )
            if not response.choices:
                pytest.skip("xAI API key appears invalid or model unavailable")
        except Exception as e:
            pytest.skip(f"xAI API not available: {e}")

    @pytest.fixture
    def story_idea(self):
        """Create a sample story idea for outline generation."""
        return StoryIdea(
            raw_idea="A detective who can read minds investigates her own murder",
            one_sentence="A telepathic detective must solve the mystery of her own death while racing against time.",
            expanded="In a noir-tinged cityscape, Detective Sarah Chen discovers she has the unique ability to read minds - a gift that becomes a curse when she finds herself investigating her own murder. As she navigates between life and death, Sarah must piece together the fragments of her final hours, confronting dark secrets and dangerous enemies. Time is running out as her consciousness begins to fade, and she must identify her killer before she loses herself forever.",
            genres=["noir", "psychological thriller", "mystery"],
            tone="Dark, suspenseful, introspective",
            themes=[
                "identity and consciousness",
                "justice vs revenge",
                "mortality and legacy",
            ],
            setting="Modern noir cityscape",
        )

    @pytest.fixture
    def characters(self):
        """Create sample characters for outline generation."""
        return [
            Character(
                name="Detective Sarah Chen",
                role="protagonist",
                bio="A brilliant telepathic detective investigating her own murder",
                goal="Identify her killer before fading away",
                flaw="Too obsessed with justice to see personal cost",
            ),
            Character(
                name="The Killer",
                role="antagonist",
                bio="A cunning murderer with secrets to hide",
                goal="Escape justice and cover tracks",
                flaw="Overconfident in their planning",
            ),
            Character(
                name="Marcus",
                role="ally",
                bio="Sarah's partner who doesn't know she's dead",
                goal="Solve the case",
                flaw="Too trusting",
            ),
        ]

    @pytest.fixture
    def locations(self):
        """Create sample locations for outline generation."""
        return [
            Location(
                name="Crime Scene Alley",
                description="A dark, rain-slicked alley where Sarah was killed",
                significance="The starting point of the mystery",
                atmosphere="Tense, ominous, foreboding",
            ),
            Location(
                name="Police Precinct",
                description="Busy police station with flickering fluorescent lights",
                significance="Sarah's workplace and base of operations",
                atmosphere="Professional, bureaucratic, haunted",
            ),
        ]

    def test_generate_outline_three_act(
        self, xai_model, check_xai_api, story_idea, characters, locations
    ):
        """Test generating outline with three-act structure using xAI Grok."""
        generator = OutlineGenerator(
            model=xai_model,
            structure_type="three-act",
            max_retries=2,
            timeout=300,
        )

        outline, usage_info = generator.generate(story_idea, characters, locations)

        # Validate structure
        assert outline.structure_type == "three-act"
        assert hasattr(outline, "acts")
        assert len(outline.acts) == 3  # Three-act structure should have 3 acts

        # Validate each act has required fields
        for act in outline.acts:
            assert hasattr(act, "title")
            assert hasattr(act, "description")
            assert hasattr(act, "story_application")
            assert hasattr(act, "percentage")
            assert len(act.title) > 0
            assert len(act.story_application) > 0, f"Act '{act.title}' missing story_application"

        # Validate percentages sum to 1.0
        total_percentage = sum(act.percentage for act in outline.acts)
        assert (
            abs(total_percentage - 1.0) < 0.001
        ), f"Percentages sum to {total_percentage}, expected 1.0"

        print("\n[PASS] Generated three-act outline with xAI Grok")
        print(f"  Acts: {len(outline.acts)}")
        for i, act in enumerate(outline.acts):
            print(f"  Act {i+1}: {act.title} ({act.percentage:.1%})")

    def test_generate_outline_save_the_cat(
        self, xai_model, check_xai_api, story_idea, characters, locations
    ):
        """Test generating outline with save-the-cat structure using xAI Grok."""
        generator = OutlineGenerator(
            model=xai_model,
            structure_type="save-the-cat",
            max_retries=2,
            timeout=300,
        )

        outline, usage_info = generator.generate(story_idea, characters, locations)

        # Validate structure
        assert outline.structure_type == "save-the-cat"
        assert hasattr(outline, "acts")
        assert len(outline.acts) > 0

        # Validate each act has required fields
        for act in outline.acts:
            assert hasattr(act, "title")
            assert hasattr(act, "description")
            assert hasattr(act, "story_application")
            assert hasattr(act, "percentage")
            assert len(act.title) > 0
            assert len(act.story_application) > 0, f"Act '{act.title}' missing story_application"

        # Validate percentages sum to 1.0
        total_percentage = sum(act.percentage for act in outline.acts)
        assert (
            abs(total_percentage - 1.0) < 0.001
        ), f"Percentages sum to {total_percentage}, expected 1.0"

        print("\n[PASS] Generated save-the-cat outline with xAI Grok")
        print(f"  Acts: {len(outline.acts)}")
        for i, act in enumerate(outline.acts):
            print(f"  Act {i+1}: {act.title} ({act.percentage:.1%})")

    def test_generate_outline_short_story(
        self, xai_model, check_xai_api, story_idea, characters, locations
    ):
        """Test generating outline with short-story structure using xAI Grok."""
        generator = OutlineGenerator(
            model=xai_model,
            structure_type="short-story",
            max_retries=2,
            timeout=300,
        )

        outline, usage_info = generator.generate(story_idea, characters, locations)

        # Validate structure
        assert outline.structure_type == "short-story"
        assert hasattr(outline, "acts")
        assert len(outline.acts) > 0

        # Validate each act has required fields
        for act in outline.acts:
            assert hasattr(act, "title")
            assert hasattr(act, "description")
            assert hasattr(act, "story_application")
            assert hasattr(act, "percentage")
            assert len(act.title) > 0
            assert len(act.story_application) > 0, f"Act '{act.title}' missing story_application"

        # Validate percentages sum to 1.0
        total_percentage = sum(act.percentage for act in outline.acts)
        assert (
            abs(total_percentage - 1.0) < 0.001
        ), f"Percentages sum to {total_percentage}, expected 1.0"

        print("\n[PASS] Generated short-story outline with xAI Grok")
        print(f"  Acts: {len(outline.acts)}")
        for i, act in enumerate(outline.acts):
            print(f"  Act {i+1}: {act.title} ({act.percentage:.1%})")

    def test_generate_outline_hero_journey(
        self, xai_model, check_xai_api, story_idea, characters, locations
    ):
        """Test generating outline with hero-journey structure using xAI Grok."""
        generator = OutlineGenerator(
            model=xai_model,
            structure_type="hero-journey",
            max_retries=2,
            timeout=300,
        )

        outline, usage_info = generator.generate(story_idea, characters, locations)

        # Validate structure
        assert outline.structure_type == "hero-journey"
        assert hasattr(outline, "acts")
        assert len(outline.acts) > 0

        # Validate each act has required fields
        for act in outline.acts:
            assert hasattr(act, "title")
            assert hasattr(act, "description")
            assert hasattr(act, "story_application")
            assert hasattr(act, "percentage")
            assert len(act.title) > 0
            assert len(act.story_application) > 0, f"Act '{act.title}' missing story_application"

        # Validate percentages sum to 1.0
        total_percentage = sum(act.percentage for act in outline.acts)
        assert (
            abs(total_percentage - 1.0) < 0.001
        ), f"Percentages sum to {total_percentage}, expected 1.0"

        print("\n[PASS] Generated hero-journey outline with xAI Grok")
        print(f"  Acts: {len(outline.acts)}")
        for i, act in enumerate(outline.acts):
            print(f"  Act {i+1}: {act.title} ({act.percentage:.1%})")

    def test_outline_quality_and_coherence(
        self, xai_model, check_xai_api, story_idea, characters, locations
    ):
        """Test that generated outline has quality content and coherence."""
        generator = OutlineGenerator(
            model=xai_model,
            structure_type="three-act",
            timeout=300,
        )

        outline, usage_info = generator.generate(story_idea, characters, locations)

        # Collect all story_application texts
        all_applications = [act.story_application for act in outline.acts]

        # Each story_application should be substantive (at least 100 characters for xAI)
        for i, app in enumerate(all_applications):
            assert (
                len(app) > 100
            ), f"Story application {i+1} should be detailed (got {len(app)} chars)"

        # Total outline text should be substantial
        total_length = sum(len(app) for app in all_applications)
        assert total_length > 1000, "Outline should be comprehensive"

        # Check that story elements are incorporated
        all_text = " ".join(all_applications).lower()
        # Should mention key story elements
        assert "detective" in all_text or "sarah" in all_text, "Should mention protagonist"
        assert "murder" in all_text or "killer" in all_text, "Should mention central mystery"

        print("\n[PASS] Outline quality validated")
        print(f"  Total acts: {len(all_applications)}")
        print(f"  Total length: {total_length} chars")
        print(f"  Average per act: {total_length // len(all_applications)} chars")

    def test_different_structures_different_outlines(
        self, xai_model, check_xai_api, story_idea, characters, locations
    ):
        """Test that different structures produce different outlines."""
        structures = ["three-act", "save-the-cat", "short-story"]

        outlines = {}
        for structure in structures:
            generator = OutlineGenerator(
                model=xai_model,
                structure_type=structure,
                timeout=300,
            )
            outline, usage_info = generator.generate(story_idea, characters, locations)
            outlines[structure] = outline

        # All should be valid
        for structure, outline in outlines.items():
            assert len(outline.acts) > 0
            assert len(outline.acts[0].story_application) > 0

        # Outlines should be different
        act_counts = [len(outline.acts) for outline in outlines.values()]
        if len(set(act_counts)) > 1:  # If they have different numbers of acts
            print(
                f"\n[PASS] Different structures produced different act counts: {dict(zip(structures, act_counts))}"
            )
        else:
            # Check that content is different
            first_acts = [outline.acts[0].story_application for outline in outlines.values()]
            unique_first_acts = set(first_acts)
            assert (
                len(unique_first_acts) > 1
            ), "Different structures should produce different content"

            print("\n[PASS] Different structures produced different content")
            print(f"  Unique first acts: {len(unique_first_acts)}/{len(structures)}")

    def test_retry_on_failure(self, xai_model, check_xai_api, story_idea, characters, locations):
        """Test that generator can recover from failures."""
        # Use very short timeout to potentially trigger retry
        generator = OutlineGenerator(
            model=xai_model,
            structure_type="three-act",
            max_retries=3,
            timeout=10,  # Very short timeout
        )

        # This should either succeed or fail gracefully with retries
        try:
            outline, usage_info = generator.generate(story_idea, characters, locations)
            assert outline is not None
            assert len(outline.acts) > 0
            print("\n[PASS] Generator succeeded within timeout")
        except Exception as e:
            # If it fails, should be due to timeout/retry limits
            error_msg = str(e).lower()
            assert (
                "timeout" in error_msg or "retry" in error_msg or "max retries" in error_msg.lower()
            )
            print(f"\n[PASS] Generator failed gracefully: {e}")
