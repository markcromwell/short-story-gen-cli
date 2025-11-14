"""Unit tests for outline_templates module."""

import pytest

from storygen.iterative.exceptions import ConfigError
from storygen.iterative.models import Act
from storygen.iterative.outline_templates import (
    STRUCTURE_TEMPLATES,
    get_template,
    list_available_structures,
)


class TestOutlineTemplates:
    """Test outline template functionality."""

    def test_list_available_structures(self):
        """Test that all expected structures are available."""
        structures = list_available_structures()
        expected_structures = {
            "three-act",
            "hero-journey",
            "fichtean",
            "save-the-cat",
            "seven-point",
            "short-story",
            "freytag",
            "five-point",
            "epiphany",
            "snowflake",
        }

        assert len(structures) == 10
        assert set(structures) == expected_structures

    def test_get_template_all_structures(self):
        """Test that all templates can be retrieved and are valid."""
        for structure_type in list_available_structures():
            template = get_template(structure_type)

            # Should return a list of Act objects
            assert isinstance(template, list)
            assert len(template) > 0

            # Each item should be an Act
            for act in template:
                assert isinstance(act, Act)
                assert act.title
                assert act.description
                assert isinstance(act.percentage, (int, float))
                assert 0 < act.percentage <= 1

                # Check sub-acts recursively
                self._validate_act_structure(act)

    def _validate_act_structure(self, act: Act):
        """Recursively validate act structure."""
        assert isinstance(act, Act)
        assert act.title
        assert act.description
        assert isinstance(act.percentage, (int, float))
        assert 0 <= act.percentage <= 1
        assert isinstance(act.order, int)
        assert act.order >= 0

        # story_application should be empty string (filled by AI)
        assert act.story_application == ""

        # sub_acts should be a list
        assert isinstance(act.sub_acts, list)
        for sub_act in act.sub_acts:
            self._validate_act_structure(sub_act)

    def test_get_template_invalid_structure(self):
        """Test that invalid structure types raise ConfigError."""
        with pytest.raises(ConfigError, match="Unknown structure type"):
            get_template("invalid-structure")

    def test_template_percentages_sum_correctly(self):
        """Test that template percentages sum to 1.0 (100%)."""
        for structure_type in list_available_structures():
            template = get_template(structure_type)

            def get_total_percentage(act: Act) -> float:
                """Recursively calculate total percentage for an act."""
                if not act.sub_acts:
                    return act.percentage
                else:
                    return act.percentage

            total_percentage = sum(get_total_percentage(act) for act in template)

            # Allow small floating point errors
            assert abs(total_percentage - 1.0) < 0.001, (
                f"Structure {structure_type} percentages sum to {total_percentage}, "
                f"expected 1.0. Acts: {[act.title for act in template]}"
            )

    def test_template_structure_details(self):
        """Test specific structure details for key templates."""
        # Test three-act has 3 main acts
        three_act = get_template("three-act")
        assert len(three_act) == 3
        assert "Setup" in three_act[0].title
        assert "Confrontation" in three_act[1].title
        assert "Resolution" in three_act[2].title

        # Test hero-journey has expected acts
        hero_journey = get_template("hero-journey")
        assert len(hero_journey) == 3
        assert "Departure" in hero_journey[0].title
        assert "Initiation" in hero_journey[1].title
        assert "Return" in hero_journey[2].title

        # Test short-story has 5 acts
        short_story = get_template("short-story")
        assert len(short_story) == 5
        expected_titles = ["Setup", "Inciting Incident", "Rising Action", "Climax", "Resolution"]
        actual_titles = [act.title for act in short_story]
        assert actual_titles == expected_titles

        # Test save-the-cat has 15 beats
        save_the_cat = get_template("save-the-cat")
        assert len(save_the_cat) == 15
        assert save_the_cat[0].title == "Opening Image"
        assert save_the_cat[-1].title == "Final Image"

    def test_templates_are_deep_copies(self):
        """Test that get_template returns deep copies, not references."""
        template1 = get_template("three-act")
        template2 = get_template("three-act")

        # Should be different objects
        assert template1 is not template2
        assert template1[0] is not template2[0]

        # Modifying one shouldn't affect the other
        original_title = template1[0].title
        template1[0].title = "Modified Title"

        assert template2[0].title == original_title

    def test_structure_templates_dict_matches_list(self):
        """Test that STRUCTURE_TEMPLATES keys match list_available_structures."""
        dict_keys = set(STRUCTURE_TEMPLATES.keys())
        list_structures = set(list_available_structures())

        assert dict_keys == list_structures
