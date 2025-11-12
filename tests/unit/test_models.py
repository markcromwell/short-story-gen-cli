"""
Unit tests for iterative generation data models.

Tests cover:
- Model creation with required fields
- JSON serialization (to_dict)
- JSON deserialization (from_dict)
- Roundtrip serialization
- Time calculations (SceneSequel)
- Nested object handling (WorkingDoc, Project)
"""

import json
from datetime import datetime
from pathlib import Path

import pytest

from storygen.iterative.models import (
    ActStructure,
    Character,
    EditorialFeedback,
    Location,
    Project,
    ProjectConfig,
    SceneSequel,
    StoryIdea,
    WorkingDoc,
    WorldBuilding,
)


class TestStoryIdea:
    """Tests for StoryIdea model."""

    def test_creation(self):
        """Test StoryIdea can be created with required fields."""
        idea = StoryIdea(
            raw_idea="A detective solves crimes",
            one_sentence="A telepath detective must solve her own murder.",
            expanded="Detective Maya Reeves dies during an investigation...",
            genres=["mystery", "supernatural"],
            tone="Dark, tense",
            themes=["mortality", "trust", "identity"],
            setting="Modern-day Portland",
        )
        assert idea.one_sentence == "A telepath detective must solve her own murder."
        assert len(idea.themes) == 3
        assert len(idea.genres) == 2
        assert "mystery" in idea.genres

    def test_to_dict(self):
        """Test StoryIdea serializes to dict."""
        idea = StoryIdea(
            raw_idea="A detective solves crimes",
            one_sentence="A telepath detective must solve her own murder.",
            expanded="Detective Maya Reeves dies...",
            genres=["mystery"],
            tone="Dark",
            themes=["mortality"],
            setting="Modern-day Portland",
        )
        data = idea.to_dict()

        assert isinstance(data, dict)
        assert data["one_sentence"] == "A telepath detective must solve her own murder."
        assert data["themes"] == ["mortality"]
        assert data["genres"] == ["mystery"]

    def test_from_dict(self):
        """Test StoryIdea deserializes from dict."""
        data = {
            "raw_idea": "A detective solves crimes",
            "one_sentence": "A telepath detective must solve her own murder.",
            "expanded": "Detective Maya Reeves dies...",
            "genres": ["mystery"],
            "tone": "Dark",
            "themes": ["mortality"],
            "setting": "Modern-day Portland",
        }
        idea = StoryIdea.from_dict(data)

        assert isinstance(idea, StoryIdea)
        assert idea.one_sentence == data["one_sentence"]
        assert idea.themes == ["mortality"]
        assert idea.genres == ["mystery"]

    def test_json_roundtrip(self):
        """Test StoryIdea survives JSON serialization."""
        original = StoryIdea(
            raw_idea="A detective solves crimes",
            one_sentence="A telepath detective must solve her own murder.",
            expanded="Detective Maya Reeves dies...",
            genres=["mystery", "supernatural"],
            tone="Dark",
            themes=["mortality", "trust"],
            setting="Modern-day Portland",
        )

        json_str = json.dumps(original.to_dict())
        restored = StoryIdea.from_dict(json.loads(json_str))

        assert original == restored
        assert len(restored.genres) == 2

    def test_multiple_genres(self):
        """Test StoryIdea supports multiple genre combinations."""
        # Sci-fi horror
        idea1 = StoryIdea(
            raw_idea="Space station horror",
            one_sentence="A crew faces an alien threat.",
            expanded="...",
            genres=["sci-fi", "horror"],
            tone="Terrifying",
            themes=["isolation"],
            setting="Remote space station",
        )
        assert idea1.genres == ["sci-fi", "horror"]

        # Romantic comedy
        idea2 = StoryIdea(
            raw_idea="Dating disaster",
            one_sentence="Two enemies fall in love.",
            expanded="...",
            genres=["romantic", "comedy"],
            tone="Light, funny",
            themes=["love"],
            setting="Modern NYC",
        )
        assert idea2.genres == ["romantic", "comedy"]

        # Post-apocalyptic fantasy
        idea3 = StoryIdea(
            raw_idea="Magic after the fall",
            one_sentence="A wizard survives the apocalypse.",
            expanded="...",
            genres=["post-apocalyptic", "fantasy"],
            tone="Grim",
            themes=["survival", "hope"],
            setting="Post-apocalyptic wasteland",
        )
        assert idea3.genres == ["post-apocalyptic", "fantasy"]
        assert len(idea3.genres) == 2

    def test_duplicate_genres_removed(self):
        """Test duplicate genres are automatically removed."""
        idea = StoryIdea(
            raw_idea="Test",
            one_sentence="Test story.",
            expanded="...",
            genres=["sci-fi", "Sci-Fi", "horror", "HORROR"],  # Duplicates with different cases
            tone="Dark",
            themes=["test"],
            setting="Test setting",
        )
        # Should normalize to lowercase and remove duplicates
        assert idea.genres == ["sci-fi", "horror"]
        assert len(idea.genres) == 2

    def test_duplicate_themes_removed(self):
        """Test duplicate themes are automatically removed."""
        idea = StoryIdea(
            raw_idea="Test",
            one_sentence="Test story.",
            expanded="...",
            genres=["mystery"],
            tone="Dark",
            themes=["love", "Love", "LOVE", "betrayal", "betrayal"],  # Duplicates
            setting="Test setting",
        )
        # Should normalize and remove duplicates
        assert idea.themes == ["love", "betrayal"]
        assert len(idea.themes) == 2

    def test_empty_genres_raises_error(self):
        """Test that empty genres list raises ValidationError."""
        from storygen.iterative.exceptions import ValidationError

        with pytest.raises(ValidationError, match="must have at least one genre"):
            StoryIdea(
                raw_idea="Test",
                one_sentence="Test story.",
                expanded="...",
                genres=[],  # Empty!
                tone="Dark",
                themes=["test"],
                setting="Test setting",
            )

    def test_whitespace_trimmed(self):
        """Test that whitespace is trimmed from genres and themes."""
        idea = StoryIdea(
            raw_idea="Test",
            one_sentence="Test story.",
            expanded="...",
            genres=["  sci-fi  ", "horror   "],
            tone="Dark",
            themes=["  love  ", "   betrayal"],
            setting="Test setting",
        )
        assert idea.genres == ["sci-fi", "horror"]
        assert idea.themes == ["love", "betrayal"]


