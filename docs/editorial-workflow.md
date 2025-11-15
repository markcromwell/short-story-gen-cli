# Editorial Workflow Design

## Overview

This document outlines the planned editorial enhancement layers for the story generation pipeline. The editorial workflow mirrors professional publishing practices, with AI-powered editors providing feedback and revisions at appropriate stages.

## Current Pipeline (Implemented)

```
Idea → Characters → Locations → Outline → Breakdown → Prose (First Draft)
  ✅       ✅           ✅          ✅         ✅           ✅
```

## Editorial Leverage Principle: Early Detection = Exponential Savings

**The earlier you catch a problem, the easier (and cheaper) it is to fix.**

### Cascading Invalidation Effect
Changes at early stages invalidate everything downstream:

```
🔴 Change IDEA → Regenerate: Characters + Locations + Outline + Prose (100% invalidation)
🟡 Change OUTLINE → Regenerate: Prose only (25% invalidation)
🟢 Change PROSE → Regenerate: Nothing (0% invalidation, surgical fixes)
```

### Cost Multipliers
- **Idea-level fix**: 1x cost (just revise the concept)
- **Outline-level fix**: 5x cost (regenerate prose from outline)
- **Prose-level fix**: 10x cost (rewrite specific scenes, but AI costs add up)

### Quality Leverage
Early editors have **higher leverage** for quality improvement:
- **Idea Editor**: Prevents bad stories from ever being written
- **Outline Editor**: Catches structural issues before prose investment
- **Content Editors**: Polish already-written prose (important but less leverage)

## Enhanced Collaborative Workflow (Planned)

The workflow emphasizes **prevention over cure** with robust early-stage validation:

### Phase 1: Idea Development (Interactive)
**User Input:** Initial story concept/pitch
**AI Role:** Suggest expansions for missing elements
**User Control:** Accept/reject/modify AI suggestions
**Protection:** User-approved content becomes protected

```
User Pitch → AI Expansion Suggestions → User Review → Protected Idea
     ↓              ↓                        ↓              ↓
  "A detective    "Add mystery tone,      Accept tone,    "A hard-boiled
   solves a case"   short story length,     reject genre    detective solves
                    noir genre, Fichtean     suggestion     a case in 1940s
                    structure"                              New York"
```

### Phase 2: Outline Construction (Manual + AI)
**User Input:** Manual scene addition or AI generation requests
**AI Role:** Generate scene suggestions, validate structure
**User Control:** Override any scene/sequel, rearrange order
**Protection:** User-created scenes marked as protected

```
Protected Idea → Scene Addition → AI Validation → Protected Outline
     ↓                ↓              ↓              ↓
  "Hard-boiled      User adds "Detective  AI suggests      "Scene 1: Detective
   detective..."     interrogates suspect"  adding sequel    interrogates suspect
                     scene                scene          (protected)
```

### Phase 3: Content Development (Protected Writing)
**User Input:** Write prose for any scene/sequel
**AI Role:** Generate suggestions for empty scenes, analyze completed work
**User Control:** Manual writing takes precedence, AI suggestions advisory
**Protection:** User-written prose protected from AI overwrites

```
Protected Outline → Prose Development → AI Analysis → Protected Manuscript
     ↓                    ↓                  ↓                ↓
  "Scene 1: Detective   User writes scene   AI suggests      "The rain-slicked
   interrogates..."      content            improvements      streets of New York
                        (protected)        but can't         glistened under
                                           overwrite         the neon signs..."
```

### Phase 4: Editorial Enhancement (Advisory AI)
**User Input:** Review AI feedback on protected content
**AI Role:** Provide editorial suggestions without overwriting
**User Control:** Accept/reject/modify all suggestions manually
**Protection:** All user content remains protected

```
Protected Manuscript → AI Editorial → User Review → Enhanced Manuscript
     ↓                      ↓              ↓                ↓
  "The rain-slicked...    AI suggests       User accepts     "The rain-slicked
   "                      "show don't tell"  some changes,     streets of New York
                         for description     modifies others   glistened under
                         (advisory only)                      the harsh neon
                                                              glare..."
```

## Current Implementation Status

