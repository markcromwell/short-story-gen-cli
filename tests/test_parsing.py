"""
Tests for parsing.py sanitization and extraction logic.

These tests lock in the behavior of our JSON parser so future edits
(by humans or AIs) don't accidentally break working functionality.
"""

import json

import pytest

from storygen.parsing import extract_json_block, parse_story_json, sanitize_llm_json


class TestExtractJsonBlock:
    """Test JSON block extraction with brace balancing."""

    def test_simple_object(self):
        """Should extract a simple JSON object."""
        text = '{"title": "Test"}'
        result = extract_json_block(text)
        assert result == '{"title": "Test"}'

    def test_nested_objects(self):
        """Should handle nested objects correctly."""
        text = '{"outer": {"inner": "value"}}'
        result = extract_json_block(text)
        assert result == '{"outer": {"inner": "value"}}'

    def test_with_prose_before(self):
        """Should extract JSON even with prose before it."""
        text = 'Here is the JSON: {"title": "Test"}'
        result = extract_json_block(text)
        assert result == '{"title": "Test"}'

    def test_with_prose_after(self):
        """Should extract just the first JSON object, ignoring trailing prose."""
        text = '{"title": "Test"} and some more text'
        result = extract_json_block(text)
        assert result == '{"title": "Test"}'

    def test_string_with_braces(self):
        """Should not be confused by braces inside strings."""
        text = '{"title": "Test {with} braces"}'
        result = extract_json_block(text)
        assert result == '{"title": "Test {with} braces"}'

    def test_no_json_raises(self):
        """Should raise ValueError when no JSON object found."""
        with pytest.raises(ValueError, match="No JSON object found"):
            extract_json_block("This is just plain text")


class TestSanitizeLlmJson:
    """Test JSON sanitization for common LLM output issues."""

    def test_valid_json_passthrough(self):
        """Valid JSON should pass through unchanged."""
        text = '{"title": "Test", "scenes": []}'
        result = sanitize_llm_json(text)
        # Should be parseable
        data = json.loads(result)
        assert data["title"] == "Test"
        assert data["scenes"] == []

    def test_code_fences_removed(self):
        """Should remove markdown code fences."""
        text = '```json\n{"title": "Test"}\n```'
        result = sanitize_llm_json(text)
        data = json.loads(result)
        assert data["title"] == "Test"

    def test_triple_quoted_strings(self):
        """Should handle Python-style triple-quoted strings."""
        text = '{"title": """Test with "quotes" inside"""}'
        result = sanitize_llm_json(text)
        data = json.loads(result)
        assert "quotes" in data["title"]

    def test_control_chars_removed(self):
        """Should remove control characters from strings."""
        text = '{"title": "Test\x00with\x01control\x02chars"}'
        result = sanitize_llm_json(text)
        data = json.loads(result)
        assert "\x00" not in data["title"]
        assert "\x01" not in data["title"]

    def test_newlines_escaped_in_strings(self):
        """Should escape raw newlines inside string values."""
        text = '{"title": "Line one\nLine two"}'
        result = sanitize_llm_json(text)
        data = json.loads(result)
        assert "Line one" in data["title"]
        assert "Line two" in data["title"]

    def test_malformed_keys_fixed(self):
        """Should fix keys with embedded newlines or special chars."""
        text = '{"title\n": "Test"}'
        result = sanitize_llm_json(text)
        data = json.loads(result)
        # Should have a valid key (either fixed or original works)
        assert len(data) == 1

    def test_trailing_commas_removed(self):
        """Should remove trailing commas before closing braces."""
        text = '{"title": "Test",}'
        result = sanitize_llm_json(text)
        data = json.loads(result)
        assert data["title"] == "Test"


class TestParseStoryJson:
    """Test the high-level parse_story_json wrapper."""

    def test_valid_story_structure(self):
        """Should parse a valid story structure."""
        text = """{
            "title": "Test Story",
            "author": "Test Author",
            "tagline": "A test",
            "scenes": [
                {
                    "content": "Scene 1",
                    "pov": "first",
                    "time": "morning",
                    "location": "home"
                }
            ]
        }"""
        result = parse_story_json(text)
        assert result["title"] == "Test Story"
        assert len(result["scenes"]) == 1
        assert result["scenes"][0]["content"] == "Scene 1"

    def test_with_markdown_fences(self):
        """Should handle JSON wrapped in markdown code fences."""
        text = """```json
        {
            "title": "Test Story",
            "scenes": []
        }
        ```"""
        result = parse_story_json(text)
        assert result["title"] == "Test Story"

    def test_with_prose_before_json(self):
        """Should extract JSON even when preceded by explanatory text."""
        text = """Here's the story structure:
        {
            "title": "Test Story",
            "scenes": []
        }
        """
        result = parse_story_json(text)
        assert result["title"] == "Test Story"

    def test_invalid_json_raises_with_context(self):
        """Should raise ValueError with helpful context for invalid JSON."""
        text = '{"title": "Unclosed string}'
        with pytest.raises(ValueError, match="Failed to parse story JSON"):
            parse_story_json(text)
