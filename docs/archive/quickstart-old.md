# Quick Start Guide

## Installation

```bash
# 1. Clone and setup
git clone https://github.com/markcromwell/short-story-gen-cli.git
cd short-story-gen-cli

# 2. Create virtual environment
python -m venv .venv
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # Mac/Linux

# 3. Install
pip install -r requirements.txt
pip install -e .
```

## Option 1: Free Testing with Ollama (No API Keys)

```bash
# 1. Install Ollama from https://ollama.ai

# 2. Pull a model
ollama pull llama2

# 3. Generate a story!
python -m storygen.cli --provider ollama/llama2 "A robot learns to paint"
```

## Option 2: Use OpenAI/Claude (Requires API Keys)

```bash
# 1. Copy environment template
cp .env.example .env

# 2. Edit .env and add your API keys
# OPENAI_API_KEY=sk-...
# ANTHROPIC_API_KEY=sk-...

# 3. Generate with GPT-3.5 (default)
python -m storygen.cli "A robot learns to paint"

# 4. Or use GPT-4
python -m storygen.cli --provider gpt-4 "A space adventure"

# 5. Or use Claude
python -m storygen.cli --provider claude-3-sonnet "A mystery story"
```

## Running Tests

```bash
# Run all tests
pytest tests/ -v

# All 5 tests should pass!
```

## Example Output

```
$ python -m storygen.cli --provider gpt-3.5-turbo "A robot learns to paint"
🎨 Generating story with gpt-3.5-turbo...

In a world of chrome and circuitry, there lived a robot named CANVAS-7...
[Your generated story appears here]

✅ Story generated successfully!
```

## What's Next?

This is the MVP. Future features:
- EPUB generation
- AI-generated cover art
- Interior illustrations
- Story templates and genres
- Interactive refinement
