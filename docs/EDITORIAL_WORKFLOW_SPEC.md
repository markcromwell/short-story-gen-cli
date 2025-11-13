# Editorial Workflow System - Detailed Specification

**Status**: Planning / Not Started
**Priority**: Future Enhancement
**Estimated Effort**: 15-20 hours
**Dependencies**: Phase 1-3 Complete ✅

---

## Overview

Implement an AI-driven editorial workflow that simulates the professional writing and editing process. The system will allow AI agents to take on different editorial roles, providing structured feedback at various stages of story development - from concept through final proofreading.

This creates a "virtual writing workshop" where the AI provides the kind of multi-stage feedback writers receive in traditional publishing.

---

## Editorial Roles & Responsibilities

### 1. Writing Coach / Mentor

**Stage**: Post-Outline, Pre-First Draft
**Focus**: High-level concept, structure, and feasibility

**Responsibilities**:
- Review story outline for structural soundness
- Identify potential pacing issues
- Suggest alternative plot paths or character dynamics
- Ensure genre conventions are met
- Check if premise can sustain target word count
- Validate character motivations align with plot

**Input**: `idea.json`, `outline.json`, `characters.json`, `locations.json`
**Output**: `feedback/coach_outline.json`

**Feedback Format**:
```json
{
  "role": "writing_coach",
  "stage": "post_outline",
  "timestamp": "2025-11-12T10:30:00",
  "overall_assessment": "Strong premise with clear character arcs...",
  "structural_feedback": [
    {
      "area": "pacing",
      "severity": "medium",
      "observation": "Act 2 feels rushed compared to Act 1 setup",
      "suggestion": "Consider expanding the midpoint conflict..."
    }
  ],
  "concept_alternatives": [
    {
      "aspect": "antagonist_motivation",
      "current": "Revenge for past betrayal",
      "alternative": "Could the antagonist believe they're the hero?",
      "rationale": "Would add moral complexity and depth"
    }
  ],
  "strengths": ["Clear protagonist goal", "Unique setting"],
  "concerns": ["Secondary characters underdeveloped", "Climax telegraphed"],
  "recommendations": [
    "Flesh out ally character's backstory",
    "Add false climax in Act 2 to misdirect reader"
  ]
}
```

**CLI Command**:
```bash
storygen-iter feedback coach <project> --stage outline
```

---

### 2. Beta Readers

**Stage**: Post-First Draft
**Focus**: Reader experience, engagement, emotional resonance

**Responsibilities**:
- Read as target audience members (not editors)
- Flag where engagement drops
- Identify confusing plot points or character actions
- Note emotional high/low points
- Point out pacing issues from reader perspective
- Suggest which scenes feel unnecessary

**Input**: Complete prose in `prose.json` or `story.epub`
**Output**: `feedback/beta_reader_1.json`, `feedback/beta_reader_2.json`, etc.

**Multiple Personas**: Generate 2-3 beta readers with different reading preferences:
- Reader 1: Genre enthusiast (looks for trope adherence, world-building)
- Reader 2: Literary focus (character depth, prose quality)
- Reader 3: Casual reader (pure entertainment, pacing)

**Feedback Format**:
```json
{
  "role": "beta_reader",
  "reader_profile": {
    "name": "Genre Enthusiast",
    "preferences": ["fast-paced", "world-building", "action"],
    "dislikes": ["slow burns", "literary tangents"]
  },
  "stage": "first_draft",
  "overall_rating": 4.0,
  "overall_impression": "Loved the world-building! The magic system is creative...",
  "engagement_curve": [
    {"chapter": 1, "engagement": 8, "note": "Great hook, jumped right in"},
    {"chapter": 2, "engagement": 6, "note": "Info-dump slowed things down"},
    {"chapter": 5, "engagement": 9, "note": "That twist! Didn't see it coming"},
    {"chapter": 8, "engagement": 4, "note": "Lost interest during the romance subplot"}
  ],
  "emotional_beats": {
    "most_impactful": "Chapter 12 - protagonist's sacrifice",
    "fell_flat": "Chapter 6 - villain reveal lacked punch"
  },
  "plot_reactions": [
    {
      "event": "Mentor's death",
      "page": 87,
      "reaction": "Saw it coming a mile away - too telegraphed"
    },
    {
      "event": "Secret door discovery",
      "page": 143,
      "reaction": "This felt like it came out of nowhere - needs foreshadowing"
    }
  ],
  "character_opinions": [
    {"name": "Protagonist", "liked": true, "reason": "Relatable struggle"},
    {"name": "Antagonist", "liked": false, "reason": "One-dimensional, needs depth"}
  ],
  "pacing_notes": [
    {"section": "Chapters 1-3", "pace": "perfect", "note": "Couldn't put it down"},
    {"section": "Chapters 6-7", "pace": "dragged", "note": "Consider cutting this subplot"}
  ],
  "confusion_points": [
    {"location": "Chapter 4, page 56", "confusion": "Wait, who is Marcus again? Forgot he was introduced in Ch 1"}
  ],
  "favorite_parts": ["The duel scene", "Opening paragraph", "Ending twist"],
  "recommendations": "Cut the romance subplot, focus on the mystery. Strengthen the antagonist."
}
```