class TestCharacter:
    """Tests for Character model."""

    def test_creation_with_all_fields(self):
        """Test Character model with complete data."""
        char = Character(
            name="Detective Maya",
            role="protagonist",
            bio="A telepath who can read minds",
            goal="Solve the case",
            flaw="Trust issues",
            arc="Learns to trust her partner",
        )
        assert char.role == "protagonist"
        assert char.arc == "Learns to trust her partner"

    def test_creation_without_arc(self):
        """Test Character with optional arc field."""
        char = Character(
            name="Detective Maya",
            role="protagonist",
            bio="A telepath",
            goal="Solve the case",
            flaw="Trust issues",
        )
        assert char.arc is None

    def test_to_dict(self):
        """Test Character serializes to dict."""
        char = Character(
            name="Detective Maya",
            role="protagonist",
            bio="A telepath",
            goal="Solve the case",
            flaw="Trust issues",
        )
        data = char.to_dict()

        assert data["name"] == "Detective Maya"
        assert data["role"] == "protagonist"

    def test_json_roundtrip(self):
        """Test Character survives JSON serialization."""
        original = Character(
            name="Detective Maya",
            role="protagonist",
            bio="A telepath",
            goal="Solve the case",
            flaw="Trust issues",
            arc="Learns to trust",
        )

        json_str = json.dumps(original.to_dict())
        restored = Character.from_dict(json.loads(json_str))

        assert original == restored


