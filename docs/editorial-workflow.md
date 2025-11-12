# Editorial Workflow Design

## Overview

This document outlines the planned editorial enhancement layers for the story generation pipeline. The editorial workflow mirrors professional publishing practices, with AI-powered editors providing feedback and revisions at appropriate stages.

## Current Pipeline (Implemented)

```
Idea → Characters → Locations → Outline → Breakdown → Prose (First Draft)
  ✅       ✅           ✅          ✅         ✅           ✅
```

## Editorial Enhancement Layers (Planned)

| Stage        | Editor Type                | Purpose                         | When to Engage  | Status |
| ------------ | -------------------------- | ------------------------------- | --------------- | ------ |
| Idea         | Developmental (consulting) | Test concept & theme            | Optional, early | 📋 Planned |
| Outline      | Developmental / Structural | Strengthen plot, character arcs | ✅ Ideal time    | 📋 Planned |
| First Draft  | None (beta readers)        | Finish the book                 | —               | ✅ Done |
| Second Draft | Developmental / Content    | Diagnose structure & logic      | ✅ Essential     | 📋 Planned |
| Third Draft  | Line Editor                | Polish voice, rhythm            | ✅               | 📋 Planned |
| Final Draft  | Copyeditor                 | Correct mechanics               | ✅               | 📋 Planned |
| Proofs       | Proofreader                | Catch typos before print        | ✅               | 📋 Planned |

---

## 1. Developmental Editor (Post-Outline) - Structural Phase

**Priority:** Medium
**Engagement Point:** After `outline` command, before `breakdown`

### Purpose
Analyze the story outline for structural integrity, character arc alignment, and thematic consistency. Catch high-level plot holes before investing in scene-level work.

### Responsibilities
- **Plot Structure**: Verify beats hit at proper story percentages
- **Character Arcs**: Ensure character development aligns with themes and goals
- **Pacing Analysis**: Check if conflict escalates appropriately across acts
- **Theme Coherence**: Verify thematic elements are woven throughout structure
- **Causality Chain**: Ensure each act logically leads to the next

### Implementation Sketch

```python
class OutlineEditor:
    """Analyzes outline for plot holes, character arc issues, pacing problems"""

    def __init__(self, model: str, max_retries: int = 3, verbose: bool = False):
        self.model = model
        self.max_retries = max_retries
        self.verbose = verbose

    def analyze(
        self,
        story_idea: StoryIdea,
        characters: list[Character],
        outline: Outline
    ) -> OutlineEditorialFeedback:
        """
        Analyze outline for structural issues.

        Returns:
            OutlineEditorialFeedback with:
            - plot_holes: List of logical inconsistencies
            - character_arc_issues: Character development problems
            - pacing_issues: Acts too rushed or too slow
            - theme_gaps: Missing thematic beats
            - suggestions: Specific revisions (add/remove/reorder acts)
        """
        pass
```

### CLI Integration

```bash
# Generate editorial feedback on outline
storygen-iter edit-outline \
  -i idea.json \
  -c characters.json \
  --outline outline.json \
  --model ollama/qwen3:30b \
  -o outline_feedback.json \
  -v

# Optionally: Auto-revise based on feedback
storygen-iter revise-outline \
  --outline outline.json \
  --feedback outline_feedback.json \
  --model ollama/qwen3:30b \
  -o outline_revised.json
```

### Output Format

```json
{
  "editorial_feedback": {
    "overall_assessment": "Strong concept but pacing needs work in Act 2",
    "plot_structure": {
      "score": 7,
      "issues": [
        "Act 2 midpoint at 42% (should be closer to 50%)",
        "Climax feels rushed - only 5% of story"
      ],
      "strengths": [
        "Inciting incident hits at perfect 12% mark",
        "Dark night of soul properly placed at 75%"
      ]
    },
    "character_arcs": {
      "score": 8,
      "issues": [
        "Marcus Reed introduced but never pays off - resolve or cut",
        "Protagonist's internal flaw (trust issues) not connected to climax"
      ],
      "strengths": [
        "Clear want vs need for protagonist",
        "Antagonist motivation well-established"
      ]
    },
    "pacing": {
      "score": 6,
      "issues": [
        "Act 1 too slow (30% of story for setup)",
        "Act 2 rushes through 5 major reveals"
      ]
    },
    "theme_coherence": {
      "score": 9,
      "issues": [],
      "strengths": [
        "Mind-reading metaphor for trust consistently developed",
        "Technology vs humanity theme woven throughout"
      ]
    },
    "suggested_revisions": [
      {
        "type": "expand",
        "target": "Act 2 - Rising Action",
        "reason": "Give more breathing room for reveals",
        "suggestion": "Split 'Confrontation' beat into two separate acts"
      },
      {
        "type": "add",
        "target": "Act 2 - After 'First Attempt'",
        "reason": "Need character reflection beat",
        "suggestion": "Add sequel beat where protagonist processes failure"
      },
      {
        "type": "reorder",
        "target": "Act 3 - 'Final Revelation' and 'Climax'",
        "reason": "Revelation should trigger climax, not precede it",
        "suggestion": "Move revelation to midpoint of climax sequence"
      }
    ]
  }
}
```

