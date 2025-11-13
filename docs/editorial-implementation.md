# Editorial Workflow Implementation Design

## Overview

This document outlines the technical implementation of the AI-powered editorial workflow system for the short-story-gen-cli. The system provides comprehensive editorial feedback across six specialized editors, from concept validation to final proofreading.

## Architecture Overview

### Core Components

```
┌─────────────────────────────────────────────────────────────┐
│                    Editorial System                         │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │ Idea Editor │  │Outline      │  │ Content Editors     │  │
│  │             │  │ Editor      │  │ ├─ Structural       │  │
│  └─────────────┘  └─────────────┘  │ ├─ Continuity       │  │
│                                    │ └─ Style            │  │
│  ┌─────────────┐  ┌─────────────┐  └─────────────────────┘  │
│  │ Line Editor │  │Copyeditor   │                           │
│  └─────────────┘  └─────────────┘                           │
│                                                             │
│  ┌─────────────┐                                            │
│  │ Proofreader │                                            │
│  └─────────────┘                                            │
└─────────────────────────────────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────────────┐
│                 Core Infrastructure                        │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │ Model       │  │ Cost        │  │ Error Handling     │  │
│  │ Manager     │  │ Optimizer   │  │ & Validation       │  │
│  └─────────────┘  └─────────────┘  └─────────────────────┘  │
│                                                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │ Context     │  │ Feedback    │  │ Quality Metrics    │  │
│  │ Manager     │  │ Processor   │  │ & Analytics        │  │
│  └─────────────┘  └─────────────┘  └─────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### Data Flow

```
Input Data ──► Context Manager ──► Editor Chain ──► Feedback Processor ──► Output
    │                │                    │                    │
    ├─ Story Idea    ├─ Full Context      ├─ Analysis         ├─ JSON Feedback
    ├─ Characters    ├─ Previous Results  ├─ Validation       ├─ CLI Output
    ├─ Locations     └─ Configuration     └─ Error Handling   └─ Revision Commands
    └─ Prose/Outline
```

## Core Data Models

### Base Classes

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional, Dict, Any, Literal
from datetime import datetime

@dataclass
class EditorialIssue:
    """Represents a single editorial issue or suggestion"""
    severity: Literal["major", "minor", "info"]
    category: str  # structure, character, pacing, continuity, pov, etc.
    description: str
    suggestion: str
    scene_ids: Optional[List[str]] = None
    line_numbers: Optional[List[int]] = None
    confidence_score: Optional[float] = None  # 0.0 to 1.0

@dataclass
class EditorialFeedback:
    """Container for all feedback from an editor"""
    editor_type: str
    overall_assessment: str
    issues: List[EditorialIssue]
    suggested_revisions: List['RevisionSuggestion']
    strengths: List[str]
    metadata: Dict[str, Any]  # timing, costs, model info

@dataclass
class RevisionSuggestion:
    """Specific revision recommendation"""
    scene_id: Optional[str] = None  # None for "add new scene"
    revision_type: Literal["rewrite", "expand", "cut", "reorder", "add"]
    priority: Literal["high", "medium", "low"]
    reason: str
    instruction: str  # Detailed guidance for AI regeneration
    target_word_count: Optional[int] = None
    insert_after: Optional[str] = None  # For "add" type
    estimated_tokens: Optional[int] = None

@dataclass
class StoryContext:
    """Complete context for editorial analysis"""
    story_idea: 'StoryIdea'
    characters: List['Character']
    locations: List['Location']
    outline: Optional['Outline'] = None
    prose: Optional['Prose'] = None
    previous_feedback: List[EditorialFeedback] = None

    def __post_init__(self):
        if self.previous_feedback is None:
            self.previous_feedback = []
```

### Editor Base Class

```python
class BaseEditor(ABC):
    """Abstract base class for all editors"""

    def __init__(self, model_manager: 'ModelManager', config: Dict[str, Any]):
        self.model_manager = model_manager
        self.config = config
        self.logger = logging.getLogger(self.__class__.__name__)

    @abstractmethod
    async def analyze(self, context: StoryContext) -> EditorialFeedback:
        """Perform editorial analysis"""
        pass

    @abstractmethod
    def validate_input(self, context: StoryContext) -> List[str]:
        """Validate input data and return error messages"""
        pass

    def _create_feedback_container(self, editor_type: str) -> EditorialFeedback:
        """Create standardized feedback container"""
        return EditorialFeedback(
            editor_type=editor_type,
            overall_assessment="",
            issues=[],
            suggested_revisions=[],
            strengths=[],
            metadata={
                "timestamp": datetime.now().isoformat(),
                "editor_version": self.config.get("version", "1.0.0"),
                "model_used": self.model_manager.current_model
            }
        )

    def _handle_analysis_error(self, error: Exception, context: StoryContext) -> EditorialFeedback:
        """Standardized error handling"""
        self.logger.error(f"Analysis failed: {error}")
        feedback = self._create_feedback_container(self.__class__.__name__)
        feedback.overall_assessment = "Analysis could not be completed due to technical issues"
        feedback.issues = [EditorialIssue(
            severity="info",
            category="technical",
            description=f"Analysis failed: {str(error)}",
            suggestion="Please try again or proceed with manual review"
        )]
        return feedback
```

## Editor Implementations

### 1. Idea Editor

```python
class IdeaEditor(BaseEditor):
    """Critiques story concepts for strength and viability"""

    async def analyze(self, context: StoryContext) -> EditorialFeedback:
        """Analyze story idea for conceptual strength"""
        feedback = self._create_feedback_container("IdeaEditor")

        try:
            # Validate input
            if not context.story_idea:
                raise ValueError("No story idea provided")

            # Build analysis prompt
            prompt = self._build_analysis_prompt(context.story_idea)

            # Get AI analysis
            response = await self.model_manager.call_model(
                prompt=prompt,
                temperature=0.3,  # Lower temperature for consistent analysis
                max_tokens=2000
            )

            # Parse and structure response
            analysis = self._parse_response(response)

            # Build feedback
            feedback.overall_assessment = analysis.get("overall_assessment", "")
            feedback.issues = self._extract_issues(analysis)
            feedback.suggested_revisions = self._extract_revisions(analysis)
            feedback.strengths = analysis.get("strengths", [])

            # Add metadata
            feedback.metadata.update({
                "hook_score": analysis.get("hook_score"),
                "originality_score": analysis.get("originality_score"),
                "emotional_engagement_score": analysis.get("emotional_score"),
                "scope_score": analysis.get("scope_score"),
                "thematic_score": analysis.get("thematic_score"),
                "market_score": analysis.get("market_score")
            })

        except Exception as e:
            return self._handle_analysis_error(e, context)

        return feedback

    def _build_analysis_prompt(self, story_idea: StoryIdea) -> str:
        """Build the analysis prompt for the AI model"""
        return f"""
Analyze this story concept for editorial quality and market viability:

STORY IDEA:
Title: {story_idea.title}
One-sentence summary: {story_idea.one_sentence}
Expanded concept: {story_idea.expanded}
Genre: {story_idea.genre}
Target length: {story_idea.target_length} words
Themes: {', '.join(story_idea.themes)}

Please provide a comprehensive analysis covering:
1. Hook strength and uniqueness
2. Concept originality
3. Emotional engagement potential
4. Scope appropriateness
5. Thematic depth
6. Market viability

Format your response as a JSON object with the following structure:
{{
  "overall_assessment": "Brief summary",
  "hook_analysis": {{
    "score": 1-10,
    "issues": ["list of problems"],
    "strengths": ["list of strengths"]
  }},
  "concept_originality": {{
    "score": 1-10,
    "issues": ["list of problems"],
    "strengths": ["list of strengths"]
  }},
  "emotional_engagement": {{
    "score": 1-10,
    "issues": [],
    "strengths": ["list of strengths"]
  }},
  "scope_assessment": {{
    "score": 1-10,
    "issues": [],
    "strengths": ["list of strengths"]
  }},
  "thematic_depth": {{
    "score": 1-10,
    "issues": ["list of problems"],
    "strengths": ["list of strengths"]
  }},
  "market_potential": {{
    "score": 1-10,
    "issues": [],
    "strengths": ["list of strengths"]
  }},
  "suggested_revisions": [
    {{
      "type": "strengthen_hook|deepen_theme|expand_concept",
      "target": "one_sentence|themes|expanded",
      "reason": "explanation",
      "suggestion": "specific suggestion",
      "expected_impact": "why this helps"
    }}
  ]
}}
"""
```

