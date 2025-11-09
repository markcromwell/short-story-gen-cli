# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- **Structured story output** with title, scenes, genre, and metadata
  - `Story` and `Scene` data models with JSON serialization
  - `--structured` flag for CLI to generate structured stories
  - `--format` option to output as JSON or formatted text
  - Scene-level details: title, setting, characters, content
  - Automatic word count calculation
- Type checking with mypy
- Pre-commit hooks for code quality
- Ruff for fast linting and formatting
- Auto-run unit tests before commit
- Test coverage reporting with 9 new model tests
- GitHub Actions CI workflow (test on Linux/Windows/macOS, Python 3.9-3.14)

## [0.1.0] - 2025-11-09

### Added
- Initial MVP release
- CLI story generator with multiple AI provider support
- Support for OpenAI GPT models (gpt-4, gpt-3.5-turbo, etc.)
- Support for Anthropic Claude models (claude-3-opus, claude-3-sonnet, etc.)
- Support for xAI Grok models (grok-2-1212, grok-beta) - fast, cheap, large context
- Support for local Ollama models (llama2, qwen3, mistral, etc.)
- Reasoning model support (qwen3:30b) with higher token limits
- Test-driven development with 8 passing tests (6 unit, 2 integration)
- Environment variable management with .env support
- Comprehensive documentation (README, QUICKSTART, TESTING, GROK_GUIDE)
- MIT License
- Modern Python packaging with pyproject.toml

### Technical Details
- Python 3.9+ support (tested on 3.14.0)
- LiteLLM for unified multi-provider AI API
- Click framework for CLI interface
- pytest with pytest-mock for testing
- Type hints and error handling throughout

### Documentation
- README.md with installation and usage instructions
- QUICKSTART.md for rapid setup
- TESTING.md for test documentation
- GROK_GUIDE.md for xAI Grok-specific instructions

[0.1.0]: https://github.com/markcromwell/short-story-gen-cli/releases/tag/v0.1.0
