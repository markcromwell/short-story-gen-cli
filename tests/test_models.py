"""
Tests for story data models
"""

import json

from storygen.models import Scene, Story


class TestScene:
    """Tests for Scene model"""

    def test_scene_creation(self):
        """Test basic scene creation"""
        scene = Scene(
            number=1,
            title="The Beginning",
            content="Once upon a time...",
            pov_character="Hero",
        )

        assert scene.number == 1
        assert scene.title == "The Beginning"
        assert scene.content == "Once upon a time..."
        assert scene.pov_character == "Hero"

    def test_scene_to_dict(self):
        """Test scene dictionary conversion"""
        scene = Scene(number=1, title="Test", content="Content")

        scene_dict = scene.to_dict()

        assert scene_dict["number"] == 1
        assert scene_dict["title"] == "Test"
        assert scene_dict["content"] == "Content"
        assert scene_dict["pov_character"] is None


class TestStory:
    """Tests for Story model"""

    def test_story_creation(self):
        """Test basic story creation"""
        scenes = [
            Scene(number=1, title="Scene 1", content="First scene"),
            Scene(number=2, title="Scene 2", content="Second scene"),
        ]

        story = Story(title="Test Story", scenes=scenes, genre="Fantasy", summary="A test story")

        assert story.title == "Test Story"
        assert len(story.scenes) == 2
        assert story.genre == "Fantasy"
        assert story.summary == "A test story"

    def test_story_word_count(self):
        """Test automatic word count calculation"""
        scenes = [
            Scene(number=1, title="Scene 1", content="One two three"),
            Scene(number=2, title="Scene 2", content="Four five six seven"),
        ]

        story = Story(title="Test", scenes=scenes)

        assert story._calculate_word_count() == 7

    def test_story_to_dict(self):
        """Test story dictionary conversion"""
        scenes = [Scene(number=1, title="Test", content="Content")]
        story = Story(title="Test Story", scenes=scenes, genre="Sci-Fi")

        story_dict = story.to_dict()

        assert story_dict["title"] == "Test Story"
        assert story_dict["genre"] == "Sci-Fi"
        assert len(story_dict["scenes"]) == 1
        assert story_dict["word_count"] == 1

    def test_story_to_json(self):
        """Test story JSON serialization"""
        scenes = [Scene(number=1, title="Test", content="Content")]
        story = Story(title="Test Story", scenes=scenes)

        json_str = story.to_json()
        parsed = json.loads(json_str)

        assert parsed["title"] == "Test Story"
        assert len(parsed["scenes"]) == 1

    def test_story_from_json(self):
        """Test story JSON deserialization"""
        json_str = """
        {
            "title": "Test Story",
            "genre": "Mystery",
            "summary": "A mysterious test",
            "characters": ["Detective Sam", "Butler James"],
            "scenes": [
                {
                    "number": 1,
                    "title": "The Discovery",
                    "content": "Something was found...",
                    "pov_character": "Detective Sam"
                }
            ]
        }
        """

        story = Story.from_json(json_str)

        assert story.title == "Test Story"
        assert story.genre == "Mystery"
        assert story.summary == "A mysterious test"
        assert story.characters == ["Detective Sam", "Butler James"]
        assert len(story.scenes) == 1
        assert story.scenes[0].title == "The Discovery"
        assert story.scenes[0].pov_character == "Detective Sam"

    def test_story_to_text(self):
        """Test story text formatting with new scene break logic"""
        scenes = [
            Scene(
                number=1,
                title="Opening",
                content="The story begins.",
                pov_character="Alice",
                location="Cafe",
                time_hours=0.0,
            ),
            Scene(
                number=2,
                title="Later",
                content="The story continues.",
                pov_character="Bob",
                location="Park",
                time_hours=3.0,
            ),
        ]

        story = Story(
            title="Test Story",
            scenes=scenes,
            genre="Drama",
            characters=["Alice Cooper", "Bob Smith"],
        )

        text = story.to_text()

        # Check metadata
        assert "# Test Story" in text
        assert "**Genre:** Drama" in text

        # Check scene content is present (no titles or POV displayed)
        assert "The story begins." in text
        assert "The story continues." in text

        # Check scene break appears (POV changed)
        assert "— • —" in text

        # Check Dramatis Personae at end
        assert "Dramatis Personae" in text
        assert "Alice Cooper" in text
        assert "Bob Smith" in text

        # Verify Dramatis Personae comes after story content
        dp_index = text.index("Dramatis Personae")
        story_index = text.index("The story continues.")
        assert dp_index > story_index

    def test_story_roundtrip(self):
        """Test JSON serialization and deserialization roundtrip"""
        scenes = [
            Scene(
                number=1,
                title="Test Scene",
                content="Test content",
                pov_character="Test Character",
            )
        ]

        original = Story(
            title="Original Story", scenes=scenes, genre="Test Genre", characters=["Test Character"]
        )

        # Convert to JSON and back
        json_str = original.to_json()
        restored = Story.from_json(json_str)

        assert restored.title == original.title
        assert restored.genre == original.genre
        assert restored.characters == original.characters
        assert len(restored.scenes) == len(original.scenes)
        assert restored.scenes[0].title == original.scenes[0].title
        assert restored.scenes[0].content == original.scenes[0].content
        assert restored.scenes[0].pov_character == original.scenes[0].pov_character

    def test_get_characters_sorted(self):
        """Test that characters are sorted by last name"""
        story = Story(
            title="Test",
            scenes=[],
            characters=["Alice Cooper", "Bob Smith", "Charlie Anderson", "David Brown"],
        )

        sorted_chars = story.get_characters()

        # Should be sorted by last name: Anderson, Brown, Cooper, Smith
        assert sorted_chars == ["Charlie Anderson", "David Brown", "Alice Cooper", "Bob Smith"]

    def test_get_characters_empty(self):
        """Test that get_characters returns empty list when no characters"""
        story = Story(title="Test", scenes=[])

        assert story.get_characters() == []