### 2. Content Editors (Structural, Continuity, Style)

```python
class StructuralEditor(BaseEditor):
    """Analyzes scene-sequel chains and plot logic"""

    async def analyze(self, context: StoryContext) -> EditorialFeedback:
        """Analyze structural integrity of prose"""
        feedback = self._create_feedback_container("StructuralEditor")

        try:
            if not context.prose:
                raise ValueError("No prose provided for structural analysis")

            # Process scenes in batches to manage context
            all_issues = []
            for batch in self._batch_scenes(context.prose.scene_sequels):
                batch_issues = await self._analyze_scene_batch(batch, context)
                all_issues.extend(batch_issues)

            feedback.issues = all_issues
            feedback.overall_assessment = self._generate_overall_assessment(all_issues)

        except Exception as e:
            return self._handle_analysis_error(e, context)

        return feedback

    async def _analyze_scene_batch(self, scenes: List[SceneSequel], context: StoryContext) -> List[EditorialIssue]:
        """Analyze a batch of scenes for structural issues"""
        prompt = self._build_structural_prompt(scenes, context)

        response = await self.model_manager.call_model(
            prompt=prompt,
            temperature=0.2,  # Very consistent analysis
            max_tokens=1500
        )

        return self._parse_structural_response(response)

    def _batch_scenes(self, scenes: List[SceneSequel], batch_size: int = 5) -> List[List[SceneSequel]]:
        """Split scenes into manageable batches"""
        return [scenes[i:i + batch_size] for i in range(0, len(scenes), batch_size)]
```

## Model Management

### Model Manager Interface

```python
class ModelManager:
    """Manages AI model interactions and cost tracking"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.current_model = config.get("default_model", "ollama/qwen3:30b")
        self.cost_tracker = CostTracker()
        self.rate_limiter = RateLimiter()

    async def call_model(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 1000,
        model: Optional[str] = None
    ) -> str:
        """Unified interface for model calls"""
        model = model or self.current_model

        # Rate limiting
        await self.rate_limiter.wait_if_needed(model)

        # Cost estimation and checking
        estimated_cost = self._estimate_cost(prompt, max_tokens, model)
        if not self._check_budget(estimated_cost):
            raise BudgetExceededError(f"Estimated cost ${estimated_cost:.4f} exceeds budget")

        # Make the call
        start_time = time.time()
        try:
            if model.startswith("ollama/"):
                response = await self._call_ollama(model, prompt, temperature, max_tokens)
            elif model.startswith("openai/"):
                response = await self._call_openai(model, prompt, temperature, max_tokens)
            else:
                raise ValueError(f"Unsupported model: {model}")

            # Track usage
            duration = time.time() - start_time
            self.cost_tracker.record_usage(model, prompt, response, duration)

            return response

        except Exception as e:
            self.logger.error(f"Model call failed: {e}")
            raise

    async def _call_ollama(self, model: str, prompt: str, temperature: float, max_tokens: int) -> str:
        """Call local Ollama model"""
        # Implementation for Ollama API
        pass

    async def _call_openai(self, model: str, prompt: str, temperature: float, max_tokens: int) -> str:
        """Call OpenAI API"""
        # Implementation for OpenAI API
        pass
```

### Cost Tracking

```python
class CostTracker:
    """Tracks API usage and costs"""

    def __init__(self):
        self.usage_log = []
        self.cost_models = {
            "ollama/qwen3:30b": {"input": 0.0, "output": 0.0},  # Free
            "openai/gpt-4o": {"input": 0.000005, "output": 0.000015},  # $ per token
            "openai/gpt-4o-mini": {"input": 0.00000015, "output": 0.0000006},
        }

    def record_usage(self, model: str, prompt: str, response: str, duration: float):
        """Record a model usage event"""
        input_tokens = self._count_tokens(prompt)
        output_tokens = self._count_tokens(response)
        cost = self._calculate_cost(model, input_tokens, output_tokens)

        usage_event = {
            "timestamp": datetime.now().isoformat(),
            "model": model,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "cost_usd": cost,
            "duration_seconds": duration
        }

        self.usage_log.append(usage_event)

    def get_total_cost(self, since: Optional[datetime] = None) -> float:
        """Get total cost since timestamp"""
        events = self.usage_log
        if since:
            events = [e for e in events if datetime.fromisoformat(e["timestamp"]) > since]

        return sum(e["cost_usd"] for e in events)

    def _calculate_cost(self, model: str, input_tokens: int, output_tokens: int) -> float:
        """Calculate cost for a usage event"""
        if model not in self.cost_models:
            return 0.0  # Unknown model, assume free

        rates = self.cost_models[model]
        return (input_tokens * rates["input"]) + (output_tokens * rates["output"])

    def _count_tokens(self, text: str) -> int:
        """Estimate token count (rough approximation)"""
        # Simple approximation: ~4 characters per token
        return len(text) // 4
```

## CLI Interface

### Command Structure

```bash
storygen-iter edit [EDITOR_TYPE] [OPTIONS] INPUT_FILE

Editors:
  idea        Analyze story concept
  outline     Analyze story outline
  content     Analyze prose content (structural/continuity/style)
  line        Polish sentence-level craft
  copy        Check grammar and style
  proof       Final typo check

Examples:
  # Analyze idea
  storygen-iter edit idea --idea idea.json -o feedback.json

  # Analyze content with specific focus
  storygen-iter edit content --focus structural --prose prose.json -o structural_feedback.json

  # Analyze with cost control
  storygen-iter edit content --max-cost 1.00 --model gpt-4o --prose prose.json -o feedback.json
```

### CLI Implementation

