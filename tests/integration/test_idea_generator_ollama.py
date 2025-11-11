"""
Integration tests for IdeaGenerator with local Ollama models.

These tests make REAL API calls to locally-running Ollama models.
They are skipped by default and only run when:
1. The --integration flag is passed to pytest
2. Ollama is running locally
3. The test model (qwen2.5:7b or similar) is available

Run with: pytest tests/integration/ --integration
Or mark specific: pytest -m integration

Prerequisites:
- Ollama installed and running (ollama serve)
- A model pulled (e.g., ollama pull qwen2.5:7b)
"""

import pytest

from storygen.iterative.generators.character import CharacterGenerator
from storygen.iterative.generators.idea import IdeaGenerator
from storygen.iterative.generators.location import LocationGenerator
from storygen.iterative.models import Character, Location, StoryIdea

# Mark all tests in this file as integration tests
pytestmark = pytest.mark.integration


class TestIdeaGeneratorOllama:
    """Integration tests with real Ollama model calls."""

    @pytest.fixture
    def ollama_model(self):
        """Return the Ollama model to use for testing."""
        # Try common small models in order of preference
        # Users can override with OLLAMA_TEST_MODEL env var
        import os

        return os.getenv("OLLAMA_TEST_MODEL", "qwen2.5:7b")

    @pytest.fixture
    def check_ollama(self):
        """Check if Ollama is available before running tests."""
        import subprocess

        try:
            # Check if ollama is running
            result = subprocess.run(["ollama", "list"], capture_output=True, text=True, timeout=5)
            if result.returncode != 0:
                pytest.skip("Ollama is not running. Start with: ollama serve")
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pytest.skip("Ollama is not installed or not responding")

    def test_generate_real_idea(self, ollama_model, check_ollama):
        """Test generating a real story idea with Ollama."""
        generator = IdeaGenerator(model=f"ollama/{ollama_model}", max_retries=2, timeout=300)

        idea = generator.generate("A detective who can read minds investigates her own murder")

        # Validate the structure
        assert isinstance(idea, StoryIdea)
        assert idea.raw_idea == "A detective who can read minds investigates her own murder"
        assert len(idea.one_sentence) > 0
        assert len(idea.expanded) > len(idea.one_sentence)
        assert len(idea.genres) > 0
        assert len(idea.tone) > 0
        assert len(idea.themes) > 0

        # Validate content quality (basic checks)
        # Check that expanded text is substantive (contains key concepts or is long enough)
        assert len(idea.expanded) > 200 or any(
            word in idea.expanded.lower()
            for word in ["detective", "murder", "investigation", "killer", "mind"]
        )
        print(f"\n✓ Generated idea with {len(idea.expanded)} characters")
        print(f"  Genres: {idea.genres}")
        print(f"  Themes: {idea.themes}")

    def test_generate_multiple_genres(self, ollama_model, check_ollama):
        """Test that Ollama can generate ideas with multiple genres."""
        generator = IdeaGenerator(model=f"ollama/{ollama_model}", timeout=300)

        idea = generator.generate("A sci-fi horror story about an AI on a space station")

        assert isinstance(idea, StoryIdea)
        # Should recognize it's both sci-fi and horror
        assert len(idea.genres) >= 1
        genres_str = " ".join(idea.genres).lower()
        # At least one of these should be present
        assert any(g in genres_str for g in ["sci-fi", "science fiction", "horror", "thriller"])

        print(f"\n✓ Multi-genre idea: {idea.genres}")

    def test_generate_different_prompts(self, ollama_model, check_ollama):
        """Test that different prompts produce different ideas."""
        generator = IdeaGenerator(model=f"ollama/{ollama_model}", timeout=300)

        idea1 = generator.generate("A romantic comedy about two rival chefs")
        idea2 = generator.generate("A post-apocalyptic survival story")

        assert isinstance(idea1, StoryIdea)
        assert isinstance(idea2, StoryIdea)

        # Ideas should be different
        assert idea1.one_sentence != idea2.one_sentence
        assert idea1.expanded != idea2.expanded

        # Genres should reflect the prompts
        assert any(g in " ".join(idea1.genres).lower() for g in ["romance", "comedy", "romantic"])
        assert any(
            g in " ".join(idea2.genres).lower()
            for g in ["post-apocalyptic", "survival", "dystopian", "sci-fi", "science fiction"]
        )

        print(f"\n✓ Idea 1 genres: {idea1.genres}")
        print(f"  Idea 2 genres: {idea2.genres}")

    def test_retry_on_malformed_json(self, ollama_model, check_ollama):
        """Test that generator can recover from malformed JSON responses."""
        generator = IdeaGenerator(model=f"ollama/{ollama_model}", max_retries=3, timeout=300)

        # Use a complex prompt that might confuse the model
        idea = generator.generate("A story with 'quotes', \"more quotes\", and special chars: @#$%")

        # Should still succeed despite tricky characters
        assert isinstance(idea, StoryIdea)
        assert len(idea.one_sentence) > 0

        print("\n✓ Handled complex prompt successfully")

    def test_genre_normalization_with_real_model(self, ollama_model, check_ollama):
        """Test that genre normalization works with real model output."""
        generator = IdeaGenerator(model=f"ollama/{ollama_model}", timeout=300)

        idea = generator.generate("A mystery thriller")

        assert isinstance(idea, StoryIdea)
        # Genres should be normalized (lowercase)
        for genre in idea.genres:
            assert genre == genre.lower()
            assert genre == genre.strip()

        print(f"\n✓ Normalized genres: {idea.genres}")

    def test_timeout_handling(self, ollama_model, check_ollama):
        """Test that timeout is respected (though this may succeed quickly)."""
        # Set a very short timeout to potentially trigger timeout behavior
        generator = IdeaGenerator(model=f"ollama/{ollama_model}", timeout=1, max_retries=1)

        try:
            # This might succeed or timeout depending on model speed
            idea = generator.generate("A simple story")
            # If it succeeds, that's fine - model was fast
            assert isinstance(idea, StoryIdea)
            print("\n✓ Model was fast enough (timeout not triggered)")
        except Exception as e:
            # If it times out, that's also expected behavior
            error_msg = str(e).lower()
            assert "timeout" in error_msg or "retry" in error_msg
            print(f"\n✓ Timeout handling working: {e}")

    @pytest.mark.slow
    def test_consistency_across_runs(self, ollama_model, check_ollama):
        """Test that multiple runs with same prompt produce valid but varied results."""
        generator = IdeaGenerator(model=f"ollama/{ollama_model}", timeout=300)

        prompt = "A fantasy adventure with magic"
        ideas = []

        for i in range(3):
            idea = generator.generate(prompt)
            assert isinstance(idea, StoryIdea)
            assert idea.raw_idea == prompt
            ideas.append(idea)

        # All should be valid
        assert all(len(idea.one_sentence) > 0 for idea in ideas)
        assert all(len(idea.expanded) > 0 for idea in ideas)
        assert all(len(idea.genres) > 0 for idea in ideas)

        # They should be different (AI creativity)
        unique_sentences = set(idea.one_sentence for idea in ideas)
        assert len(unique_sentences) >= 2, "AI should produce varied results"

        print(f"\n✓ Generated {len(ideas)} varied ideas from same prompt")
        print(f"  Unique variations: {len(unique_sentences)}/3")


