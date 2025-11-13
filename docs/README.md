# Documentation

This folder contains all project documentation organized by purpose.

## User Guides

- **[quickstart-guide.md](quickstart-guide.md)** - Getting started guide for new users
- **[project-workflow.md](project-workflow.md)** - How to use the project-based workflow
- **[iterative-generation.md](iterative-generation.md)** - Understanding the iterative story generation process
- **[editorial-workflow.md](editorial-workflow.md)** - Using the editorial workflow features
- **[grok-guide.md](grok-guide.md)** - Using xAI Grok models with the CLI

## Development

- **[TESTING.md](TESTING.md)** - Testing guide and best practices
- **[migrations.md](migrations.md)** - Database/data migration guides

## Architecture & Planning

- **[ARCHITECTURE_REVIEW.md](ARCHITECTURE_REVIEW.md)** - Current architecture analysis and recommendations
- **[WEB_SERVICE_READINESS.md](WEB_SERVICE_READINESS.md)** - Analysis of web service readiness
- **[EDITORIAL_WORKFLOW_SPEC.md](EDITORIAL_WORKFLOW_SPEC.md)** - Detailed specification for editorial workflow system

## Archive

The `archive/` folder contains outdated documentation that may be useful for historical reference:

- **Phase completion reports** - Status of completed refactoring phases
- **Refactoring plans** - Detailed plans for code restructuring (now complete)
- **Old guides** - Outdated user guides with old command syntax

## Contributing

When adding new documentation:

1. **User-facing docs** → Place in root `docs/` folder
2. **Planning/architecture docs** → Place in root `docs/` folder
3. **Outdated docs** → Move to `docs/archive/` with descriptive names
4. **Update this README** when adding new files

## File Organization Principles

- **Current and useful** → `docs/` root
- **Historical reference only** → `docs/archive/`
- **User guides** → Clear, tutorial-style content
- **Technical docs** → Detailed specifications and analysis
