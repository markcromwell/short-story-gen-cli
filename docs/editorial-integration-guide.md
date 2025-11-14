# Editorial Workflow Integration Guide

## Overview

This guide explains how the editorial workflow system integrates with the existing short-story-gen-cli codebase, data formats, and user workflows.

## Existing Architecture Integration

### Data Format Compatibility

The editorial system uses existing data models and JSON schemas:

```python
# Uses existing classes from src/story.py, src/characters.py, etc.
from src.story import StoryIdea, Prose, SceneSequel
from src.characters import Character
from src.locations import Location
from src.structure import Outline

# Editorial system extends these with analysis results
@dataclass
class StoryContext:
    story_idea: StoryIdea
    characters: List[Character]
    locations: List[Location]
    outline: Optional[Outline] = None
    prose: Optional[Prose] = None
    previous_feedback: List[EditorialFeedback] = None
```

### CLI Integration

Extends existing `storygen-iter` command structure:

```bash
# Existing commands (unchanged)
storygen-iter generate idea
storygen-iter generate characters
storygen-iter generate locations
storygen-iter generate outline
storygen-iter generate prose

# New editorial commands
storygen-iter edit idea --idea idea.json -o feedback.json
storygen-iter edit content --prose prose.json -o structural_feedback.json
storygen-iter edit analyze --prose prose.json --focus comprehensive -o analysis.json
storygen-iter edit revise --prose prose.json --feedback analysis.json -o revised.json
```

### Configuration Integration

Extends existing configuration system:

```yaml
# Add to existing config/editorial_config.yaml
editors:
  idea:
    enabled: true
    default_model: "ollama/qwen3:30b"
    max_retries: 3
    timeout_seconds: 300
    cost_limits:
      max_per_analysis: 1.00
      daily_budget: 10.00

# Existing config remains unchanged
generation:
  models:
    default: "ollama/qwen3:30b"
  costs:
    max_per_story: 5.00
```

## Workflow Integration

### Story Generation → Editorial Feedback Loop

```
1. Generate Story Idea
   ↓
2. [NEW] Run Idea Editor → Get concept feedback
   ↓
3. Generate Characters & Locations
   ↓
4. Generate Outline
   ↓
5. [NEW] Run Outline Editor → Get structure feedback
   ↓
6. Generate Prose
   ↓
7. [NEW] Run Content Editors → Get detailed feedback
   ↓
8. Revise based on feedback → Regenerate sections
   ↓
9. [NEW] Run Line/Copy/Proof editors → Final polish
   ↓
10. Export to EPUB
```

### Iterative Improvement Workflow

```bash
# Generate initial story
storygen-iter generate idea -o idea.json
storygen-iter generate characters --idea idea.json -o chars.json
storygen-iter generate outline --idea idea.json --chars chars.json -o outline.json
storygen-iter generate prose --outline outline.json -o prose.json

# Run editorial analysis
storygen-iter edit idea --idea idea.json -o idea_feedback.json
storygen-iter edit content --prose prose.json -o content_feedback.json

# Review feedback and revise
# (manual step: user reviews feedback.json files)

# Regenerate improved sections
storygen-iter generate prose --outline outline.json --feedback content_feedback.json -o improved_prose.json

# Continue with line editing
storygen-iter edit line --prose improved_prose.json -o line_feedback.json
```

## File Structure Integration

### New Files Added

```
src/editorial/
├── __init__.py
├── base.py              # BaseEditor, EditorialFeedback, etc.
├── editors/
│   ├── __init__.py
│   ├── idea.py          # IdeaEditor
│   ├── outline.py       # OutlineEditor
│   ├── structural.py    # StructuralEditor
│   ├── continuity.py    # ContinuityEditor
│   ├── style.py         # StyleEditor
│   ├── line.py          # LineEditor
│   ├── copy.py          # Copyeditor
│   └── proof.py         # Proofreader
├── core/
│   ├── __init__.py
│   ├── model_manager.py # ModelManager
│   ├── cost_tracker.py  # CostTracker
│   └── context.py       # ContextManager
├── cli/
│   ├── __init__.py
│   └── commands.py      # CLI commands
└── utils/
    ├── __init__.py
    ├── validation.py    # Input validation
    └── errors.py        # Error handling

config/
└── editorial_config.yaml  # Editorial-specific config

tests/
└── editorial/           # Editorial test suite
    ├── __init__.py
    ├── test_editors.py
    └── test_integration.py

docs/
├── editorial-workflow.md
├── editorial-implementation.md
└── editorial-mvp-roadmap.md
```

### Modified Files

```
# Existing files that need minor changes
pyproject.toml           # Add editorial dependencies
src/cli/main.py          # Add editorial command group
src/config/__init__.py   # Load editorial config
```

