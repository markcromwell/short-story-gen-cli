"""
Unit tests for chapter decision logic in EPUB generation.

Tests the ChapterDecider class and its break point determination algorithms.
"""

import pytest

from storygen.iterative.formatters.epub import ChapterDecider
from storygen.iterative.models import SceneSequel


class TestChapterDecider:
    """Test chapter break decision logic."""

    @pytest.fixture
    def decider(self):
        """Create a chapter decider with default settings."""
        return ChapterDecider()

    @pytest.fixture
    def sample_scene_sequels(self):
        """Create sample scene-sequels for testing."""
        return [
            SceneSequel(
                id="ss_001",
                type="scene",
                source_act="Act 1",
                pov_character="Alice",
                location="home",
                start_hours=0.0,
                duration_hours=1.0,
                goal="introduce character",
                conflict="internal struggle",
                disaster="decision made",
                content="Alice sat at her desk...",
                actual_word_count=800,
            ),
            SceneSequel(
                id="ss_002",
                type="sequel",
                source_act="Act 1",
                pov_character="Alice",
                location="home",
                start_hours=1.0,
                duration_hours=1.0,
                reaction="Emotional response",
                dilemma="Weighing options",
                decision="Choice leading to next scene",
                content="Alice reflected on her choice...",
                actual_word_count=600,
            ),
            SceneSequel(
                id="ss_003",
                type="scene",
                source_act="Act 1",
                pov_character="Bob",
                location="office",
                start_hours=5.0,
                duration_hours=1.0,
                goal="advance plot",
                conflict="external obstacle",
                disaster="partial success",
                content="Bob arrived at work...",
                actual_word_count=900,
            ),
        ]

    def test_initialization(self):
        """Test chapter decider initialization with custom parameters."""
        decider = ChapterDecider(
            target_chapter_length=2500,
            min_chapter_length=1000,
            max_chapter_length=4000,
        )

        assert decider.target_chapter_length == 2500
        assert decider.min_chapter_length == 1000
        assert decider.max_chapter_length == 4000

    def test_no_manual_breaks_single_chapter(self, decider, sample_scene_sequels):
        """Test that content without manual breaks creates single chapter."""
        breaks = decider.decide_chapters(sample_scene_sequels, "numbered")

        assert len(breaks) == 1
        assert breaks[0].chapter_number == 1
        assert breaks[0].scene_sequel_id == "ss_001"
        assert breaks[0].reason == "story_start"

    def test_manual_chapter_start_break(self, decider, sample_scene_sequels):
        """Test manual chapter break via chapter_start flag."""
        sample_scene_sequels[1].chapter_start = True

        breaks = decider.decide_chapters(sample_scene_sequels, "numbered")

        assert len(breaks) == 2
        assert breaks[0].chapter_number == 1
        assert breaks[0].scene_sequel_id == "ss_001"
        assert breaks[1].chapter_number == 2
        assert breaks[1].scene_sequel_id == "ss_002"
        assert breaks[1].reason == "manual_break"

    def test_force_break_functionality(self, decider, sample_scene_sequels):
        """Test force break via force_breaks parameter."""
        breaks = decider.decide_chapters(sample_scene_sequels, "numbered", force_breaks=["ss_002"])

        assert len(breaks) == 2
        assert breaks[1].chapter_number == 2
        assert breaks[1].scene_sequel_id == "ss_002"
        assert breaks[1].reason == "manual_break"

    def test_none_chapter_style(self, decider, sample_scene_sequels):
        """Test none chapter style returns no breaks."""
        breaks = decider.decide_chapters(sample_scene_sequels, "none")

        assert len(breaks) == 0

    def test_titled_chapter_style(self, decider, sample_scene_sequels):
        """Test titled chapter style generates titles from acts."""
        breaks = decider.decide_chapters(sample_scene_sequels, "titled")

        assert len(breaks) == 1
        assert breaks[0].chapter_title == "Act 1"

    def test_titled_chapter_style_no_act(self, decider):
        """Test titled chapter style with no act information."""
        scene_sequels = [
            SceneSequel(
                id="ss_001",
                type="scene",
                source_act="",
                pov_character="Alice",
                location="home",
                start_hours=0.0,
                duration_hours=1.0,
                goal="test",
                conflict="test",
                disaster="test",
                content="Content",
                actual_word_count=500,
            )
        ]

        breaks = decider.decide_chapters(scene_sequels, "titled")

        assert len(breaks) == 1
        assert breaks[0].chapter_title is None

    def test_sections_chapter_style(self, decider, sample_scene_sequels):
        """Test sections chapter style uses no titles."""
        breaks = decider.decide_chapters(sample_scene_sequels, "sections")

        assert len(breaks) == 1
        assert breaks[0].chapter_title is None

    def test_act_boundary_break(self, decider):
        """Test that act boundaries create strong break points."""
        scene_sequels = [
            SceneSequel(
                id="ss_001",
                type="scene",
                source_act="Act 1",
                pov_character="Alice",
                location="home",
                start_hours=0.0,
                duration_hours=1.0,
                goal="test",
                conflict="test",
                disaster="test",
                content="Content 1",
                actual_word_count=2500,  # Above target * 0.8 (2400) for good break
            ),
            SceneSequel(
                id="ss_002",
                type="scene",
                source_act="Act 2",  # Act boundary (+5)
                pov_character="Alice",
                location="home",
                start_hours=1.0,
                duration_hours=1.0,
                goal="test",
                conflict="test",
                disaster="test",
                content="Content 2",
                actual_word_count=1000,
            ),
        ]

        breaks = decider.decide_chapters(scene_sequels, "numbered")

        assert len(breaks) == 2
        assert breaks[1].reason == "good_break_point (score: 5)"

    def test_sequel_ending_break(self, decider):
        """Test that sequel endings create good break points."""
        scene_sequels = [
            SceneSequel(
                id="ss_001",
                type="scene",
                source_act="Act 1",
                pov_character="Alice",
                location="home",
                start_hours=0.0,
                duration_hours=1.0,
                goal="test",
                conflict="test",
                disaster="test",
                content="Content 1",
                actual_word_count=2500,  # Above target * 0.8 for good break
            ),
            SceneSequel(
                id="ss_002",
                type="sequel",  # Sequel
                source_act="Act 1",
                pov_character="Alice",
                location="home",
                start_hours=1.0,
                duration_hours=1.0,
                reaction="Emotional response",
                dilemma="Weighing options",
                decision="Choice leading to next scene",
                content="Content 2",
                actual_word_count=1000,
            ),
            SceneSequel(
                id="ss_003",
                type="scene",  # Break before scene following sequel
                source_act="Act 1",
                pov_character="Alice",
                location="office",  # Location change (+2) + sequel (+3) = 5
                start_hours=2.0,
                duration_hours=1.0,
                goal="test",
                conflict="test",
                disaster="test",
                content="Content 3",
                actual_word_count=1000,
            ),
        ]

        breaks = decider.decide_chapters(scene_sequels, "numbered")

        assert len(breaks) == 2
        assert breaks[1].scene_sequel_id == "ss_003"  # Break before scene after sequel
        assert breaks[1].reason == "good_break_point (score: 5)"

    def test_pov_change_break(self, decider):
        """Test that POV changes create strong break points."""
        scene_sequels = [
            SceneSequel(
                id="ss_001",
                type="scene",
                source_act="Act 1",
                pov_character="Alice",
                location="home",
                start_hours=0.0,
                duration_hours=1.0,
                goal="test",
                conflict="test",
                disaster="test",
                content="Content 1",
                actual_word_count=2500,  # Above target * 0.8 for good break
            ),
            SceneSequel(
                id="ss_002",
                type="scene",
                source_act="Act 1",
                pov_character="Bob",  # POV change (+3)
                location="office",  # Location change (+2) = score 5
                start_hours=1.0,
                duration_hours=1.0,
                goal="test",
                conflict="test",
                disaster="test",
                content="Content 2",
                actual_word_count=1000,
            ),
        ]

        breaks = decider.decide_chapters(scene_sequels, "numbered")

        assert len(breaks) == 2
        assert breaks[1].reason == "good_break_point (score: 5)"

    def test_major_time_gap_break(self, decider):
        """Test that major time gaps create strong break points."""
        scene_sequels = [
            SceneSequel(
                id="ss_001",
                type="scene",
                source_act="Act 1",
                pov_character="Alice",
                location="home",
                start_hours=0.0,
                duration_hours=1.0,
                goal="test",
                conflict="test",
                disaster="test",
                content="Content 1",
                actual_word_count=2500,  # Above target * 0.8 for good break
            ),
            SceneSequel(
                id="ss_002",
                type="scene",
                source_act="Act 1",
                pov_character="Alice",
                location="office",  # Location change (+2) + time gap (+4) = 6
                start_hours=14.0,  # 13+ hour gap (>12)
                duration_hours=1.0,
                goal="test",
                conflict="test",
                disaster="test",
                content="Content 2",
                actual_word_count=1000,
            ),
        ]

        breaks = decider.decide_chapters(scene_sequels, "numbered")

        assert len(breaks) == 2
        assert breaks[1].reason == "good_break_point (score: 6)"

    def test_location_change_break(self, decider):
        """Test that location changes create minor break points."""
        scene_sequels = [
            SceneSequel(
                id="ss_001",
                type="scene",
                source_act="Act 1",
                pov_character="Alice",
                location="home",
                start_hours=0.0,
                duration_hours=1.0,
                goal="test",
                conflict="test",
                disaster="test",
                content="Content 1",
                actual_word_count=2500,  # Above target * 0.8 for good break
            ),
            SceneSequel(
                id="ss_002",
                type="scene",
                source_act="Act 1",
                pov_character="Alice",
                location="office",  # Location change (+2)
                start_hours=8.0,  # 7+ hour gap (+2) = score 4, not enough for break
                duration_hours=1.0,
                goal="test",
                conflict="test",
                disaster="test",
                content="Content 2",
                actual_word_count=1000,
            ),
        ]

        breaks = decider.decide_chapters(scene_sequels, "numbered")

        # Location change alone doesn't trigger break - need higher score
        assert len(breaks) == 1

    def test_max_length_forced_break(self, decider):
        """Test that max chapter length forces breaks."""
        # Create scene-sequels that exceed max length
        scene_sequels = [
            SceneSequel(
                id="ss_001",
                type="scene",
                source_act="Act 1",
                pov_character="Alice",
                location="home",
                start_hours=0.0,
                duration_hours=1.0,
                goal="test",
                conflict="test",
                disaster="test",
                content="Content 1",
                actual_word_count=4000,  # Exceeds max (5000)
            ),
            SceneSequel(
                id="ss_002",
                type="scene",
                source_act="Act 1",
                pov_character="Alice",
                location="home",
                start_hours=1.0,
                duration_hours=1.0,
                goal="test",
                conflict="test",
                disaster="test",
                content="Content 2",
                actual_word_count=2000,  # Would exceed max when added
            ),
        ]

        breaks = decider.decide_chapters(scene_sequels, "numbered")

        assert len(breaks) == 2
        assert "max_length_exceeded" in breaks[1].reason

    def test_break_score_calculation(self, decider, sample_scene_sequels):
        """Test individual break score components."""
        ss1 = sample_scene_sequels[0]
        ss2 = sample_scene_sequels[1]

        # Test act boundary (5 points)
        ss2.source_act = "Act 2"
        score = decider._calculate_break_score(ss2, ss1, sample_scene_sequels)
        assert score >= 5

        # Test sequel ending (3 points)
        ss2.source_act = "Act 1"
        ss1.type = "sequel"
        score = decider._calculate_break_score(ss2, ss1, sample_scene_sequels)
        assert score >= 3

        # Test POV change (3 points)
        ss1.type = "scene"
        ss2.pov_character = "Bob"
        score = decider._calculate_break_score(ss2, ss1, sample_scene_sequels)
        assert score >= 3

        # Test major time gap (4 points) - need to set end_hours for proper gap calculation
        ss2.pov_character = "Alice"
        ss1.start_hours = 1.0  # Set ss1 to end at 1.0 + duration
        ss1.duration_hours = 1.0  # So ss1.end_hours = 2.0
        ss2.start_hours = 14.0  # 12+ hour gap from ss1.end_hours (2.0 to 14.0 = 12h gap)
        score = decider._calculate_break_score(ss2, ss1, sample_scene_sequels)
        assert score >= 4

        # Test location change (2 points)
        ss2.start_hours = 1.0
        ss2.location = "office"
        score = decider._calculate_break_score(ss2, ss1, sample_scene_sequels)
        assert score >= 2

    def test_generate_chapter_title_act_based(self, decider):
        """Test chapter title generation from act names."""
        ss = SceneSequel(
            id="ss_001",
            type="scene",
            source_act="Act 1: The Beginning",
            pov_character="Alice",
            location="home",
            start_hours=0.0,
            duration_hours=1.0,
            goal="test",
            conflict="test",
            disaster="test",
            content="Content",
            actual_word_count=500,
        )

        title = decider._generate_chapter_title(ss, "titled")
        assert title == "The Beginning"

    def test_generate_chapter_title_cleanup(self, decider):
        """Test chapter title cleanup removes prefixes."""
        ss = SceneSequel(
            id="ss_001",
            type="scene",
            source_act="Part 2: Middle Section",
            pov_character="Alice",
            location="home",
            start_hours=0.0,
            duration_hours=1.0,
            goal="test",
            conflict="test",
            disaster="test",
            content="Content",
            actual_word_count=500,
        )

        title = decider._generate_chapter_title(ss, "titled")
        assert title == "Middle Section"
