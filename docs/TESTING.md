# Testing Guide

This project uses **Test-Driven Development (TDD)** with comprehensive unit and integration tests.

## Running Tests

### Quick Tests (Unit Tests Only)
Fast tests with mocked AI calls - run these during development:

```bash
# Run all unit tests (default - integration tests skipped)
pytest

# Run only unit tests explicitly
pytest tests/unit/ -v

# Run specific test file
pytest tests/unit/test_models.py -v
pytest tests/unit/test_idea_generator.py -v
```

### Integration Tests (Real Ollama)
Tests that make **real API calls** to local Ollama models - requires Ollama running:

```bash
# Run integration tests (requires --integration flag)
pytest tests/integration/ --integration -v

# Run all tests including integration
pytest --integration -v

# Skip slow integration tests
pytest tests/integration/ --integration -m "not slow" -v

# Use specific Ollama model
$env:OLLAMA_TEST_MODEL = "qwen2.5:14b"
pytest tests/integration/ --integration -v
```

**Prerequisites:**
1. Install Ollama: [ollama.ai](https://ollama.ai)
2. Start Ollama: `ollama serve`
3. Pull model: `ollama pull qwen2.5:7b`

See `tests/integration/README.md` for detailed setup instructions.

### Run All Tests
```bash
# Unit tests only (fast, default)
pytest

# Everything (unit + integration)
pytest --integration -v
```

## Test Structure

### Unit Tests (`tests/unit/`)
- **Fast** (~2 seconds) - Mock all AI calls, no real API usage
- **Isolated** - Test individual components with controlled inputs
- **Always run** - Part of CI/CD pipeline (default)
- **Coverage**: 97-100% for tested modules
- Location: `tests/unit/test_*.py`

**Current unit tests:**
- ✅ Data Models (43 tests) - StoryIdea, Character, Location, etc.
- ✅ IdeaGenerator (16 tests) - AI integration, retry logic, parsing
- Total: **59 unit tests**

### Integration Tests (`tests/integration/`)
- **Slow** (~30-60 seconds) - Use real local Ollama models
- **End-to-end** - Test actual AI generation with real responses
- **Optional** - Require `--integration` flag and Ollama running
- **Coverage**: Full story generation pipeline validation
- Location: `tests/integration/test_*_ollama.py`

**Current integration tests:**
- ✅ Real story idea generation (7 tests)
- ✅ Multi-genre detection with real AI
- ✅ Prompt variation handling
- ✅ JSON parsing of real model output
- ✅ Genre normalization with real data
- ✅ Timeout and retry with real failures
- Total: **7 integration tests**

### Legacy Tests (`tests/`)
Tests for the original non-iterative story generator:
- ✅ CLI functionality
- ✅ Story generator (6 tests)
- ✅ EPUB layout
- ✅ Parsing

## CI/CD

The CI pipeline runs **unit tests only** (fast feedback):
```yaml
# .github/workflows/test.yml or .gitlab-ci.yml
pytest  # integration tests skipped by default
```

Integration tests are run manually before releases or when explicitly needed.

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