## Dependency Integration

### New Dependencies (add to pyproject.toml)

```toml
[tool.poetry.dependencies]
# Existing dependencies...
aiohttp = "^3.9.0"          # For Ollama API calls
pydantic = "^2.5.0"         # Data validation
structlog = "^23.2.0"       # Structured logging
prometheus-client = "^0.19.0"  # Metrics
pyyaml = "^6.0.1"           # Configuration
click = "^8.1.7"            # CLI (if not already present)

[tool.poetry.group.dev.dependencies]
pytest-asyncio = "^0.21.0"  # Async testing
respx = "^0.20.0"           # HTTP mocking
freezegun = "^1.2.0"        # Time mocking
```

### Model Dependencies

- **Local**: Ollama with qwen3:30b model
- **Cloud**: OpenAI API (optional fallback)
- **Hardware**: 16GB+ RAM recommended for local models

## Data Migration

### Existing Project Compatibility

For existing projects, create adapters to convert current JSON formats:

```python
class DataAdapter:
    """Convert existing project data to editorial formats"""

    @staticmethod
    def project_to_story_context(project_dir: Path) -> StoryContext:
        """Load existing project files into StoryContext"""
        # Load existing JSON files
        idea_data = json.loads((project_dir / "idea.json").read_text())
        chars_data = json.loads((project_dir / "characters.json").read_text())
        locs_data = json.loads((project_dir / "locations.json").read_text())

        # Convert to editorial format
        story_idea = StoryIdea(**idea_data)
        characters = [Character(**c) for c in chars_data]
        locations = [Location(**l) for l in locs_data]

        return StoryContext(
            story_idea=story_idea,
            characters=characters,
            locations=locations
        )
```

### Backward Compatibility

- Existing `storygen-iter generate` commands unchanged
- Editorial features are opt-in
- No breaking changes to existing workflows
- Can run editorial analysis on existing projects

## Error Handling Integration

### Existing Error Patterns

Follow existing error handling patterns:

```python
# Use existing logging
import logging
logger = logging.getLogger(__name__)

# Use existing exception types where possible
from src.exceptions import StoryGenError

class EditorialError(StoryGenError):
    """Base editorial error"""
    pass
```

### Graceful Degradation

- If editorial features fail, generation continues normally
- Model failures fall back to basic suggestions
- Network issues retry with backoff
- Invalid input shows helpful error messages

## Testing Integration

### Test Structure

```python
# tests/editorial/conftest.py
@pytest.fixture
def mock_model_manager():
    """Mock model manager for testing"""
    manager = MagicMock()
    manager.call_model = AsyncMock()
    return manager

# tests/editorial/test_editors.py
class TestIdeaEditor:
    @pytest.mark.asyncio
    async def test_successful_analysis(self, mock_model_manager):
        # Test editorial analysis
        pass
```

### Integration Testing

```python
# tests/test_editorial_integration.py
def test_full_editorial_workflow(cli_runner, tmp_path):
    """Test complete editorial workflow"""
    # Create test data
    # Run editorial commands
    # Verify outputs
    pass
```

## Performance Integration

### Resource Usage

- **Memory**: 2-4GB RAM for typical analysis
- **Disk**: ~100MB for job storage and checkpoints
- **Network**: API calls to local Ollama (no external dependencies required)
- **CPU**: Moderate usage, can run in background

### Scaling Considerations

- Job queue limits concurrent analyses
- Batch processing manages memory usage
- Checkpointing prevents work loss on interruption
- Caching reduces redundant API calls

## Deployment Integration

### Local Development

```bash
# Install editorial dependencies
pip install -e ".[editorial]"

# Start Ollama (if not running)
ollama serve

# Run editorial commands
storygen-iter edit idea --idea idea.json -o feedback.json
```

### Production Deployment

- Docker container with editorial code
- Ollama service (separate container or external)
- Job storage on persistent volumes
- Monitoring integrated with existing metrics

## Migration Path

### Phase 1: Infrastructure (Week 1-3)
- Add editorial package structure
- Implement core classes
- Basic CLI integration
- Unit tests

### Phase 2: Feature Integration (Week 4-6)
- Add editorial commands to main CLI
- Implement data adapters
- Add configuration loading
- Integration tests

### Phase 3: User Workflow (Week 7-9)
- Update user documentation
- Add examples and tutorials
- Performance optimization
- User acceptance testing

This integration maintains backward compatibility while adding powerful new editorial capabilities to the existing story generation workflow.</content>
<parameter name="filePath">c:\Users\markc\Projects\short-story-gen-cli\docs\editorial-integration-guide.md