### ✅ Implemented (Post-Prose Analysis)
- **Structural Editor**: Analyzes scene-sequel chains and plot logic
- **Continuity Editor**: Tracks character states, locations, and timeline consistency
- **Style Editor**: Analyzes POV consistency, filter words, and narrative voice
- **Comprehensive Editor**: Combines all three specialized editors
- **Human Language Reports**: All editors generate readable summaries for users
- **CLI Commands**: Separate editorial CLI available (`storygen-iter edit analyze <file>`)

### ❌ Not Implemented (Pre-Prose Analysis)
- **Idea Editor**: Concept critique before character generation
- **Outline Editor**: Structural analysis before prose writing

### 🔄 Partially Implemented
- **Pipeline Integration**: Editorial placeholders exist in main pipeline but editors not yet integrated
- **Revision Application**: Basic revision logic exists but not fully integrated with pipeline

## Enhanced Collaborative Workflow (Planned)

| Stage        | Editor Type                | Purpose                         | When to Engage  | Status |
| ------------ | -------------------------- | ------------------------------- | --------------- | ------ |
| Idea         | Developmental (consulting) | Test concept & theme            | ✅ Essential     | 📋 Planned |
| Outline      | Developmental / Structural | Strengthen plot, character arcs | ✅ Ideal time    | 📋 Planned |
| First Draft  | None (beta readers)        | Finish the book                 | —               | ✅ Done |
| Second Draft | Developmental / Content    | Diagnose structure & logic      | ✅ Essential     | ✅ Implemented |
| Third Draft  | Line Editor                | Polish voice, rhythm            | ✅               | 📋 Planned |
| Final Draft  | Copyeditor                 | Correct mechanics               | ✅               | 📋 Planned |
| Proofs       | Proofreader                | Catch typos before print        | ✅               | 📋 Planned |

---

## 0. Idea Editor (Pre-Generation) - Concept Phase

**Priority:** HIGH (Foundation for everything)
**Engagement Point:** After initial idea generation, before character creation

### Purpose
Critique the story concept at its earliest stage to ensure the foundation is strong. This is the most impactful editorial phase because weak ideas cannot be saved by good execution.

### Responsibilities
- **Hook Analysis**: Evaluate if the one-sentence summary has a compelling hook
- **Concept Uniqueness**: Check for originality and fresh angles
- **Emotional Core**: Verify stakes, emotional investment, and reader empathy
- **Scope Assessment**: Ensure concept fits target word count and complexity
- **Theme Depth**: Analyze thematic richness and resonance
- **Market Viability**: Assess commercial and literary potential

### Implementation Sketch

```python
class IdeaEditor:
    """Critiques story concepts for strength, originality, and viability"""

    def __init__(self, model: str, max_retries: int = 3, verbose: bool = False):
        self.model = model
        self.max_retries = max_retries
        self.verbose = verbose

    def analyze(self, story_idea: StoryIdea) -> IdeaEditorialFeedback:
        """
        Analyze story idea for conceptual strength and market potential.

        Returns:
            IdeaEditorialFeedback with:
            - hook_strength: Analysis of one-sentence summary
            - concept_originality: Uniqueness assessment
            - emotional_engagement: Reader investment potential
            - scope_appropriateness: Fit for target length/format
            - thematic_depth: Theme richness and resonance
            - market_potential: Commercial viability
            - suggested_revisions: Concept improvements
        """
        pass
```

### CLI Integration

```bash
# Generate editorial feedback on story idea
storygen-iter edit-idea \
  --idea idea.json \
  --model ollama/qwen3:30b \
  -o idea_feedback.json \
  -v

# Revise idea based on feedback
storygen-iter revise-idea \
  --idea idea.json \
  --feedback idea_feedback.json \
  --model ollama/qwen3:30b \
  -o idea_revised.json
```

### Output Format