**CLI Command**:
```bash
storygen-iter feedback beta <project> --readers 3
```

---

### 3. Developmental Editor

**Stage**: Post-Beta Feedback, Pre-Revision
**Focus**: Big-picture story elements, structure, character arcs

**Responsibilities**:
- Analyze plot holes and logic gaps
- Evaluate character arc completion
- Assess pacing across entire manuscript
- Check thematic consistency
- Identify structural weaknesses
- Suggest major revisions (reordering, cutting, adding scenes)
- Ensure genre expectations are met

**Input**: Complete prose + beta feedback
**Output**: `feedback/developmental_edit.json`

**Feedback Format**:
```json
{
  "role": "developmental_editor",
  "stage": "post_beta",
  "editorial_letter": "Overall, this is a solid draft with a compelling premise. However, there are three major areas that need attention before the story is ready for line editing...",
  "major_issues": [
    {
      "category": "plot_hole",
      "severity": "critical",
      "location": "Chapters 8-12",
      "issue": "Protagonist knows about the artifact in Ch 8, but Ch 12 shows their surprise at discovering it",
      "solution": "Either remove Ch 8 foreshadowing or revise Ch 12 reaction",
      "impact": "High - breaks reader trust"
    },
    {
      "category": "character_arc",
      "severity": "major",
      "character": "Protagonist",
      "issue": "Arc incomplete - they never overcome their stated flaw (cowardice)",
      "solution": "Add a scene in Act 3 where they must face their fear directly",
      "suggested_location": "Between current Ch 14-15"
    }
  ],
  "pacing_analysis": {
    "act_1": {"assessment": "good", "percentage": 28, "note": "Setup is thorough but efficient"},
    "act_2": {"assessment": "rushed", "percentage": 42, "note": "Too short - needs 2-3 more scenes of rising tension"},
    "act_3": {"assessment": "good", "percentage": 30, "note": "Resolution satisfying"}
  },
  "character_assessments": [
    {
      "name": "Protagonist",
      "arc_complete": false,
      "development": "Strong setup but payoff missing",
      "relationships": "Romance feels forced - needs more organic development",
      "recommendation": "Add 1-2 scenes showing growing trust before romance"
    },
    {
      "name": "Antagonist",
      "arc_complete": true,
      "development": "Well-developed with clear motivation",
      "relationships": "Good dynamic with protagonist",
      "recommendation": "Consider adding a humanizing moment to avoid 'pure evil' trope"
    }
  ],
  "thematic_analysis": {
    "stated_themes": ["redemption", "sacrifice", "identity"],
    "delivered_themes": ["redemption", "identity"],
    "missing_theme": "sacrifice",
    "recommendation": "Sacrifice theme is stated but never dramatized - add a sacrifice moment in climax"
  },
  "structural_recommendations": [
    {
      "type": "reorder",
      "current": "Chapter 7 -> Chapter 8",
      "suggested": "Chapter 8 -> Chapter 7",
      "reason": "Current order creates confusion about timeline"
    },
    {
      "type": "cut",
      "target": "Chapter 11 (market scene)",
      "reason": "Doesn't advance plot or character - feels like filler",
      "word_count_saved": 2500
    },
    {
      "type": "add",
      "location": "Between Ch 14-15",
      "description": "Scene showing protagonist confronting their mentor about lies",
      "purpose": "Completes protagonist's trust issues arc",
      "estimated_words": 1800
    }
  ],
  "genre_adherence": {
    "genre": "dark fantasy",
    "conventions_met": ["magic system explained", "moral ambiguity", "world-building"],
    "conventions_missing": ["sense of wonder", "cost of magic"],
    "recommendation": "Add more scenes showing the price/cost of using magic"
  },
  "priority_revisions": [
    "1. Fix plot hole in Chapters 8-12 (Critical)",
    "2. Complete protagonist's arc (Major)",
    "3. Add missing sacrifice theme moment (Major)",
    "4. Cut Chapter 11 market scene (Medium)",
    "5. Reorder Chapters 7-8 (Medium)"
  ]
}
```

