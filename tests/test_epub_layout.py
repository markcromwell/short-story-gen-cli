"""
Tests for EPUB layout and scene break behavior.

These tests lock in the scene break logic so future edits don't accidentally
introduce visual regressions like underlines between every scene or missing
ornamental breaks for POV changes.
"""

import tempfile
import zipfile
from pathlib import Path

from storygen.epub import generate_epub
from storygen.models import Scene, Story


class TestSceneBreakBehavior:
    """Test that scene breaks render correctly for different transition types."""

    def test_pov_change_gets_ornament(self):
        """POV changes should get ornamental break: — • —"""
        story = Story(
            title="Test Story",
            scenes=[
                Scene(
                    number=1,
                    title="First Scene",
                    content="First scene content",
                    pov_character="Alice",
                    location="home",
                    time_hours=0.0,
                ),
                Scene(
                    number=2,
                    title="Second Scene",
                    content="Second scene content",
                    pov_character="Bob",  # POV changed
                    location="home",
                    time_hours=0.0,
                ),
            ],
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            epub_path = generate_epub(story, output_path=str(Path(tmpdir) / "test.epub"))

            # Read the EPUB content to verify ornament is present
            with zipfile.ZipFile(epub_path, "r") as zf:
                # Read the main story content file
                content = zf.read("EPUB/story.xhtml").decode("utf-8")

                # Should have ornamental break
                assert "— • —" in content, "POV change should have ornamental break"
                # Should NOT have underline (<hr> element)
                assert "<hr" not in content, "Should not use <hr> for scene breaks"

    def test_time_change_gets_whitespace_only(self):
        """Time/location changes should get whitespace break, no ornament."""
        story = Story(
            title="Test Story",
            scenes=[
                Scene(
                    number=1,
                    title="First Scene",
                    content="First scene content",
                    pov_character="Alice",
                    location="home",
                    time_hours=0.0,
                ),
                Scene(
                    number=2,
                    title="Second Scene",
                    content="Second scene content",
                    pov_character="Alice",  # Same POV
                    location="home",
                    time_hours=3.0,  # Time gap > 2 hours triggers break
                ),
            ],
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            epub_path = generate_epub(story, output_path=str(Path(tmpdir) / "test.epub"))

            with zipfile.ZipFile(epub_path, "r") as zf:
                content = zf.read("EPUB/story.xhtml").decode("utf-8")

                # Should have scene-break class with non-breaking space
                assert 'class="scene-break"' in content, "Should have scene-break element"
                # Non-breaking space entity gets converted to actual character by ebooklib
                assert "\xa0" in content, "Should use non-breaking space for whitespace gap"
                # Should NOT have ornament for time-only changes
                assert "— • —" not in content, "Time change should not have ornament"
                # Should NOT have underline
                assert "<hr" not in content, "Should not use <hr> for scene breaks"

    def test_location_change_gets_whitespace_only(self):
        """Location changes should get whitespace break, no ornament."""
        story = Story(
            title="Test Story",
            scenes=[
                Scene(
                    number=1,
                    title="First Scene",
                    content="First scene content",
                    pov_character="Alice",
                    location="home",
                    time_hours=0.0,
                ),
                Scene(
                    number=2,
                    title="Second Scene",
                    content="Second scene content",
                    pov_character="Alice",  # Same POV
                    location="office",  # Location changed
                    time_hours=0.0,
                ),
            ],
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            epub_path = generate_epub(story, output_path=str(Path(tmpdir) / "test.epub"))

            with zipfile.ZipFile(epub_path, "r") as zf:
                content = zf.read("EPUB/story.xhtml").decode("utf-8")

                # Should have whitespace gap, not ornament
                assert 'class="scene-break"' in content, "Should have scene-break element"
                # Non-breaking space entity gets converted to actual character by ebooklib
                assert "\xa0" in content, "Should use non-breaking space"
                assert "— • —" not in content, "Location change should not have ornament"
                assert "<hr" not in content, "Should not use <hr> for scene breaks"

    def test_no_change_no_break(self):
        """Consecutive scenes with no metadata changes should have no break."""
        story = Story(
            title="Test Story",
            scenes=[
                Scene(
                    number=1,
                    title="First Scene",
                    content="First scene content",
                    pov_character="Alice",
                    location="home",
                    time_hours=0.0,
                ),
                Scene(
                    number=2,
                    title="Second Scene",
                    content="Second scene content",
                    pov_character="Alice",  # Same POV
                    location="home",  # Same location
                    time_hours=0.0,  # Same time
                ),
            ],
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            epub_path = generate_epub(story, output_path=str(Path(tmpdir) / "test.epub"))

            with zipfile.ZipFile(epub_path, "r") as zf:
                content = zf.read("EPUB/story.xhtml").decode("utf-8")

                # Count scene-break elements (should be 0 since there's no change)
                scene_breaks = content.count('class="scene-break"')
                assert scene_breaks == 0, "No metadata change should mean no scene break"

    def test_first_scene_no_break(self):
        """The first scene should never have a break before it."""
        story = Story(
            title="Test Story",
            scenes=[
                Scene(
                    number=1,
                    title="Only Scene",
                    content="Only scene content",
                    pov_character="Alice",
                    location="home",
                    time_hours=0.0,
                ),
            ],
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            epub_path = generate_epub(story, output_path=str(Path(tmpdir) / "test.epub"))

            with zipfile.ZipFile(epub_path, "r") as zf:
                content = zf.read("EPUB/story.xhtml").decode("utf-8")

                # Should have no scene breaks at all
                assert 'class="scene-break"' not in content, "First scene should have no break"


class TestEpubStructure:
    """Test overall EPUB structure and navigation."""

    def test_nav_xhtml_exists(self):
        """EPUB should always include nav.xhtml for navigation."""
        story = Story(
            title="Test Story",
            scenes=[
                Scene(
                    number=1,
                    title="Test Scene",
                    content="Test content",
                    pov_character="Alice",
                    location="home",
                    time_hours=0.0,
                ),
            ],
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            epub_path = generate_epub(story, output_path=str(Path(tmpdir) / "test.epub"))

            with zipfile.ZipFile(epub_path, "r") as zf:
                # Check that nav.xhtml is present in the EPUB
                assert "EPUB/nav.xhtml" in zf.namelist(), "nav.xhtml must exist in EPUB"

    def test_css_has_scene_break_class(self):
        """CSS should define .scene-break for both ornaments and whitespace."""
        story = Story(
            title="Test Story",
            scenes=[
                Scene(
                    number=1,
                    title="Test Scene",
                    content="Test content",
                    pov_character="Alice",
                    location="home",
                    time_hours=0.0,
                ),
            ],
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            epub_path = generate_epub(story, output_path=str(Path(tmpdir) / "test.epub"))

            with zipfile.ZipFile(epub_path, "r") as zf:
                # Find the CSS file
                css_files = [name for name in zf.namelist() if name.endswith(".css")]
                assert len(css_files) > 0, "EPUB should include a CSS file"

                css_content = zf.read(css_files[0]).decode("utf-8")

                # Should define .scene-break
                assert ".scene-break" in css_content, "CSS must define .scene-break class"
                # Should NOT define the old .scene-gap class
                assert ".scene-gap" not in css_content, "Old .scene-gap class should be removed"

    def test_no_hr_elements_in_content(self):
        """Content chapters should never contain <hr> elements."""
        story = Story(
            title="Test Story",
            scenes=[
                Scene(
                    number=1,
                    title="First Scene",
                    content="First content",
                    pov_character="Alice",
                    location="home",
                    time_hours=0.0,
                ),
                Scene(
                    number=2,
                    title="Second Scene",
                    content="Second content",
                    pov_character="Bob",  # POV change
                    location="home",
                    time_hours=0.0,
                ),
                Scene(
                    number=3,
                    title="Third Scene",
                    content="Third content",
                    pov_character="Alice",  # POV change back
                    location="office",  # Location change
                    time_hours=2.0,  # Time change
                ),
            ],
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            epub_path = generate_epub(story, output_path=str(Path(tmpdir) / "test.epub"))

            with zipfile.ZipFile(epub_path, "r") as zf:
                content = zf.read("EPUB/story.xhtml").decode("utf-8")
                assert "<hr" not in content, "story.xhtml should not contain <hr> elements"