class TestLocation:
    """Tests for Location model."""

    def test_creation(self):
        """Test Location can be created."""
        loc = Location(
            name="The Precinct",
            description="A busy police station in downtown",
            atmosphere="Tense, bureaucratic",
            significance="Where Maya works",
        )
        assert loc.name == "The Precinct"

    def test_json_roundtrip(self):
        """Test Location survives JSON serialization."""
        original = Location(
            name="The Precinct",
            description="A busy police station",
            atmosphere="Tense",
            significance="Where Maya works",
        )

        json_str = json.dumps(original.to_dict())
        restored = Location.from_dict(json.loads(json_str))

        assert original == restored


class TestWorldBuilding:
    """Tests for WorldBuilding model."""

    def test_creation_empty(self):
        """Test WorldBuilding with no fields set."""
        wb = WorldBuilding()
        assert wb.magic_system is None
        assert len(wb.key_rules) == 0

    def test_creation_with_fields(self):
        """Test WorldBuilding with magic system."""
        wb = WorldBuilding(
            magic_system="Telepathy",
            key_rules=["Cannot read other telepaths", "Range limited to 50 feet"],
            constraints=["Causes headaches with prolonged use"],
        )
        assert wb.magic_system == "Telepathy"
        assert len(wb.key_rules) == 2

    def test_json_roundtrip(self):
        """Test WorldBuilding survives JSON serialization."""
        original = WorldBuilding(
            magic_system="Telepathy",
            key_rules=["Cannot read other telepaths"],
            constraints=["Causes headaches"],
        )

        json_str = json.dumps(original.to_dict())
        restored = WorldBuilding.from_dict(json.loads(json_str))

        assert original == restored


class TestActStructure:
    """Tests for ActStructure model."""

    def test_creation(self):
        """Test ActStructure can be created."""
        act = ActStructure(
            act=1, summary="Setup and inciting incident", hook="Maya finds herself dead"
        )
        assert act.act == 1
        assert act.hook == "Maya finds herself dead"

    def test_json_roundtrip(self):
        """Test ActStructure survives JSON serialization."""
        original = ActStructure(
            act=2,
            summary="Rising action",
            midpoint="Maya discovers the killer's identity",
            climax="Confrontation with killer",
        )

        json_str = json.dumps(original.to_dict())
        restored = ActStructure.from_dict(json.loads(json_str))

        assert original == restored