```python
import click
import asyncio
from pathlib import Path
from typing import Optional

@click.group()
def edit():
    """Editorial analysis commands"""
    pass

@edit.command()
@click.option("--idea", "idea_file", type=click.Path(exists=True), required=True)
@click.option("--output", "-o", type=click.Path(), required=True)
@click.option("--model", default="ollama/qwen3:30b")
@click.option("--max-cost", type=float, help="Maximum cost in USD")
@click.option("--verbose", "-v", is_flag=True)
def idea(idea_file: str, output: str, model: str, max_cost: Optional[float], verbose: bool):
    """Analyze story idea"""
    asyncio.run(_run_editor("idea", {
        "input_file": idea_file,
        "output_file": output,
        "model": model,
        "max_cost": max_cost,
        "verbose": verbose
    }))

@edit.command()
@click.option("--outline", "outline_file", type=click.Path(exists=True), required=True)
@click.option("--idea", "idea_file", type=click.Path(exists=True), required=True)
@click.option("--characters", "characters_file", type=click.Path(exists=True), required=True)
@click.option("--output", "-o", type=click.Path(), required=True)
@click.option("--model", default="ollama/qwen3:30b")
@click.option("--max-cost", type=float)
@click.option("--verbose", "-v", is_flag=True)
def outline(outline_file: str, idea_file: str, characters_file: str, output: str,
           model: str, max_cost: Optional[float], verbose: bool):
    """Analyze story outline"""
    asyncio.run(_run_editor("outline", {
        "outline_file": outline_file,
        "idea_file": idea_file,
        "characters_file": characters_file,
        "output_file": output,
        "model": model,
        "max_cost": max_cost,
        "verbose": verbose
    }))

@edit.command()
@click.option("--prose", "prose_file", type=click.Path(exists=True), required=True)
@click.option("--focus", type=click.Choice(["structural", "continuity", "style", "comprehensive"]),
              default="comprehensive")
@click.option("--output", "-o", type=click.Path(), required=True)
@click.option("--model", default="ollama/qwen3:30b")
@click.option("--max-cost", type=float)
@click.option("--batch-size", type=int, default=5, help="Scenes per batch")
@click.option("--verbose", "-v", is_flag=True)
def content(prose_file: str, focus: str, output: str, model: str,
           max_cost: Optional[float], batch_size: int, verbose: bool):
    """Analyze prose content"""
    asyncio.run(_run_editor("content", {
        "prose_file": prose_file,
        "focus": focus,
        "output_file": output,
        "model": model,
        "max_cost": max_cost,
        "batch_size": batch_size,
        "verbose": verbose
    }))

async def _run_editor(editor_type: str, config: Dict[str, Any]):
    """Generic editor runner"""
    try:
        # Load configuration
        system_config = load_config()

        # Initialize components
        model_manager = ModelManager(system_config)
        context_manager = ContextManager()
        feedback_processor = FeedbackProcessor()

        # Load input data
        context = await context_manager.load_context(config)

        # Select and run editor
        if editor_type == "idea":
            editor = IdeaEditor(model_manager, system_config)
        elif editor_type == "outline":
            editor = OutlineEditor(model_manager, system_config)
        elif editor_type == "content":
            if config["focus"] == "structural":
                editor = StructuralEditor(model_manager, system_config)
            elif config["focus"] == "continuity":
                editor = ContinuityEditor(model_manager, system_config)
            elif config["focus"] == "style":
                editor = StyleEditor(model_manager, system_config)
            else:
                editor = ComprehensiveContentEditor(model_manager, system_config)
        # ... other editors

        # Validate input
        validation_errors = editor.validate_input(context)
        if validation_errors:
            click.echo("Input validation errors:", err=True)
            for error in validation_errors:
                click.echo(f"  - {error}", err=True)
            return

        # Run analysis
        if config.get("verbose"):
            click.echo(f"Running {editor_type} analysis...")

        feedback = await editor.analyze(context)

        # Process and save results
        await feedback_processor.save_feedback(feedback, config["output_file"])

        # Display summary
        click.echo(f"Analysis complete. {len(feedback.issues)} issues found.")
        if feedback.metadata.get("cost_usd"):
            click.echo(f"Cost: ${feedback.metadata['cost_usd']:.4f}")

    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()
```

## Configuration System

### Configuration Schema

```python
# config/editorial_config.yaml
editors:
  idea:
    enabled: true
    default_model: "ollama/qwen3:30b"
    max_retries: 3
    timeout_seconds: 300
    cost_limits:
      max_per_analysis: 1.00
      daily_budget: 10.00

  outline:
    enabled: true
    default_model: "ollama/qwen3:30b"
    max_retries: 3
    timeout_seconds: 300

  content:
    enabled: true
    default_model: "ollama/qwen3:30b"
    batch_size: 5
    max_concurrent_batches: 3
    structural:
      focus_areas: ["scene_goals", "disaster_consequences", "causality_chains"]
    continuity:
      track_elements: ["character_states", "timeline", "locations"]
    style:
      check_elements: ["pov_consistency", "filter_words", "voice_shifts"]

models:
  ollama:
    base_url: "http://localhost:11434"
    timeout: 120
    retry_delay: 5
    supported_models:
      - "qwen3:30b"
      - "llama3.2:70b"

  openai:
    api_key_env: "OPENAI_API_KEY"
    timeout: 60
    retry_delay: 2
    supported_models:
      - "gpt-4o"
      - "gpt-4o-mini"

cost_control:
  enabled: true
  default_budget: 5.00  # USD per day
  alert_threshold: 0.80  # Alert at 80% of budget
  hard_limit: true  # Block requests over budget

logging:
  level: "INFO"
  file: "logs/editorial.log"
  max_file_size: "10MB"
  retention_days: 30

quality_metrics:
  enabled: true
  track_user_feedback: true
  automated_testing: true
  improvement_tracking: true
```

## Error Handling & Validation

### Validation Framework

```python
class ValidationError(Exception):
    """Custom exception for validation failures"""
    pass

class InputValidator:
    """Validates input data for editors"""

    @staticmethod
    def validate_story_idea(idea: Dict[str, Any]) -> List[str]:
        """Validate story idea data"""
        errors = []

        if not idea.get("title"):
            errors.append("Story idea missing title")

        if not idea.get("one_sentence"):
            errors.append("Story idea missing one-sentence summary")

        if len(idea.get("one_sentence", "")) > 500:
            errors.append("One-sentence summary too long (max 500 characters)")

        if not idea.get("expanded"):
            errors.append("Story idea missing expanded concept")

        return errors

    @staticmethod
    def validate_prose(prose: Dict[str, Any]) -> List[str]:
        """Validate prose data"""
        errors = []

        if not prose.get("scene_sequels"):
            errors.append("Prose missing scene-sequels")

        scene_sequels = prose["scene_sequels"]
        if not isinstance(scene_sequels, list):
            errors.append("Scene-sequels must be a list")

        for i, ss in enumerate(scene_sequels):
            if not ss.get("id"):
                errors.append(f"Scene-sequel {i} missing ID")

            if not ss.get("scene_goal") and not ss.get("disaster"):
                errors.append(f"Scene-sequel {i} missing both scene goal and disaster")

        return errors

    @staticmethod
    def validate_context_completeness(context: StoryContext, editor_type: str) -> List[str]:
        """Validate that context has required data for editor"""
        errors = []

        if editor_type in ["idea"] and not context.story_idea:
            errors.append("Idea editor requires story idea")

        if editor_type in ["outline"] and not context.outline:
            errors.append("Outline editor requires outline")

        if editor_type in ["content"] and not context.prose:
            errors.append("Content editor requires prose")

        return errors
```

### Error Recovery