---

## 2. Developmental Editor (Post-First Draft) - Content Phase

**Priority:** HIGH (Most impactful)
**Engagement Point:** After `prose` command, before revisions

### Purpose
Deep analysis of completed prose for structure, logic, character consistency, and scene-level pacing. This is the most critical editorial phase for story quality.

### Responsibilities
- **Scene Causality**: Verify scene-sequel chain maintains cause-and-effect
- **Character Consistency**: Track character voice, motivation, and behavior across scenes
- **Continuity Tracking**: Catch timeline errors, location inconsistencies, contradictions
- **Pacing Analysis**: Identify rushed or dragging sections based on word count and content density
- **POV Issues**: Detect POV breaks, head-hopping, filter words
- **Emotional Beats**: Ensure emotional arc flows naturally scene to scene

### Implementation Sketch

```python
class ContentEditor:
    """Deep analysis of completed prose for structure & logic issues"""

    def __init__(self, model: str, max_retries: int = 3, verbose: bool = False):
        self.model = model
        self.max_retries = max_retries
        self.verbose = verbose

    def analyze(
        self,
        story_idea: StoryIdea,
        characters: list[Character],
        locations: list[Location],
        scene_sequels: list[SceneSequel]
    ) -> ContentEditorialFeedback:
        """
        Analyze completed prose for structural and logical issues.

        Processes scene-sequels in sequence, building context of:
        - Character states (emotions, knowledge, physical condition)
        - Plot threads (open vs resolved)
        - Timeline tracking
        - Location transitions

        Returns:
            ContentEditorialFeedback with:
            - structure_issues: Scene causality breaks, missing sequels
            - character_issues: Inconsistent behavior, unresolved arcs
            - continuity_errors: Timeline problems, contradictions
            - pacing_issues: Scenes too long/short relative to importance
            - pov_issues: Filter words, head-hopping, inconsistent voice
            - suggested_revisions: Scene-specific revision instructions
        """
        pass

    def _analyze_scene_causality(self, scene_sequels: list[SceneSequel]) -> list[Issue]:
        """Check that disasters lead to sequels, decisions lead to new scenes"""
        pass

    def _track_character_consistency(
        self,
        characters: list[Character],
        scene_sequels: list[SceneSequel]
    ) -> list[Issue]:
        """Track character knowledge, emotions, physical state across scenes"""
        pass

    def _check_continuity(self, scene_sequels: list[SceneSequel]) -> list[Issue]:
        """Verify timeline, locations, and details stay consistent"""
        pass
```

### CLI Integration

```bash
# Generate content editorial feedback
storygen-iter edit-content \
  -i idea.json \
  -c characters.json \
  -l locations.json \
  --prose prose.json \
  --model ollama/qwen3:30b \
  -o content_feedback.json \
  -v

# Revise specific scenes based on feedback
storygen-iter revise-prose \
  --prose prose.json \
  --feedback content_feedback.json \
  --scenes ss_007,ss_012,ss_015 \
  --model ollama/qwen3:30b \
  -o prose_revised.json \
  -v
```

### Output Format