```json
{
  "editorial_feedback": {
    "overall_assessment": "Solid concept with strong emotional core but needs more unique hook",
    "hook_analysis": {
      "score": 6,
      "issues": [
        "One-sentence lacks specificity - 'detective solves crimes' is too generic",
        "No unique constraint or twist that makes THIS story compelling"
      ],
      "strengths": [
        "Clear protagonist role and core conflict",
        "Emotional stakes are present"
      ]
    },
    "concept_originality": {
      "score": 7,
      "issues": [
        "Telepath detective concept exists but resurrection twist is fresh"
      ],
      "strengths": [
        "Combines familiar tropes in novel way",
        "Time pressure creates unique tension"
      ]
    },
    "emotional_engagement": {
      "score": 8,
      "issues": [],
      "strengths": [
        "Personal stakes (protagonist's own death)",
        "Trust/betrayal themes create reader empathy",
        "Moral dilemma forces character growth"
      ]
    },
    "scope_assessment": {
      "score": 9,
      "issues": [],
      "strengths": [
        "24-hour timeframe fits short story format perfectly",
        "Single POV keeps scope manageable",
        "Investigation plot allows natural pacing"
      ]
    },
    "thematic_depth": {
      "score": 7,
      "issues": [
        "Trust theme could be deeper - explore institutional vs personal betrayal"
      ],
      "strengths": [
        "Technology vs humanity dichotomy well-established",
        "Identity questions raised by resurrection"
      ]
    },
    "market_potential": {
      "score": 8,
      "issues": [],
      "strengths": [
        "Mystery/thriller genre has strong market",
        "Supernatural elements appeal to genre readers",
        "Short story length suits online publication"
      ]
    },
    "suggested_revisions": [
      {
        "type": "strengthen_hook",
        "target": "one_sentence",
        "reason": "Hook needs more specificity and uniqueness",
        "suggestion": "Add resurrection window constraint: 'A telepath detective must solve her own murder before her 24-hour resurrection window closes'",
        "expected_impact": "Creates urgency and unique premise"
      },
      {
        "type": "deepen_theme",
        "target": "themes",
        "reason": "Trust theme could be more nuanced",
        "suggestion": "Add 'identity' theme - resurrection raises questions about what makes someone 'them'",
        "expected_impact": "Adds philosophical depth"
      },
      {
        "type": "expand_concept",
        "target": "expanded",
        "reason": "World-building could be richer",
        "suggestion": "Add details about resurrection technology costs, societal attitudes, and legal implications",
        "expected_impact": "Makes world feel more lived-in"
      }
    ]
  }
}
```

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

### Split into Focused Editors

To avoid scope creep, the Content Editor is split into three specialized editors:

#### 2.1 Structural Editor (Scene-Sequel Logic)
**Focus:** Plot causality, scene goals, disaster-consequence chains

#### 2.2 Continuity Editor (Timeline & Details)
**Focus:** Character consistency, location transitions, timeline accuracy

#### 2.3 Style Editor (POV & Voice)
**Focus:** Point of view consistency, filter words, emotional beats

### Implementation Sketch

```python
class StructuralEditor:
    """Analyzes scene-sequel chains and plot logic"""

    def analyze_scene_causality(self, scene_sequels: list[SceneSequel]) -> list[Issue]:
        """Check that disasters lead to sequels, decisions lead to new scenes"""
        pass

class ContinuityEditor:
    """Tracks character states, locations, and timeline consistency"""

    def track_character_consistency(
        self,
        characters: list[Character],
        scene_sequels: list[SceneSequel]
    ) -> list[Issue]:
        """Track character knowledge, emotions, physical state across scenes"""
        pass

    def check_timeline_continuity(self, scene_sequels: list[SceneSequel]) -> list[Issue]:
        """Verify timeline, locations, and details stay consistent"""
        pass

class StyleEditor:
    """Analyzes POV consistency, filter words, and narrative voice"""

    def analyze_pov_consistency(self, scene_sequels: list[SceneSequel]) -> list[Issue]:
        """Check for head-hopping, filter words, voice shifts"""
        pass
```

### Error Handling & Edge Cases

Each editor includes robust error handling:

```python
class ContentEditor:
    def analyze_with_fallback(self, scene_sequels: list[SceneSequel]) -> EditorialFeedback:
        """Analyze with graceful degradation if AI fails"""
        try:
            return self.analyze(scene_sequels)
        except AIModelError:
            return self.fallback_analysis(scene_sequels)
        except ValidationError as e:
            logger.warning(f"Content analysis failed: {e}")
            return EditorialFeedback(
                overall_assessment="Analysis incomplete due to technical issues",
                issues=[EditorialIssue(
                    severity="minor",
                    category="technical",
                    description=f"Could not complete analysis: {e}",
                    suggestion="Try again or proceed with manual review"
                )],
                suggested_revisions=[],
                strengths=[]
            )
```

### Performance Considerations