**CLI Command**:
```bash
storygen-iter feedback dev-edit <project>
```

---

### 4. Line Editor

**Stage**: Post-Revision, Pre-Copy Edit
**Focus**: Sentence-level prose quality, clarity, style

**Responsibilities**:
- Improve sentence flow and rhythm
- Enhance clarity without changing meaning
- Tighten verbose passages
- Vary sentence structure for better pacing
- Strengthen word choice
- Maintain consistent voice and tone
- Cut unnecessary words and clichés
- Ensure smooth transitions between paragraphs

**Input**: Revised prose from `prose.json`
**Output**: `feedback/line_edit.json` with inline suggestions

**Feedback Format**:
```json
{
  "role": "line_editor",
  "stage": "pre_copy_edit",
  "overall_prose_quality": "good",
  "summary": "Strong voice overall. Main areas for improvement: sentence variety in action scenes, some filtering language, occasional purple prose in descriptions.",
  "inline_edits": [
    {
      "scene_id": "1.1",
      "paragraph": 3,
      "original": "She saw the shadow move across the wall. She heard a sound behind her. She felt her heart pounding.",
      "suggestion": "The shadow slid across the wall. A sound—behind her. Her heart hammered.",
      "reason": "Varied sentence structure, removed 'she saw/heard/felt' filtering, more immediate",
      "edit_type": "sentence_variety"
    },
    {
      "scene_id": "2.3",
      "paragraph": 12,
      "original": "The castle loomed before them, its ancient stones weathered by countless centuries of wind and rain, standing as a testament to the passage of time.",
      "suggestion": "The castle loomed before them, its ancient stones weathered by centuries of wind and rain.",
      "reason": "Cut redundancy ('countless centuries' + 'passage of time'), tightened",
      "edit_type": "conciseness"
    },
    {
      "scene_id": "5.2",
      "paragraph": 8,
      "original": "He was very angry.",
      "suggestion": "Rage coiled in his chest. OR His hands clenched into fists. OR He slammed the door.",
      "reason": "Show, don't tell - demonstrate anger through action/physical reaction",
      "edit_type": "show_dont_tell"
    }
  ],
  "prose_patterns": [
    {
      "pattern": "filtering_language",
      "frequency": "high",
      "examples": ["she saw", "he felt", "they heard", "she realized"],
      "recommendation": "Remove filter words to make prose more immediate: 'She saw the door open' -> 'The door opened'"
    },
    {
      "pattern": "weak_verbs",
      "frequency": "medium",
      "examples": ["was walking", "started to run", "began to speak"],
      "recommendation": "Use stronger, more specific verbs: 'was walking' -> 'strolled/trudged/crept'"
    }
  ],
  "style_observations": [
    {
      "area": "dialogue_tags",
      "assessment": "good",
      "note": "Nice variety of tags and action beats. Good balance of 'said' and description."
    },
    {
      "area": "paragraph_length",
      "assessment": "needs_variety",
      "note": "Paragraphs in action scenes are too long (6-8 sentences). Break for pace."
    }
  ],
  "voice_consistency": {
    "overall": "strong",
    "inconsistencies": [
      {
        "location": "Chapter 7",
        "issue": "Protagonist uses modern slang ('That's wild') despite medieval setting",
        "fix": "Use period-appropriate language"
      }
    ]
  },
  "word_count_changes": {
    "original": 45000,
    "suggested": 42000,
    "reduction": 3000,
    "note": "Primarily from tightening verbose passages and removing filter words"
  }
}
```