```json
{
  "editorial_feedback": {
    "overall_assessment": "Strong prose but several continuity issues and pacing problems in Act 2",
    "structure_issues": [
      {
        "scene_id": "ss_007",
        "severity": "major",
        "type": "unclear_goal",
        "description": "Scene goal is vague - what specifically is Elara trying to achieve?",
        "suggestion": "Clarify that she's attempting to read Marcus's guilt about a specific detail"
      },
      {
        "scene_id": "ss_012",
        "severity": "major",
        "type": "missing_causality",
        "description": "Transition from ss_012 to ss_013 is abrupt - no clear decision leads to next scene",
        "suggestion": "Add decision in ss_012 sequel where Elara chooses to confront Silas directly"
      },
      {
        "scene_id": "ss_009",
        "severity": "minor",
        "type": "weak_disaster",
        "description": "Scene disaster feels anticlimactic - Dr. Aris just... tells her information",
        "suggestion": "Consider Dr. Aris refusing to help, forcing Elara to find another way"
      }
    ],
    "character_issues": [
      {
        "character": "Marcus Reed",
        "severity": "major",
        "type": "unresolved_arc",
        "description": "Marcus appears in ss_001 and ss_007, then vanishes - his arc incomplete",
        "suggestion": "Either resolve his subplot (add scene where Elara reconciles) or explain his absence"
      },
      {
        "character": "Detective Elara Vance",
        "scene_id": "ss_011",
        "severity": "minor",
        "type": "inconsistent_behavior",
        "description": "Elara suddenly trusts Dr. Aris after distrusting everyone - no character beat justifying shift",
        "suggestion": "Add internal monologue showing why this moment changes her perspective"
      }
    ],
    "continuity_errors": [
      {
        "scenes": ["ss_005", "ss_006"],
        "severity": "minor",
        "type": "weather_inconsistency",
        "description": "ss_005 mentions heavy rain at Rain-Slicked Alley, ss_006 at Silent Apartment has no rain sounds",
        "suggestion": "Add rain sounds to apartment window or explain time has passed"
      },
      {
        "scenes": ["ss_003", "ss_011"],
        "severity": "minor",
        "type": "location_detail",
        "description": "Silent Market described as 'bustling' in ss_003 but 'deserted' in ss_011 at same time of day",
        "suggestion": "Either change time of day or explain why market emptied"
      }
    ],
    "pacing_issues": [
      {
        "act": "Act 2 - Rising Action",
        "severity": "major",
        "description": "Act 2 rushes through critical reveals (800 words) while Act 1 setup drags (600 words)",
        "affected_scenes": ["ss_007", "ss_008", "ss_009"],
        "suggestion": "Expand ss_008 and ss_009 by 100-150 words each to give emotional beats room to breathe"
      },
      {
        "scene_id": "ss_015",
        "severity": "minor",
        "description": "Climax scene at 160 words feels rushed for story's biggest moment",
        "suggestion": "Expand to 250-300 words - add sensory details, slow down the confrontation"
      }
    ],
    "pov_issues": [
      {
        "scene_id": "ss_004",
        "severity": "minor",
        "type": "filter_word",
        "description": "Overuse of 'she felt' and 'she thought' - distances reader from Elara's experience",
        "examples": ["she felt the terror", "she thought about dying"],
        "suggestion": "Direct internal monologue: *Terror clawed at her chest* instead of 'she felt terror'"
      }
    ],
    "suggested_revisions": [
      {
        "scene_id": "ss_007",
        "revision_type": "rewrite",
        "priority": "high",
        "reason": "Goal unclear, disaster weak",
        "instruction": "Clarify Elara's specific goal (read Marcus's memory of who killed her) and make disaster more concrete (her power backfires, showing her own guilt instead)"
      },
      {
        "scene_id": "ss_012",
        "revision_type": "expand",
        "priority": "high",
        "reason": "Missing emotional processing and decision",
        "instruction": "Add 100-150 words of Elara processing Silas's betrayal, then making explicit decision to confront him at lighthouse",
        "target_word_count": 250
      },
      {
        "scene_id": "ss_015",
        "revision_type": "expand",
        "priority": "medium",
        "reason": "Climax feels rushed",
        "instruction": "Slow down confrontation with sensory details, add back-and-forth dialogue, show Elara's internal struggle before final choice",
        "target_word_count": 300
      },
      {
        "scene_id": "new_scene_after_ss_007",
        "revision_type": "add",
        "priority": "high",
        "reason": "Marcus Reed arc unresolved",
        "instruction": "Add 150-word sequel where Elara realizes Marcus was trying to protect her, resolving his character arc"
      }
    ]
  }
}
```

