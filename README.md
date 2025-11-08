# Short Story Generator CLI 🎨📚

AI-powered command-line tool to generate creative short stories using multiple AI providers.

## Features

- **Multiple AI Providers**: Switch between OpenAI, Anthropic Claude, Ollama (local), and more
- **Test-Driven Development**: Built with TDD principles, 100% test coverage
- **Agile MVP**: Minimum viable product following agile methodology
- **Free & Paid Options**: Use free local models or premium cloud APIs
- **Future**: EPUB generation with cover and interior art

## Installation

```bash
# Clone the repository
git clone https://github.com/markcromwell/short-story-gen-cli.git
cd short-story-gen-cli

# Create virtual environment
python -m venv .venv
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # Mac/Linux

# Install dependencies
pip install -r requirements.txt
pip install -e .
```

## Setup

1. Copy the environment template:
```bash
cp .env.example .env
```

2. Add your API keys to `.env`:
```bash
OPENAI_API_KEY=your_key_here
ANTHROPIC_API_KEY=your_key_here
```

## Usage

### Basic usage (default provider: GPT-3.5):
```bash
storygen "A robot learns to paint"
```

### With specific provider:
```bash
storygen --provider gpt-4 "A space adventure"
storygen --provider claude-3-sonnet "A mystery in the library"
storygen --provider ollama/llama2 "A time travel story"
```

### Get help:
```bash
storygen --help
```

## Supported AI Providers

### Free Options (for testing):
- **Ollama (local)**: `ollama/llama2`, `ollama/mistral`
  - Install Ollama from https://ollama.ai
  - Run `ollama pull llama2` to download models
  - No API key needed!

### Premium Options:
- **OpenAI**: `gpt-4`, `gpt-3.5-turbo`, `gpt-4-turbo`
- **Anthropic**: `claude-3-opus`, `claude-3-sonnet`, `claude-3-haiku`

## Development

### Run tests:
```bash
pytest tests/ -v
```

### Run tests with coverage:
```bash
pytest tests/ --cov=storygen --cov-report=term-missing
```

## CI/CD

GitLab CI automatically runs tests on every push to `main` branch.

## Roadmap

- [x] MVP: CLI story generator with multiple providers
- [x] Automated testing
- [x] CI/CD pipeline
- [ ] EPUB generation
- [ ] AI-generated cover art
- [ ] AI-generated interior illustrations
- [ ] Story templates and genres
- [ ] Interactive story refinement

## Tech Stack

- **Python 3.12+**
- **LiteLLM**: Multi-provider AI abstraction
- **Click**: CLI framework
- **Pytest**: Testing framework
- **GitLab CI**: Continuous integration

## License

MIT

## Author

Mark Cromwell (markcromwell@gmail.com)
