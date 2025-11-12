"""Unit tests for CLI module structure and utilities."""

from click.testing import CliRunner

from storygen.iterative.cli.commands import utils
from storygen.iterative.cli.main import cli


class TestCLIStructure:
    """Test CLI package structure and organization."""

    def test_cli_group_exists(self):
        """Test that main CLI group is properly defined."""
        assert cli is not None
        assert cli.name == "cli"  # CLI group is named "cli"
        assert hasattr(cli, "commands")

    def test_all_commands_registered(self):
        """Test that all expected commands are registered."""
        expected_commands = {
            "new",
            "status",
            "projects",
            "idea",
            "characters",
            "locations",
            "outline",
            "breakdown",
            "prose",
            "epub",
        }
        actual_commands = set(cli.commands.keys())
        assert (
            expected_commands == actual_commands
        ), f"Missing commands: {expected_commands - actual_commands}"

    def test_verbose_flag_exists(self):
        """Test that verbose flag is available on main CLI."""
        runner = CliRunner()
        result = runner.invoke(cli, ["--help"])
        assert result.exit_code == 0
        assert "--verbose" in result.output or "-v" in result.output


class TestCLIUtils:
    """Test CLI utility functions."""

    def test_get_default_word_count_short_story(self):
        """Test default word count for short story."""
        count = utils.get_default_word_count("short-story")
        assert count == 5000

    def test_get_default_word_count_novelette(self):
        """Test default word count for novelette."""
        count = utils.get_default_word_count("novelette")
        assert count == 12000

    def test_get_default_word_count_novella(self):
        """Test default word count for novella."""
        count = utils.get_default_word_count("novella")
        assert count == 30000

    def test_get_default_word_count_novel(self):
        """Test default word count for novel."""
        count = utils.get_default_word_count("novel")
        assert count == 80000

    def test_get_default_word_count_invalid(self):
        """Test default word count for invalid type."""
        count = utils.get_default_word_count("invalid")
        assert count == 5000  # Falls back to short story

    def test_format_word_count_small(self):
        """Test formatting word count less than 1000."""
        assert utils.format_word_count(500) == "500"
        assert utils.format_word_count(999) == "999"

    def test_format_word_count_thousands(self):
        """Test formatting word count in thousands."""
        assert utils.format_word_count(1000) == "1,000"
        assert utils.format_word_count(5000) == "5,000"
        assert utils.format_word_count(12345) == "12,345"

    def test_format_word_count_large(self):
        """Test formatting large word counts."""
        assert utils.format_word_count(100000) == "100,000"
        assert utils.format_word_count(1234567) == "1,234,567"

    def test_format_list_no_truncation(self):
        """Test format_list when list is smaller than max."""
        items = ["apple", "banana", "cherry"]
        result = utils.format_list(items, max_items=5)
        assert result == "apple, banana, cherry"

    def test_format_list_truncation(self):
        """Test format_list when list exceeds max."""
        items = ["one", "two", "three", "four", "five", "six"]
        result = utils.format_list(items, max_items=3)
        assert result == "one, two, three, +3 more"

    def test_format_list_empty(self):
        """Test format_list with empty list."""
        result = utils.format_list([], max_items=3)
        assert result == ""

    def test_format_list_single_item(self):
        """Test format_list with single item."""
        result = utils.format_list(["only"], max_items=3)
        assert result == "only"


class TestProjectCommands:
    """Test project management commands."""

    def test_new_command_exists(self):
        """Test that new command is registered."""
        assert "new" in cli.commands

    def test_status_command_exists(self):
        """Test that status command is registered."""
        assert "status" in cli.commands

    def test_projects_command_exists(self):
        """Test that projects command is registered."""
        assert "projects" in cli.commands

    def test_new_command_has_options(self):
        """Test that new command has required options."""
        runner = CliRunner()
        result = runner.invoke(cli, ["new", "--help"])
        assert result.exit_code == 0
        assert "name" in result.output.lower()  # NAME argument is shown
        assert "--pitch" in result.output.lower() or "-p" in result.output.lower()

    def test_status_command_has_project_arg(self):
        """Test that status command accepts project argument."""
        runner = CliRunner()
        result = runner.invoke(cli, ["status", "--help"])
        assert result.exit_code == 0
        assert "PROJECT" in result.output or "project" in result.output.lower()


class TestGenerateCommands:
    """Test generation commands."""

    def test_idea_command_exists(self):
        """Test that idea command is registered."""
        assert "idea" in cli.commands

    def test_characters_command_exists(self):
        """Test that characters command is registered."""
        assert "characters" in cli.commands

    def test_locations_command_exists(self):
        """Test that locations command is registered."""
        assert "locations" in cli.commands

    def test_outline_command_exists(self):
        """Test that outline command is registered."""
        assert "outline" in cli.commands

    def test_idea_command_has_prompt(self):
        """Test that idea command accepts prompt argument."""
        runner = CliRunner()
        result = runner.invoke(cli, ["idea", "--help"])
        assert result.exit_code == 0
        assert "PROMPT" in result.output or "prompt" in result.output.lower()


class TestProseCommands:
    """Test prose generation commands."""

    def test_breakdown_command_exists(self):
        """Test that breakdown command is registered."""
        assert "breakdown" in cli.commands

    def test_prose_command_exists(self):
        """Test that prose command is registered."""
        assert "prose" in cli.commands


class TestExportCommands:
    """Test export commands."""

    def test_epub_command_exists(self):
        """Test that epub command is registered."""
        assert "epub" in cli.commands

    def test_epub_command_has_options(self):
        """Test that epub command has expected options."""
        runner = CliRunner()
        result = runner.invoke(cli, ["epub", "--help"])
        assert result.exit_code == 0
        # Should have project argument
        assert "PROJECT" in result.output or "project" in result.output.lower()