class TestSceneSequel:
    """Tests for SceneSequel model with time calculations."""

    def test_creation_basic(self):
        """Test SceneSequel can be created with basic fields."""
        ss = SceneSequel(
            id="ss_001",
            type="scene",
            source_act="act_1",
            pov_character="Maya",
            location="The Precinct",
            start_hours=0.0,
            duration_hours=1.0,
            goal="Find the killer",
            conflict="Evidence is missing",
            disaster="Discovers first clue",
        )
        assert ss.id == "ss_001"
        assert ss.type == "scene"

    def test_time_calculation(self):
        """Test SceneSequel auto-calculates time fields."""
        ss = SceneSequel(
            id="ss_001",
            type="scene",
            source_act="act_1",
            pov_character="Maya",
            location="The Precinct",
            goal="Find the killer",
            conflict="Evidence is missing",
            disaster="Discovers first clue",
            start_hours=0.0,
            duration_hours=0.5,
        )

        assert ss.end_hours == 0.5
        assert ss.day_number == 1
        assert ss.time_of_day in ["dead of night", "pre-dawn", "early morning"]

    def test_time_of_day_categories(self):
        """Test time_of_day calculation for different hours."""
        # Dead of night (0-4)
        ss1 = SceneSequel(
            id="ss_001",
            type="scene",
            source_act="act_1",
            pov_character="Maya",
            location="Precinct",
            goal="Test",
            conflict="Test conflict",
            disaster="Test disaster",
            start_hours=2.0,
            duration_hours=0.5,
        )
        assert ss1.time_of_day == "dead of night"

        # Early morning (6-9)
        ss2 = SceneSequel(
            id="ss_002",
            type="scene",
            source_act="act_1",
            pov_character="Maya",
            location="Precinct",
            goal="Test",
            conflict="Test conflict",
            disaster="Test disaster",
            start_hours=7.0,
            duration_hours=0.5,
        )
        assert ss2.time_of_day == "early morning"

        # Midday (12-14)
        ss3 = SceneSequel(
            id="ss_003",
            type="scene",
            source_act="act_1",
            pov_character="Maya",
            location="Precinct",
            goal="Test",
            conflict="Test conflict",
            disaster="Test disaster",
            start_hours=13.0,
            duration_hours=0.5,
        )
        assert ss3.time_of_day == "midday"

        # Evening (17-20)
        ss4 = SceneSequel(
            id="ss_004",
            type="scene",
            source_act="act_1",
            pov_character="Maya",
            location="Precinct",
            goal="Test",
            conflict="Test conflict",
            disaster="Test disaster",
            start_hours=18.0,
            duration_hours=0.5,
        )
        assert ss4.time_of_day == "evening"

    def test_day_number_calculation(self):
        """Test day_number increments correctly."""
        # Day 1
        ss1 = SceneSequel(
            id="ss_001",
            type="scene",
            source_act="act_1",
            pov_character="Maya",
            location="Precinct",
            goal="Test",
            conflict="Test conflict",
            disaster="Test disaster",
            start_hours=12.0,
            duration_hours=0.5,
        )
        assert ss1.day_number == 1

        # Day 2 (after 24 hours)
        ss2 = SceneSequel(
            id="ss_002",
            type="scene",
            source_act="act_1",
            pov_character="Maya",
            location="Precinct",
            goal="Test",
            conflict="Test conflict",
            disaster="Test disaster",
            start_hours=26.0,
            duration_hours=0.5,
        )
        assert ss2.day_number == 2

        # Day 3
        ss3 = SceneSequel(
            id="ss_003",
            type="scene",
            source_act="act_1",
            pov_character="Maya",
            location="Precinct",
            goal="Test",
            conflict="Test conflict",
            disaster="Test disaster",
            start_hours=50.0,
            duration_hours=0.5,
        )
        assert ss3.day_number == 3

    def test_get_time_gap(self):
        """Test calculating time gap between scenes."""
        ss1 = SceneSequel(
            id="ss_001",
            type="scene",
            source_act="act_1",
            pov_character="Maya",
            location="Precinct",
            goal="Test",
            conflict="Test conflict",
            disaster="Test disaster",
            start_hours=0.0,
            duration_hours=0.5,
        )

        ss2 = SceneSequel(
            id="ss_002",
            type="scene",
            source_act="act_1",
            pov_character="Maya",
            location="Precinct",
            goal="Test",
            conflict="Test conflict",
            disaster="Test disaster",
            start_hours=1.0,
            duration_hours=0.5,
        )

        gap = ss2.get_time_gap_from(ss1)
        assert gap == 0.5  # 1.0 - 0.5 = 0.5 hours

    def test_get_time_summary(self):
        """Test human-readable time summary."""
        ss = SceneSequel(
            id="ss_001",
            type="scene",
            source_act="act_1",
            pov_character="Maya",
            location="Precinct",
            goal="Test",
            conflict="Test conflict",
            disaster="Test disaster",
            start_hours=14.5,
            duration_hours=1.0,
        )

        summary = ss.get_time_summary()
        assert "Day 1" in summary
        assert "afternoon" in summary
        assert "14.5h" in summary
        assert "15.5h" in summary

    def test_scene_structure(self):
        """Test scene has required goal/conflict/disaster."""
        scene = SceneSequel(
            id="ss_001",
            type="scene",
            source_act="act_1",
            pov_character="Maya",
            location="Precinct",
            goal="Find the killer",
            conflict="Evidence is missing",
            disaster="Witness is murdered",
            start_hours=8.0,
            duration_hours=2.0,
        )

        assert scene.goal == "Find the killer"
        assert scene.conflict == "Evidence is missing"
        assert scene.disaster == "Witness is murdered"
        assert scene.reaction is None
        assert scene.dilemma is None
        assert scene.decision is None

    def test_sequel_structure(self):
        """Test sequel has reaction/dilemma/decision."""
        sequel = SceneSequel(
            id="ss_002",
            type="sequel",
            source_act="act_1",
            pov_character="Maya",
            location="Maya's Apartment",
            reaction="Maya feels defeated",
            dilemma="Give up or push forward?",
            decision="She decides to dig deeper",
            start_hours=10.0,
            duration_hours=0.5,
        )

        assert sequel.reaction == "Maya feels defeated"
        assert sequel.dilemma == "Give up or push forward?"
        assert sequel.decision == "She decides to dig deeper"
        assert sequel.goal is None
        assert sequel.conflict is None
        assert sequel.disaster is None

    def test_markdown_to_plain_text(self):
        """Test conversion of markdown content to plain text."""
        scene = SceneSequel(
            id="ss_001",
            type="scene",
            source_act="act_1",
            pov_character="Maya",
            location="Precinct",
            goal="Test",
            conflict="Test",
            disaster="Test",
            start_hours=8.0,
            duration_hours=1.0,
            content="Detective Maya **strode** into the room. *She knew the truth.*\n\n---\n\n## Chapter 1\n\nThe investigation began.",
        )

        plain = scene.get_plain_text()

        # Check markdown formatting is removed
        assert "**" not in plain
        assert "*" not in plain
        assert "---" not in plain
        assert "##" not in plain
        # Check content is preserved
        assert "Detective Maya" in plain
        assert "strode" in plain
        assert "She knew the truth" in plain
        assert "investigation began" in plain

    def test_summary_and_key_points(self):
        """Test summary and key_points fields for continuity tracking."""
        scene = SceneSequel(
            id="ss_001",
            type="scene",
            source_act="act_1",
            pov_character="Maya",
            location="Precinct",
            goal="Interrogate suspect",
            conflict="Telepathy causes overload",
            disaster="Interrogation abandoned",
            start_hours=0.0,
            duration_hours=0.5,
            content="Detective Maya pressed her fingers...",
            summary="Elara attempts to interrogate a suspect using telepathy but experiences severe sensory overload, forcing her to abandon the interrogation.",
            key_points=[
                "Elara's telepathy triggered by suspect's guilt",
                "Mental overload worse than previous cases",
                "Marcus Reed witnesses her struggle",
                "Interrogation incomplete",
            ],
        )

        assert (
            scene.summary
            == "Elara attempts to interrogate a suspect using telepathy but experiences severe sensory overload, forcing her to abandon the interrogation."
        )
        assert len(scene.key_points) == 4
        assert "Mental overload worse than previous cases" in scene.key_points

    def test_json_roundtrip(self):
        """Test SceneSequel survives JSON serialization."""
        original = SceneSequel(
            id="ss_001",
            type="scene",
            source_act="act_1",
            pov_character="Maya",
            location="The Precinct",
            goal="Find the killer",
            conflict="Witness is uncooperative",
            disaster="Discovers first clue",
            start_hours=14.5,
            duration_hours=1.0,
            summary="Maya interrogates witness and discovers key clue",
            key_points=["Witness reveals suspect's location", "Maya's intuition proves correct"],
        )

        json_str = json.dumps(original.to_dict())
        restored = SceneSequel.from_dict(json.loads(json_str))

        # Compare key fields (calculated fields will be regenerated)
        assert restored.id == original.id
        assert restored.source_act == original.source_act
        assert restored.pov_character == original.pov_character
        assert restored.location == original.location
        assert restored.start_hours == original.start_hours
        assert restored.duration_hours == original.duration_hours
        assert restored.end_hours == original.end_hours
        assert restored.summary == original.summary
        assert restored.key_points == original.key_points
        assert restored.time_of_day == original.time_of_day
        assert restored.day_number == original.day_number


