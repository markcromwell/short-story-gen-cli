# Short Story Generator CLI 🎨📚

AI-powered command-line tool to generate creative short stories using multiple AI providers.

## Features

- **Multiple AI Providers**: Switch between OpenAI, Anthropic Claude, Ollama (local), and more
- **Structured Story Output**: Generate stories with title, scenes, genre, and metadata (JSON or formatted text)
- **EPUB Generation**: Create professional ebook files from AI-generated stories
- **Test-Driven Development**: Built with TDD principles, comprehensive test coverage
- **Agile MVP**: Minimum viable product following agile methodology
- **Free & Paid Options**: Use free local models or premium cloud APIs
- **Type-Safe Models**: Structured data models for stories and scenes
- **Future**: AI-generated cover art and interior illustrations

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

**Important**: Make sure your virtual environment is activated first!
```bash
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # Mac/Linux
```

### Basic usage (default provider: GPT-3.5):
```bash
storygen "A robot learns to paint"

# Or without activating venv:
python -m storygen.cli "A robot learns to paint"
```

### With specific provider:
```bash
# Grok (fast, cheap, large context - recommended!)
storygen --provider xai/grok-2-1212 "A space adventure"

# Other providers
storygen --provider gpt-4 "A mystery in the library"
storygen --provider claude-3-sonnet "A detective story"
storygen --provider ollama/llama2 "A time travel tale"
```

### Structured output (with title, scenes, metadata):
```bash
# Generate structured story with formatted text output
storygen --structured "A mystery in an old mansion"

# Generate structured story as JSON
storygen --structured --format json "A space adventure" > story.json

# Structured stories include:
# - Title and genre
# - Multiple scenes with titles
# - Scene settings and characters
# - Story summary
# - Automatic word count
```

### Story Structure Options:
Choose from classic narrative structures to guide the AI:

```bash
# Three-Act Structure (default): Setup → Confrontation → Resolution
storygen --epub story.epub --structure three_act "A heist gone wrong"

# Freytag's Pyramid: Exposition → Rising Action → Climax → Falling Action → Denouement
storygen --structure freytag "A tragic romance"

# Hero's Journey: Ordinary World → Call to Adventure → Trials → Return
storygen --structure heros_journey "A reluctant hero's quest"

# Fichtean Curve: Immediate crisis → Rising crises → Climax (great for thrillers!)
storygen --structure fichtean "A detective races against time"

# Seven-Point Structure: Hook → Plot Turns → Pinches → Midpoint → Resolution
storygen --structure seven_point "A mystery with a twist"

# Let AI Choose: AI picks the best structure for your story
storygen --structure ai_choice "A mysterious disappearance"
```

### Point of View (POV) Options:
```bash
# First person (I/we)
storygen --pov first_person "My journey through the wasteland"

# Third person deep POV (intimate access to character thoughts - default)
storygen --pov third_person_deep "Her secret would change everything"

# Multiple POV (switching perspectives)
storygen --pov multiple_pov "A thriller from three perspectives"

# Stream of consciousness
storygen --pov stream_of_consciousness "A mind unraveling"

# 11 POV options available! Use --help for full list
```

### Control Story Length:
```bash
# Request minimum word count
storygen --min-words 2000 "A detailed fantasy epic"
storygen --min-words 5000 --epub novel.epub "A long-form mystery"
```

### Debug Mode:
```bash
# Show detailed information about what's sent to the AI
storygen --verbose "A mystery story"

# Verbose mode shows:
# - Full system prompt with structure instructions
# - User prompt with word count requirements
# - Model and token settings
# - Raw AI response (first/last 500 chars for long responses)
# - Token usage statistics

# Perfect for debugging or understanding how structures work
storygen --verbose --structure fichtean --min-words 1000 "A bank heist"
```

### EPUB generation:
```bash
# Generate an EPUB ebook file (auto-saved to output/ folder)
storygen --epub my_story.epub "A magical adventure"

# With custom author name
storygen --epub story.epub --author "John Doe" "A cyberpunk detective story"

# Combine all options
storygen --epub heist.epub --author "Mark Cromwell" \
  --structure fichtean --pov third_person_deep \
  --min-words 3000 "A bank heist with unexpected twists"

# Using local Ollama (free!)
storygen --provider ollama/llama2 --epub adventure.epub "A space odyssey"
```

### Get help:
```bash
storygen --help
```

## Supported AI Providers

### Free/Local Options:
- **Ollama (local)**: `ollama/llama2`, `ollama/mistral`
  - Install Ollama from https://ollama.ai
  - Run `ollama pull llama2` to download models
  - No API key needed!

### Premium Options:

**Recommended: xAI Grok** ⚡
- **xAI Grok**: `xai/grok-2-1212`, `xai/grok-beta`
  - **Fast** - Low latency responses
  - **Cheap** - Cost-effective pricing
  - **Large Context** - 128K+ token context window
  - Get API key from: https://console.x.ai

**Other Premium Providers:**
- **OpenAI**: `gpt-4`, `gpt-3.5-turbo`, `gpt-4-turbo`
- **Anthropic**: `claude-3-opus`, `claude-3-sonnet`, `claude-3-haiku`

## Development

### Setup development environment:
```bash
pip install -r requirements.txt
pip install -e .
pre-commit install  # Install git hooks for code quality
```

### Run tests:
```bash
pytest tests/ -v
```

### Run tests with coverage:
```bash
pytest tests/ --cov=storygen --cov-report=term-missing --cov-report=html
# Open htmlcov/index.html to see detailed coverage report
```

### Run only unit tests (skip integration tests):
```bash
pytest tests/ -v -m "not integration"
```

### Code quality checks:
```bash
# Type checking
mypy src/storygen

# Linting and formatting (auto-fix)
ruff check --fix src/ tests/
ruff format src/ tests/

# Run all pre-commit hooks manually
pre-commit run --all-files
```

### Pre-commit Hooks
Pre-commit hooks automatically run on every commit:
- **Ruff**: Fast linting and auto-formatting
- **Mypy**: Type checking
- **Pytest**: Unit tests (integration tests skipped for speed)
- **Standard checks**: Trailing whitespace, file endings, YAML validation, etc.

To skip hooks temporarily:
```bash
git commit --no-verify
```

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

- **Python 3.9+** (tested on 3.14)
- **LiteLLM**: Multi-provider AI abstraction
- **Click**: CLI framework
- **Pytest**: Testing framework

## License

MIT - See [LICENSE](LICENSE) file for details

## Author

Mark Cromwell (markcromwell@gmail.com)