- **Token Limits:** Process scenes in batches to avoid context overflow
- **Caching:** Cache analysis results for unchanged scenes
- **Progressive Analysis:** Start with structural issues, then continuity, then style
- **Cost Estimation:** Track token usage and provide cost warnings

### CLI Integration

```bash
# Analyze specific aspects
storygen-iter edit-content --structural \
  --prose prose.json \
  --model ollama/qwen3:30b \
  -o structural_feedback.json

storygen-iter edit-content --continuity \
  --prose prose.json \
  --model ollama/qwen3:30b \
  -o continuity_feedback.json

storygen-iter edit-content --style \
  --prose prose.json \
  --model ollama/qwen3:30b \
  -o style_feedback.json

# Or analyze all aspects
storygen-iter edit-content --comprehensive \
  --prose prose.json \
  --model ollama/qwen3:30b \
  -o content_feedback.json \
  --budget-warning  # Warn if analysis will exceed token budget
```

### Quality Metrics

**Success Criteria:**
- **Structural Score:** 80%+ of scenes have clear goals and disasters
- **Continuity Score:** <5 continuity errors per 1000 words
- **Style Score:** <3 POV breaks per scene
- **User Satisfaction:** 70%+ of suggestions deemed helpful

**Automated Testing:**
```python
def test_editor_quality(editor: ContentEditor, test_corpus: list[SceneSequel]):
    """Test editor against known good/bad examples"""
    results = editor.analyze(test_corpus)
    assert results.overall_score >= 7.0, "Editor quality below threshold"
    assert len(results.issues) <= expected_max_issues, "Too many false positives"
```

### Output Format

```json
{
  "editorial_feedback": {
    "overall_assessment": "Strong prose but several continuity issues and pacing problems in Act 2",
    "structural_score": 8.5,
    "continuity_score": 6.2,
    "style_score": 7.8,
    "estimated_cost": {"tokens": 12500, "cost_usd": 0.25},
    "analysis_time_seconds": 45.2,
    "structure_issues": [
      {
        "scene_id": "ss_007",
        "severity": "major",
        "type": "unclear_goal",
        "description": "Scene goal is vague - what specifically is Elara trying to achieve?",
        "suggestion": "Clarify that she's attempting to read Marcus's guilt about a specific detail"
      }
    ],
    "continuity_issues": [
      {
        "character": "Marcus Reed",
        "severity": "major",
        "type": "unresolved_arc",
        "description": "Marcus appears in ss_001 and ss_007, then vanishes - his arc incomplete",
        "suggestion": "Either resolve his subplot or explain his absence"
      }
    ],
    "style_issues": [
      {
        "scene_id": "ss_004",
        "severity": "minor",
        "type": "filter_word",
        "description": "Overuse of 'she felt' distances reader from Elara's experience",
        "examples": ["she felt the terror"],
        "suggestion": "Use direct internal monologue: *Terror clawed at her chest*"
      }
    ],
    "suggested_revisions": [
      {
        "scene_id": "ss_007",
        "revision_type": "rewrite",
        "priority": "high",
        "reason": "Goal unclear, disaster weak",
        "instruction": "Clarify Elara's specific goal and make disaster more concrete",
        "estimated_tokens": 800
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

## Error Handling & Edge Cases

### AI Model Failures
**Graceful Degradation:** If AI analysis fails, provide fallback feedback:
```python
def analyze_with_fallback(self, content: Any) -> EditorialFeedback:
    try:
        return self.analyze(content)
    except AIModelError as e:
        logger.warning(f"AI analysis failed: {e}")
        return EditorialFeedback(
            overall_assessment="Analysis could not be completed due to technical issues",
            issues=[EditorialIssue(
                severity="info",
                category="technical",
                description="AI model unavailable - manual review recommended",
                suggestion="Please review manually or try again later"
            )],
            suggested_revisions=[],
            strengths=["Content appears structurally sound"]
        )
```

### Content Validation Errors
**Input Validation:** Check for malformed or incomplete data:
```python
def validate_input(self, scene_sequels: list[SceneSequel]) -> list[str]:
    """Return list of validation errors, empty if valid"""
    errors = []
    if not scene_sequels:
        errors.append("No scene-sequels provided")
    for ss in scene_sequels:
        if not ss.scene_goal:
            errors.append(f"Scene {ss.id} missing goal")
        if not ss.disaster and not ss.decision:
            errors.append(f"Scene-Sequel {ss.id} missing disaster or decision")
    return errors