class TestEditorialFeedback:
    """Tests for EditorialFeedback model."""

    def test_creation(self):
        """Test EditorialFeedback can be created."""
        feedback = EditorialFeedback(
            step="idea",
            rating="good",
            issues=["One-sentence could be more specific"],
            suggestions=["Add more details about the telepathy"],
            praise=["Strong hook", "Clear genre"],
        )

        assert feedback.rating == "good"
        assert len(feedback.issues) == 1
        assert len(feedback.praise) == 2

    def test_json_roundtrip(self):
        """Test EditorialFeedback survives JSON serialization."""
        original = EditorialFeedback(
            step="characters",
            rating="excellent",
            issues=[],
            suggestions=[],
            praise=["Well-developed characters"],
        )

        json_str = json.dumps(original.to_dict())
        restored = EditorialFeedback.from_dict(json.loads(json_str))

        assert original == restored


class TestProjectConfig:
    """Tests for ProjectConfig model."""

    def test_creation_defaults(self):
        """Test ProjectConfig with default values."""
        config = ProjectConfig()

        assert config.target_length == "short"
        assert config.structure == "three_act"
        assert config.writer_model == "gpt-4"
        assert config.use_editor is True

    def test_creation_custom(self):
        """Test ProjectConfig with custom values."""
        config = ProjectConfig(
            target_length="novella",
            writer_model="ollama/qwen3:30b",
            use_editor=False,
            pacing_profile="thriller",
            use_chapters=True,
        )

        assert config.target_length == "novella"
        assert config.writer_model == "ollama/qwen3:30b"
        assert config.use_editor is False
        assert config.use_chapters is True

    def test_time_tracking_config(self):
        """Test time tracking configuration fields."""
        config = ProjectConfig(
            start_timestamp="Monday 8:00 AM",
            story_duration_hours=48.0,
            validate_travel_times=True,
            max_time_gap_hours=12.0,
            location_distances={"Precinct": {"Crime Scene": 0.5}},
        )

        assert config.start_timestamp == "Monday 8:00 AM"
        assert config.story_duration_hours == 48.0
        assert config.validate_travel_times is True
        assert "Precinct" in config.location_distances

    def test_json_roundtrip(self):
        """Test ProjectConfig survives JSON serialization."""
        original = ProjectConfig(
            target_length="novella",
            pacing_profile="thriller",
            use_chapters=True,
            location_distances={"A": {"B": 2.0}},
        )

        json_str = json.dumps(original.to_dict())
        restored = ProjectConfig.from_dict(json.loads(json_str))

        assert original == restored