---

## 3. Line Editor (Third Draft)

**Priority:** Medium
**Engagement Point:** After content revisions, before copyediting

### Purpose
Polish voice, rhythm, and sentence-level craft. Focus on how the story is told rather than what is told.

### Responsibilities
- **Sentence Variety**: Analyze sentence length and structure patterns
- **Rhythm & Flow**: Check paragraph pacing, dialogue balance
- **Voice Consistency**: Ensure narrative voice stays consistent
- **Show vs Tell**: Identify opportunities to show emotion/action instead of telling
- **Word Choice**: Suggest stronger verbs, more specific nouns
- **Dialogue Polish**: Improve subtext, eliminate on-the-nose dialogue

### Implementation Sketch

```python
class LineEditor:
    """Polish voice, rhythm, sentence structure"""

    def edit(
        self,
        scene_sequels: list[SceneSequel],
        writing_style: str
    ) -> LineEditorialRevisions:
        """
        Analyze and improve sentence-level craft.

        Returns:
            LineEditorialRevisions with:
            - sentence_variety_issues: Repetitive structures
            - rhythm_issues: Monotonous pacing
            - voice_inconsistencies: Tone shifts
            - show_dont_tell_suggestions: Specific rewrites
            - dialogue_improvements: Subtext and realism fixes
            - revised_prose: Scene-by-scene polished versions
        """
        pass
```

### Output Format

```json
{
  "line_edits": {
    "scene_id": "ss_001",
    "edits": [
      {
        "line_number": 3,
        "original": "She felt overwhelmed by the noise in her head.",
        "revised": "The noise in her head *screamed*—a thousand voices clawing for attention.",
        "reason": "Show don't tell - demonstrate overwhelm through metaphor",
        "category": "show_dont_tell"
      },
      {
        "line_number": 7,
        "original": "Marcus said, 'I don't believe you can really read minds.'",
        "revised": "Marcus crossed his arms. 'Convenient, your power failing right when we need proof.'",
        "reason": "Add subtext - show his skepticism through implication, not direct statement",
        "category": "dialogue_subtext"
      },
      {
        "line_number": 12,
        "original": "The interrogation room was cold. The lights were bright. The suspect looked nervous.",
        "revised": "The interrogation room's fluorescent glare turned the suspect's sweat to mercury.",
        "reason": "Combine choppy sentences, use stronger imagery",
        "category": "sentence_variety"
      }
    ]
  }
}
```

---

## 4. Copyeditor (Final Draft)

**Priority:** Medium
**Engagement Point:** After line editing, before proofreading

### Purpose
Correct grammar, spelling, punctuation, and internal consistency. Ensure style guide compliance.

### Responsibilities
- **Grammar & Mechanics**: Fix grammatical errors, punctuation issues
- **Spelling**: Catch typos, ensure consistency (e.g., "mind-reading" vs "mindreading")
- **Internal Consistency**: Character names, location details, timeline
- **Style Guide Compliance**: Chicago Manual of Style, dialogue formatting rules
- **Fact Checking**: Verify real-world details are accurate

### Implementation Sketch

```python
class CopyEditor:
    """Grammar, spelling, continuity, style guide compliance"""

    def edit(
        self,
        scene_sequels: list[SceneSequel],
        style_guide: str = "chicago"  # or "ap", "mla"
    ) -> CopyEditorialCorrections:
        """
        Check and correct mechanical errors and consistency.

        Returns:
            CopyEditorialCorrections with:
            - grammar_errors: Specific corrections with line numbers
            - spelling_errors: Typos and inconsistencies
            - punctuation_fixes: Comma splices, missing periods, etc.
            - consistency_issues: Name variations, detail contradictions
            - style_guide_violations: Formatting issues
        """
        pass
```

---

## 5. Proofreader (Proofs)

**Priority:** Low
**Engagement Point:** After EPUB generation, before final export

### Purpose
Final typo catching on formatted text. Last line of defense before publication.

### Responsibilities
- **Typo Detection**: Catch remaining spelling errors
- **Formatting Errors**: Extra spaces, malformed quotes, line breaks
- **EPUB-Specific Issues**: Broken links, malformed HTML, CSS problems
- **Visual Checks**: Confirm chapter breaks, scene transitions display correctly