```

### Rate Limiting & Cost Control
**Budget Warnings:** Alert users before expensive operations:
```bash
# Warn if analysis will exceed token budget
storygen-iter edit-content --prose prose.json \
  --budget-warning \
  --max-tokens 10000 \
  --model gpt-4o  # Expensive model
```

### Edge Cases Handled
- **Empty Stories:** Single-scene stories, incomplete outlines
- **Long Stories:** Batch processing for 50k+ word manuscripts
- **Complex Characters:** Multiple POV characters, unreliable narrators
- **Genre Variations:** Literary fiction vs genre fiction analysis rules
- **Cultural Context:** Region-specific dialogue and cultural references

---

## Quality Metrics & Success Criteria

### Automated Quality Scoring
```python
class EditorialQualityMetrics:
    def score_feedback(self, feedback: EditorialFeedback) -> QualityScore:
        """Calculate quality metrics for editorial feedback"""
        return QualityScore(
            specificity_score=self._calculate_specificity(feedback),
            actionability_score=self._calculate_actionability(feedback),
            false_positive_rate=self._estimate_false_positives(feedback),
            user_satisfaction_estimate=self._predict_satisfaction(feedback)
        )
```

### Success Criteria by Editor

**Idea Editor:**
- **Hook Strength:** 85%+ of flagged weak ideas improved after revision
- **Concept Originality:** Identifies 90%+ of cliché concepts
- **False Positives:** <5% of strong ideas incorrectly flagged

**Outline Editor:**
- **Structure Score:** 80%+ of outlines pass structural validation
- **Arc Completeness:** Catches 95%+ of missing plot beats
- **Pacing Issues:** Identifies 75%+ of pacing problems

**Content Editors (Structural/Continuity/Style):**
- **Issue Detection:** 90%+ of major structural problems found
- **Suggestion Quality:** 70%+ of suggestions deemed helpful by users
- **False Positives:** <10% suggestions that users reject as unnecessary

**Line Editor:**
- **Voice Consistency:** 85%+ improvement in voice consistency scores
- **Sentence Variety:** Reduces repetitive structures by 60%+
- **Show vs Tell:** Identifies 80%+ of telling opportunities

**Copyeditor:**
- **Error Detection:** Catches 95%+ of grammar/spelling errors
- **Consistency:** 100% accuracy on name/location consistency
- **Style Compliance:** 90%+ adherence to chosen style guide

### User Experience Metrics
- **Analysis Time:** <2 minutes for 5k-word story
- **Feedback Clarity:** 80%+ of users understand suggestions without clarification
- **Integration Ease:** 90%+ of users successfully apply suggestions
- **Satisfaction Rate:** 75%+ of users report improved story quality

### Continuous Improvement
**Feedback Loop:** Collect user ratings on suggestions:
```json
{
  "feedback_rating": {
    "suggestion_id": "ss_007_goal_clarification",
    "rating": 4,  // 1-5 scale
    "helpful": true,
    "comments": "Good suggestion but could be more specific",
    "applied": true
  }
}
```

---

## Cost & Performance Considerations

### Token Usage Estimation
**Per-Editor Estimates:**
- **Idea Editor:** 2k-5k tokens (concept analysis + expansion suggestions)
- **Outline Editor:** 3k-8k tokens (full outline analysis)
- **Content Editors:** 8k-15k tokens (scene-by-scene deep analysis)
- **Line Editor:** 5k-10k tokens (sentence-level polish)
- **Copyeditor:** 2k-4k tokens (grammar/mechanics check)

**Cost Optimization Strategies:**
```python
class CostOptimizer:
    def estimate_cost(self, content_length: int, editor_type: str) -> CostEstimate:
        """Estimate token usage and cost before analysis"""
        base_tokens = self._get_base_tokens(editor_type)
        content_multiplier = self._calculate_content_multiplier(content_length)
        model_cost_per_token = self._get_model_cost()

        estimated_tokens = base_tokens * content_multiplier
        estimated_cost = estimated_tokens * model_cost_per_token

        return CostEstimate(
            tokens=estimated_tokens,
            cost_usd=estimated_cost,
            model=self.model,
            warnings=self._generate_warnings(estimated_cost)
        )