**CLI Command**:
```bash
storygen-iter feedback line-edit <project> --scene <scene-id>
# Or for all scenes:
storygen-iter feedback line-edit <project> --all
```

---

### 5. Copy Editor

**Stage**: Post-Line Edit, Pre-Proofread
**Focus**: Grammar, consistency, style guide adherence

**Responsibilities**:
- Correct grammar, spelling, punctuation errors
- Check for consistency in:
  - Character names, descriptions, eye/hair color
  - Place names and descriptions
  - Timeline and chronology
  - Terminology and world-building elements
- Verify factual accuracy (for historical settings)
- Ensure style guide adherence (Chicago, AP, house style)
- Flag unclear antecedents and ambiguous pronouns
- Check for proper dialogue formatting

**Input**: Line-edited prose
**Output**: `feedback/copy_edit.json`

**Feedback Format**:
```json
{
  "role": "copy_editor",
  "stage": "pre_proofread",
  "style_guide": "Chicago Manual of Style, 17th ed",
  "error_summary": {
    "grammar": 12,
    "spelling": 3,
    "punctuation": 18,
    "consistency": 7,
    "factual": 2
  },
  "corrections": [
    {
      "scene_id": "1.1",
      "paragraph": 4,
      "line": 2,
      "error_type": "grammar",
      "original": "Neither of the guards were watching.",
      "correction": "Neither of the guards was watching.",
      "rule": "Subject-verb agreement: 'neither' takes singular verb"
    },
    {
      "scene_id": "3.2",
      "error_type": "consistency",
      "issue": "Character name variation",
      "original": "Katherine (Ch 1-5) vs. Catherine (Ch 6-10)",
      "correction": "Standardize to 'Katherine' throughout",
      "severity": "high"
    },
    {
      "scene_id": "2.4",
      "error_type": "punctuation",
      "original": "\"Where are you going?\" She asked.",
      "correction": "\"Where are you going?\" she asked.",
      "rule": "Lowercase dialogue tag after question mark"
    },
    {
      "scene_id": "7.1",
      "error_type": "factual",
      "issue": "Historical inaccuracy",
      "original": "The telephone rang in 1885",
      "correction": "Telephones existed but were extremely rare in homes in 1885",
      "severity": "medium",
      "suggestion": "Consider telegraph or letter for this communication"
    }
  ],
  "consistency_report": {
    "character_details": [
      {
        "character": "Protagonist",
        "attribute": "eye_color",
        "variations": ["blue (Ch 1)", "green (Ch 8)", "blue-green (Ch 14)"],
        "recommendation": "Choose one and standardize"
      }
    ],
    "location_details": [
      {
        "location": "Main Street",
        "variations": ["Main Street", "Main St.", "main street"],
        "recommendation": "Standardize to 'Main Street' (no abbreviation, capitalize)"
      }
    ],
    "timeline_issues": [
      {
        "issue": "Day/night discrepancy",
        "location": "Chapters 5-6",
        "detail": "Ch 5 ends at sunset, Ch 6 opens 'an hour later' but sun is at zenith",
        "recommendation": "Revise to 'the next morning'"
      }
    ],
    "terminology": [
      {
        "term": "magic system",
        "variations": ["channeling", "weaving", "shaping"],
        "recommendation": "Clarify if these are synonyms or different techniques",
        "locations": ["Ch 2, 5, 8"]
      }
    ]
  },
  "style_queries": [
    {
      "location": "Ch 4, para 15",
      "query": "Author uses 'alright' - Chicago prefers 'all right'. Confirm preference?",
      "type": "style_preference"
    }
  ]
}
```

**CLI Command**:
```bash
storygen-iter feedback copy-edit <project>
```

---

### 6. Proofreader

**Stage**: Final pass before publication
**Focus**: Surface-level errors, formatting

**Responsibilities**:
- Catch remaining typos
- Check formatting consistency
- Verify chapter breaks and scene transitions
- Ensure proper em-dash, en-dash usage
- Check for double spaces, extra line breaks
- Verify EPUB/PDF formatting is clean
- Final consistency check on names/places

