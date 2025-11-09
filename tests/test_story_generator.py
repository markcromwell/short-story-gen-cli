"""
Test story generation functionality (TDD)
"""
import pytest


class TestStoryGenerator:
    """Test the story generator with different providers"""
    
    def test_generator_creates_story_from_prompt(self, mocker):
        """
        MVP Test: Generator should take a prompt and return a story string
        
        This is our first red test - it will fail until we implement the generator
        """
        from storygen.generator import StoryGenerator
        
        # Mock the LiteLLM call to avoid real API calls in tests
        mock_completion = mocker.patch('litellm.completion')
        mock_completion.return_value.choices = [
            mocker.Mock(message=mocker.Mock(content="Once upon a time, a robot discovered colors..."))
        ]
        
        # Create generator with a provider
        generator = StoryGenerator(provider="gpt-3.5-turbo")
        
        # Generate story from prompt
        story = generator.generate("A robot learns to paint")
        
        # Assert we got a story back
        assert isinstance(story, str)
        assert len(story) > 0
        assert "robot" in story.lower()
    
    def test_generator_accepts_different_providers(self, mocker):
        """Test that we can switch between different AI providers"""
        from storygen.generator import StoryGenerator
        
        mock_completion = mocker.patch('litellm.completion')
        mock_completion.return_value.choices = [
            mocker.Mock(message=mocker.Mock(content="A test story"))
        ]
        
        # Test with different providers including Grok
        providers = ["gpt-4", "claude-3-sonnet", "ollama/llama2", "xai/grok-2-1212"]
        
        for provider in providers:
            generator = StoryGenerator(provider=provider)
            story = generator.generate("Test prompt")
            assert isinstance(story, str)
            
            # Verify LiteLLM was called with correct provider
            call_args = mock_completion.call_args
            assert call_args.kwargs['model'] == provider
    
    def test_generator_supports_grok_models(self, mocker):
        """Test that Grok models are supported for fast, cheap generation"""
        from storygen.generator import StoryGenerator
        
        mock_completion = mocker.patch('litellm.completion')
        mock_completion.return_value.choices = [
            mocker.Mock(message=mocker.Mock(content="A Grok-generated story with large context!"))
        ]
        
        # Test Grok models
        grok_models = ["xai/grok-2-1212", "xai/grok-beta"]
        
        for model in grok_models:
            generator = StoryGenerator(provider=model)
            story = generator.generate("Write a story", max_tokens=2000)
            
            assert isinstance(story, str)
            assert len(story) > 0
            
            # Verify correct model was used
            call_args = mock_completion.call_args
            assert call_args.kwargs['model'] == model


@pytest.mark.integration
class TestOllamaIntegration:
    """Integration tests with real Ollama models (run with: pytest -m integration)"""
    
    def test_ollama_qwen3_generates_story(self):
        """
        Integration test: Generate a real story with Ollama qwen3:30b
        
        This test requires:
        - Ollama installed and running
        - qwen3:30b model pulled (ollama pull qwen3:30b)
        
        Run with: pytest tests/test_story_generator.py -m integration -v
        Skip by default to keep fast unit tests
        """
        from storygen.generator import StoryGenerator
        
        generator = StoryGenerator(provider="ollama/qwen3:30b")
        story = generator.generate(
            prompt="Write a very short story about a cat who learns to code",
            max_tokens=200
        )
        
        # Verify we got a real story back
        assert isinstance(story, str)
        assert len(story) > 50, "Story should be at least 50 characters"
        print(f"\n\nGenerated story:\n{story}\n")
    
    def test_ollama_llama2_generates_story(self):
        """Integration test with llama2 (smaller, faster model)"""
        from storygen.generator import StoryGenerator
        
        generator = StoryGenerator(provider="ollama/llama2")
        story = generator.generate(
            prompt="Write a two-sentence story about a robot",
            max_tokens=100
        )
        
        assert isinstance(story, str)
        assert len(story) > 20
        print(f"\n\nLlama2 story:\n{story}\n")
