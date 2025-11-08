"""
Test CLI functionality (TDD)
"""
import pytest
from click.testing import CliRunner


class TestCLI:
    """Test the command-line interface"""
    
    def test_cli_generates_story_with_prompt(self, mocker):
        """
        Test: CLI should accept a prompt and generate a story
        Command: storygen "A robot learns to paint"
        """
        from storygen.cli import main
        
        # Mock the generator to avoid real API calls
        mock_generator = mocker.patch('storygen.cli.StoryGenerator')
        mock_instance = mock_generator.return_value
        mock_instance.generate.return_value = "Once upon a time, a robot discovered colors..."
        
        runner = CliRunner()
        result = runner.invoke(main, ['A robot learns to paint'])
        
        # Assert CLI ran successfully
        assert result.exit_code == 0
        assert "robot" in result.output.lower()
        
    def test_cli_accepts_provider_flag(self, mocker):
        """
        Test: CLI should accept --provider flag to switch AI models
        Command: storygen --provider claude-3-sonnet "Test prompt"
        """
        from storygen.cli import main
        
        mock_generator = mocker.patch('storygen.cli.StoryGenerator')
        mock_instance = mock_generator.return_value
        mock_instance.generate.return_value = "A test story"
        
        runner = CliRunner()
        result = runner.invoke(main, ['--provider', 'claude-3-sonnet', 'Test prompt'])
        
        assert result.exit_code == 0
        # Verify the generator was initialized with the correct provider
        mock_generator.assert_called_once_with(provider='claude-3-sonnet')
        
    def test_cli_shows_help(self):
        """Test: CLI should show help with --help flag"""
        from storygen.cli import main
        
        runner = CliRunner()
        result = runner.invoke(main, ['--help'])
        
        assert result.exit_code == 0
        assert "story" in result.output.lower()
        assert "prompt" in result.output.lower()