**Input**: Copy-edited prose, generated EPUB
**Output**: `feedback/proofread.json`

**Feedback Format**:
```json
{
  "role": "proofreader",
  "stage": "final_pass",
  "format_checked": "epub",
  "error_summary": {
    "typos": 5,
    "formatting": 3,
    "minor_consistency": 2
  },
  "corrections": [
    {
      "location": "Chapter 3, paragraph 7",
      "error_type": "typo",
      "original": "recieve",
      "correction": "receive"
    },
    {
      "location": "Chapter 5, paragraph 12",
      "error_type": "formatting",
      "issue": "Double space after period",
      "original": "He ran.  She followed.",
      "correction": "He ran. She followed."
    },
    {
      "location": "Chapter 8, scene break",
      "error_type": "formatting",
      "issue": "Missing scene break ornament",
      "correction": "Add '* * *' or ornament between POV changes"
    },
    {
      "location": "Chapter 12, paragraph 3",
      "error_type": "minor_consistency",
      "original": "gray eyes",
      "note": "Previous refs use 'grey' - choose one spelling",
      "correction": "Standardize to 'grey' (or 'gray')"
    }
  ],
  "formatting_checks": {
    "chapter_headings": "consistent",
    "scene_breaks": "needs_attention",
    "dialogue_formatting": "clean",
    "paragraph_spacing": "consistent",
    "em_dashes": "consistent",
    "ellipses": "needs_standardization"
  },
  "epub_specific": [
    {
      "element": "table_of_contents",
      "status": "good",
      "note": "All chapters properly linked"
    },
    {
      "element": "scene_ornaments",
      "status": "issue",
      "detail": "Ornaments not displaying - check CSS class",
      "fix": "Update .scene-break class in stylesheet"
    }
  ],
  "final_checks": {
    "total_errors_found": 10,
    "critical": 0,
    "major": 0,
    "minor": 10,
    "ready_for_publication": true
  }
}
```

**CLI Command**:
```bash
storygen-iter feedback proofread <project>
```

---

## Implementation Architecture

### New Components

#### 1. Editorial Feedback Generator

**File**: `src/storygen/iterative/generators/editorial.py`

```python
class EditorialFeedbackGenerator(BaseGenerator[dict]):
    """
    Generate editorial feedback for different stages of the writing process.

    Takes on different editorial roles (coach, beta, dev editor, etc.) and
    provides role-appropriate feedback on story content.
    """

    def __init__(
        self,
        role: EditorialRole,
        model: str = "gpt-4",
        max_retries: int = 3,
        timeout: int = 600,
        verbose: bool = False
    ):
        super().__init__(model=model, max_retries=max_retries, timeout=timeout, verbose=verbose)
        self.role = role

    def generate(
        self,
        project: Project,
        stage: str,
        **kwargs
    ) -> EditorialFeedback:
        """Generate feedback based on role and stage."""
        pass
```

#### 2. Editorial Role Enum

**File**: `src/storygen/iterative/models.py`

```python
class EditorialRole(Enum):
    """Editorial roles in the writing process."""
    WRITING_COACH = "writing_coach"
    BETA_READER = "beta_reader"
    DEVELOPMENTAL_EDITOR = "developmental_editor"
    LINE_EDITOR = "line_editor"
    COPY_EDITOR = "copy_editor"
    PROOFREADER = "proofreader"
```

#### 3. Enhanced Editorial Feedback Model

**Update**: `src/storygen/iterative/models.py`

```python
@dataclass
class EditorialFeedback:
    """Editorial feedback from different roles."""
    role: EditorialRole
    stage: str  # outline, first_draft, revision, etc.
    timestamp: str
    overall_assessment: str

    # Role-specific fields (Optional)
    structural_feedback: list[dict] | None = None  # Coach
    engagement_curve: list[dict] | None = None  # Beta
    major_issues: list[dict] | None = None  # Dev Editor
    inline_edits: list[dict] | None = None  # Line Editor
    corrections: list[dict] | None = None  # Copy Editor

    # Common fields
    strengths: list[str] = field(default_factory=list)
    concerns: list[str] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)
    priority_actions: list[str] = field(default_factory=list)
```