class TestWorkingDoc:
    """Tests for WorkingDoc model."""

    def test_creation_empty(self):
        """Test WorkingDoc with no story components."""
        doc = WorkingDoc(id="test-story", created_at=datetime(2025, 1, 1, 12, 0, 0))

        assert doc.id == "test-story"
        assert doc.idea is None
        assert len(doc.characters) == 0

    def test_creation_with_components(self):
        """Test WorkingDoc holds all story components."""
        doc = WorkingDoc(id="test-story", created_at=datetime(2025, 1, 1, 12, 0, 0))

        doc.idea = StoryIdea(
            raw_idea="Test",
            one_sentence="A detective solves a crime",
            expanded="...",
            genres=["mystery"],
            tone="Dark",
            themes=["justice"],
            setting="Test setting",
        )

        doc.characters = [
            Character(
                name="Maya",
                role="protagonist",
                bio="Detective",
                goal="Solve crime",
                flaw="Trust issues",
            ),
            Character(
                name="John", role="antagonist", bio="Killer", goal="Escape", flaw="Arrogance"
            ),
        ]

        doc.locations = [
            Location(
                name="Precinct",
                description="Police station",
                atmosphere="Busy",
                significance="Maya's workplace",
            )
        ]

        assert doc.idea is not None
        assert len(doc.characters) == 2
        assert len(doc.locations) == 1

    def test_json_roundtrip_empty(self):
        """Test empty WorkingDoc survives JSON serialization."""
        original = WorkingDoc(
            id="test-story",
            created_at=datetime(2025, 1, 1, 12, 0, 0),
            updated_at=datetime(2025, 1, 1, 13, 0, 0),
        )

        json_str = json.dumps(original.to_dict())
        restored = WorkingDoc.from_dict(json.loads(json_str))

        assert restored.id == original.id
        assert restored.created_at == original.created_at
        assert restored.updated_at == original.updated_at

    def test_json_roundtrip_complete(self):
        """Test complete WorkingDoc serialization."""
        original = WorkingDoc(id="test-story", created_at=datetime(2025, 1, 1, 12, 0, 0))

        # Populate with full story
        original.idea = StoryIdea(
            raw_idea="Test",
            one_sentence="A detective solves a crime",
            expanded="...",
            genres=["mystery"],
            tone="Dark",
            themes=["justice"],
            setting="Test setting",
        )

        original.characters = [
            Character(
                name="Maya",
                role="protagonist",
                bio="Detective",
                goal="Solve crime",
                flaw="Trust issues",
            )
        ]

        original.locations = [
            Location(
                name="Precinct",
                description="Police station",
                atmosphere="Busy",
                significance="Maya's workplace",
            )
        ]

        original.outline = [ActStructure(act=1, summary="Setup", hook="Maya discovers the body")]

        original.scene_sequel_breakdown = [
            SceneSequel(
                id="ss_001",
                type="scene",
                source_act="act_1",
                pov_character="Maya",
                location="Precinct",
                goal="Find clues",
                conflict="Evidence is scattered",
                disaster="Discovers evidence",
                start_hours=8.0,
                duration_hours=1.0,
            )
        ]

        original.editorial_feedback = [
            EditorialFeedback(
                step="idea",
                rating="good",
                issues=["Could be more specific"],
                suggestions=["Add more detail"],
            )
        ]

        json_str = json.dumps(original.to_dict())
        restored = WorkingDoc.from_dict(json.loads(json_str))

        assert restored.id == original.id
        assert restored.idea is not None
        assert original.idea is not None
        assert restored.idea.one_sentence == original.idea.one_sentence
        assert len(restored.characters) == len(original.characters)
        assert restored.characters[0].name == "Maya"
        assert len(restored.locations) == 1
        assert len(restored.outline) == 1
        assert len(restored.scene_sequel_breakdown) == 1
        assert restored.scene_sequel_breakdown[0].id == "ss_001"
        assert len(restored.editorial_feedback) == 1