```python
class ErrorHandler:
    """Handles errors and provides recovery strategies"""

    @staticmethod
    def classify_error(error: Exception) -> str:
        """Classify error type for appropriate handling"""
        if isinstance(error, aiohttp.ClientError):
            return "network"
        elif isinstance(error, json.JSONDecodeError):
            return "parsing"
        elif isinstance(error, ValidationError):
            return "validation"
        elif isinstance(error, BudgetExceededError):
            return "budget"
        else:
            return "unknown"

    @staticmethod
    def get_recovery_strategy(error_type: str, attempt: int) -> Dict[str, Any]:
        """Get recovery strategy for error type and attempt number"""

        strategies = {
            "network": {
                1: {"action": "retry", "delay": 5, "model": "same"},
                2: {"action": "retry", "delay": 15, "model": "fallback"},
                3: {"action": "fail", "fallback_response": "network_error"}
            },
            "parsing": {
                1: {"action": "retry", "delay": 0, "model": "same"},
                2: {"action": "retry", "delay": 0, "model": "simpler"},
                3: {"action": "fail", "fallback_response": "parsing_error"}
            },
            "budget": {
                1: {"action": "fail", "message": "Budget exceeded"}
            },
            "validation": {
                1: {"action": "fail", "message": "Invalid input data"}
            }
        }

        return strategies.get(error_type, {}).get(attempt, {"action": "fail"})
```

## Testing Strategy

### Unit Testing

```python
# tests/test_editors.py
import pytest
from unittest.mock import AsyncMock, MagicMock
from editorial.editors.idea import IdeaEditor

class TestIdeaEditor:

    @pytest.fixture
    def mock_model_manager(self):
        manager = MagicMock()
        manager.call_model = AsyncMock()
        return manager

    @pytest.fixture
    def editor(self, mock_model_manager):
        config = {"version": "1.0.0"}
        return IdeaEditor(mock_model_manager, config)

    @pytest.mark.asyncio
    async def test_successful_analysis(self, editor, mock_model_manager):
        # Mock successful model response
        mock_response = """
        {
          "overall_assessment": "Strong concept",
          "hook_analysis": {"score": 8, "issues": [], "strengths": ["Good hook"]},
          "concept_originality": {"score": 7, "issues": [], "strengths": ["Original"]},
          "emotional_engagement": {"score": 9, "issues": [], "strengths": ["Emotional"]},
          "scope_assessment": {"score": 8, "issues": [], "strengths": ["Good scope"]},
          "thematic_depth": {"score": 7, "issues": [], "strengths": ["Thematic"]},
          "market_potential": {"score": 8, "issues": [], "strengths": ["Marketable"]},
          "suggested_revisions": []
        }
        """
        mock_model_manager.call_model.return_value = mock_response

        context = create_test_context()
        feedback = await editor.analyze(context)

        assert feedback.editor_type == "IdeaEditor"
        assert "Strong concept" in feedback.overall_assessment
        assert len(feedback.issues) == 0  # No issues in this test case

    @pytest.mark.asyncio
    async def test_model_failure_fallback(self, editor, mock_model_manager):
        # Mock model failure
        mock_model_manager.call_model.side_effect = Exception("Model unavailable")

        context = create_test_context()
        feedback = await editor.analyze(context)

        assert feedback.overall_assessment == "Analysis could not be completed due to technical issues"
        assert len(feedback.issues) == 1
        assert feedback.issues[0].category == "technical"
```

### Integration Testing

```python
# tests/test_integration.py
import pytest
import tempfile
import json
from pathlib import Path
from editorial.cli import main

class TestEditorialCLI:

    def test_idea_editor_cli(self, cli_runner):
        """Test idea editor through CLI"""
        # Create test data
        idea_data = {
            "title": "Test Story",
            "one_sentence": "A detective solves a mystery",
            "expanded": "Detailed concept here",
            "genre": "mystery",
            "target_length": 5000,
            "themes": ["justice", "redemption"]
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            idea_file = Path(tmpdir) / "idea.json"
            output_file = Path(tmpdir) / "feedback.json"

            # Write test data
            idea_file.write_text(json.dumps(idea_data))

            # Run CLI command
            result = cli_runner.invoke(main, [
                "edit", "idea",
                "--idea", str(idea_file),
                "--output", str(output_file)
            ])

            assert result.exit_code == 0
            assert output_file.exists()

            # Verify output structure
            feedback = json.loads(output_file.read_text())
            assert "editor_type" in feedback
            assert "overall_assessment" in feedback
            assert "issues" in feedback

    def test_cost_tracking(self, cli_runner):
        """Test cost tracking functionality"""
        # Test with budget limits
        pass
```

### Quality Assurance

```python
# tests/test_quality.py
class TestEditorialQuality:

    def test_feedback_consistency(self):
        """Test that similar inputs produce consistent feedback"""
        # Run same analysis multiple times, check variance is low
        pass

    def test_false_positive_rate(self):
        """Test false positive rate on known good content"""
        # Analyze professionally edited stories, ensure low false positives
        pass

    def test_suggestion_helpfulness(self):
        """Test that suggestions are actionable and helpful"""
        # Human evaluation of suggestion quality
        pass
```

## Performance Optimization

### Caching Strategy

```python
class AnalysisCache:
    """Cache analysis results to avoid redundant work"""

    def __init__(self, cache_dir: Path, max_age_hours: int = 24):
        self.cache_dir = cache_dir
        self.max_age_hours = max_age_hours

    def get_cache_key(self, editor_type: str, content_hash: str, config_hash: str) -> str:
        """Generate cache key from inputs"""
        return f"{editor_type}_{content_hash}_{config_hash}"

    def get_cached_result(self, cache_key: str) -> Optional[EditorialFeedback]:
        """Retrieve cached result if valid"""
        cache_file = self.cache_dir / f"{cache_key}.json"

        if not cache_file.exists():
            return None

        # Check age
        if self._is_cache_stale(cache_file):
            cache_file.unlink()
            return None

        try:
            data = json.loads(cache_file.read_text())
            return EditorialFeedback(**data)
        except Exception:
            return None

    def cache_result(self, cache_key: str, feedback: EditorialFeedback):
        """Cache analysis result"""
        cache_file = self.cache_dir / f"{cache_key}.json"
        cache_file.parent.mkdir(parents=True, exist_ok=True)

        data = {
            "editor_type": feedback.editor_type,
            "overall_assessment": feedback.overall_assessment,
            "issues": [issue.__dict__ for issue in feedback.issues],
            "suggested_revisions": [rev.__dict__ for rev in feedback.suggested_revisions],
            "strengths": feedback.strengths,
            "metadata": feedback.metadata
        }

        cache_file.write_text(json.dumps(data, indent=2))

    def _is_cache_stale(self, cache_file: Path) -> bool:
        """Check if cache file is too old"""
        age_hours = (time.time() - cache_file.stat().st_mtime) / 3600
        return age_hours > self.max_age_hours
```

### Batch Processing

```python
class BatchProcessor:
    """Process multiple analysis requests efficiently"""

    def __init__(self, model_manager: ModelManager, max_concurrent: int = 3):
        self.model_manager = model_manager
        self.max_concurrent = max_concurrent
        self.semaphore = asyncio.Semaphore(max_concurrent)

    async def process_batch(self, requests: List[AnalysisRequest]) -> List[EditorialFeedback]:
        """Process multiple analysis requests in parallel"""

        async def process_single(request: AnalysisRequest) -> EditorialFeedback:
            async with self.semaphore:
                return await self._process_request(request)

        # Process in parallel with concurrency limit
        tasks = [process_single(req) for req in requests]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Handle exceptions
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                # Create error feedback for failed requests
                error_feedback = EditorialFeedback(
                    editor_type=requests[i].editor_type,
                    overall_assessment="Analysis failed",
                    issues=[EditorialIssue(
                        severity="info",
                        category="technical",
                        description=f"Analysis failed: {str(result)}",
                        suggestion="Please try again"
                    )],
                    suggested_revisions=[],
                    strengths=[]
                )
                processed_results.append(error_feedback)
            else:
                processed_results.append(result)

        return processed_results
```