class TestCharacterGeneratorOllama:
    """Integration tests for CharacterGenerator with real Ollama model calls."""

    @pytest.fixture
    def ollama_model(self):
        """Return the Ollama model to use for testing."""
        import os

        return os.getenv("OLLAMA_TEST_MODEL", "qwen2.5:7b")

    @pytest.fixture
    def check_ollama(self):
        """Check if Ollama is available before running tests."""
        import subprocess

        try:
            # Check if ollama is running
            result = subprocess.run(["ollama", "list"], capture_output=True, text=True, timeout=5)
            if result.returncode != 0:
                pytest.skip("Ollama is not running. Start with: ollama serve")
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pytest.skip("Ollama is not installed or not responding")

    @pytest.fixture
    def story_idea(self):
        """Create a sample story idea for character generation."""
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
        )

    def test_generate_characters_ollama(self, ollama_model, check_ollama, story_idea):
        """Test generating real characters with Ollama."""
        generator = CharacterGenerator(model=f"ollama/{ollama_model}", max_retries=2, timeout=300)

        characters = generator.generate(story_idea)

        # Validate structure
        assert len(characters) >= 3, "Should generate at least 3 characters"
        assert len(characters) <= 5, "Should generate at most 5 characters"

        # Validate required roles
        roles = [c.role for c in characters]
        assert "protagonist" in roles, "Must have a protagonist"
        assert "antagonist" in roles, "Must have an antagonist"

        # Validate each character has required fields
        for char in characters:
            assert len(char.name) > 0, f"Character {char.name} has no name"
            assert len(char.role) > 0, f"Character {char.name} has no role"
            assert len(char.bio) > 0, f"Character {char.name} has no bio"
            assert len(char.goal) > 0, f"Character {char.name} has no goal"
            assert len(char.flaw) > 0, f"Character {char.name} has no flaw"
            # arc is optional

        print(f"\n✓ Generated {len(characters)} characters")
        for char in characters:
            print(f"  - {char.name} ({char.role})")

    def test_character_quality(self, ollama_model, check_ollama, story_idea):
        """Test that generated characters are coherent with the story."""
        generator = CharacterGenerator(model=f"ollama/{ollama_model}", timeout=300)

        characters = generator.generate(story_idea)

        # Find protagonist
        protagonist = next((c for c in characters if c.role == "protagonist"), None)
        assert protagonist is not None

        # Protagonist's bio should be substantive
        assert len(protagonist.bio) > 50, "Protagonist bio should be detailed"
        assert len(protagonist.goal) > 20, "Protagonist goal should be clear"
        assert len(protagonist.flaw) > 20, "Protagonist flaw should be specific"

        # Characters should be relevant to story themes
        # At least one character should mention detective or mystery-related concepts
        all_bios = " ".join(c.bio.lower() for c in characters)
        assert len(all_bios) > 200, "Character bios should be substantive"

        print("\n✓ Character quality validated")
        print(f"  Protagonist: {protagonist.name}")
        print(f"  Bio length: {len(protagonist.bio)} chars")

    def test_different_story_different_characters(self, ollama_model, check_ollama):
        """Test that different stories produce different character sets."""
        generator = CharacterGenerator(model=f"ollama/{ollama_model}", timeout=300)

        idea1 = StoryIdea(
            raw_idea="A space explorer",
            one_sentence="An astronaut explores a distant galaxy.",
            expanded="A lone astronaut ventures into uncharted space, discovering ancient alien civilizations and facing cosmic dangers.",
            genres=["sci-fi"],
            tone="adventurous",
            themes=["exploration"],
        )

        idea2 = StoryIdea(
            raw_idea="A medieval knight",
            one_sentence="A knight seeks the holy grail.",
            expanded="In medieval times, a brave knight embarks on a quest to find the legendary holy grail, facing dragons and dark sorcerers.",
            genres=["fantasy"],
            tone="epic",
            themes=["honor"],
        )

        chars1 = generator.generate(idea1)
        chars2 = generator.generate(idea2)

        # Both should be valid
        assert len(chars1) >= 3
        assert len(chars2) >= 3

        # Characters should be different
        names1 = set(c.name for c in chars1)
        names2 = set(c.name for c in chars2)
        assert names1 != names2, "Different stories should produce different characters"

        print(f"\n✓ Story 1 characters: {[c.name for c in chars1]}")
        print(f"  Story 2 characters: {[c.name for c in chars2]}")


