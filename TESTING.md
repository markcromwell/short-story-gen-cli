# Testing Guide

This project uses **Test-Driven Development (TDD)** with comprehensive unit and integration tests.

## Running Tests

### Quick Tests (Unit Tests Only)
Fast tests with mocked AI calls - run these during development:

```bash
# Run all unit tests (default)
pytest tests/ -v

# Run only unit tests (skip integration)
pytest tests/ -m "not integration" -v

# Run specific test file
pytest tests/test_story_generator.py -v
pytest tests/test_cli.py -v
```

### Integration Tests (Real Ollama)
Tests that use real Ollama models - slower but verify actual functionality:

```bash
# Run all integration tests
pytest tests/ -m integration -v -s

# Test with qwen3:30b (requires model to be pulled)
pytest tests/test_story_generator.py::TestOllamaIntegration::test_ollama_qwen3_generates_story -m integration -v -s

# Test with llama2 (faster, smaller model)
pytest tests/test_story_generator.py::TestOllamaIntegration::test_ollama_llama2_generates_story -m integration -v -s
```

### Run All Tests
```bash
# Everything (unit + integration)
pytest tests/ -v -s
```

## Test Structure

### Unit Tests
- **Fast** - Mock AI calls, no real API usage
- **Isolated** - Test individual components
- **Always run** - Part of CI/CD pipeline
- Located in: `tests/test_*.py` classes without `@pytest.mark.integration`

### Integration Tests
- **Slow** - Use real Ollama models
- **End-to-end** - Test actual story generation
- **Optional** - Run locally before commits
- Marked with: `@pytest.mark.integration`

## Test Coverage

Current test suite:
- ✅ Story generator with multiple providers
- ✅ CLI argument parsing
- ✅ Provider switching (GPT, Claude, Grok, Ollama)
- ✅ Error handling
- ✅ Help documentation
- ✅ Real Ollama integration (qwen3:30b, llama2)

**Total: 8 tests** (6 unit + 2 integration)

## Prerequisites for Integration Tests

1. **Ollama must be installed and running**:
   ```bash
   ollama --version
   ```

2. **Pull required models**:
   ```bash
   ollama pull qwen3:30b
   ollama pull llama2
   ```

3. **Ollama should be running** (usually auto-starts):
   ```bash
   # Check if running
   curl http://localhost:11434

   # Or manually start
   ollama serve
   ```

## CI/CD

The CI pipeline runs **unit tests only** (fast feedback):
```yaml
# .gitlab-ci.yml
pytest tests/ -m "not integration" -v
```

Integration tests are run manually before releases.

## Adding New Tests

### Unit Test (Mocked)
```python
def test_my_feature(self, mocker):
    mock_completion = mocker.patch('litellm.completion')
    mock_completion.return_value.choices = [
        mocker.Mock(message=mocker.Mock(content="Test output"))
    ]
    # Your test code
```

### Integration Test (Real Ollama)
```python
@pytest.mark.integration
class TestMyIntegration:
    def test_with_real_model(self):
        # Uses real Ollama - no mocking
        generator = StoryGenerator(provider="ollama/llama2")
        story = generator.generate("Test prompt")
        assert len(story) > 0
```

## TDD Workflow

1. **Red** - Write failing test first
2. **Green** - Write minimum code to pass
3. **Refactor** - Clean up while keeping tests green

Example:
```bash
# 1. Write test (it fails)
pytest tests/test_new_feature.py -v  # ❌ FAILS

# 2. Implement feature
# ... edit code ...

# 3. Test passes
pytest tests/test_new_feature.py -v  # ✅ PASSES

# 4. Run all tests
pytest tests/ -v  # ✅ All PASS
```