## Restartability & Job Management

### Overview

Given the potentially long-running nature of editorial analyses (especially for longer manuscripts), the system must support restartability, background processing, and robust error recovery. This section outlines the job management system that enables users to pause, resume, and monitor editorial analyses.

### Job Management System

```python
from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List
from datetime import datetime
import asyncio
import json
import uuid

class JobStatus(Enum):
    """Job execution states"""
    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

@dataclass
class JobMetadata:
    """Metadata for tracking job execution"""
    job_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    status: JobStatus = JobStatus.PENDING
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    progress: float = 0.0  # 0.0 to 1.0
    estimated_completion: Optional[datetime] = None
    current_stage: str = ""
    error_message: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3

    # Cost and resource tracking
    total_cost_usd: float = 0.0
    tokens_used: int = 0
    duration_seconds: float = 0.0

    # Configuration
    editor_type: str = ""
    model_used: str = ""
    batch_size: int = 5
    max_concurrent_batches: int = 3

@dataclass
class CheckpointData:
    """Data saved at checkpoints for resume capability"""
    job_id: str
    stage: str
    progress: float
    completed_items: List[str]  # IDs of completed scenes/batches
    partial_results: Dict[str, Any]  # Intermediate results
    context_state: Dict[str, Any]  # Current context
    timestamp: datetime = field(default_factory=datetime.now)

class JobManager:
    """Manages long-running editorial analysis jobs"""

    def __init__(self, storage_dir: Path, max_concurrent_jobs: int = 5):
        self.storage_dir = storage_dir
        self.jobs_dir = storage_dir / "jobs"
        self.checkpoints_dir = storage_dir / "checkpoints"
        self.jobs_dir.mkdir(parents=True, exist_ok=True)
        self.checkpoints_dir.mkdir(parents=True, exist_ok=True)

        self.active_jobs: Dict[str, asyncio.Task] = {}
        self.job_metadata: Dict[str, JobMetadata] = {}
        self.semaphore = asyncio.Semaphore(max_concurrent_jobs)

    async def start_job(
        self,
        editor_type: str,
        context: StoryContext,
        config: Dict[str, Any]
    ) -> str:
        """Start a new editorial analysis job"""
        job_id = str(uuid.uuid4())

        # Create job metadata
        metadata = JobMetadata(
            job_id=job_id,
            editor_type=editor_type,
            model_used=config.get("model", "ollama/qwen3:30b"),
            batch_size=config.get("batch_size", 5),
            max_concurrent_batches=config.get("max_concurrent_batches", 3)
        )

        # Save initial metadata
        await self._save_job_metadata(metadata)

        # Start the job task
        task = asyncio.create_task(
            self._run_job(job_id, editor_type, context, config)
        )

        self.active_jobs[job_id] = task
        self.job_metadata[job_id] = metadata

        return job_id

    async def pause_job(self, job_id: str) -> bool:
        """Pause a running job"""
        if job_id not in self.active_jobs:
            return False

        metadata = await self._load_job_metadata(job_id)
        if metadata.status != JobStatus.RUNNING:
            return False

        # Signal pause (implementation depends on editor)
        # This would require editors to check for pause signals
        metadata.status = JobStatus.PAUSED
        await self._save_job_metadata(metadata)

        return True

    async def resume_job(self, job_id: str) -> bool:
        """Resume a paused job"""
        metadata = await self._load_job_metadata(job_id)
        if metadata.status != JobStatus.PAUSED:
            return False

        # Load checkpoint
        checkpoint = await self._load_checkpoint(job_id)
        if not checkpoint:
            return False

        # Resume from checkpoint
        metadata.status = JobStatus.RUNNING
        metadata.started_at = datetime.now()
        await self._save_job_metadata(metadata)

        # Restart the job task from checkpoint
        context = await self._restore_context_from_checkpoint(checkpoint)
        config = await self._load_job_config(job_id)

        task = asyncio.create_task(
            self._resume_job_from_checkpoint(job_id, checkpoint, context, config)
        )

        self.active_jobs[job_id] = task
        return True

    async def cancel_job(self, job_id: str) -> bool:
        """Cancel a job"""
        if job_id not in self.active_jobs:
            return False

        # Cancel the task
        task = self.active_jobs[job_id]
        task.cancel()

        # Update metadata
        metadata = await self._load_job_metadata(job_id)
        metadata.status = JobStatus.CANCELLED
        metadata.completed_at = datetime.now()
        await self._save_job_metadata(metadata)

        # Clean up
        del self.active_jobs[job_id]
        del self.job_metadata[job_id]

        return True

    async def get_job_status(self, job_id: str) -> Optional[JobMetadata]:
        """Get current job status"""
        return await self._load_job_metadata(job_id)

    async def list_jobs(self, status_filter: Optional[JobStatus] = None) -> List[JobMetadata]:
        """List all jobs, optionally filtered by status"""
        all_jobs = []

        for job_file in self.jobs_dir.glob("*.json"):
            try:
                metadata = await self._load_job_metadata(job_file.stem)
                if not status_filter or metadata.status == status_filter:
                    all_jobs.append(metadata)
            except Exception:
                continue  # Skip corrupted job files

        return sorted(all_jobs, key=lambda j: j.created_at, reverse=True)

    async def cleanup_old_jobs(self, max_age_days: int = 30):
        """Clean up completed/failed jobs older than max_age_days"""
        cutoff = datetime.now().timestamp() - (max_age_days * 24 * 60 * 60)

        for job_file in self.jobs_dir.glob("*.json"):
            if job_file.stat().st_mtime < cutoff:
                try:
                    metadata = await self._load_job_metadata(job_file.stem)
                    if metadata.status in [JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED]:
                        # Remove job files
                        job_file.unlink()
                        # Remove checkpoints
                        checkpoint_dir = self.checkpoints_dir / job_file.stem
                        if checkpoint_dir.exists():
                            import shutil
                            shutil.rmtree(checkpoint_dir)
                except Exception:
                    continue

    async def _run_job(
        self,
        job_id: str,
        editor_type: str,
        context: StoryContext,
        config: Dict[str, Any]
    ):
        """Execute a job with checkpointing and error recovery"""
        metadata = await self._load_job_metadata(job_id)
        metadata.status = JobStatus.RUNNING
        metadata.started_at = datetime.now()
        await self._save_job_metadata(metadata)

        try:
            async with self.semaphore:
                # Initialize editor
                editor = await self._create_editor(editor_type, config)

                # Run analysis with checkpointing
                feedback = await self._run_with_checkpointing(
                    job_id, editor, context, metadata
                )

                # Save final result
                await self._save_job_result(job_id, feedback)

                # Update metadata
                metadata.status = JobStatus.COMPLETED
                metadata.completed_at = datetime.now()
                metadata.progress = 1.0
                metadata.duration_seconds = (
                    metadata.completed_at - metadata.started_at
                ).total_seconds()
                await self._save_job_metadata(metadata)

        except asyncio.CancelledError:
            metadata.status = JobStatus.CANCELLED
            await self._save_job_metadata(metadata)
            raise

        except Exception as e:
            metadata.status = JobStatus.FAILED
            metadata.error_message = str(e)
            metadata.completed_at = datetime.now()
            await self._save_job_metadata(metadata)

            # Auto-retry if under retry limit
            if metadata.retry_count < metadata.max_retries:
                await self._schedule_retry(job_id, editor_type, context, config)

        finally:
            # Clean up active job tracking
            if job_id in self.active_jobs:
                del self.active_jobs[job_id]
            if job_id in self.job_metadata:
                del self.job_metadata[job_id]

    async def _run_with_checkpointing(
        self,
        job_id: str,
        editor: BaseEditor,
        context: StoryContext,
        metadata: JobMetadata
    ) -> EditorialFeedback:
        """Run analysis with periodic checkpointing"""

        # For content editors that process in batches
        if hasattr(editor, '_analyze_scene_batch'):
            return await self._run_batch_with_checkpointing(
                job_id, editor, context, metadata
            )
        else:
            # Single-shot analysis
            metadata.current_stage = "analyzing"
            await self._save_job_metadata(metadata)

            feedback = await editor.analyze(context)

            metadata.progress = 1.0
            await self._save_job_metadata(metadata)

            return feedback

    async def _run_batch_with_checkpointing(
        self,
        job_id: str,
        editor: BaseEditor,
        context: StoryContext,
        metadata: JobMetadata
    ) -> EditorialFeedback:
        """Run batch processing with checkpointing"""

        # Get batches to process
        batches = editor._batch_scenes(context.prose.scene_sequels, metadata.batch_size)
        total_batches = len(batches)

        completed_issues = []
        checkpoint_frequency = max(1, total_batches // 10)  # Checkpoint every 10%

        for i, batch in enumerate(batches):
            # Check for pause/cancel signals
            current_metadata = await self._load_job_metadata(job_id)
            if current_metadata.status == JobStatus.PAUSED:
                # Save checkpoint and pause
                await self._save_checkpoint(job_id, f"batch_{i}", i/total_batches,
                                          completed_issues, context)
                return None  # Will be resumed later

            if current_metadata.status == JobStatus.CANCELLED:
                raise asyncio.CancelledError()

            # Process batch
            metadata.current_stage = f"Processing batch {i+1}/{total_batches}"
            metadata.progress = i / total_batches
            await self._save_job_metadata(metadata)

            try:
                batch_issues = await editor._analyze_scene_batch(batch, context)
                completed_issues.extend(batch_issues)
            except Exception as e:
                # Save checkpoint on error
                await self._save_checkpoint(job_id, f"batch_{i}_error", i/total_batches,
                                          completed_issues, context)
                raise

            # Periodic checkpointing
            if (i + 1) % checkpoint_frequency == 0:
                await self._save_checkpoint(job_id, f"batch_{i+1}", (i+1)/total_batches,
                                          completed_issues, context)

        # Create final feedback
        feedback = editor._create_feedback_container(editor.__class__.__name__)
        feedback.issues = completed_issues
        feedback.overall_assessment = editor._generate_overall_assessment(completed_issues)

        return feedback

    async def _save_checkpoint(
        self,
        job_id: str,
        stage: str,
        progress: float,
        completed_items: List[Any],
        context: StoryContext
    ):
        """Save checkpoint data for resume capability"""
        checkpoint_dir = self.checkpoints_dir / job_id
        checkpoint_dir.mkdir(parents=True, exist_ok=True)

        checkpoint = CheckpointData(
            job_id=job_id,
            stage=stage,
            progress=progress,
            completed_items=[str(item) for item in completed_items],
            partial_results={"issues": [issue.__dict__ for issue in completed_items]},
            context_state=self._serialize_context(context)
        )

        checkpoint_file = checkpoint_dir / f"{stage}.json"
        checkpoint_file.write_text(json.dumps({
            "job_id": checkpoint.job_id,
            "stage": checkpoint.stage,
            "progress": checkpoint.progress,
            "completed_items": checkpoint.completed_items,
            "partial_results": checkpoint.partial_results,
            "context_state": checkpoint.context_state,
            "timestamp": checkpoint.timestamp.isoformat()
        }, indent=2))

    async def _load_checkpoint(self, job_id: str) -> Optional[CheckpointData]:
        """Load the most recent checkpoint for a job"""
        checkpoint_dir = self.checkpoints_dir / job_id
        if not checkpoint_dir.exists():
            return None

        # Find most recent checkpoint
        checkpoint_files = list(checkpoint_dir.glob("*.json"))
        if not checkpoint_files:
            return None

        latest_file = max(checkpoint_files, key=lambda f: f.stat().st_mtime)

        try:
            data = json.loads(latest_file.read_text())
            return CheckpointData(
                job_id=data["job_id"],
                stage=data["stage"],
                progress=data["progress"],
                completed_items=data["completed_items"],
                partial_results=data["partial_results"],
                context_state=data["context_state"],
                timestamp=datetime.fromisoformat(data["timestamp"])
            )
        except Exception:
            return None

    async def _resume_job_from_checkpoint(
        self,
        job_id: str,
        checkpoint: CheckpointData,
        context: StoryContext,
        config: Dict[str, Any]
    ):
        """Resume job execution from checkpoint"""
        # This would need to be implemented based on the specific editor
        # For now, restart from beginning (could be enhanced to resume mid-batch)
        await self._run_job(job_id, config.get("editor_type"), context, config)

    async def _save_job_metadata(self, metadata: JobMetadata):
        """Save job metadata to disk"""
        job_file = self.jobs_dir / f"{metadata.job_id}.json"
        job_file.write_text(json.dumps({
            "job_id": metadata.job_id,
            "status": metadata.status.value,
            "created_at": metadata.created_at.isoformat(),
            "started_at": metadata.started_at.isoformat() if metadata.started_at else None,
            "completed_at": metadata.completed_at.isoformat() if metadata.completed_at else None,
            "progress": metadata.progress,
            "estimated_completion": metadata.estimated_completion.isoformat() if metadata.estimated_completion else None,
            "current_stage": metadata.current_stage,
            "error_message": metadata.error_message,
            "retry_count": metadata.retry_count,
            "max_retries": metadata.max_retries,
            "total_cost_usd": metadata.total_cost_usd,
            "tokens_used": metadata.tokens_used,
            "duration_seconds": metadata.duration_seconds,
            "editor_type": metadata.editor_type,
            "model_used": metadata.model_used,
            "batch_size": metadata.batch_size,
            "max_concurrent_batches": metadata.max_concurrent_batches
        }, indent=2))

    async def _load_job_metadata(self, job_id: str) -> JobMetadata:
        """Load job metadata from disk"""
        job_file = self.jobs_dir / f"{job_id}.json"
        data = json.loads(job_file.read_text())

        return JobMetadata(
            job_id=data["job_id"],
            status=JobStatus(data["status"]),
            created_at=datetime.fromisoformat(data["created_at"]),
            started_at=datetime.fromisoformat(data["started_at"]) if data["started_at"] else None,
            completed_at=datetime.fromisoformat(data["completed_at"]) if data["completed_at"] else None,
            progress=data["progress"],
            estimated_completion=datetime.fromisoformat(data["estimated_completion"]) if data["estimated_completion"] else None,
            current_stage=data["current_stage"],
            error_message=data["error_message"],
            retry_count=data["retry_count"],
            max_retries=data["max_retries"],
            total_cost_usd=data["total_cost_usd"],
            tokens_used=data["tokens_used"],
            duration_seconds=data["duration_seconds"],
            editor_type=data["editor_type"],
            model_used=data["model_used"],
            batch_size=data["batch_size"],
            max_concurrent_batches=data["max_concurrent_batches"]
        )

    def _serialize_context(self, context: StoryContext) -> Dict[str, Any]:
        """Serialize context for checkpointing"""
        # Implementation would serialize the context data
        return {}

    async def _restore_context_from_checkpoint(self, checkpoint: CheckpointData) -> StoryContext:
        """Restore context from checkpoint"""
        # Implementation would deserialize context
        return None
```