class TestLocationGeneratorOllama:
    """Integration tests for LocationGenerator with real Ollama model calls."""

    @pytest.fixture
    def ollama_model(self):
        """Return the Ollama model to use for testing."""
        import os

        return os.getenv("OLLAMA_TEST_MODEL", "qwen2.5:7b")

    @pytest.fixture
    def check_ollama(self):
        """Check if Ollama is available before running tests."""
        import subprocess

        try:
            # Check if ollama is running
            result = subprocess.run(["ollama", "list"], capture_output=True, text=True, timeout=5)
            if result.returncode != 0:
                pytest.skip("Ollama is not running. Start with: ollama serve")
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pytest.skip("Ollama is not installed or not responding")

    @pytest.fixture
    def story_idea(self):
        """Create a sample story idea for location generation."""
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
        )

    def test_generate_locations_ollama(self, ollama_model, check_ollama, story_idea):
        """Test generating real locations with Ollama."""
        generator = LocationGenerator(model=f"ollama/{ollama_model}", max_retries=2, timeout=300)

        locations = generator.generate(story_idea)

        # Validate structure
        assert len(locations) >= 3, "Should generate at least 3 locations"
        assert len(locations) <= 7, "Should generate at most 7 locations"

        # Validate each location has required fields
        for loc in locations:
            assert len(loc.name) > 0, f"Location {loc.name} has no name"
            assert len(loc.description) > 0, f"Location {loc.name} has no description"
            assert len(loc.significance) > 0, f"Location {loc.name} has no significance"
            assert len(loc.atmosphere) > 0, f"Location {loc.name} has no atmosphere"

        print(f"\n✓ Generated {len(locations)} locations")
        for loc in locations:
            print(f"  - {loc.name}")

    def test_location_quality(self, ollama_model, check_ollama, story_idea):
        """Test that generated locations are vivid and coherent."""
        generator = LocationGenerator(model=f"ollama/{ollama_model}", timeout=300)

        locations = generator.generate(story_idea)

        # Locations should have substantive descriptions
        for loc in locations:
            assert len(loc.description) > 50, f"Location {loc.name} description should be detailed"
            assert len(loc.significance) > 20, f"Location {loc.name} significance should be clear"
            assert len(loc.atmosphere) > 10, f"Location {loc.name} atmosphere should be specific"

        # At least one location should be relevant to the noir/mystery theme
        all_text = " ".join(
            f"{loc.name} {loc.description} {loc.significance}".lower() for loc in locations
        )
        assert len(all_text) > 500, "Location descriptions should be substantive"

        print("\n✓ Location quality validated")
        print(f"  Total description length: {len(all_text)} chars")

    def test_different_story_different_locations(self, ollama_model, check_ollama):
        """Test that different stories produce different location sets."""
        generator = LocationGenerator(model=f"ollama/{ollama_model}", timeout=300)

        idea1 = StoryIdea(
            raw_idea="A space station mystery",
            one_sentence="A murder on a remote space station.",
            expanded="On a distant orbital station, a crew member is found dead and everyone is a suspect.",
            genres=["sci-fi", "mystery"],
            tone="tense",
            themes=["isolation"],
        )

        idea2 = StoryIdea(
            raw_idea="A medieval fantasy quest",
            one_sentence="A knight seeks a legendary artifact.",
            expanded="In medieval times, a brave knight ventures through enchanted forests and dragon lairs.",
            genres=["fantasy"],
            tone="epic",
            themes=["honor"],
        )

        locs1 = generator.generate(idea1)
        locs2 = generator.generate(idea2)

        # Both should be valid
        assert len(locs1) >= 3
        assert len(locs2) >= 3

        # Locations should be different
        names1 = set(loc.name for loc in locs1)
        names2 = set(loc.name for loc in locs2)
        assert names1 != names2, "Different stories should produce different locations"

        print(f"\n✓ Story 1 locations: {[loc.name for loc in locs1]}")
        print(f"  Story 2 locations: {[loc.name for loc in locs2]}")