class TestProject:
    """Tests for Project model."""

    def test_creation(self):
        """Test Project can be created."""
        project = Project(
            id="test-story", title="Test Story", created_at=datetime(2025, 1, 1, 12, 0, 0)
        )

        assert project.id == "test-story"
        assert project.title == "Test Story"
        assert project.current_step == "created"

    def test_creation_with_config(self):
        """Test Project with custom config."""
        config = ProjectConfig(target_length="novella", use_chapters=True)

        project = Project(
            id="test-story",
            title="Test Story",
            created_at=datetime(2025, 1, 1, 12, 0, 0),
            config=config,
        )

        assert project.config.target_length == "novella"
        assert project.config.use_chapters is True

    def test_json_roundtrip(self):
        """Test Project survives JSON serialization."""
        original = Project(
            id="test-story",
            title="Test Story",
            created_at=datetime(2025, 1, 1, 12, 0, 0),
            updated_at=datetime(2025, 1, 1, 13, 0, 0),
            current_step="idea",
        )

        json_str = json.dumps(original.to_dict())
        restored = Project.from_dict(json.loads(json_str))

        assert restored.id == original.id
        assert restored.title == original.title
        assert restored.created_at == original.created_at
        assert restored.current_step == original.current_step

    def test_json_roundtrip_with_paths(self):
        """Test Project with file paths survives JSON serialization."""
        original = Project(
            id="test-story",
            title="Test Story",
            created_at=datetime(2025, 1, 1, 12, 0, 0),
            current_step="idea",
        )
        # Simulate ProjectManager setting paths
        original.project_dir = Path("c:/projects/test-story")
        original.working_doc_path = Path("c:/projects/test-story/working_doc.json")
        original.versions_dir = Path("c:/projects/test-story/versions")
        original.output_dir = Path("c:/projects/test-story/output")

        json_str = json.dumps(original.to_dict())
        data = json.loads(json_str)

        # Paths should be converted to strings in JSON
        assert (
            data["project_dir"] == "c:\\projects\\test-story"
            or data["project_dir"] == "c:/projects/test-story"
        )

        restored = Project.from_dict(data)
        assert restored.id == original.id
        assert restored.title == original.title