```

### Performance Optimization
**Batching Strategies:**
- Process scenes in groups of 3-5 to maintain context
- Cache analysis results for unchanged content
- Parallel processing for independent scenes

**Progressive Analysis:**
```bash
# Quick structural check first
storygen-iter edit-content --quick-structural \
  --prose prose.json \
  --model fast-model \
  -o quick_feedback.json

# Deep analysis only if structural issues found
storygen-iter edit-content --deep-analysis \
  --prose prose.json \
  --feedback quick_feedback.json \
  --model slow-model \
  -o deep_feedback.json
```

### Model Selection Guidelines
**Cost vs Quality Trade-offs:**
- **Idea/Outline:** Use faster, cheaper models (Grok, Claude Haiku)
- **Content Analysis:** Use capable models (GPT-4, Claude Sonnet)
- **Line Editing:** Use creative models (GPT-4, Claude Opus)
- **Copyediting:** Use specialized models or rule-based systems

**Local vs Cloud:**
- **Local Models:** Free but slower, good for development
- **Cloud Models:** Pay-per-use, faster, better quality
- **Hybrid Approach:** Local for drafts, cloud for final polish

### User Cost Control
**Budget Features:**
```bash
# Set spending limits
storygen-iter edit-content --max-cost 1.00 \
  --prose prose.json \
  --model gpt-4o \
  -o feedback.json

# Get cost estimates before running
storygen-iter estimate-cost \
  --editor content \
  --input-size prose.json \
  --model gpt-4o
```

**Cost Transparency:**
```json
{
  "cost_breakdown": {
    "editor": "ContentEditor",
    "model": "gpt-4o",
    "input_tokens": 8500,
    "output_tokens": 2100,
    "total_tokens": 10600,
    "cost_usd": 0.32,
    "time_seconds": 45.2
  }
}
```

---

## Implementation Priority

### Phase 1 (Next Sprint) - Early Detection MVP
**Priority:** CRITICAL - Maximum leverage for quality improvement
**Timeline:** 3-4 weeks
**Focus:** Implement pre-prose editors to prevent expensive downstream regeneration

**Why This MVP?**
- **Cascading Invalidation Prevention**: Early editors catch problems before they cascade through outline → characters → locations → prose
- **Cost Efficiency**: 1x cost to fix idea issues vs 10x cost to fix prose issues
- **Quality Leverage**: Problems caught early are exponentially easier to resolve
- **User Experience**: Fail fast on bad concepts rather than investing in doomed stories

1. **Idea Editor** - CRITICAL: Concept validation and enhancement (prevents bad stories entirely)
2. **Outline Editor** - HIGH: Structural critique before prose investment
3. Unit tests for early editors
4. CLI integration for idea and outline editing
5. Quality gates in pipeline (optional blocking before character generation)

### Phase 2 (Following Sprint) - Pipeline Integration
**Priority:** HIGH - Seamless user experience
**Timeline:** 2-3 weeks
**Focus:** Integrate existing content editors into main pipeline

**Why After Early Editors?**
- **Foundation First**: Early detection provides the most value
- **Existing Code**: Content editors already implemented and tested
- **Immediate ROI**: Users get automated feedback on generated prose

1. **Pipeline Integration**: Add editorial analysis after prose generation
2. **Feedback Storage**: Store editorial feedback with project data
3. **Revision Workflow**: Allow selective application of suggestions
4. **User Controls**: Skip analysis, control editors, set budgets

### Phase 3 (Polish Sprint) - Advanced Content Analysis
**Priority:** MEDIUM - Quality of life improvements
**Timeline:** 3-4 weeks
**Focus:** Style, line editing, and comprehensive analysis

1. **Style Editor** (POV & voice consistency) - already implemented
2. **Line Editor** - Polish prose quality and rhythm
3. **Enhanced Comprehensive Editor** - Multi-pass analysis
4. Unit tests and performance optimization
5. Integration with revision workflows

### Phase 4 (Future) - Final Polish & Proofing
**Priority:** LOW - Nice-to-have enhancements
**Timeline:** Ongoing
**Focus:** Mechanical corrections and final validation

1. **Copyeditor** - Grammar, spelling, style guide compliance
2. **Proofreader** - Final EPUB pass for typos and formatting
3. Multi-model editing (ensemble feedback)
4. Custom style guides and author voice training

### Success Metrics by Phase

**Phase 1 Success (Early Detection):**
- Idea Editor catches 80%+ of weak concepts before character generation
- Outline Editor identifies 75%+ of structural issues before prose writing
- Prevents 60%+ of stories that would require major downstream rewrites
- CLI commands work reliably with proper error messages
- Quality gates reduce average story development cost by 30%+

**Phase 2 Success (Pipeline Integration):**
- Content editors integrate seamlessly into main workflow
- Editorial analysis runs automatically after prose generation
- Users can selectively apply suggestions and regenerate improved content
- False positive rate <10% (editors don't suggest unnecessary changes)
- Analysis completes in <2 minutes for typical 5k-word story

**Phase 3 Success (Advanced Analysis):**
- Style/Line editors improve prose quality scores by 20%+
- Comprehensive editor provides holistic feedback
- Integration with revision workflows is seamless
- Multi-pass editing shows cumulative quality improvements

**Phase 4 Success (Final Polish):**
- Copyeditor catches 95%+ of mechanical errors
- Proofreader catches remaining 5% of issues in EPUB exports
- Multi-model editing improves feedback quality by 15%+
- Advanced features adopted by 50%+ of users

---

## Advanced AI Capabilities (Future Considerations)

### Multi-Modal Analysis
**Beyond Text-Only Editing:**
```python
class MultiModalEditor:
    """Analyze text alongside visual/audio elements"""

    def analyze_visual_consistency(self, manuscript: Manuscript, images: list[Image]) -> list[Issue]:
        """Check if descriptions match accompanying images"""
        pass

    def analyze_audio_narrative(self, manuscript: Manuscript, audio_clips: list[Audio]) -> list[Issue]:
        """Verify audio descriptions match narrative tone"""
        pass