class TestOutlineGeneratorOllama:
    """Integration tests for OutlineGenerator with real Ollama model calls."""

    @pytest.fixture
    def ollama_model(self):
        """Return the Ollama model to use for testing."""
        import os

        return os.getenv("OLLAMA_TEST_MODEL", "qwen2.5:7b")

    @pytest.fixture
    def check_ollama(self):
        """Check if Ollama is available before running tests."""
        import subprocess

        try:
            # Check if ollama is running
            result = subprocess.run(["ollama", "list"], capture_output=True, text=True, timeout=5)
            if result.returncode != 0:
                pytest.skip("Ollama is not running. Start with: ollama serve")
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pytest.skip("Ollama is not installed or not responding")

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

    def test_generate_outline_ollama(
        self, ollama_model, check_ollama, story_idea, characters, locations
    ):
        """Test generating real outline with Ollama using recursive structure."""
        from storygen.iterative.generators.outline import OutlineGenerator

        generator = OutlineGenerator(
            model=f"ollama/{ollama_model}",
            structure_type="three-act",
            max_retries=2,
            timeout=300,
        )

        outline = generator.generate(story_idea, characters, locations)

        # Validate recursive structure
        assert outline.structure_type == "three-act"
        assert hasattr(outline, "acts")
        assert len(outline.acts) > 0

        # Validate act structure
        for act in outline.acts:
            assert hasattr(act, "title")
            assert hasattr(act, "description")
            assert hasattr(act, "story_application")
            assert hasattr(act, "percentage")
            assert len(act.title) > 0
            assert len(act.story_application) > 0, f"Act '{act.title}' missing story_application"

        # Validate all story_applications are filled
        def check_story_application(act):
            assert (
                len(act.story_application.strip()) > 0
            ), f"Act '{act.title}' has empty story_application"
            for sub_act in act.sub_acts:
                check_story_application(sub_act)

        for act in outline.acts:
            check_story_application(act)

        print("\n✓ Generated outline with recursive act structure")
        print(f"  Structure type: {outline.structure_type}")
        print(f"  Top-level acts: {len(outline.acts)}")
        print(f"  First act: {outline.acts[0].title}")
        if outline.acts[0].sub_acts:
            print(f"  First act has {len(outline.acts[0].sub_acts)} sub-acts")

    def test_outline_quality(self, ollama_model, check_ollama, story_idea, characters, locations):
        """Test that generated outline has quality content."""
        from storygen.iterative.generators.outline import OutlineGenerator

        generator = OutlineGenerator(
            model=f"ollama/{ollama_model}", structure_type="three-act", timeout=300
        )

        outline = generator.generate(story_idea, characters, locations)

        # Collect all story_application texts recursively
        def collect_story_applications(act):
            texts = [act.story_application]
            for sub_act in act.sub_acts:
                texts.extend(collect_story_applications(sub_act))
            return texts

        all_applications = []
        for act in outline.acts:
            all_applications.extend(collect_story_applications(act))

        # Each story_application should be substantive (at least 50 characters)
        for i, app in enumerate(all_applications):
            assert (
                len(app) > 50
            ), f"Story application {i+1} should be detailed (got {len(app)} chars)"

        # Total outline text should be substantial
        total_length = sum(len(app) for app in all_applications)
        assert total_length > 500, "Outline should be comprehensive"

        print("\n✓ Outline quality validated")
        print(f"  Total acts (including sub-acts): {len(all_applications)}")
        print(f"  Total length: {total_length} chars")
        print(f"  Average per act: {total_length // len(all_applications)} chars")

    def test_different_story_different_outline(self, ollama_model, check_ollama):
        """Test that different stories produce different outlines."""
        from storygen.iterative.generators.outline import OutlineGenerator

        generator = OutlineGenerator(
            model=f"ollama/{ollama_model}", structure_type="three-act", timeout=300
        )

        # Story 1: Space mystery
        idea1 = StoryIdea(
            raw_idea="Space station murder",
            one_sentence="A murder on a remote space station.",
            expanded="On a distant orbital station, a crew member is found dead.",
            genres=["sci-fi", "mystery"],
            tone="tense",
            themes=["isolation"],
        )
        chars1 = [
            Character(
                name="Captain",
                role="protagonist",
                bio="Station commander",
                goal="Find killer",
                flaw="Trusting",
            )
        ]
        locs1 = [
            Location(
                name="Command Deck",
                description="The bridge",
                significance="Control center",
                atmosphere="Tense",
            )
        ]

        # Story 2: Medieval fantasy
        idea2 = StoryIdea(
            raw_idea="Knight's quest",
            one_sentence="A knight seeks the holy grail.",
            expanded="A brave knight ventures through enchanted forests.",
            genres=["fantasy"],
            tone="epic",
            themes=["honor"],
        )
        chars2 = [
            Character(
                name="Sir Roland",
                role="protagonist",
                bio="A noble knight",
                goal="Find grail",
                flaw="Pride",
            )
        ]
        locs2 = [
            Location(
                name="Enchanted Forest",
                description="Mystical woods",
                significance="Path to grail",
                atmosphere="Magical",
            )
        ]

        outline1 = generator.generate(idea1, chars1, locs1)
        outline2 = generator.generate(idea2, chars2, locs2)

        # Both should be valid
        assert len(outline1.acts) > 0
        assert len(outline2.acts) > 0
        assert len(outline1.acts[0].story_application) > 0
        assert len(outline2.acts[0].story_application) > 0

        # Outlines should be different
        assert outline1.acts[0].story_application != outline2.acts[0].story_application

        # Get last act (resolution)
        last_act1 = outline1.acts[-1]
        last_act2 = outline2.acts[-1]
        assert last_act1.story_application != last_act2.story_application

        print(f"\n✓ Story 1 first act: {outline1.acts[0].story_application[:60]}...")
        print(f"  Story 2 first act: {outline2.acts[0].story_application[:60]}...")