#### 4. CLI Commands

**File**: `src/storygen/iterative/cli/commands/feedback.py` (new)

```python
@click.group()
def feedback():
    """Generate editorial feedback on story drafts."""
    pass

@feedback.command()
@click.argument("project_name")
@click.option("--stage", default="outline", help="outline or first_draft")
def coach(project_name: str, stage: str):
    """Get writing coach feedback on concept and structure."""
    pass

@feedback.command()
@click.argument("project_name")
@click.option("--readers", default=3, help="Number of beta readers (1-5)")
def beta(project_name: str, readers: int):
    """Get beta reader feedback on complete draft."""
    pass

@feedback.command()
@click.argument("project_name")
def dev_edit(project_name: str):
    """Get developmental editor feedback on story structure."""
    pass

@feedback.command()
@click.argument("project_name")
@click.option("--scene", help="Specific scene ID or --all for entire story")
def line_edit(project_name: str, scene: str | None):
    """Get line editor feedback on prose quality."""
    pass

@feedback.command()
@click.argument("project_name")
def copy_edit(project_name: str):
    """Get copy editor feedback on grammar and consistency."""
    pass

@feedback.command()
@click.argument("project_name")
def proofread(project_name: str):
    """Get proofreader feedback for final polish."""
    pass
```

### Integration with Existing System

#### Project Structure Updates

```
projects/<project_name>/
├── idea.json
├── characters.json
├── locations.json
├── outline.json
├── breakdown.json
├── prose.json
├── story.epub
└── feedback/                    # NEW
    ├── coach_outline.json       # Writing coach feedback
    ├── beta_reader_1.json       # Beta reader 1
    ├── beta_reader_2.json       # Beta reader 2
    ├── beta_reader_3.json       # Beta reader 3
    ├── developmental_edit.json  # Dev editor feedback
    ├── line_edit_1.1.json      # Line edits per scene
    ├── line_edit_1.2.json
    ├── copy_edit.json          # Copy editor feedback
    └── proofread.json          # Proofreader feedback
```

#### Workflow Integration

```bash
# Typical workflow with editorial feedback:

# 1. Generate initial content
storygen-iter generate idea "A detective story in 1920s Chicago"
storygen-iter generate characters my-story
storygen-iter generate locations my-story
storygen-iter generate outline my-story

# 2. Get coach feedback on outline
storygen-iter feedback coach my-story --stage outline

# 3. Review coach feedback, revise outline manually if needed
# (Future: could have "apply suggestions" command)

# 4. Generate prose
storygen-iter prose breakdown my-story
storygen-iter prose generate my-story

# 5. Get beta reader feedback
storygen-iter feedback beta my-story --readers 3

# 6. Review beta feedback, decide on major revisions
# (Future: could regenerate specific scenes based on feedback)

# 7. Get developmental editor feedback
storygen-iter feedback dev-edit my-story

# 8. Apply major structural changes
# (Future: automated revision commands)

# 9. Get line editor feedback
storygen-iter feedback line-edit my-story --all

# 10. Polish prose based on line edit suggestions

# 11. Get copy editor feedback
storygen-iter feedback copy-edit my-story

# 12. Final proofreading pass
storygen-iter feedback proofread my-story

# 13. Export final version
storygen-iter export epub my-story --output final.epub
```

---

## Prompt Engineering Considerations

### Key Prompt Elements for Each Role

**Writing Coach**:
- Emphasize constructive, encouraging tone
- Focus on "Does this work?" rather than "Fix this"
- Offer alternatives rather than dictates
- Consider writer's skill level and goals

**Beta Readers**:
- Write as enthusiastic reader, not editor
- Use casual, conversational language
- React emotionally to story events
- Note where you got confused or bored
- Different personalities for variety

**Developmental Editor**:
- Professional, direct tone
- Evidence-based feedback ("This doesn't work because...")
- Prioritize issues by severity
- Offer concrete solutions
- Balance criticism with recognition of strengths

**Line Editor**:
- Focus on prose craft, not content changes
- Explain reasoning for each suggestion
- Preserve author's voice
- Provide multiple options when appropriate