```

### Real-Time Collaborative Editing
**Live Feedback During Writing:**
```bash
# Real-time analysis as you write
storygen-iter edit-live \
  --input manuscript.txt \
  --model fast-model \
  --stream-feedback \
  --focus continuity  # Only check continuity issues
```

### Writing Analytics Integration
**Quantitative Writing Metrics:**
```json
{
  "writing_analytics": {
    "readability_scores": {
      "flesch_kincaid": 8.2,
      "gunning_fog": 9.1,
      "dale_chall": 7.8
    },
    "style_metrics": {
      "avg_sentence_length": 18.3,
      "passive_voice_percentage": 12.4,
      "adverb_density": 8.7
    },
    "engagement_indicators": {
      "dialogue_ratio": 0.23,
      "action_beat_frequency": 4.2,
      "emotional_word_density": 0.15
    }
  }
}
```

### Plagiarism & Originality Detection
**Content Uniqueness Verification:**
```python
class OriginalityChecker:
    def check_plagiarism(self, manuscript: str) -> PlagiarismReport:
        """Detect potential plagiarism against web sources"""
        pass

    def analyze_tropes(self, manuscript: str) -> TropeAnalysis:
        """Identify overused story elements and suggest alternatives"""
        pass
```

### Predictive Success Modeling
**Market Viability Prediction:**
```python
class MarketPredictor:
    def predict_commercial_potential(self, manuscript: str) -> MarketAnalysis:
        """Estimate market success based on genre trends and reader preferences"""
        pass

    def suggest_target_audience(self, manuscript: str) -> AudienceProfile:
        """Identify ideal reader demographics and marketing angles"""
        pass
```

### Automated A/B Testing
**Content Optimization:**
```bash
# Generate multiple versions of problematic scenes
storygen-iter generate-variants \
  --scene ss_007 \
  --variants 3 \
  --focus readability \
  --test-audience "young_adult"

# Compare reader engagement metrics
storygen-iter compare-variants \
  --variants variant_1.json,variant_2.json,variant_3.json \
  --metric engagement_score
```

### Integration with Writing Tools
**Seamless Workflow Integration:**
- **Grammarly API**: Real-time grammar and style checking
- **ProWritingAid**: Advanced style and readability analysis
- **Hemingway App**: Sentence structure optimization
- **Scrivener Integration**: Direct manuscript import/export
- **Google Docs Add-on**: Collaborative editing with AI assistance

### Continuous Learning System
**Self-Improving Editors:**
```python
class LearningEditor:
    def incorporate_user_feedback(self, feedback: UserFeedback):
        """Learn from user ratings to improve future suggestions"""
        pass

    def adapt_to_author_style(self, author_samples: list[str]):
        """Customize analysis based on author's unique voice"""
        pass
