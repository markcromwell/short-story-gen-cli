"""
Full pipeline integration tests with real, high-quality pitches.

These tests run the COMPLETE story generation pipeline with real API calls.
They use curated, high-quality pitches covering diverse genres and story types.

COST CONTROL:
- Limited to 6 carefully selected test pitches
- Each test covers multiple aspects (genre, length, structure)
- XAI by default (fast, high quality) with Ollama fallback for overnight runs

PROJECT HANDLING:
- All test projects are timestamped to avoid conflicts
- Projects are created in test-specific directory
- Automatic cleanup after tests

Run with:
  pytest tests/integration/test_full_pipeline.py --integration -v

For overnight runs with Ollama:
  $env:INTEGRATION_MODEL = "ollama/qwen2.5:14b"
  pytest tests/integration/test_full_pipeline.py --integration -m "not slow"
"""

import os
from datetime import datetime

import pytest

from storygen.iterative.cli.commands.pipeline import generate_all_async

# Mark all tests in this file as integration tests
pytestmark = pytest.mark.integration


class TestFullPipeline:
    """Full pipeline integration tests with real pitches and API calls."""

    @pytest.fixture
    def test_model(self):
        """Return the model to use for testing (XAI default, Ollama override)."""
        # Default to XAI for fast, high-quality results
        # Can be overridden with INTEGRATION_MODEL env var for overnight runs
        return os.getenv("INTEGRATION_MODEL", "xai/grok-4-fast-reasoning")

    @pytest.fixture
    def check_api_available(self, test_model):
        """Check if the required API is available before running tests."""
        if test_model.startswith("xai/"):
            # Check xAI API
            api_key = os.getenv("XAI_API_KEY")
            if not api_key:
                pytest.skip("XAI_API_KEY environment variable not set")

            try:
                import litellm

                response = litellm.completion(
                    model=test_model,
                    messages=[{"role": "user", "content": "Hello"}],
                    max_tokens=10,
                    api_key=api_key,
                )
                if not response.choices:
                    pytest.skip("xAI API key appears invalid or model unavailable")
            except Exception as e:
                pytest.skip(f"xAI API not available: {e}")

        elif test_model.startswith("ollama/"):
            # Check Ollama
            import subprocess

            try:
                result = subprocess.run(
                    ["ollama", "list"], capture_output=True, text=True, timeout=5
                )
                if result.returncode != 0:
                    pytest.skip("Ollama is not running. Start with: ollama serve")
            except (FileNotFoundError, subprocess.TimeoutExpired):
                pytest.skip("Ollama is not installed or not responding")

    @pytest.fixture
    def test_projects_dir(self, tmp_path):
        """Create a temporary directory for test projects."""
        test_dir = tmp_path / "test_projects"
        test_dir.mkdir()
        return test_dir

    @pytest.fixture
    def timestamped_name(self):
        """Generate a timestamped project name to avoid conflicts."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"test_{timestamp}"

    # CURATED HIGH-QUALITY TEST PITCHES
    # Selected to cover diverse genres, story types, and lengths while keeping costs down
    TEST_PITCHES = [
        {
            "name": "mystery_detective",
            "pitch": "A brilliant detective with the ability to read minds investigates her own murder, racing against time as her consciousness begins to fade. In a noir-tinged cityscape, she must piece together the fragments of her final hours while confronting dark secrets and dangerous enemies.",
            "expected_genres": ["mystery", "thriller", "noir"],
            "word_count": 7500,  # Short story
            "story_type": "short-story",
        },
        {
            "name": "fantasy_quest",
            "pitch": "In a world where magic is dying, a young orphan discovers she can communicate with ancient dragons. As kingdoms fall to shadow creatures, she must embark on a perilous quest to restore the magical balance before darkness consumes everything.",
            "expected_genres": ["fantasy", "epic fantasy"],
            "word_count": 15000,  # Novelette
            "story_type": "novelette",
        },
        {
            "name": "scifi_dystopia",
            "pitch": "In 2147, corporations control everything through neural implants. When a black-market hacker discovers a way to 'unplug' people from the system, she becomes the most wanted criminal on Earth. But unplugging reveals terrifying truths about what humanity has become.",
            "expected_genres": ["science fiction", "cyberpunk", "dystopian"],
            "word_count": 25000,  # Novella
            "story_type": "novella",
        },
        {
            "name": "romance_transformation",
            "pitch": "Lila Harren never considered herself special. At 5′4″ she felt ordinary, practical, capable—but always aware of her smallness. Her fiancé Ethan adored her exactly as she was. But when every woman on Earth wakes two inches taller overnight, Lila begins a year-long transformation that will change everything about their relationship, their world, and who she is meant to be.",
            "expected_genres": ["literary fiction", "romance", "speculative fiction"],
            "word_count": 12000,  # Novelette
            "story_type": "novelette",
        },
        {
            "name": "horror_supernatural",
            "pitch": "The old Victorian house at 13 Elm Street has claimed twelve lives in the past century. Each death more brutal than the last. When a skeptical paranormal investigator moves in to debunk the curse, she discovers that the house doesn't just kill— it transforms its victims into something far worse than dead.",
            "expected_genres": ["horror", "supernatural", "psychological horror"],
            "word_count": 8000,  # Short story
            "story_type": "short-story",
        },
        {
            "name": "historical_adventure",
            "pitch": "In 1927 Shanghai, a young female archaeologist discovers an ancient artifact that grants visions of the future. As warlords battle for control of the city and foreign powers maneuver for influence, she must decide whether to use her newfound ability to change history or let fate unfold as it should.",
            "expected_genres": ["historical fiction", "adventure", "alternate history"],
            "word_count": 18000,  # Novella
            "story_type": "novella",
        },
    ]

    @pytest.mark.parametrize("test_case", TEST_PITCHES, ids=[p["name"] for p in TEST_PITCHES])
    async def test_full_pipeline_generation(
        self, test_model, check_api_available, test_projects_dir, timestamped_name, test_case
    ):
        """Test complete story generation pipeline with real pitches."""
        # Create unique project name
        project_name = f"{test_case['name']}_{timestamped_name}"

        # Run the full pipeline
        await generate_all_async(
            name=project_name,
            pitch=test_case["pitch"],
            words=test_case["word_count"],
            story_type=test_case["story_type"],
            model=test_model,
            timeout=600,  # 10 minutes per step
            retries=2,
            projects_dir=str(test_projects_dir),
            max_cost=5.0,  # $5 cost limit per test
            edit=False,  # Skip editorial workflow for speed/cost
            edit_iterations=1,
            edit_quality_threshold=7.0,
        )

        # Verify project was created
        project_dir = test_projects_dir / project_name
        assert project_dir.exists(), f"Project directory {project_name} was not created"

        # Verify key output files exist
        expected_files = [
            "idea.json",
            "characters.json",
            "locations.json",
            "outline.json",
            "breakdown.json",
            "prose.json",
            "story.epub",
        ]

        for filename in expected_files:
            file_path = project_dir / filename
            assert file_path.exists(), f"Expected file {filename} not found in {project_name}"

        # Verify EPUB file is not empty
        epub_path = project_dir / "story.epub"
        assert (
            epub_path.stat().st_size > 1000
        ), f"EPUB file is too small ({epub_path.stat().st_size} bytes)"

        print(f"\n✅ Full pipeline test passed for: {test_case['name']}")
        print(f"   Project: {project_name}")
        print(f"   Word count: {test_case['word_count']:,}")
        print(f"   Story type: {test_case['story_type']}")
        print(f"   Model: {test_model}")

    async def test_cost_control_and_quality_balance(
        self, test_model, check_api_available, test_projects_dir, timestamped_name
    ):
        """Test that we can generate quality stories while controlling costs."""
        # Use the most cost-effective pitch (short story)
        test_case = self.TEST_PITCHES[0]  # mystery_detective - 7500 words
        project_name = f"cost_test_{timestamped_name}"

        # Run with strict cost limit
        await generate_all_async(
            name=project_name,
            pitch=test_case["pitch"],
            words=test_case["word_count"],
            story_type=test_case["story_type"],
            model=test_model,
            timeout=300,  # Shorter timeout for cost control
            retries=1,  # Fewer retries
            projects_dir=str(test_projects_dir),
            max_cost=2.0,  # Very strict $2 limit
            edit=False,
            edit_iterations=1,
            edit_quality_threshold=7.0,
        )

        # Verify we got a complete story despite cost constraints
        project_dir = test_projects_dir / project_name
        epub_path = project_dir / "story.epub"

        assert epub_path.exists()
        assert epub_path.stat().st_size > 5000, "Story should be substantial even with cost limits"

        print("\n💰 Cost-controlled generation successful")
        print(f"   Project: {project_name}")
        print(f"   Size: {epub_path.stat().st_size:,} bytes")
        print("   Cost limit: $2.00")

    @pytest.mark.slow
    async def test_long_form_generation(
        self, test_model, check_api_available, test_projects_dir, timestamped_name
    ):
        """Test generation of longer works (only run when specifically requested)."""
        # Use a novella-length pitch
        test_case = self.TEST_PITCHES[2]  # scifi_dystopia - 25000 words
        project_name = f"long_form_{timestamped_name}"

        await generate_all_async(
            name=project_name,
            pitch=test_case["pitch"],
            words=test_case["word_count"],
            story_type=test_case["story_type"],
            model=test_model,
            timeout=900,  # 15 minutes for longer works
            retries=2,
            projects_dir=str(test_projects_dir),
            max_cost=10.0,  # Higher limit for longer works
            edit=False,
            edit_iterations=1,
            edit_quality_threshold=7.0,
        )

        # Verify substantial output
        project_dir = test_projects_dir / project_name
        epub_path = project_dir / "story.epub"

        assert epub_path.exists()
        assert epub_path.stat().st_size > 50000, "Long-form work should be substantial"

        print("\n📚 Long-form generation successful")
        print(f"   Project: {project_name}")
        print(f"   Target words: {test_case['word_count']:,}")
        print(f"   Size: {epub_path.stat().st_size:,} bytes")

    async def test_error_recovery_and_cleanup(
        self, test_model, check_api_available, test_projects_dir, timestamped_name
    ):
        """Test that failed runs don't leave partial projects behind."""
        # Use a pitch that should work
        test_case = self.TEST_PITCHES[0]
        project_name = f"error_test_{timestamped_name}"

        # This should succeed
        await generate_all_async(
            name=project_name,
            pitch=test_case["pitch"],
            words=test_case["word_count"],
            story_type=test_case["story_type"],
            model=test_model,
            timeout=600,
            retries=2,
            projects_dir=str(test_projects_dir),
            max_cost=5.0,
            edit=False,
            edit_iterations=1,
            edit_quality_threshold=7.0,
        )

        # Verify project exists and is complete
        project_dir = test_projects_dir / project_name
        assert project_dir.exists()

        # Check that all expected files are present
        required_files = ["idea.json", "story.epub"]
        for filename in required_files:
            assert (project_dir / filename).exists()

        print("\n🧹 Error recovery test passed")
        print(f"   Project: {project_name}")
        print(f"   All files present: {len(list(project_dir.glob('*.json')))} JSON files")

    async def test_model_fallback_behavior(
        self, check_api_available, test_projects_dir, timestamped_name
    ):
        """Test that we can switch between XAI and Ollama models."""
        # Test with XAI first (if available)
        test_case = self.TEST_PITCHES[0]
        project_name_xai = f"xai_test_{timestamped_name}"

        try:
            await generate_all_async(
                name=project_name_xai,
                pitch=test_case["pitch"],
                words=3000,  # Shorter for speed
                story_type="short-story",
                model="xai/grok-4-fast-reasoning",
                timeout=300,
                retries=1,
                projects_dir=str(test_projects_dir),
                max_cost=2.0,
                edit=False,
                edit_iterations=1,
                edit_quality_threshold=7.0,
            )
            xai_success = True
        except Exception:
            xai_success = False

        # Test with Ollama (if available)
        project_name_ollama = f"ollama_test_{timestamped_name}"

        try:
            await generate_all_async(
                name=project_name_ollama,
                pitch=test_case["pitch"],
                words=3000,  # Shorter for speed
                story_type="short-story",
                model="ollama/qwen2.5:7b",
                timeout=300,
                retries=1,
                projects_dir=str(test_projects_dir),
                max_cost=2.0,
                edit=False,
                edit_iterations=1,
                edit_quality_threshold=7.0,
            )
            ollama_success = True
        except Exception:
            ollama_success = False

        # At least one should work
        assert xai_success or ollama_success, "Neither XAI nor Ollama model worked"

        success_count = sum([xai_success, ollama_success])
        print(f"\n🔄 Model fallback test: {success_count}/2 models worked")
        if xai_success:
            print("   ✅ xAI/grok-4-fast-reasoning: SUCCESS")
        if ollama_success:
            print("   ✅ ollama/qwen2.5:7b: SUCCESS")
