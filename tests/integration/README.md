# Integration Tests

Integration tests that make **real API calls** to locally-running Ollama models.

## Prerequisites

1. **Install Ollama**: Download from [ollama.ai](https://ollama.ai)
2. **Start Ollama**: Run `ollama serve` in a terminal
3. **Pull a model**: Run `ollama pull qwen2.5:7b` (or another small model)

## Running Integration Tests

By default, integration tests are **skipped** during normal test runs to keep tests fast.

### Run only integration tests:
```bash
pytest tests/integration/ --integration
```

### Run all tests including integration:
```bash
pytest --integration
```

### Run with verbose output:
```bash
pytest tests/integration/ --integration -v
```

### Skip slow tests:
```bash
pytest tests/integration/ --integration -m "not slow"
```

## Supported Models

Default model: `qwen2.5:7b`

Override with environment variable:
```bash
# Windows PowerShell
$env:OLLAMA_TEST_MODEL = "qwen2.5:14b"
pytest tests/integration/ --integration

# Linux/Mac
export OLLAMA_TEST_MODEL="qwen2.5:14b"
pytest tests/integration/ --integration
```

Good alternatives:
- `qwen2.5:7b` - Fast, good quality (default)
- `qwen2.5:14b` - Slower, better quality
- `llama3.2:3b` - Very fast, decent quality
- `mistral:7b` - Good general purpose

## What's Tested

- ✅ Real story idea generation with Ollama
- ✅ Multi-genre detection
- ✅ Prompt variation handling
- ✅ JSON parsing of real model output
- ✅ Genre normalization
- ✅ Timeout handling
- ✅ Consistency across multiple runs

## Troubleshooting

### "Ollama is not running"
Start Ollama in a separate terminal:
```bash
ollama serve
```

### "Model not found"
Pull the test model:
```bash
ollama pull qwen2.5:7b
```

### "Connection refused"
Check if Ollama is running and listening on default port (11434):
```bash
ollama list
```

### Tests are slow
Use a smaller/faster model:
```bash
$env:OLLAMA_TEST_MODEL = "llama3.2:3b"
```

Or skip slow tests:
```bash
pytest tests/integration/ --integration -m "not slow"
```