### Implementation Sketch

```python
class Proofreader:
    """Final typo catching before EPUB export"""

    def proof(
        self,
        epub_content: str,
        scene_sequels: list[SceneSequel]
    ) -> ProofreadingCorrections:
        """
        Final pass for typos and formatting issues.

        Returns:
            ProofreadingCorrections with:
            - remaining_typos: Last-minute spelling errors
            - formatting_errors: Spacing, quote issues
            - epub_issues: HTML/CSS problems
        """
        pass
```

---

## Implementation Priority

### Phase 1 (Next Sprint)
1. **Content Editor** - Highest value for story quality
2. Unit tests for Content Editor
3. CLI integration for content editing

### Phase 2 (Future)
1. **Outline Editor** - Catch issues early
2. **Line Editor** - Polish prose quality
3. Unit tests for both

### Phase 3 (Polish)
1. **Copyeditor** - Mechanical corrections
2. **Proofreader** - Final EPUB pass
3. Integration with EPUB export pipeline

---

## Key Design Principles

### 1. Surgical Revisions
The scene-sequel structure enables **targeted revisions**:
- Regenerate single scenes based on feedback
- Preserve surrounding context
- No need to regenerate entire story

### 2. Iterative Improvement
Support multiple editorial passes:
```bash
# First pass
storygen-iter edit-content --prose prose.json -o feedback_v1.json
storygen-iter revise-prose --prose prose.json --feedback feedback_v1.json -o prose_v2.json

# Second pass after reviewing v2
storygen-iter edit-content --prose prose_v2.json -o feedback_v2.json
storygen-iter revise-prose --prose prose_v2.json --feedback feedback_v2.json -o prose_v3.json
```

### 3. Human-in-the-Loop
Editorial feedback is **advisory**, not mandatory:
- Review feedback JSON
- Manually edit if AI suggestions miss the mark
- Cherry-pick which scenes to regenerate
- Preserve human creative control

### 4. Context Preservation
Each editor has access to full story context:
- Story idea (themes, tone)
- Character profiles (arcs, goals)
- Location details (atmosphere)
- Outline structure (plot beats)
- Previous editorial feedback (learning from past issues)

### 5. Explainable Feedback
All feedback includes:
- **Severity**: major/minor to prioritize fixes
- **Category**: structure/character/pacing/continuity for filtering
- **Specific Examples**: Line numbers, quoted text
- **Actionable Suggestions**: Concrete revision instructions, not vague advice

---

## Data Models

### EditorialFeedback (Base)
```python
@dataclass
class EditorialIssue:
    severity: Literal["major", "minor"]
    category: str  # structure, character, pacing, continuity, pov, etc.
    description: str
    suggestion: str
    scene_ids: list[str] | None = None
    line_numbers: list[int] | None = None

@dataclass
class EditorialFeedback:
    overall_assessment: str
    issues: list[EditorialIssue]
    suggested_revisions: list[RevisionSuggestion]
    strengths: list[str]  # Positive reinforcement
```

### RevisionSuggestion
```python
@dataclass
class RevisionSuggestion:
    scene_id: str | None  # None for "add new scene"
    revision_type: Literal["rewrite", "expand", "cut", "reorder", "add"]
    priority: Literal["high", "medium", "low"]
    reason: str
    instruction: str  # Detailed guidance for AI regeneration
    target_word_count: int | None = None
    insert_after: str | None = None  # For "add" type
```

---

## Future Enhancements

### AI Editor Training
- Fine-tune models on editorial feedback examples
- Train on before/after revision pairs
- Improve feedback specificity over time

### Multi-Model Editing
- Use different models for different editorial stages
- Larger models for deep analysis, smaller for grammar checks
- Ensemble feedback from multiple models

### Batch Processing
- Edit multiple scenes in parallel
- Generate feedback for entire acts at once
- Smart batching based on dependencies

### Version Control
- Track all editorial passes
- Allow rollback to previous versions
- Compare drafts side-by-side
- Generate "track changes" view

### Custom Style Guides
- User-defined rules (Oxford comma preference, etc.)
- Genre-specific guidelines
- Author voice preservation training

---

## Related Documentation
- [Iterative Generation](./iterative-generation.md) - Core pipeline architecture
- [Migrations](./migrations.md) - Version compatibility for editorial data models