### Background Processing CLI Commands

```python
# CLI commands for job management
@click.group()
def job():
    """Job management commands"""
    pass

@job.command()
@click.option("--editor", required=True, type=click.Choice(["idea", "outline", "content", "line", "copy", "proof"]))
@click.option("--input", "-i", required=True, type=click.Path(exists=True))
@click.option("--output", "-o", type=click.Path())
@click.option("--model", default="ollama/qwen3:30b")
@click.option("--background", "-b", is_flag=True, help="Run in background")
@click.option("--job-id", help="Resume specific job")
def start(editor: str, input: str, output: str, model: str, background: bool, job_id: str):
    """Start or resume an editorial analysis job"""
    asyncio.run(_start_job(editor, input, output, model, background, job_id))

@job.command()
@click.argument("job_id")
def status(job_id: str):
    """Check job status"""
    asyncio.run(_show_job_status(job_id))

@job.command()
@click.argument("job_id")
def pause(job_id: str):
    """Pause a running job"""
    asyncio.run(_pause_job(job_id))

@job.command()
@click.argument("job_id")
def resume(job_id: str):
    """Resume a paused job"""
    asyncio.run(_resume_job(job_id))

@job.command()
@click.argument("job_id")
def cancel(job_id: str):
    """Cancel a job"""
    asyncio.run(_cancel_job(job_id))

@job.command()
@click.option("--status", type=click.Choice(["pending", "running", "paused", "completed", "failed", "cancelled"]))
def list(status: str):
    """List jobs"""
    status_filter = JobStatus(status) if status else None
    asyncio.run(_list_jobs(status_filter))

async def _start_job(editor: str, input_file: str, output_file: str, model: str, background: bool, job_id: str):
    """Start a job"""
    try:
        # Load configuration and context
        config = load_config()
        context_manager = ContextManager()
        context = await context_manager.load_context_from_file(input_file)

        # Initialize job manager
        job_manager = JobManager(Path(config.get("job_storage_dir", "./jobs")))

        if job_id:
            # Resume existing job
            success = await job_manager.resume_job(job_id)
            if success:
                click.echo(f"Resumed job {job_id}")
            else:
                click.echo(f"Failed to resume job {job_id}", err=True)
                return
        else:
            # Start new job
            job_config = {
                "model": model,
                "output_file": output_file,
                "background": background
            }

            job_id = await job_manager.start_job(editor, context, job_config)
            click.echo(f"Started job {job_id}")

        if background:
            click.echo(f"Job {job_id} running in background. Use 'storygen-iter job status {job_id}' to check progress.")
        else:
            # Wait for completion
            while True:
                metadata = await job_manager.get_job_status(job_id)
                if metadata.status in [JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED]:
                    break
                await asyncio.sleep(2)

            if metadata.status == JobStatus.COMPLETED:
                click.echo(f"Job {job_id} completed successfully")
            else:
                click.echo(f"Job {job_id} {metadata.status.value}: {metadata.error_message}", err=True)

    except Exception as e:
        click.echo(f"Error: {e}", err=True)

async def _show_job_status(job_id: str):
    """Show detailed job status"""
    try:
        config = load_config()
        job_manager = JobManager(Path(config.get("job_storage_dir", "./jobs")))

        metadata = await job_manager.get_job_status(job_id)
        if not metadata:
            click.echo(f"Job {job_id} not found", err=True)
            return

        click.echo(f"Job ID: {metadata.job_id}")
        click.echo(f"Status: {metadata.status.value}")
        click.echo(f"Editor: {metadata.editor_type}")
        click.echo(f"Model: {metadata.model_used}")
        click.echo(f"Progress: {metadata.progress:.1%}")
        click.echo(f"Stage: {metadata.current_stage}")
        click.echo(f"Created: {metadata.created_at}")
        if metadata.started_at:
            click.echo(f"Started: {metadata.started_at}")
        if metadata.completed_at:
            click.echo(f"Completed: {metadata.completed_at}")
        if metadata.duration_seconds > 0:
            click.echo(f"Duration: {metadata.duration_seconds:.1f}s")
        if metadata.total_cost_usd > 0:
            click.echo(f"Cost: ${metadata.total_cost_usd:.4f}")
        if metadata.error_message:
            click.echo(f"Error: {metadata.error_message}")

    except Exception as e:
        click.echo(f"Error: {e}", err=True)
```