**Copy Editor**:
- Factual, rules-based approach
- Cite style guide when relevant
- Query rather than correct when ambiguous
- Distinguish errors from style choices

**Proofreader**:
- Minimal, focused feedback
- Only flag objective errors
- No style suggestions at this stage
- Quick, efficient corrections

---

## Testing Strategy

### Unit Tests

- Test each role generates appropriate feedback structure
- Verify feedback JSON schema validation
- Test feedback file storage/retrieval
- Mock AI responses for consistent testing

### Integration Tests

- Test full workflow: outline -> coach -> revision -> beta -> etc.
- Verify feedback accumulates properly
- Test with different story lengths and genres

### Manual Testing Scenarios

1. **Historical Fiction**: Check if copy editor catches anachronisms
2. **Fantasy**: Verify consistency checking works for invented terms
3. **Mystery**: Test if beta readers identify plot holes
4. **Literary**: Ensure line editor preserves lyrical prose style

---

## Success Metrics

### Quantitative

- Feedback generation time < 2 minutes per role
- 95%+ valid JSON output
- User applies at least 1 suggestion per feedback session
- Reduction in reported "finished story has issues"

### Qualitative

- Feedback feels appropriate to role
- Suggestions are actionable and specific
- Different roles provide distinct value
- Writers report improved final output quality

---

## Future Enhancements

### Phase 1.5: Feedback Application

- **Auto-apply suggestions**: `storygen-iter feedback apply coach-1.structural.3`
- **Revision tracking**: Track which suggestions were applied
- **A/B comparison**: Compare original vs. revised versions

### Phase 2: Collaborative Editing

- **Feedback discussion**: AI responds to writer's questions about feedback
- **Consensus building**: If beta readers disagree, AI synthesizes perspectives
- **Iterative refinement**: Re-run feedback after changes

### Phase 3: Learning System

- **Style memory**: Remember writer's preferences across projects
- **Improvement tracking**: Show how writing improves over time
- **Custom rules**: Writer can add their own style rules to copy editor

---

## Dependencies & Prerequisites

### Required

- ✅ Phase 1-3 complete (CLI, BaseGenerator, Setting Integration)
- ✅ EditorialFeedback model exists in models.py
- ✅ Project file structure in place

### Recommended

- Streaming support in BaseGenerator (for real-time feedback)
- Rich console output for better feedback display
- Diff viewer for showing before/after suggestions

---

## Estimated Timeline

| Task | Effort | Dependencies |
|------|--------|--------------|
| Design feedback JSON schemas | 2h | None |
| Create EditorialFeedbackGenerator base | 3h | BaseGenerator |
| Implement Writing Coach role | 2h | Generator base |
| Implement Beta Reader role (3 personas) | 3h | Generator base |
| Implement Dev Editor role | 3h | Generator base |
| Implement Line Editor role | 2h | Generator base |
| Implement Copy Editor role | 2h | Generator base |
| Implement Proofreader role | 1h | Generator base |
| CLI commands for all roles | 2h | All generators |
| Integration testing | 3h | Everything |
| Documentation & examples | 2h | Everything |
| **Total** | **~25h** | |

---

## Open Questions

1. **Apply suggestions automatically?**
   - Start with manual application, add automation later?
   - How to handle conflicting suggestions?

2. **Feedback on feedback?**
   - Allow writer to rate usefulness of feedback?
   - Use ratings to improve future feedback?

3. **Multi-draft tracking?**
   - Track Draft 1, Draft 2, etc. in separate folders?
   - Show improvement metrics across drafts?

4. **Real-time vs. batch?**
   - Generate all feedback roles at once or one at a time?
   - Streaming feedback for immediate display?

5. **Cost management?**
   - Feedback generation uses a lot of tokens
   - Option to run cheaper model for some roles?
   - Cache feedback to avoid re-generation?

---

## Notes

- Editorial feedback is **advisory**, not prescriptive
- Writers should always have final say on changes
- Different roles provide different perspectives - all valuable
- System should encourage iteration and experimentation
- Keep feedback constructive and encouraging
- Balance criticism with recognition of strengths

---

**Last Updated**: November 12, 2025
**Status**: Ready for implementation after Phase 1-3 completion ✅
