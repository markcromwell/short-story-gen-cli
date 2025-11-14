# Integration Tests

Comprehensive integration tests that run the **COMPLETE story generation pipeline** with real, high-quality pitches and API calls.

## 🎯 Test Strategy

**Cost-Controlled Quality Coverage:**
- 6 carefully curated, high-quality pitches covering diverse genres
- Each test validates the full pipeline (idea → characters → locations → outline → breakdown → prose → EPUB)
- XAI by default for fast, high-quality results
- Ollama fallback for overnight/budget runs

**Project Safety:**
- All test projects are timestamped to avoid conflicts
- Projects created in temporary directories
- Automatic cleanup prevents accumulation

## 📚 Test Pitches

Our curated test suite covers:

1. **Mystery Detective** (7,500 words) - Noir thriller with mind-reading twist
2. **Fantasy Quest** (15,000 words) - Epic fantasy with dying magic
3. **Sci-Fi Dystopia** (25,000 words) - Cyberpunk neural implant rebellion
4. **Romance Transformation** (12,000 words) - Speculative growth/transformation story
5. **Horror Supernatural** (8,000 words) - Haunted house psychological horror
6. **Historical Adventure** (18,000 words) - 1920s Shanghai artifact mystery

## 🚀 Running Tests

### Quick Integration Test (XAI Default)
```bash
# Run all full pipeline tests with xAI (fast, high quality)
pytest tests/integration/test_full_pipeline.py --integration -v
```

### Overnight Runs (Ollama)
```bash
# Windows PowerShell
$env:INTEGRATION_MODEL = "ollama/qwen2.5:14b"
pytest tests/integration/test_full_pipeline.py --integration -m "not slow"

# Linux/Mac
export INTEGRATION_MODEL="ollama/qwen2.5:14b"
pytest tests/integration/test_full_pipeline.py --integration -m "not slow"
```

### Cost-Controlled Testing
```bash
# Run with strict cost limits
pytest tests/integration/test_full_pipeline.py::TestFullPipeline::test_cost_control_and_quality_balance --integration
```

### Long-Form Testing (Expensive)
```bash
# Only run novella-length tests when needed
pytest tests/integration/test_full_pipeline.py::TestFullPipeline::test_long_form_generation --integration
```

## ⚙️ Model Configuration

### Default Models
- **XAI**: `xai/grok-4-fast-reasoning` (fast, high quality, recommended)
- **Ollama**: `ollama/qwen2.5:7b` (free, slower, good quality)

### Environment Variables
```bash
# Override test model
export INTEGRATION_MODEL="ollama/qwen2.5:14b"

# XAI API key (required for XAI tests)
export XAI_API_KEY="your-xai-key-here"

# Ollama model override
export OLLAMA_TEST_MODEL="qwen2.5:14b"
```

## 📊 Test Coverage

**What Each Test Validates:**
- ✅ **Complete Pipeline**: Idea → Characters → Locations → Outline → Breakdown → Prose → EPUB
- ✅ **Genre Recognition**: Proper genre detection and application
- ✅ **Word Count Accuracy**: Stories meet target lengths
- ✅ **Story Type Handling**: Different structures for different lengths
- ✅ **Project Management**: Unique project names, proper file creation
- ✅ **Cost Control**: Budget limits respected
- ✅ **Error Recovery**: Failed runs don't corrupt projects

**Cost Breakdown (per full test):**
- XAI (grok-4-fast-reasoning): ~$1-3 per story
- Ollama (local): $0 per story
- Total test suite: ~$10-20 with XAI, $0 with Ollama

## 🛠️ Prerequisites

### For XAI Tests
1. **xAI API Key**: Get from [xAI platform](https://x.ai)
2. **Environment**: `export XAI_API_KEY="your-key"`

### For Ollama Tests
1. **Install Ollama**: `curl -fsSL https://ollama.ai/install.sh | sh`
2. **Start Service**: `ollama serve`
3. **Pull Model**: `ollama pull qwen2.5:7b`

## 🎛️ Advanced Usage

### Custom Model Selection
```bash
# Command line override
pytest tests/integration/test_full_pipeline.py --integration --model "ollama/llama3.2:3b"

# Environment override (takes precedence)
export INTEGRATION_MODEL="xai/grok-beta"
pytest tests/integration/test_full_pipeline.py --integration
```

### Selective Test Running
```bash
# Run only mystery genre test
pytest tests/integration/test_full_pipeline.py -k "mystery_detective" --integration

# Skip expensive long-form tests
pytest tests/integration/test_full_pipeline.py --integration -m "not slow"

# Run only cost-control test
pytest tests/integration/test_full_pipeline.py::TestFullPipeline::test_cost_control_and_quality_balance --integration
```

### Debugging Failed Tests
```bash
# Verbose output with model info
pytest tests/integration/test_full_pipeline.py --integration -v -s

# Stop on first failure
pytest tests/integration/test_full_pipeline.py --integration -x

# Check project output after test
ls projects/test_mystery_detective_*
```

## 🚨 Troubleshooting

### "Project already exists"
**Solution**: Tests use timestamped names, but if you run tests rapidly, wait a few seconds between runs.

### "API rate limit exceeded"
**Solution**: Use Ollama for unlimited testing, or add delays between XAI tests.

### "Ollama model not found"
**Solution**:
```bash
ollama pull qwen2.5:7b
# Or change model
export OLLAMA_TEST_MODEL="llama3.2:3b"
```

### Tests are too slow
**Solutions**:
- Use XAI instead of Ollama
- Skip slow tests: `-m "not slow"`
- Use smaller models: `llama3.2:3b`
- Run fewer tests: `-k "short_story"`

## 📈 Performance Benchmarks

**XAI Grok (grok-4-fast-reasoning):**
- 7,500-word story: ~2-3 minutes, $1-2
- Quality: Excellent, creative, consistent

**Ollama (qwen2.5:7b):**
- 7,500-word story: ~5-8 minutes, $0
- Quality: Good, less creative than XAI

**Cost Efficiency:**
- XAI: Best for quality-focused testing
- Ollama: Best for unlimited testing/budgets