### Progress Monitoring & Notifications

```python
class ProgressMonitor:
    """Monitor job progress and provide notifications"""

    def __init__(self, job_manager: JobManager):
        self.job_manager = job_manager
        self.callbacks: Dict[str, List[Callable]] = defaultdict(list)

    def on_progress_update(self, job_id: str, callback: Callable[[JobMetadata], None]):
        """Register callback for progress updates"""
        self.callbacks[job_id].append(callback)

    async def monitor_job(self, job_id: str):
        """Monitor a job and trigger callbacks on progress updates"""
        last_progress = -1

        while True:
            metadata = await self.job_manager.get_job_status(job_id)
            if not metadata:
                break

            # Trigger callbacks on progress change
            if metadata.progress != last_progress:
                for callback in self.callbacks[job_id]:
                    callback(metadata)
                last_progress = metadata.progress

            # Stop monitoring if job is complete
            if metadata.status in [JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED]:
                break

            await asyncio.sleep(5)  # Check every 5 seconds

    def notify_completion(self, metadata: JobMetadata):
        """Send completion notification"""
        if metadata.status == JobStatus.COMPLETED:
            message = f"Editorial analysis completed for job {metadata.job_id}"
        elif metadata.status == JobStatus.FAILED:
            message = f"Editorial analysis failed for job {metadata.job_id}: {metadata.error_message}"
        else:
            message = f"Editorial analysis {metadata.status.value} for job {metadata.job_id}"

        # Could integrate with system notifications, email, etc.
        print(f"NOTIFICATION: {message}")
```

### Resource Management & Cleanup

```python
class ResourceManager:
    """Manage system resources for long-running jobs"""

    def __init__(self, base_dir: Path):
        self.base_dir = base_dir
        self.temp_dir = base_dir / "temp"
        self.temp_dir.mkdir(parents=True, exist_ok=True)

    async def allocate_job_resources(self, job_id: str) -> JobResources:
        """Allocate resources for a job"""
        job_dir = self.temp_dir / job_id
        job_dir.mkdir(parents=True, exist_ok=True)

        return JobResources(
            job_dir=job_dir,
            temp_files=[],
            memory_limit="1GB",  # Could be configurable
            disk_limit="10GB"
        )

    async def cleanup_job_resources(self, job_id: str):
        """Clean up resources for a completed job"""
        job_dir = self.temp_dir / job_id
        if job_dir.exists():
            import shutil
            shutil.rmtree(job_dir)

    async def cleanup_old_resources(self, max_age_hours: int = 24):
        """Clean up temporary resources older than max_age_hours"""
        cutoff = time.time() - (max_age_hours * 60 * 60)

        for item in self.temp_dir.iterdir():
            if item.is_dir() and item.stat().st_mtime < cutoff:
                shutil.rmtree(item)

    def get_resource_usage(self) -> Dict[str, Any]:
        """Get current resource usage statistics"""
        # Implementation would check disk usage, memory, etc.
        return {
            "temp_dir_size": sum(f.stat().st_size for f in self.temp_dir.rglob("*") if f.is_file()),
            "active_jobs": len(list(self.temp_dir.iterdir())),
            "disk_free": shutil.disk_usage(self.base_dir).free
        }
```

