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
            setting="A dark forest",
            characters=["Hero", "Villain"],
        )

        assert scene.number == 1
        assert scene.title == "The Beginning"
        assert scene.content == "Once upon a time..."
        assert scene.setting == "A dark forest"
        assert scene.characters == ["Hero", "Villain"]

    def test_scene_to_dict(self):
        """Test scene dictionary conversion"""
        scene = Scene(number=1, title="Test", content="Content")

        scene_dict = scene.to_dict()

        assert scene_dict["number"] == 1
        assert scene_dict["title"] == "Test"
        assert scene_dict["content"] == "Content"
        assert scene_dict["setting"] is None
        assert scene_dict["characters"] is None


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
            "scenes": [
                {
                    "number": 1,
                    "title": "The Discovery",
                    "content": "Something was found...",
                    "setting": "Old mansion",
                    "characters": ["Detective", "Butler"]
                }
            ]
        }
        """

        story = Story.from_json(json_str)

        assert story.title == "Test Story"
        assert story.genre == "Mystery"
        assert story.summary == "A mysterious test"
        assert len(story.scenes) == 1
        assert story.scenes[0].title == "The Discovery"
        assert story.scenes[0].setting == "Old mansion"
        assert story.scenes[0].characters == ["Detective", "Butler"]

    def test_story_to_text(self):
        """Test story text formatting"""
        scenes = [
            Scene(
                number=1,
                title="Opening",
                content="The story begins.",
                setting="A cafe",
                characters=["Alice", "Bob"],
            )
        ]

        story = Story(title="Test Story", scenes=scenes, genre="Drama")

        text = story.to_text()

        assert "# Test Story" in text
        assert "**Genre:** Drama" in text
        assert "## Scene 1: Opening" in text
        assert "*Setting: A cafe*" in text
        assert "*Characters: Alice, Bob*" in text
        assert "The story begins." in text

    def test_story_roundtrip(self):
        """Test JSON serialization and deserialization roundtrip"""
        scenes = [
            Scene(
                number=1,
                title="Test Scene",
                content="Test content",
                setting="Test setting",
                characters=["Test Character"],
            )
        ]

        original = Story(title="Original Story", scenes=scenes, genre="Test Genre")

        # Convert to JSON and back
        json_str = original.to_json()
        restored = Story.from_json(json_str)

        assert restored.title == original.title
        assert restored.genre == original.genre
        assert len(restored.scenes) == len(original.scenes)
        assert restored.scenes[0].title == original.scenes[0].title
        assert restored.scenes[0].content == original.scenes[0].content
        assert restored.scenes[0].setting == original.scenes[0].setting
        assert restored.scenes[0].characters == original.scenes[0].characters