```

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

### Accessibility & Inclusive Design
**Universal Design Principles:**
- **Screen Reader Compatibility**: Ensure all feedback is accessible to visually impaired users
- **Color-Blind Friendly**: Use high-contrast colors and avoid color-only indicators
- **Cognitive Load Management**: Break complex feedback into digestible chunks
- **Multilingual Support**: Provide feedback in user's preferred language
- **Diverse Representation**: Train on diverse literary traditions and cultural contexts

### Ethical AI Considerations
**Responsible AI Development:**
- **Bias Mitigation**: Regular audits for algorithmic bias in editorial suggestions
- **Transparency**: Clear disclosure of AI involvement in editing process
- **User Consent**: Opt-in/opt-out controls for different types of analysis
- **Data Privacy**: Secure handling of user manuscripts and personal data
- **Intellectual Property**: Respect for author's creative ownership and rights

---

## Next Appropriate MVP: Early Detection Editors

### Current Gap
**The existing content editors (Structural, Continuity, Style, Comprehensive) are fully implemented and working**, but the **pre-prose editors (Idea and Outline) are not implemented**. These early editors have the highest leverage for quality improvement because they prevent cascading invalidation.

### Why This is the Next MVP
1. **Maximum Leverage**: Early editors prevent problems from cascading through the entire pipeline
2. **Cost Prevention**: Fix idea issues at 1x cost vs prose issues at 10x cost
3. **Quality Assurance**: Better to reject bad concepts than rewrite thousands of words
4. **User Experience**: Fail fast on fundamentally flawed ideas before heavy investment

### MVP Scope: Early Detection Pipeline

**Goal**: Implement Idea and Outline editors as quality gates before character/location/prose generation.

#### Features to Implement:
1. **Idea Editor**: Concept validation and enhancement suggestions
2. **Outline Editor**: Structural critique and plot hole detection
3. **Pipeline Integration**: Quality gates before downstream generation
4. **Human Language Reports**: Readable feedback for concept and structural issues
5. **Revision Workflow**: Allow concept refinement before proceeding

#### Implementation Approach:
1. **Idea Editor**: Analyze story concepts for strength, originality, and viability
2. **Outline Editor**: Validate plot structure, character arcs, and thematic coherence
3. **Quality Gates**: Optional blocking before character generation
4. **Feedback Integration**: Store early feedback with project data

#### Success Criteria:
- **Concept Validation**: Idea Editor catches 80%+ of weak concepts
- **Structural Analysis**: Outline Editor identifies 75%+ of plot issues
- **Cost Efficiency**: Prevents expensive downstream regeneration
- **User Acceptance**: 70%+ of suggestions deemed helpful
- **Performance**: Analysis completes in <1 minute for typical inputs

#### Timeline: 3-4 weeks
- **Week 1**: Implement Idea Editor with concept analysis and CLI
- **Week 2**: Implement Outline Editor with structural validation
- **Week 3**: Integrate quality gates into pipeline, add revision workflow
- **Week 4**: Testing, performance optimization, and documentation

#### Dependencies:
- ✅ Project data models (support editorial feedback)
- ✅ Human language report framework (already implemented)
- ✅ CLI framework (for new editor commands)

#### Risk Assessment:
- **Low Risk**: Builds on existing editorial framework and data models
- **Incremental**: Can be implemented without breaking existing functionality
- **Fallback Options**: Pipeline can skip early editors if issues occur

### Post-MVP Roadmap
After early detection is complete:
1. **Pipeline Integration**: Connect content editors to main workflow
2. **GUI Integration**: Add early editors to web interface
3. **Advanced Editors**: Line Editor, Copyeditor, Proofreader
4. **Multi-Iteration Workflows**: Support multiple editorial passes with learning

---

## Related Documentation
- [Iterative Generation](./iterative-generation.md) - Core pipeline architecture
- [GUI TODO](./GUI_TODO.md) - Web interface development roadmap
- [Migrations](./migrations.md) - Version compatibility for editorial data models