### Error Recovery & Retry Logic

```python
class RetryManager:
    """Handle retries for failed operations"""

    def __init__(self, max_retries: int = 3, base_delay: float = 5.0):
        self.max_retries = max_retries
        self.base_delay = base_delay

    async def execute_with_retry(
        self,
        operation: Callable[[], Awaitable[T]],
        operation_name: str,
        job_id: str
    ) -> T:
        """Execute an operation with exponential backoff retry"""
        last_exception = None

        for attempt in range(self.max_retries + 1):
            try:
                return await operation()
            except Exception as e:
                last_exception = e

                if attempt < self.max_retries:
                    delay = self.base_delay * (2 ** attempt)  # Exponential backoff
                    logger.warning(f"{operation_name} failed (attempt {attempt + 1}), retrying in {delay}s: {e}")

                    # Update job status
                    await self._update_job_retry_status(job_id, attempt + 1, str(e))

                    await asyncio.sleep(delay)
                else:
                    logger.error(f"{operation_name} failed after {self.max_retries + 1} attempts: {e}")
                    raise last_exception

        raise last_exception  # Should not reach here

    async def _update_job_retry_status(self, job_id: str, attempt: int, error: str):
        """Update job metadata with retry information"""
        # Implementation would update job metadata with retry status
        pass
```

### CLI Examples for Restartability

```bash
# Start a long content analysis in background
storygen-iter job start --editor content --input manuscript.json --output feedback.json --background

# Check status
storygen-iter job status abc123-def456-ghi789

# Output:
# Job ID: abc123-def456-ghi789
# Status: running
# Editor: content
# Progress: 45.2%
# Stage: Processing batch 23/50
# Created: 2025-11-13 14:30:15
# Started: 2025-11-13 14:30:20
# Cost so far: $0.234
# Estimated completion: 2025-11-13 15:15:00

# Pause if needed
storygen-iter job pause abc123-def456-ghi789

# Resume later
storygen-iter job resume abc123-def456-ghi789

# Cancel if necessary
storygen-iter job cancel abc123-def456-ghi789

# List all jobs
storygen-iter job list

# List only running jobs
storygen-iter job list --status running
```

This restartability system ensures that editorial analyses can be interrupted and resumed without losing progress, making the system robust for long-running operations on lengthy manuscripts.

### Docker Configuration

```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/ ./src/
COPY config/ ./config/

# Create non-root user
RUN useradd --create-home --shell /bin/bash editorial
USER editorial

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

EXPOSE 8000

CMD ["python", "-m", "editorial.api"]
```

### Kubernetes Deployment

```yaml
# k8s/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: editorial-service
spec:
  replicas: 3
  selector:
    matchLabels:
      app: editorial
  template:
    metadata:
      labels:
        app: editorial
    spec:
      containers:
      - name: editorial
        image: editorial-service:latest
        ports:
        - containerPort: 8000
        env:
        - name: CONFIG_FILE
          value: "/app/config/production.yaml"
        resources:
          requests:
            memory: "1Gi"
            cpu: "500m"
          limits:
            memory: "2Gi"
            cpu: "1000m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
```

### Monitoring & Observability

```python
# monitoring/metrics.py
from prometheus_client import Counter, Histogram, Gauge

# Request metrics
REQUEST_COUNT = Counter(
    'editorial_requests_total',
    'Total number of editorial requests',
    ['editor_type', 'status']
)

REQUEST_LATENCY = Histogram(
    'editorial_request_duration_seconds',
    'Request duration in seconds',
    ['editor_type']
)

# Cost metrics
COST_TOTAL = Counter(
    'editorial_cost_total_usd',
    'Total editorial costs in USD',
    ['model']
)

# Quality metrics
QUALITY_SCORE = Gauge(
    'editorial_quality_score',
    'Average quality score for feedback',
    ['editor_type']
)

def record_request(editor_type: str, status: str, duration: float):
    """Record request metrics"""
    REQUEST_COUNT.labels(editor_type=editor_type, status=status).inc()
    REQUEST_LATENCY.labels(editor_type=editor_type).observe(duration)

def record_cost(model: str, cost_usd: float):
    """Record cost metrics"""
    COST_TOTAL.labels(model=model).inc(cost_usd)

def update_quality_score(editor_type: str, score: float):
    """Update quality metrics"""
    QUALITY_SCORE.labels(editor_type=editor_type).set(score)
```

## Implementation Roadmap

### Phase 1: Core Infrastructure (2-3 weeks)
1. **Base Classes & Interfaces**
   - Implement `BaseEditor`, `EditorialFeedback`, `StoryContext`
   - Create `ModelManager` with Ollama integration
   - Basic CLI structure

2. **Idea Editor**
   - Complete implementation with prompt engineering
   - Unit tests and integration tests
   - CLI command integration

3. **Configuration System**
   - YAML-based configuration
   - Environment-specific settings
   - Model management

### Phase 2: Content Analysis (3-4 weeks)
1. **Structural Editor**
   - Scene-sequel analysis
   - Causality chain validation
   - Batch processing

2. **Continuity Editor**
   - Character state tracking
   - Timeline validation
   - Location consistency

3. **Style Editor**
   - POV consistency checking
   - Filter word detection
   - Voice analysis

4. **Performance Optimization**
   - Caching system
   - Batch processing
   - Cost tracking

### Phase 3: Polish & Integration (2-3 weeks)
1. **Line Editor & Copyeditor**
   - Sentence-level polish
   - Grammar and style checking

2. **Proofreader**
   - Final typo detection
   - EPUB integration

3. **Quality Assurance**
   - Comprehensive test suite
   - Performance benchmarking
   - User feedback integration

### Phase 4: Advanced Features (Ongoing)
1. **Multi-Modal Support**
   - Image and audio analysis
   - Real-time collaborative editing

2. **API & Integrations**
   - REST API for external integrations
   - Third-party tool integrations

3. **Machine Learning Enhancements**
   - User preference learning
   - Quality improvement algorithms
   - Predictive analytics

## Success Metrics

### Technical Metrics
- **Performance**: <2 minutes for 5k-word analysis
- **Reliability**: 99.5% uptime, <1% error rate
- **Cost Efficiency**: <$0.50 per comprehensive analysis
- **Scalability**: Support 100+ concurrent analyses

### Quality Metrics
- **Accuracy**: 90%+ issue detection rate
- **Helpfulness**: 75%+ user satisfaction with suggestions
- **Consistency**: <5% variance in repeated analyses
- **False Positives**: <10% incorrect suggestions

### Business Metrics
- **Adoption**: 50%+ of users utilize editorial features
- **Retention**: 80%+ monthly active user retention
- **Revenue**: Positive ROI from premium editorial features

This implementation design provides a comprehensive blueprint for building a professional-grade AI-powered editorial system that scales from local development to production deployment.</content>
<parameter name="filePath">c:\Users\markc\Projects\short-story-gen-cli\docs\editorial-implementation.md
