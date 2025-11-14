"""
Unit tests for EPUB validation and structure.

Tests EPUB generation to ensure compliance with EPUB standards
and proper structure for retail distribution.
"""

import tempfile
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

import pytest

from storygen.iterative.formatters.epub import EpubFormatter
from storygen.iterative.models import Character, Location, SceneSequel, StoryIdea


class TestEpubValidation:
    """Test EPUB structure and validation."""

    @pytest.fixture
    def sample_story_data(self):
        """Create sample story data for testing."""
        story_idea = StoryIdea(
            raw_idea="A test story about validation",
            one_sentence="This is a test story for EPUB validation.",
            expanded="A longer description of the test story.",
            genres=["fantasy", "mystery"],
            themes=["validation", "testing"],
            tone="serious",
            setting="Modern coastal village",
        )

        characters = [
            Character(
                name="Test Character",
                role="protagonist",
                bio="A character for testing.",
                goal="validate EPUB",
                flaw="technical issues",
            )
        ]

        locations = [
            Location(
                name="Test Location",
                description="A place for testing.",
                atmosphere="mysterious",
                significance="validation site",
            )
        ]

        scene_sequels = [
            SceneSequel(
                id="ss_001",
                type="scene",
                source_act="Act 1",
                pov_character="Test Character",
                location="Test Location",
                start_hours=0.0,
                duration_hours=1.0,
                goal="validate EPUB",
                conflict="technical issues",
                disaster="bugs found",
                content="This is test content for validation.\n\nIt has multiple paragraphs.",
                actual_word_count=12,
            )
        ]

        return story_idea, characters, locations, scene_sequels

    def test_epub_basic_structure(self, sample_story_data):
        """Test that EPUB has required files and structure."""
        story_idea, characters, locations, scene_sequels = sample_story_data

        formatter = EpubFormatter(verbose=True)

        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "test.epub"

            epub_path = formatter.format(
                story_idea=story_idea,
                characters=characters,
                locations=locations,
                scene_sequels=scene_sequels,
                output_path=str(output_path),
                title_override="Test Title",
            )

            # Verify EPUB was created
            assert epub_path.exists()

            # Extract and verify structure
            with zipfile.ZipFile(epub_path, "r") as epub_zip:
                file_list = [f.filename for f in epub_zip.filelist]

                # Required files
                assert "mimetype" in file_list
                assert "META-INF/container.xml" in file_list
                assert "EPUB/content.opf" in file_list
                assert "EPUB/toc.ncx" in file_list
                assert "EPUB/nav.xhtml" in file_list

                # CSS should be present
                css_files = [f for f in file_list if f.endswith(".css")]
                assert len(css_files) > 0, "No CSS files found"

                # Chapter files should exist
                chapter_files = [
                    f for f in file_list if f.startswith("EPUB/chapter_") and f.endswith(".xhtml")
                ]
                assert len(chapter_files) > 0, "No chapter files found"

    def test_mimetype_format(self, sample_story_data):
        """Test that mimetype file is properly formatted (uncompressed, first in zip)."""
        story_idea, characters, locations, scene_sequels = sample_story_data

        formatter = EpubFormatter()

        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "test.epub"

            epub_path = formatter.format(
                story_idea=story_idea,
                characters=characters,
                locations=locations,
                scene_sequels=scene_sequels,
                output_path=str(output_path),
                title_override="Test Title",
            )

            with zipfile.ZipFile(epub_path, "r") as epub_zip:
                # mimetype should be first file and uncompressed
                first_file = epub_zip.filelist[0]
                assert first_file.filename == "mimetype"
                assert (
                    first_file.compress_type == zipfile.ZIP_STORED
                ), "mimetype should be uncompressed"

                # Content should be exactly "application/epub+zip"
                mimetype_content = epub_zip.read("mimetype").decode()
                assert mimetype_content == "application/epub+zip"

    def test_opf_metadata_completeness(self, sample_story_data):
        """Test that OPF contains all required metadata fields."""
        story_idea, characters, locations, scene_sequels = sample_story_data

        formatter = EpubFormatter(author="Test Author")

        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "test.epub"

            epub_path = formatter.format(
                story_idea=story_idea,
                characters=characters,
                locations=locations,
                scene_sequels=scene_sequels,
                output_path=str(output_path),
                title_override="Test Title",
            )

            with zipfile.ZipFile(epub_path, "r") as epub_zip:
                opf_content = epub_zip.read("EPUB/content.opf").decode()

                # Parse XML
                root = ET.fromstring(opf_content)
                metadata = root.find(".//{http://www.idpf.org/2007/opf}metadata")

                assert metadata is not None, "No metadata element found in OPF"

                # Check extended metadata

                # Required Dublin Core fields
                dc_ns = "{http://purl.org/dc/elements/1.1/}"
                required_fields = ["title", "creator", "language", "identifier"]

                for field in required_fields:
                    elements = metadata.findall(f".//{dc_ns}{field}")
                    assert len(elements) > 0, f"Missing required field: {field}"

                    # Check content is not empty
                    assert elements[0].text and elements[0].text.strip(), f"Empty {field} field"

                # Should have dcterms:modified
                modified_elements = metadata.findall(
                    ".//{http://www.idpf.org/2007/opf}meta[@property='dcterms:modified']"
                )
                assert len(modified_elements) > 0, "Missing dcterms:modified"

    def test_xhtml_structure_validity(self, sample_story_data):
        """Test that XHTML files have proper HTML structure."""
        story_idea, characters, locations, scene_sequels = sample_story_data

        formatter = EpubFormatter()

        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "test.epub"

            epub_path = formatter.format(
                story_idea=story_idea,
                characters=characters,
                locations=locations,
                scene_sequels=scene_sequels,
                output_path=str(output_path),
                title_override="Test Title",
            )

            with zipfile.ZipFile(epub_path, "r") as epub_zip:
                # Check all XHTML files
                xhtml_files = [f for f in epub_zip.filelist if f.filename.endswith(".xhtml")]

                for xhtml_file in xhtml_files:
                    content = epub_zip.read(xhtml_file.filename).decode()

                    # Should have proper XML declaration
                    assert content.startswith(
                        "<?xml"
                    ), f"Missing XML declaration in {xhtml_file.filename}"

                    # Should have DOCTYPE
                    assert "<!DOCTYPE html>" in content, f"Missing DOCTYPE in {xhtml_file.filename}"

                    # Should have html, head, body tags
                    assert "<html" in content, f"Missing <html> tag in {xhtml_file.filename}"
                    assert "<head>" in content, f"Missing <head> tag in {xhtml_file.filename}"
                    assert "<body>" in content, f"Missing <body> tag in {xhtml_file.filename}"

                    # Should have closing tags
                    assert "</html>" in content, f"Missing </html> tag in {xhtml_file.filename}"
                    assert "</head>" in content, f"Missing </head> tag in {xhtml_file.filename}"
                    assert "</body>" in content, f"Missing </body> tag in {xhtml_file.filename}"

    def test_navigation_files_present(self, sample_story_data):
        """Test that navigation files are properly structured."""
        story_idea, characters, locations, scene_sequels = sample_story_data

        formatter = EpubFormatter()

        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "test.epub"

            epub_path = formatter.format(
                story_idea=story_idea,
                characters=characters,
                locations=locations,
                scene_sequels=scene_sequels,
                output_path=str(output_path),
                title_override="Test Title",
            )

            with zipfile.ZipFile(epub_path, "r") as epub_zip:
                file_list = [f.filename for f in epub_zip.filelist]

                # Both navigation files should be present
                assert "EPUB/toc.ncx" in file_list
                assert "EPUB/nav.xhtml" in file_list

                # toc.ncx should be valid XML
                toc_content = epub_zip.read("EPUB/toc.ncx").decode()
                assert "<?xml" in toc_content
                assert "<ncx" in toc_content

                # nav.xhtml should be valid XHTML
                nav_content = epub_zip.read("EPUB/nav.xhtml").decode()
                assert "<?xml" in nav_content
                assert "<html" in nav_content

    def test_css_styling_present(self, sample_story_data):
        """Test that CSS provides proper typography styling."""
        story_idea, characters, locations, scene_sequels = sample_story_data

        formatter = EpubFormatter()

        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "test.epub"

            epub_path = formatter.format(
                story_idea=story_idea,
                characters=characters,
                locations=locations,
                scene_sequels=scene_sequels,
                output_path=str(output_path),
                title_override="Test Title",
            )

            with zipfile.ZipFile(epub_path, "r") as epub_zip:
                css_files = [f for f in epub_zip.filelist if f.filename.endswith(".css")]

                # Should have at least one CSS file
                assert len(css_files) > 0

                # Check CSS content for essential styles
                css_content = epub_zip.read(css_files[0].filename).decode()

                # Should have body styling
                assert "body" in css_content

                # Should have paragraph styling
                assert "p" in css_content

                # Should have typography settings
                essential_styles = ["font-family", "line-height", "text-indent"]
                found_styles = sum(1 for style in essential_styles if style in css_content)
                assert (
                    found_styles >= 2
                ), f"Missing essential typography styles. Found: {found_styles}/{len(essential_styles)}"

    def test_scene_break_styling(self, sample_story_data):
        """Test that scene breaks are properly styled when present."""
        story_idea, characters, locations, scene_sequels = sample_story_data

        formatter = EpubFormatter()

        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "test.epub"

            epub_path = formatter.format(
                story_idea=story_idea,
                characters=characters,
                locations=locations,
                scene_sequels=scene_sequels,
                output_path=str(output_path),
                title_override="Test Title",
            )

            with zipfile.ZipFile(epub_path, "r") as epub_zip:
                # Check CSS for scene break styling
                css_files = [f for f in epub_zip.filelist if f.filename.endswith(".css")]
                css_content = epub_zip.read(css_files[0].filename).decode()

                # Should have scene-break class defined
                assert ".scene-break" in css_content, "Missing scene-break CSS class"

                # Should have proper scene break styling
                assert "text-align: center" in css_content, "Scene breaks should be center-aligned"
                assert "margin:" in css_content, "Scene breaks should have margin styling"

    def test_extended_metadata_fields(self, sample_story_data):
        """Test that extended metadata fields are included when provided."""
        story_idea, characters, locations, scene_sequels = sample_story_data

        formatter = EpubFormatter(
            author="Test Author",
            publisher="Test Publisher",
            rights="© 2024 Test Rights",
            contributor="AI Assistant",
            include_accessibility=True,
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "test.epub"

            epub_path = formatter.format(
                story_idea=story_idea,
                characters=characters,
                locations=locations,
                scene_sequels=scene_sequels,
                output_path=str(output_path),
                title_override="Test Title",
            )

            with zipfile.ZipFile(epub_path, "r") as epub_zip:
                opf_content = epub_zip.read("EPUB/content.opf").decode()

                # Parse XML
                root = ET.fromstring(opf_content)
                metadata = root.find(".//{http://www.idpf.org/2007/opf}metadata")

                if metadata is None:
                    pytest.fail("No metadata element found in OPF")

                # Check extended metadata
                dc_ns = "{http://purl.org/dc/elements/1.1/}"
                publisher_elements = metadata.findall(f".//{dc_ns}publisher")
                assert len(publisher_elements) > 0, "Missing publisher field"
                assert publisher_elements[0].text == "Test Publisher"

                rights_elements = metadata.findall(f".//{dc_ns}rights")
                assert len(rights_elements) > 0, "Missing rights field"
                assert rights_elements[0].text == "© 2024 Test Rights"

                contributor_elements = metadata.findall(f".//{dc_ns}contributor")
                assert len(contributor_elements) > 0, "Missing contributor field"
                assert contributor_elements[0].text == "AI Assistant"

                # Check rendition properties
                rendition_layout = metadata.findall(
                    ".//{http://www.idpf.org/2007/opf}meta[@property='rendition:layout']"
                )
                assert len(rendition_layout) > 0, "Missing rendition:layout"

                # Check accessibility metadata
                access_mode = metadata.findall(
                    ".//{http://www.idpf.org/2007/opf}meta[@property='schema:accessMode']"
                )
                assert len(access_mode) > 0, "Missing accessibility metadata"

    def test_scene_break_styling_options(self, sample_story_data):
        """Test that scene break styling can be configured."""
        story_idea, characters, locations, scene_sequels = sample_story_data

        # Add another scene-sequel with different POV to trigger scene break
        scene_sequels.append(
            SceneSequel(
                id="ss_002",
                type="scene",
                source_act="Act 1",
                pov_character="Different Character",  # Different POV to trigger break
                location="Test Location",
                start_hours=2.0,
                duration_hours=1.0,
                goal="test scene break",
                conflict="style testing",
                disaster="none",
                content="Second scene content.",
                actual_word_count=4,
            )
        )

        # Test different scene break styles
        for style in ["asterism", "ornament", "blank", "glyph"]:
            formatter = EpubFormatter(scene_break_style=style)  # type: ignore

            with tempfile.TemporaryDirectory() as temp_dir:
                output_path = Path(temp_dir) / "test.epub"

                epub_path = formatter.format(
                    story_idea=story_idea,
                    characters=characters,
                    locations=locations,
                    scene_sequels=scene_sequels,
                    output_path=str(output_path),
                    title_override="Test Title",
                )

                with zipfile.ZipFile(epub_path, "r") as epub_zip:
                    # Check that scene break appears in chapter content
                    chapter_files = [
                        f for f in epub_zip.filelist if f.filename.startswith("EPUB/chapter_")
                    ]
                    if chapter_files:
                        chapter_content = epub_zip.read(chapter_files[0].filename).decode()
                        assert (
                            'class="scene-break"' in chapter_content
                        ), f"Scene break not found for style {style}"

    def test_spine_nav_consistency_validation(self, sample_story_data):
        """Test that spine and navigation consistency is validated."""
        story_idea, characters, locations, scene_sequels = sample_story_data

        formatter = EpubFormatter(verbose=True)

        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "test.epub"

            # This should not raise any exceptions and should validate consistency
            epub_path = formatter.format(
                story_idea=story_idea,
                characters=characters,
                locations=locations,
                scene_sequels=scene_sequels,
                output_path=str(output_path),
                title_override="Test Title",
            )

            # Verify EPUB was created successfully
            assert epub_path.exists()

    def test_epub_validator_function(self, sample_story_data):
        """Test the built-in EPUB validator function."""
        story_idea, characters, locations, scene_sequels = sample_story_data

        formatter = EpubFormatter()

        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "test.epub"

            epub_path = formatter.format(
                story_idea=story_idea,
                characters=characters,
                locations=locations,
                scene_sequels=scene_sequels,
                output_path=str(output_path),
                title_override="Test Title",
            )

            # Test the validator
            report = EpubFormatter.validate_epub(epub_path)

            # Should be valid
            assert report["valid"] is True, f"Validation failed: {report.get('issues', [])}"

            # Should have structure info
            assert "structure" in report
            assert report["structure"]["total_files"] > 0
            assert report["structure"]["xhtml_files"] > 0

            # Test with non-existent file
            invalid_report = EpubFormatter.validate_epub("nonexistent.epub")
            assert invalid_report["valid"] is False
            assert "error" in invalid_report
