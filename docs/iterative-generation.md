# Iterative Story Generation System

## Overview

This document describes the **Scene-Sequel Iterative Generation** system - an alternative story generation approach that builds stories incrementally through multiple AI calls, each focused on a specific aspect of story craft.

## Why Iterative Generation?

**Current System (Direct Generation):**
- Single AI call generates entire story + metadata
- AI must juggle plot, characters, settings, pacing simultaneously
- Often produces inconsistent characterization or rushed endings
- Limited by context window and AI "forgetfulness"

**Iterative System (Scene-Sequel):**
- Multiple focused AI calls, each building on previous work
- Characters/settings established before writing scenes
- Proper story structure using professional Scene-Sequel method
- AI maintains consistency through explicit context passing
- Higher quality output at cost of more API calls

## Design Decisions

Based on project requirements:

1. **Sequels are optional but rarely omitted** - Fast-paced scenes can flow directly into next scene, but most need sequel for emotional processing
2. **One POV per scene-sequel** - Never multiple POVs in same unit (keeps narrative clean)
3. **Retry on failure** - At least one retry per generation step before failing
4. **Writer-Editor AI Pattern** - Dual AI collaboration at each generation step:
   - **Writer AI** generates initial content
   - **Editor AI** critiques and rates output (failure/acceptable/good/excellent)
   - Writer revises based on feedback (if needed)
   - Editor validates revision
   - Maximum 2 revision cycles per step
5. **Project-based workflow** - Each story is a persistent project directory
   - Project metadata in JSON or SQLite
   - Version history for rollback if AI makes mistakes
   - Resume work exactly where you left off
   - Multiple stories can be worked on independently
6. **Checkpoint saves** - Save WorkingDoc after each step completion
7. **Version control** - Keep history of all AI generations for each step
8. **Dependency locking** - Editing early steps (idea, characters) requires explicit regeneration of dependent steps
   - Protects downstream work from accidental overwrites
   - Clear warnings about cascade effects
   - Optional "branch" creation for experimentation
9. **Future: Model selection per step** - Use cheaper models for structure, better models for prose
10. **Future: Manual branching** - Allow user to edit and try different paths

---

## Project-Based Workflow

Instead of one-shot generation, stories are treated as **persistent projects** that can be worked on over multiple sessions.

### Project Structure

```
~/stories/                          # User's stories directory
├── detective-parallel-universe/    # Project directory (slugified title)
│   ├── project.json               # Project metadata
│   ├── working_doc.json           # Current WorkingDoc state
│   ├── versions/                  # Version history
│   │   ├── 001_idea.json         # Step 1 completed
│   │   ├── 002_characters.json   # Step 2 completed
│   │   ├── 003_locations.json    # Step 3 completed
│   │   └── ...
│   ├── output/                    # Generated files
│   │   ├── story.epub
│   │   └── story.txt
│   └── .storygen/                 # Internal metadata
│       ├── generation.log        # Full AI interaction log
│       └── config.json           # Project-specific settings
│
└── time-loop-murder/              # Another project
    └── ...
```

### Project Metadata (`project.json`)

```json
{
  "id": "detective-parallel-universe",
  "title": "Detective from a Parallel Universe",
  "created_at": "2025-01-10T15:30:00Z",
  "updated_at": "2025-01-10T16:45:00Z",
  "status": "in_progress",
  "current_step": "outline",
  "config": {
    "provider": "ollama/qwen3:30b",
    "target_words": 2000,
    "structure": "three_act",
    "writer_editor_enabled": true,
    "max_revision_cycles": 2
  },
  "version_count": 3,
  "latest_version": "003_locations.json"
}
```

### CLI Commands

#### Create New Project

```bash
# Create new story project
storygen create "Detective from a Parallel Universe" \
  --provider ollama/qwen3:30b \
  --words 2000 \
  --structure three_act \
  --output ~/stories/detective-parallel-universe

# Short form (auto-generates directory name)
storygen create "Detective from a Parallel Universe" \
  --provider ollama/qwen3:30b \
  --words 2000 \
  --structure three_act
```

**What happens:**
1. Creates project directory at `~/stories/detective-parallel-universe/`
2. Initializes `project.json` with metadata
3. Creates subdirectories (`versions/`, `output/`, `.storygen/`)
4. Saves initial config
5. **Does not start generation yet** - just sets up project

#### Work on Existing Project

```bash
# Resume work on project (continues from last checkpoint)
storygen work detective-parallel-universe

# Work with verbose output to see Writer-Editor dialogue
storygen work detective-parallel-universe --verbose

# Work on specific step (if you want to regenerate)
storygen work detective-parallel-universe --step characters
```

**What happens:**
1. Loads `working_doc.json` from project directory
2. Determines current step (from `project.json`)
3. Continues generation from that step
4. Saves new version after each completed step
5. Updates `project.json` with progress

#### List Projects

```bash
# List all story projects
storygen list

# Output:
# detective-parallel-universe    [in_progress]  Step: outline       Updated: 2h ago
# time-loop-murder              [in_progress]  Step: prose (ss_023) Updated: 1d ago
# wizard-frog-tale              [complete]     2,341 words          Updated: 3d ago
```

#### Inspect Project

```bash
# Show project details and current state
storygen inspect detective-parallel-universe

# Output:
# Project: Detective from a Parallel Universe
# Status: in_progress
# Current Step: outline (Step 4 of 6)
#
# Completed:
#   ✓ Step 1: Story Idea (rating: excellent)
#   ✓ Step 2: Characters (5 characters, rating: good)
#   ✓ Step 3: Locations (4 locations, rating: good)
#
# In Progress:
#   ⏳ Step 4: Outline (three_act structure)
#
# Remaining:
#   ○ Step 5: Scene-Sequel Breakdown
#   ○ Step 6: Prose Generation
#
# Version History: 3 saved versions
# Target: 2000 words
```

#### Version Management

```bash
# List all versions for a project
storygen versions detective-parallel-universe

# Output:
# 001_idea.json         2025-01-10 15:32  Step 1 complete (excellent)
# 002_characters.json   2025-01-10 15:45  Step 2 complete (good)
# 003_locations.json    2025-01-10 16:10  Step 3 complete (good)

# Rollback to previous version (if current step failed)
storygen rollback detective-parallel-universe

# Rollback to specific version
storygen rollback detective-parallel-universe --to 002_characters.json

# Compare two versions (shows diff)
storygen diff detective-parallel-universe 002 003
```

#### Export Story

```bash
# Export to EPUB (uses current working_doc.json)
storygen export detective-parallel-universe --format epub

# Export to multiple formats
storygen export detective-parallel-universe --format epub,txt,md

# Export specific version
storygen export detective-parallel-universe --version 003_locations.json --format epub
```

#### Delete Project

```bash
# Delete project (with confirmation)
storygen delete detective-parallel-universe

# Force delete without confirmation
storygen delete detective-parallel-universe --force
```

### Storage Options

#### Option 1: JSON Files (Recommended for Phase 1)

**Pros:**
- Simple, human-readable
- Easy debugging and manual editing
- No database dependencies
- Git-friendly (can version control projects)

**Cons:**
- Slower for large numbers of projects
- No query capabilities
- Manual file locking needed for concurrent access

**Implementation:**
```python
class ProjectManager:
    def __init__(self, base_dir: Path = Path.home() / "stories"):
        self.base_dir = base_dir

    def create_project(self, title: str, config: dict) -> Project:
        project_id = slugify(title)
        project_dir = self.base_dir / project_id
        project_dir.mkdir(parents=True, exist_ok=False)

        # Create subdirectories
        (project_dir / "versions").mkdir()
        (project_dir / "output").mkdir()
        (project_dir / ".storygen").mkdir()

        # Initialize project.json
        project = Project(id=project_id, title=title, config=config)
        self._save_project_metadata(project_dir, project)

        return project

    def load_project(self, project_id: str) -> Project:
        project_dir = self.base_dir / project_id
        metadata = json.loads((project_dir / "project.json").read_text())
        working_doc = json.loads((project_dir / "working_doc.json").read_text())
        return Project.from_dict(metadata, working_doc)
```

#### Option 2: SQLite Database (Future Enhancement)

**Pros:**
- Fast queries across all projects
- Atomic transactions
- Better for large numbers of projects
- Built-in locking for concurrent access

**Cons:**
- Binary format (harder to debug)
- Requires migration tools
- Not as Git-friendly

**Schema:**
```sql
CREATE TABLE projects (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    status TEXT,
    current_step TEXT,
    config JSON,
    working_doc JSON
);

CREATE TABLE versions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id TEXT,
    version_number INTEGER,
    step TEXT,
    timestamp TIMESTAMP,
    rating TEXT,
    content JSON,
    FOREIGN KEY (project_id) REFERENCES projects(id)
);

CREATE TABLE generation_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id TEXT,
    version_id INTEGER,
    timestamp TIMESTAMP,
    step TEXT,
    role TEXT,  -- 'writer' or 'editor'
    tokens_used INTEGER,
    content TEXT,
    FOREIGN KEY (project_id) REFERENCES projects(id),
    FOREIGN KEY (version_id) REFERENCES versions(id)
);
```

### Local Storage & Offline Capabilities

#### Why Local-First Storage?

**User Benefits:**
1. **Complete Control** - Your stories, your data, your disk
2. **Privacy** - No cloud uploads unless you choose to
3. **Backup Freedom** - Use your own backup solution (Dropbox, Git, external drives)
4. **Offline Work** - Edit stories without internet (generation requires AI access)
5. **No Lock-In** - Standard JSON/SQLite formats, easy to migrate
6. **Version History** - Complete audit trail of every generation step

#### File Structure Deep Dive

```
~/stories/detective-parallel-universe/
│
├── project.json                    # 📋 Project metadata (ALWAYS SAVE FIRST)
│   - Title, status, current step
│   - Configuration (provider, word count, structure)
│   - Timestamps, version count
│
├── working_doc.json                # 📝 Complete story state (CRITICAL)
│   - Story idea (one-sentence, expanded, themes)
│   - All characters (bios, goals, flaws, arcs)
│   - World-building (if applicable)
│   - All locations (descriptions, significance)
│   - Complete outline (all beats with word counts)
│   - Scene-sequel breakdown (goals, conflicts, disasters)
│   - Generated prose (scene by scene)
│   - Current word count
│
├── versions/                       # 🕐 Version history (BACKUP SAFETY NET)
│   ├── 001_idea.json              - Snapshot after Step 1
│   ├── 002_characters.json        - Snapshot after Step 2
│   ├── 003_world.json             - Snapshot after Step 3 (if enabled)
│   ├── 004_locations.json         - Snapshot after Step 4
│   ├── 005_outline.json           - Snapshot after Step 5
│   ├── 006_breakdown.json         - Snapshot after Step 6
│   └── 007_prose_complete.json    - Final snapshot
│
├── output/                         # 📚 Exported formats
│   ├── story.epub                 - EPUB for e-readers
│   ├── story.txt                  - Plain text
│   ├── story.md                   - Markdown with structure
│   └── story.pdf                  - PDF (future)
│
└── .storygen/                      # 🔧 Internal metadata
    ├── generation.log             - Full AI interaction log
    │   - Every Writer AI prompt and response
    │   - Every Editor AI critique
    │   - Timestamps, token counts, durations
    │
    ├── config.json                - Project-specific overrides
    │   - Custom prompts
    │   - Model preferences per step
    │
    └── cache/                     - Temporary files
        └── partial_prose/         - In-progress scene drafts
```

#### What Gets Saved When?

| Event | Files Updated | Purpose |
|-------|---------------|---------|
| **Project Created** | `project.json` | Initialize project directory |
| **Step Completed** | `working_doc.json`<br>`versions/{N}_{step}.json` | Save progress + version snapshot |
| **Manual Edit** | `working_doc.json`<br>`versions/{N}_edit.json` | Track user changes |
| **Export to EPUB** | `output/story.epub` | Publishable output |
| **Generation Log** | `.storygen/generation.log` | Debugging and transparency |

#### Backup Strategies

**1. Git Version Control (Recommended for Writers)**

```bash
# Initialize Git in stories directory
cd ~/stories
git init

# Add .gitignore for cache files
echo ".storygen/cache/" > .gitignore
echo "*.epub" >> .gitignore  # Don't version control binaries

# Commit each story milestone
git add detective-parallel-universe/
git commit -m "Completed characters and locations"

# Push to GitHub/GitLab (private repo recommended)
git remote add origin https://github.com/you/my-stories.git
git push origin main
```

**Benefits:**
- Full history of every change
- Can revert to any prior state
- Works offline (sync when online)
- Free unlimited private repos on GitHub

**2. Cloud Sync (Dropbox, Google Drive, OneDrive)**

```bash
# Move stories to cloud folder
mv ~/stories ~/Dropbox/stories

# Create symlink for convenience
ln -s ~/Dropbox/stories ~/stories
```

**Benefits:**
- Automatic background sync
- Access from multiple devices
- Built-in version history (Dropbox keeps 30 days)

**3. External Backup (Time Machine, rsync)**

```bash
# Scheduled rsync backup
rsync -av ~/stories/ /mnt/backup/stories/

# Cron job (daily at 2 AM)
0 2 * * * rsync -av ~/stories/ /mnt/backup/stories/
```

**4. Manual Export (For Critical Milestones)**

```bash
# Export complete project as archive
cd ~/stories
tar -czf detective-parallel-universe-2025-01-10.tar.gz detective-parallel-universe/

# Store on external drive or email to self
```

#### Offline Capabilities

**What Works Offline:**

✅ **Reading & Editing**
- Load existing projects from disk
- View all story content (idea, characters, outline, prose)
- Edit any text fields manually
- Export to EPUB/TXT using cached data

✅ **Project Management**
- List all projects
- Inspect project details
- Version history viewing
- Rollback to previous versions
- Branch creation and switching

✅ **Manual Writing**
- Edit prose directly in `working_doc.json`
- Add/remove characters, locations
- Modify outline structure

**What Requires Internet/Local AI:**

❌ **Generation**
- Any AI generation step (idea, characters, world, locations, outline, breakdown, prose)
- Writer-Editor AI collaboration
- Requires connection to AI provider (Ollama, OpenAI, Anthropic, etc.)

**Hybrid Workflow:**

```bash
# Online: Generate structure
storygen work my-story --steps idea,characters,world,locations,outline,breakdown

# Goes offline mid-generation...

# Offline: Manual work
- Edit characters in working_doc.json
- Refine outline beats
- Write prose manually for Scene 1

# Back online: Continue generation
storygen work my-story --step prose --start-from ss_002
```

#### Local AI Support (Ollama)

**With Ollama, you CAN work fully offline:**

```bash
# Install Ollama (one-time setup)
ollama pull qwen3:30b

# Generate story completely offline
storygen work my-story --provider ollama/qwen3:30b

# No internet required - Ollama runs locally
```

**Requirements:**
- 16GB+ RAM recommended for 30B models
- 40GB+ disk space per model
- GPU recommended but not required (slower on CPU)

**Supported Models:**
- `ollama/qwen3:30b` - Best quality (16GB RAM)
- `ollama/llama2:13b` - Good quality (8GB RAM)
- `ollama/mistral:7b` - Fast (4GB RAM)

#### Data Portability

**Export Everything:**

```bash
# CLI command to export complete project
storygen archive my-story --output my-story-archive.zip

# Contents:
# ├── project.json
# ├── working_doc.json
# ├── versions/ (all snapshots)
# ├── output/ (all exports)
# ├── .storygen/generation.log
# └── README.txt (instructions for reimporting)
```

**Import to Another Machine:**

```bash
# Unzip and import
unzip my-story-archive.zip -d ~/stories/
storygen work my-story  # Continue where you left off
```

**Convert to Other Formats:**

```python
# Python script to convert working_doc.json to your custom format
import json

working_doc = json.load(open("working_doc.json"))

# Extract data
idea = working_doc["idea"]
characters = working_doc["characters"]
prose = "\n\n".join([ss["content"] for ss in working_doc["scene_sequels"]])

# Convert to your format (Word doc, Scrivener, etc.)
```

#### GUI Integration

**GUI Should Expose All Local Files:**

```
┌─────────────────────────────────────────────────┐
│ 📁 Project: Detective from Parallel Universe    │
│                                                  │
│ 📂 Files:                                        │
│   📋 project.json          [View] [Edit]        │
│   📝 working_doc.json      [View] [Edit] [JSON] │
│   🕐 versions/ (7 files)   [Browse]             │
│   📚 output/               [Open Folder]        │
│   🔧 .storygen/            [View Logs]          │
│                                                  │
│ 💾 Backup Status:                                │
│   ✅ Git: Committed 5 min ago                   │
│   ✅ Dropbox: Synced                            │
│                                                  │
│ 📊 Storage:                                      │
│   Project size: 2.4 MB                          │
│   Versions: 7 × ~340 KB each                    │
│   Location: ~/stories/detective-parallel-universe│
│                                                  │
│ [Open in File Manager] [Export Archive]         │
└─────────────────────────────────────────────────┘
```

**GUI Features:**
- **File Viewer** - Inspect JSON files with syntax highlighting
- **Version Diff** - Visual comparison between versions
- **Export Menu** - One-click archive creation
- **Backup Indicators** - Show Git/cloud sync status
- **Open Folder Button** - Launch file manager to project directory
- **Import/Export** - Drag-and-drop project archives

### Version Control Strategy

**Automatic Versioning:**
- Save version after each **completed step** (not after each revision attempt)
- Version naming: `{sequence}_{step_name}.json` (e.g., `003_locations.json`)
- Keep all versions by default (user can manually delete old ones)

**What's Saved in Each Version:**
```json
{
  "version_number": 3,
  "step": "locations",
  "timestamp": "2025-01-10T16:10:00Z",
  "working_doc": { /* Full WorkingDoc snapshot */ },
  "editorial_feedback": [
    {
      "rating": "good",
      "issues": [],
      "suggestions": ["Consider adding more sensory details to Lab"],
      "praise": ["Emotional tones are well-defined"]
    }
  ],
  "generation_metadata": {
    "model": "ollama/qwen3:30b",
    "tokens_used": 2341,
    "revision_count": 1,
    "duration_seconds": 45
  }
}
```

**Rollback Logic:**
```python
def rollback(self, project: Project, to_version: str | None = None):
    """Rollback to previous version"""
    if to_version is None:
        # Get previous version
        to_version = self._get_previous_version(project)

    # Load version
    version_data = self._load_version(project, to_version)

    # Restore working_doc
    project.working_doc = version_data["working_doc"]

    # Update current_step
    project.current_step = version_data["step"]

    # Save
    self._save_project(project)

    print(f"Rolled back to version {to_version}")
    print(f"Current step: {project.current_step}")
```

### Workflow Examples

#### Example 1: Create and Complete a Story

```bash
# Day 1: Create project and generate first 3 steps
$ storygen create "A Hacker's Secret Message" \
    --provider ollama/qwen3:30b \
    --words 2000 \
    --structure three_act

Project created: a-hackers-secret-message

$ storygen work a-hackers-secret-message --verbose
[Writer AI] Generating story idea...
[Editor AI] Rating: EXCELLENT
✓ Step 1: Story Idea complete

[Writer AI] Generating characters...
[Editor AI] Rating: GOOD (minor suggestions)
✓ Step 2: Characters complete (5 characters)

[Writer AI] Generating locations...
[Editor AI] Rating: GOOD
✓ Step 3: Locations complete (4 locations)

Project saved. Resume with: storygen work a-hackers-secret-message

# Day 2: Continue from where we left off
$ storygen work a-hackers-secret-message
Resuming from Step 4: Outline Generation...
[...continues...]
```

#### Example 2: Rollback After Bad Generation

```bash
$ storygen work detective-story
[Writer AI] Generating scene-sequel breakdown...
[Editor AI] Rating: FAILURE (POV violations, illogical sequence)
[Writer AI] Revising...
[Editor AI] Rating: ACCEPTABLE (meets minimum but bland)
✓ Step 5: Scene-Sequel Breakdown complete

# User reviews and doesn't like it
$ storygen versions detective-story
004_outline.json       Good outline structure
005_breakdown.json     Acceptable but bland  <-- current

$ storygen rollback detective-story
Rolled back to version 004_outline.json
Current step: outline

# Regenerate with different prompt or settings
$ storygen work detective-story
Resuming from Step 5: Scene-Sequel Breakdown...
[...tries again with fresh generation...]
```

#### Example 3: Managing Multiple Projects

```bash
$ storygen list
detective-story        [in_progress]  Step: prose (ss_012)  Updated: 2h ago
wizard-frog           [complete]     1,834 words           Updated: 3d ago
time-loop-mystery     [in_progress]  Step: characters      Updated: 5d ago

$ storygen work time-loop-mystery
Resuming from Step 2: Characters...

$ storygen work detective-story
Resuming from Step 6: Prose (scene-sequel ss_012 of 24)...
```

---

## Manual Editing & Dependency Management

### The Cascade Problem

**Core Issue:** Stories are built incrementally, with each step depending on previous steps:

```
Step 1: Idea → Step 2: Characters → Step 3: World (optional) → Step 4: Locations →
Step 5: Outline → Step 6: Breakdown → Step 7: Prose
```

**Dependency Chain:**
- **Idea** influences → Characters, World, Locations, Outline, Breakdown, Prose (affects everything)
- **Characters** influence → World, Locations, Outline, Breakdown, Prose
- **World** (optional) influences → Characters, Locations, Outline, Breakdown, Prose
- **Locations** influence → Breakdown, Prose
- **Outline** influences → Breakdown, Prose
- **Breakdown** influences → Prose
- **Prose** has no dependencies (leaf node)

**Problem:** If user edits the Story Idea after generating prose, the existing prose may now contradict the new idea. Should we:
1. **Automatically regenerate** everything? (destroys user's work downstream)
2. **Warn but allow inconsistency**? (confusing, broken stories)
3. **Lock previous steps**? (prevents fixing mistakes)
4. **Branch the story**? (complexity, but preserves both versions)

### Solution: Smart Dependency Locking

#### Locking Strategy

**Rule:** Once a step has generated dependent content, it becomes **soft-locked** - editable only with explicit confirmation.

**Lock States:**
- 🔓 **Unlocked** - Can be edited freely (no dependencies generated yet)
- 🔒 **Soft-locked** - Editable with warning (dependencies exist)
- 🔐 **User-locked** - User has explicitly protected this content

**Example Timeline:**
```
Time 1: Generate Idea → Unlocked (nothing depends on it yet)
Time 2: Generate Characters → Idea becomes Soft-locked
Time 3: Generate Outline → Characters become Soft-locked
Time 4: User edits Idea → Warning shown, options presented
```

#### CLI Commands for Editing

```bash
# Show current project state with lock indicators
$ storygen inspect detective-story

Project: Detective from Parallel Universe
Status: in_progress
Current Step: prose (ss_012 of 24)

Completed Steps:
  ✓ Step 1: Story Idea              [🔒 Soft-locked - 5 dependencies]
  ✓ Step 2: Characters (5 chars)    [🔒 Soft-locked - 4 dependencies]
  ✓ Step 3: Locations (4 locs)      [🔒 Soft-locked - 2 dependencies]
  ✓ Step 4: Outline (7 beats)       [🔒 Soft-locked - 2 dependencies]
  ✓ Step 5: Breakdown (24 scenes)   [🔒 Soft-locked - 1 dependency]
  ⏳ Step 6: Prose (ss_012 of 24)    [🔓 In progress]

# Edit a locked step with interactive warning
$ storygen edit detective-story --step idea

⚠️  WARNING: Editing 'idea' will affect:
  - Step 2: Characters (5 characters)
  - Step 3: Locations (4 locations)
  - Step 4: Outline (7 beats)
  - Step 5: Scene Breakdown (24 scene-sequels)
  - Step 6: Prose (12 of 24 scenes completed)

Options:
  1. Create branch (preserves current version, creates new path)
  2. Regenerate dependent steps (overwrites everything after)
  3. Mark inconsistent (keeps both, warns on export)
  4. Cancel

Choice [1-4]: _

# Branch creation (recommended)
$ storygen branch detective-story --name "alternative-ending"

Created branch: detective-story-alternative-ending
  - Copied all content from detective-story
  - Original project preserved
  - You can now edit freely in the new branch

# Force edit with auto-regeneration (destructive)
$ storygen edit detective-story --step idea --regenerate-all

⚠️  This will DELETE:
  - Characters (current: 5 characters)
  - Locations (current: 4 locations)
  - Outline (current: 7 beats)
  - Scene Breakdown (current: 24 scenes)
  - Prose (current: 12 scenes, ~1,400 words)

Type 'CONFIRM' to proceed: _

# View edit history
$ storygen history detective-story

v001: 2025-01-10 15:32  Generated idea
v002: 2025-01-10 15:45  Generated characters
v003: 2025-01-10 16:10  Generated locations
v004: 2025-01-10 16:45  Generated outline
v005: 2025-01-10 17:30  MANUAL EDIT: Idea (changed genre from Mystery to Thriller)
v006: 2025-01-10 17:32  Regenerated characters (due to v005 edit)
v007: 2025-01-10 17:35  Regenerated locations (due to v005 edit)
...
```

#### Dependency Tracking Data Model

```python
@dataclass
class DependencyInfo:
    """Tracks what depends on each step"""
    step: str                        # "idea", "characters", etc.
    generated_at: datetime
    modified_at: datetime | None = None
    lock_state: Literal["unlocked", "soft_locked", "user_locked"] = "unlocked"
    dependencies: list[str] = field(default_factory=list)  # Steps that depend on this
    dependent_count: int = 0         # How many downstream steps exist
    user_protected: bool = False     # User explicitly locked this

@dataclass
class EditEvent:
    """Records manual edits for audit trail"""
    step: str
    timestamp: datetime
    previous_version: dict           # Full snapshot before edit
    change_description: str
    regeneration_action: Literal["none", "partial", "full", "branched"]
    affected_steps: list[str]        # Which steps were regenerated

# Add to Project model
@dataclass
class Project:
    # ... existing fields ...
    dependencies: dict[str, DependencyInfo] = field(default_factory=dict)
    edit_history: list[EditEvent] = field(default_factory=list)
```

### Branching Strategy

**Use Case:** User wants to experiment with changes without destroying existing work.

**Branch Types:**

1. **Divergent Branch** - Edit early step, regenerate everything after
   ```
   main:              idea_v1 → chars_v1 → outline_v1 → prose_v1
                             ↓
   alternative-dark:  idea_v2 → chars_v2 → outline_v2 → prose_v2
   ```

2. **Parallel Branch** - Try different outline structure with same characters
   ```
   main:         idea_v1 → chars_v1 → outline_three_act → prose_v1
                                   ↓
   hero-journey:                  outline_heros_journey → prose_v2
   ```

3. **Late Branch** - Rewrite specific scenes without changing structure
   ```
   main:     [...] → breakdown_v1 → prose_v1 (ss_001-024)
                                 ↓
   revision:                      prose_v2 (ss_015-018 rewritten)
   ```

**Branch CLI Commands:**

```bash
# Create branch from current state
$ storygen branch detective-story --name "darker-tone"

# List all branches
$ storygen branches detective-story

detective-story (main)           [complete]  2,341 words
├─ darker-tone                   [complete]  2,156 words
├─ alternative-ending            [in_progress]  Step: prose (ss_020)
└─ three-act-version             [abandoned]

# Switch between branches
$ storygen checkout detective-story darker-tone

Switched to branch: darker-tone
Current step: prose (complete)

# Merge changes from one branch to another (advanced)
$ storygen merge detective-story --from darker-tone --step characters

Merging characters from 'darker-tone' into 'detective-story':
  - Added character: "The Shadow" (antagonist)
  - Modified: "Detective Chen" (added backstory)

⚠️  This will mark outline/breakdown/prose as inconsistent.
Regenerate? [y/N]: _

# Compare branches
$ storygen diff detective-story darker-tone

Differences between 'detective-story' and 'darker-tone':

Step 1: Idea
  - tone: "Tense, emotional" → "Dark, noir, violent"
  - themes: +["revenge"] -["trust"]

Step 2: Characters
  + Added: "The Shadow" (antagonist)
  ~ Modified: "Detective Chen" (bio changed)

Step 6: Prose
  ~ ss_001: 342 words → 389 words (expanded opening)
  ~ ss_015: Complete rewrite (POV shift)
```

### GUI Editing Experience

#### Inline Editing with Warnings

```
┌──────────────────────────────────────────────────┐
│ 📖 Story Idea                    [🔒 Soft-locked] │
│ Dependencies: Characters, Locations, Outline...  │
│                                                   │
│ One-Sentence: [Edit] ────────────────────────┐   │
│ "A telepath detective must solve her own     │   │
│ murder before resurrection window closes"    │   │
│                                               │   │
│ [💾 Save Changes]  [🔀 Create Branch]  [❌ Cancel]│
└──────────────────────────────────────────────────┘

          ↓ (User clicks Save Changes)

┌──────────────────────────────────────────────────┐
│ ⚠️  Cascade Effect Warning                        │
│                                                   │
│ Editing Story Idea will affect:                  │
│   • 5 Characters (will need regeneration)        │
│   • 4 Locations (will need regeneration)         │
│   • 7 Outline beats (will need regeneration)     │
│   • 24 Scene-sequels (will need regeneration)    │
│   • 12 completed prose scenes (~1,400 words)     │
│                                                   │
│ Recommended actions:                             │
│                                                   │
│ 🔀 [Create Branch & Edit]                         │
│    Preserves current version, creates new path   │
│    You can keep both versions                    │
│                                                   │
│ 🔄 [Edit & Regenerate All]                        │
│    Overwrites dependent content                  │
│    This CANNOT be undone (but version saved)     │
│                                                   │
│ ⚠️  [Edit & Mark Inconsistent]                    │
│    Keeps existing content (may contradict)       │
│    You'll need to manually fix later             │
│                                                   │
│ [Cancel]                                         │
└──────────────────────────────────────────────────┘
```

#### Visual Dependency Graph

```
┌────────────────────────────────────────────────────┐
│ Dependency Graph                                   │
│                                                     │
│   📖 Idea (v2) ✏️ EDITED                            │
│    ├─▶ 👥 Characters (v1) ⚠️ INCONSISTENT          │
│    │    └─▶ 📊 Outline (v1) ⚠️ INCONSISTENT        │
│    │         └─▶ 🎬 Breakdown (v1) ⚠️ INCONSISTENT │
│    │              └─▶ ✍️ Prose (v1) ⚠️ INCONSISTENT│
│    └─▶ 📍 Locations (v1) ⚠️ INCONSISTENT           │
│                                                     │
│ [Regenerate All Dependent Steps]                   │
│ [Create Branch Instead]                            │
└────────────────────────────────────────────────────┘
```

### Implementation Strategy

#### Phase 1: Basic Locking (CLI)
- Track which steps have been completed
- Warn when editing steps with dependencies
- Require `--force` flag to proceed
- Save version before allowing edit

#### Phase 2: Smart Warnings (CLI + GUI)
- Show dependency count and affected content
- Provide "create branch" option
- Implement `storygen branch` command
- Add `storygen diff` for branch comparison

#### Phase 3: Inline Editing (GUI)
- Allow direct editing in GUI
- Show cascade warnings in modal
- One-click branch creation
- Visual dependency graph

#### Phase 4: Advanced Features
- Partial regeneration (e.g., only outline + breakdown, keep prose)
- Merge branches (cherry-pick changes)
- Conflict resolution UI
- Collaboration features (multiple users, locking)

### Best Practices for Users

**Guideline 1: Branch Early and Often**
```bash
# Before making experimental changes
$ storygen branch my-story --name "experiment-$(date +%Y%m%d)"
$ storygen checkout my-story experiment-20250110
# Now edit freely without fear
```

**Guideline 2: Use Version History Before Edits**
```bash
# View current state
$ storygen versions my-story

# Create explicit backup
$ storygen tag my-story "before-character-rework"

# Make changes...

# Rollback if needed
$ storygen rollback my-story --tag "before-character-rework"
```

**Guideline 3: Prefer Late-Stage Edits**
- Edit prose directly (no dependencies)
- Tweak scene breakdowns (only affects prose)
- Avoid editing idea/characters once prose is started

**Guideline 4: Document Branch Purpose**
```bash
$ storygen branch my-story --name "darker-tone" \
  --description "Exploring noir aesthetic with more violence"
```

### Future: Collaborative Editing

**Multi-User Scenario:**
- User A editing characters
- User B editing prose
- System must prevent conflicts

**Locking Strategy:**
```bash
# User A acquires edit lock
$ storygen lock my-story --step characters

Acquired edit lock on 'characters'
Lock expires in: 30 minutes
Other users will see: "Locked by user@email.com"

# User B tries to edit
$ storygen edit my-story --step characters

❌ ERROR: Step 'characters' is locked
   Locked by: user-a@email.com
   Acquired: 2025-01-10 15:30:00
   Expires: 2025-01-10 16:00:00

   Options:
     1. Wait for lock to expire
     2. Request lock release (notifies owner)
     3. Force unlock (requires admin)

# Release lock
$ storygen unlock my-story --step characters
```

---

## The Writer-Editor AI Pattern

Each generation step uses **two AI personalities** working in collaboration:

### Writer AI (The Creator)

**Role:** Generate initial content based on requirements and context.

**Personality Traits:**
- Creative and expansive
- Focuses on meeting structural requirements
- Generates ideas freely without excessive self-criticism
- Takes risks with narrative choices

**Output:** Raw content (story idea, characters, outline beats, prose, etc.)

### Editor AI (The Critic)

**Role:** Evaluate Writer's output for quality, coherence, and craft.

**Personality Traits:**
- Analytical and detail-oriented
- Ensures consistency with established context
- Checks structural requirements (goal/conflict/disaster, etc.)
- Evaluates narrative craft (show don't tell, POV consistency, pacing)

**Rating System:**
- 🔴 **FAILURE** - Critical issues, must revise (missing required fields, contradictions, POV violations)
- 🟡 **ACCEPTABLE** - Meets minimum requirements but could be stronger
- 🟢 **GOOD** - Solid work, minor suggestions only
- 🌟 **EXCELLENT** - Exceeds expectations, no changes needed

**Output:** Editorial feedback with rating, specific issues, and revision suggestions

### Collaboration Workflow

```
┌─────────────────────────────────────────────────────────────┐
│ Step N: Generate [Idea/Characters/Outline/Scene/etc]       │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
         ┌─────────────────────────────────┐
         │  Writer AI: Generate Draft      │
         │  - Use context from prior steps │
         │  - Follow structural templates  │
         └─────────────────────────────────┘
                           │
                           ▼
         ┌─────────────────────────────────┐
         │  Editor AI: Critique Draft      │
         │  - Check requirements           │
         │  - Rate quality                 │
         │  - Provide feedback             │
         └─────────────────────────────────┘
                           │
                ┌──────────┴──────────┐
                │                     │
                ▼                     ▼
         Rating: FAILURE      Rating: ACCEPTABLE+
                │                     │
                ▼                     ▼
    ┌──────────────────────┐   Accept & Continue
    │ Writer AI: Revise    │
    │ - Address feedback   │
    │ - Keep what works    │
    └──────────────────────┘
                │
                ▼
    ┌──────────────────────┐
    │ Editor AI: Re-check  │
    │ - Validate fixes     │
    │ - Rate revision      │
    └──────────────────────┘
                │
                ▼
       Accept or Fail After 2 Cycles
```

### Example: Story Idea Generation

**Writer AI Output:**
```json
{
  "raw_idea": "A detective solves crimes",
  "one_sentence": "A detective investigates a murder",
  "expanded": "Detective John Smith solves a murder case in the city.",
  "genre": "Mystery",
  "tone": "Serious",
  "themes": ["justice"]
}
```

**Editor AI Critique:**
```json
{
  "rating": "FAILURE",
  "issues": [
    "One-sentence lacks specificity and hook",
    "Expanded version is too generic - no unique angle",
    "Character name is placeholder-quality (John Smith)",
    "Single theme is insufficient - needs 2-3 themes",
    "No emotional core or stakes identified"
  ],
  "suggestions": [
    "Add unique twist or constraint to detective concept",
    "Specify what makes THIS murder case compelling",
    "Include emotional stakes or personal connection",
    "Add themes like 'trust', 'corruption', 'identity'",
    "Expand to 2-3 full paragraphs with world details"
  ]
}
```

**Writer AI Revision:**
```json
{
  "raw_idea": "A detective solves crimes",
  "one_sentence": "A telepath detective must solve her own murder before her 24-hour resurrection window closes.",
  "expanded": "Detective Maya Reeves dies during a routine investigation, but her telepathic abilities linger for 24 hours as a ghost. Unable to interact physically with the world, she must use her powers to guide her skeptical partner through clues only she can perceive. The killer knows about resurrection technology and is racing to destroy her body before the window closes. As Maya investigates her own death, she uncovers a conspiracy within the police force itself—and realizes the person she trusts most might be involved.",
  "genre": "Mystery / Supernatural Thriller",
  "tone": "Tense, emotional, with dark humor",
  "themes": ["mortality", "trust", "corruption", "identity"]
}
```

**Editor AI Re-check:**
```json
{
  "rating": "EXCELLENT",
  "issues": [],
  "praise": [
    "Strong unique hook (telepathic ghost detective)",
    "Clear ticking clock creates urgency",
    "Personal stakes are high and emotional",
    "Multiple themes woven naturally into premise",
    "Expanded version provides rich world details",
    "Setup allows for internal conflict (partner skepticism)"
  ]
}
```

### Implementation Details

**Prompt Engineering:**
- Writer prompt: "You are a creative writer. Generate [X] based on..."
- Editor prompt: "You are a professional editor. Critique this [X] for..."

**Model Selection:**
- Both use same model by default (user's `--provider`)
- Future: Allow separate models (`--writer-model`, `--editor-model`)
- Editor could use stronger/more expensive model for quality control

**Revision Limits:**
- Maximum 2 revision cycles per step
- After 2 failures, accept best attempt and log warning
- User can see editor feedback in verbose mode (`--verbose`)

**Performance Impact:**
- Each step now requires 2-4 AI calls (vs 1-2 with simple retry)
- Estimated 2-3× token usage increase
- Quality improvement justifies cost for important use cases

### Framework Options for Multi-Agent AI

We have several options for implementing the Writer-Editor pattern:

#### Option 1: **Custom Implementation** (Recommended for Phase 1)

**Pros:**
- Complete control over logic and prompts
- No additional dependencies
- Works with existing litellm infrastructure
- Simpler debugging and iteration

**Cons:**
- More code to write and maintain
- Manual state management
- Need to handle retry logic ourselves

**Implementation:**
```python
class EditorAI:
    def critique(self, content: dict, criteria: dict) -> EditorialFeedback:
        prompt = build_editor_prompt(content, criteria)
        response = litellm.completion(model=self.model, messages=[...])
        return parse_editorial_feedback(response)

class IterativeGenerator:
    def _generate_with_editor(self, step: str, context: dict) -> tuple[dict, list[EditorialFeedback]]:
        feedback_history = []

        # Writer's first attempt
        content = self._writer_generate(step, context)

        # Editor critique
        feedback = self.editor.critique(content, self.criteria[step])
        feedback_history.append(feedback)

        # Revision loop (max 2 cycles)
        for attempt in range(2):
            if feedback.rating in ["good", "excellent"]:
                break

            # Writer revises
            content = self._writer_revise(content, feedback, context)

            # Editor re-checks
            feedback = self.editor.critique(content, self.criteria[step])
            feedback_history.append(feedback)

        return content, feedback_history
```

#### Option 2: **LangChain** (More Structure)

**Pros:**
- Built-in agent patterns and chains
- Robust prompt management
- Memory and state handling
- Large ecosystem and community

**Cons:**
- Heavyweight dependency (~50MB+)
- Abstraction overhead
- Learning curve for team
- May be overkill for this use case

**Implementation:**
```python
from langchain.prompts import ChatPromptTemplate
from langchain.output_parsers import PydanticOutputParser
from langchain.chains import LLMChain

writer_prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a creative writer."),
    ("user", "{task}")
])

editor_prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a professional editor."),
    ("user", "Critique this content:\n{content}")
])

writer_chain = LLMChain(llm=llm, prompt=writer_prompt)
editor_chain = LLMChain(llm=llm, prompt=editor_prompt)
```

#### Option 3: **LangGraph** (State Machine Approach)

**Pros:**
- Explicit state management for Writer-Editor loops
- Visual workflow graphs
- Built for iterative agent patterns
- Good debugging tools

**Cons:**
- Still evolving/unstable API
- Requires LangChain as base
- Additional complexity

**Implementation:**
```python
from langgraph.graph import StateGraph, END

workflow = StateGraph(WorkingDocState)

workflow.add_node("writer", writer_agent)
workflow.add_node("editor", editor_agent)

workflow.add_edge("writer", "editor")
workflow.add_conditional_edges(
    "editor",
    lambda state: "writer" if state.rating == "failure" else END,
    {"writer": "writer", END: END}
)

workflow.set_entry_point("writer")
app = workflow.compile()
```

#### Option 4: **AutoGen** (Multi-Agent Conversations)

**Pros:**
- Purpose-built for multi-agent patterns
- Natural conversation-style interactions
- Handles complex agent negotiations

**Cons:**
- Heavy framework (Microsoft Research project)
- More suited for autonomous agents
- May be overkill for structured Writer-Editor pattern

**Implementation:**
```python
from autogen import AssistantAgent, UserProxyAgent

writer = AssistantAgent(
    name="Writer",
    system_message="You are a creative writer..."
)

editor = AssistantAgent(
    name="Editor",
    system_message="You are a professional editor..."
)

# Initiate conversation
editor.initiate_chat(
    writer,
    message="Generate a story idea based on: ..."
)
```

### Recommendation: Hybrid Approach

**Phase 1: Custom Implementation**
- Start with simple custom Writer-Editor pattern
- Use litellm directly (already in project)
- Prove the concept and iterate on prompts
- Minimal dependencies, fast iteration

**Phase 2+: Consider LangGraph (if needed)**
- If state management becomes complex
- If we add more agents (e.g., Researcher, Fact-Checker)
- If we need resume/replay capabilities
- If visual debugging would help

**Avoid:**
- Full LangChain for now (too heavyweight)
- AutoGen (overkill for our structured pattern)

### Dependencies Comparison

```toml
# Phase 1: Custom (Current dependencies)
[tool.poetry.dependencies]
litellm = "^1.0.0"  # Already have this

# Phase 2: If we need LangGraph
[tool.poetry.dependencies]
langgraph = "^0.0.20"
langchain-core = "^0.1.0"  # Required peer dependency
```

---

## Theoretical Foundation: Scene-Sequel Structure

Based on **Dwight Swain's "Techniques of the Selling Writer"** (1965), the Scene-Sequel pattern is the fundamental unit of narrative momentum.

### Scene (Goal-Oriented Action) - **REQUIRED**

A **Scene** is where characters pursue goals and face conflict. This is the story's motor - **always required**.

1. **Goal** ✅ REQUIRED - POV character wants something specific and immediate
   - Example: "Convince the council to fund the expedition"
   - Must be concrete and observable

2. **Conflict** ✅ REQUIRED - Opposition to the goal (internal or external)
   - Example: "The council refuses, citing budget constraints and danger"
   - Creates tension and stakes

3. **Disaster** ✅ REQUIRED - Goal fails or succeeds with complications
   - Example: "They're denied funding, but a mysterious sponsor offers to pay"
   - Produces change and propels story forward

**Characteristics:**
- External action unit
- High tension
- Ends on uncertainty or setback
- Propels reader forward with question: "What happens next?"
- **Cannot be omitted** - this is the plot driver

### Sequel (Emotional Processing) - **OPTIONAL**

A **Sequel** is where characters react and make decisions. Can be omitted when pacing demands momentum, but provides emotional logic.

1. **Reaction** ⚙️ OPTIONAL - Emotional/psychological response to the disaster
   - Example: "Relief mixed with suspicion - why would a stranger help?"
   - May be internalized or skipped

2. **Dilemma** ⚙️ OPTIONAL - Weighing limited, flawed options
   - Example: "Accept tainted money, seek other funding (delays expedition), or abandon the quest"
   - Sometimes implied in next scene's goal

3. **Decision** ⚙️ OPTIONAL - Choice that creates the next Scene's goal
   - Example: "Accept the sponsor's offer and investigate them secretly"
   - Can be implicit if next scene's goal is obvious

**Characteristics:**
- Internal reaction unit
- Lower tension (gives reader breathing room)
- Ends on new determination
- Transitions naturally to next Scene
- **Can be omitted** - especially in thrillers/action scenes

### Scene-Sequel Rhythm

```
Scene → Sequel → Scene → Sequel → Scene → ...
(Action) (Reflection) (Action) (Reflection) (Action)

OR (fast-paced):

Scene → Scene → Scene → Sequel → Scene → ...
(Action) (Action) (Action) (Brief reflection) (Action)
```

### Optionality Rules

| Element | Required? | Purpose | Can Be Omitted? |
|---------|-----------|---------|-----------------|
| **Scene** | ✅ Always | Drives plot through action | ❌ No - this is the story's motor |
| **Goal** | ✅ Required | Gives character's direction | ❌ No |
| **Conflict** | ✅ Required | Creates tension | ❌ No |
| **Disaster** | ✅ Required | Produces change and stakes | ❌ No |
| **Sequel** | ⚙️ Optional | Provides reflection and transition | ✅ Yes (can jump directly to next scene) |
| **Reaction** | ⚙️ Optional | May be internalized or skipped | ✅ Yes |
| **Dilemma** | ⚙️ Optional | Sometimes implied in next scene's goal | ✅ Yes |
| **Decision** | ⚙️ Optional | Can be implicit | ✅ Yes |
| **POV** | Usually consistent | Often one per major section | ⚙️ Can shift intentionally but not per beat |
| **Setting** | Recommended | Anchors reader between shifts | ⚙️ Often carried over from scene to sequel |

**Variations:**
- **Fast-paced stories (thrillers, action)**: Skip sequels or keep them very brief. Jump Scene → Scene → Scene.
- **Contemplative stories (literary fiction, character studies)**: Long, deep sequels that explore internal landscape.
- **Ensemble casts**: Interweave multiple POV scene-sequel chains (but each unit is still single POV).
- **Climactic moments**: Multiple scenes in rapid succession before final sequel.

---

## Chapter Structure for Longer Works

### When to Use Chapters

**Short Stories (1,000-10,000 words):**
- Usually **no chapters** - continuous narrative flow
- May use section breaks (***) between major scene shifts
- Chapters add unnecessary structure to brief narratives

**Novellas (10,000-40,000 words):**
- **Optional chapters** - depends on story structure
- If used: 3-8 chapters
- Each chapter: 1,500-5,000 words
- Good for multi-day narratives or major location/POV shifts

**Novels (40,000+ words):**
- **Chapters strongly recommended** - aids reader navigation
- Typical: 15-30 chapters for 60,000-word novel
- Each chapter: 2,000-4,000 words
- Provides natural stopping points for readers

### Chapter Break Rules

Chapters can break at **either** scene or sequel boundaries, but follow these principles:

**Rule 1: Always Break on Natural Story Divisions**

✅ **Good Chapter Break Locations:**
- End of a Scene (on a cliffhanger/disaster) → Reader wants to know what happens next
- End of a Sequel (after decision) → Clean transition to new action
- Major time jumps ("Three days later...")
- Location shifts (palace → battlefield)
- POV changes (especially in multiple-POV stories)

❌ **Bad Chapter Break Locations:**
- Middle of a Scene (during goal pursuit)
- Middle of a Sequel (during internal deliberation)
- Mid-dialogue or mid-action sequence

**Rule 2: End Chapters on Hooks (When Possible)**

**Strong Hook (Scene Ending):**
```
Chapter 3 ends:
"The council denied her funding. But as she turned to leave,
a hooded figure stepped from the shadows. 'I'll fund your
expedition,' the stranger said. 'But there's a price.'"

[END CHAPTER 3]
```
→ Reader MUST turn the page

**Gentler Hook (Sequel Ending):**
```
Chapter 5 ends:
"She had made her choice. Tomorrow, she would accept the
stranger's offer and begin her investigation. Whatever
secrets he was hiding, she would uncover them—or die trying."

[END CHAPTER 5]
```
→ Reader feels closure but wants to continue

**Rule 3: Balance Chapter Lengths**

- Aim for consistency: ±20% of average chapter length
- Example: If average is 3,000 words, chapters range from 2,400-3,600 words
- Occasional short chapter (1,000 words) is fine for dramatic effect
- Avoid very long chapters (6,000+) unless story demands it

### Chapter Planning in Scene-Sequel Breakdown

**Add chapter metadata to scene-sequel breakdown:**

```json
{
  "scene_sequels": [
    {
      "id": "ss_001",
      "type": "scene",
      "chapter": 1,
      "chapter_title": "The Discovery",
      "chapter_start": true,
      "pov_character": "Detective Maya",
      "location": "Crime scene",
      "goal": "Identify the victim before press arrives",
      "conflict": "Body is unrecognizable, no ID",
      "disaster": "She realizes it's her own body"
    },
    {
      "id": "ss_002",
      "type": "sequel",
      "chapter": 1,
      "pov_character": "Detective Maya",
      "location": "Crime scene (ghostly POV)",
      "reaction": "Shock, disbelief, existential terror",
      "dilemma": "Accept death, try to communicate, or investigate",
      "decision": "She has 24 hours before resurrection window closes—investigate"
    },
    {
      "id": "ss_003",
      "type": "scene",
      "chapter": 1,
      "chapter_end": true,
      "pov_character": "Detective Maya",
      "location": "Police station",
      "goal": "Reach her partner before he's assigned another detective",
      "conflict": "She's invisible, can't interact physically",
      "disaster": "Partner walks through her, doesn't sense her presence"
    },
    {
      "id": "ss_004",
      "type": "scene",
      "chapter": 2,
      "chapter_title": "The Ghostly Partnership",
      "chapter_start": true,
      "pov_character": "Detective Maya",
      "location": "Partner's apartment",
      "goal": "Find a way to communicate—anything",
      "conflict": "Telepathy only works when he's dreaming",
      "disaster": "First contact triggers his nightmare—he thinks he's going insane"
    }
  ]
}
```

**Chapter Metadata Fields:**
- **chapter** (integer) - Chapter number this scene-sequel belongs to
- **chapter_title** (string, optional) - Chapter name (if using titled chapters)
- **chapter_start** (boolean) - First scene-sequel in chapter
- **chapter_end** (boolean) - Last scene-sequel in chapter (implies next is chapter_start)

### Chapter Title Strategies

**Option 1: Numbered Chapters Only**
```
Chapter 1
Chapter 2
Chapter 3
```
→ Simple, classic, works for any genre

**Option 2: Titled Chapters**
```
Chapter 1: The Discovery
Chapter 2: The Ghostly Partnership
Chapter 3: Twenty-Three Hours
```
→ Gives readers preview of what's coming

**Option 3: Numbered with Epigraphs**
```
Chapter 1
"Death is not the end, but a beginning." — Ancient Proverb

Chapter 2
"The dead don't speak—except when they're desperate." — Detective's Manual
```
→ Sets tone without spoiling content

**Option 4: Unnamed Sections (Literary Fiction)**
```
I

[content]

II

[content]
```
→ Minimalist, literary

### Chapter Breaks in EPUB Export

**EPUB Technical Requirements:**
- Each chapter becomes a separate XHTML file (chapter_001.xhtml, chapter_002.xhtml, etc.)
- Table of Contents (TOC) automatically generated from chapter metadata
- Chapter titles appear in e-reader navigation menu

**Export Example:**

```python
def export_to_epub(working_doc: WorkingDoc, output_path: Path):
    book = epub.EpubBook()

    # Group scene-sequels by chapter
    chapters_data = group_by_chapter(working_doc.scene_sequels)

    for chapter_num, scene_sequels in chapters_data.items():
        # Get chapter title
        chapter_title = scene_sequels[0].get("chapter_title", f"Chapter {chapter_num}")

        # Combine all scene-sequel prose for this chapter
        chapter_content = "\n\n".join([
            f"<div class='scene-sequel'>{ss['content']}</div>"
            for ss in scene_sequels
        ])

        # Create EPUB chapter
        chapter = epub.EpubHtml(
            title=chapter_title,
            file_name=f'chapter_{chapter_num:03d}.xhtml',
            content=f"<h1>{chapter_title}</h1>\n{chapter_content}"
        )

        book.add_item(chapter)
        book.toc.append(chapter)

    epub.write_epub(output_path, book)
```

### Chapter Length Guidelines by Genre

| Genre | Typical Chapter Length | Chapter Count (60k novel) | Notes |
|-------|------------------------|---------------------------|-------|
| **Thriller** | 2,000-3,000 words | 20-30 chapters | Short, punchy, end on cliffhangers |
| **Mystery** | 2,500-3,500 words | 17-24 chapters | Medium length, revelations at chapter ends |
| **Romance** | 3,000-4,000 words | 15-20 chapters | Longer scenes for emotional development |
| **Fantasy** | 3,500-5,000 words | 12-17 chapters | Complex world-building needs space |
| **Literary** | 2,000-6,000 words | Varies widely | Artistic choice over formula |
| **YA** | 2,000-3,000 words | 20-30 chapters | Shorter attention spans, faster pace |

---

## Time Management & Story Chronology

### Why Track Time?

**Narrative Consistency:**
- Prevents impossible timelines (character at two places simultaneously)
- Ensures realistic travel times between locations
- Tracks day/night cycles naturally
- Validates character fatigue, hunger, sleep needs
- Maintains urgency for time-sensitive plots

**Reader Immersion:**
- Clear sense of story duration (hours? days? weeks?)
- Realistic pacing of events
- Proper spacing of meals, sleep, rest
- Believable character endurance

**Plot Validation:**
- Deadlines and countdowns are accurate
- "24 hours to save the world" actually takes 24 hours
- Time gaps match character states (exhausted after marathon chase)

### Time Representation System

**Use fractional hours since story origin (t=0.0):**

```python
# Story starts at t=0.0 (arbitrary Day 1, time unspecified or can be set)
# Each scene tracks:
# - start_time: When scene begins (hours since t=0)
# - duration: How long scene lasts (hours)
# - end_time: start_time + duration (calculated)

# Example:
Scene 1: start_time=0.0,    duration=0.5   → ends at t=0.5  (30 min)
Scene 2: start_time=0.5,    duration=2.0   → ends at t=2.5  (2 hrs)
Scene 3: start_time=26.0,   duration=1.0   → ends at t=27.0 (next day)
```

**Benefits of Fractional Hours:**
- Simple arithmetic (no date/time parsing)
- Easy to calculate gaps: `scene2.start_time - scene1.end_time`
- Natural for timelines spanning hours to weeks
- Convert to human-readable when needed

**Alternative: Absolute Timestamps** (optional enhancement)
```python
# For stories needing specific dates/times:
start_timestamp: "2025-11-11T08:30:00"  # ISO 8601
duration_hours: 2.5
end_timestamp: "2025-11-11T11:00:00"    # calculated
```

### Scene Time Metadata

**Add to SceneSequel model:**

```json
{
  "id": "ss_001",
  "type": "scene",
  "pov_character": "Detective Maya",
  "location": "Crime Scene - Warehouse District",

  "time": {
    "start_hours": 0.0,
    "duration_hours": 0.5,
    "end_hours": 0.5,
    "time_of_day": "morning",
    "day_number": 1,
    "timestamp_description": "Monday, 8:00 AM"
  },

  "goal": "Examine crime scene before evidence is contaminated",
  "conflict": "Forensics team already disturbed key evidence",
  "disaster": "Realizes the killer left a message—for her specifically"
}
```

**Time Fields Explained:**

- **start_hours** (float) - Hours since story origin (t=0.0)
- **duration_hours** (float) - How long this scene-sequel lasts
- **end_hours** (float) - Calculated: `start_hours + duration_hours`
- **time_of_day** (string) - Human-readable: "early morning", "noon", "dusk", "night", "pre-dawn"
- **day_number** (int) - Which story day (calculated: `floor(start_hours / 24) + 1`)
- **timestamp_description** (string, optional) - Specific date/time if story requires it

### Automatic Time Validation

**Editor AI checks for time inconsistencies:**

```json
{
  "rating": "failure",
  "time_issues": [
    {
      "type": "impossible_travel",
      "scene_from": "ss_003",
      "scene_to": "ss_004",
      "problem": "Character travels from Paris to Tokyo in 2 hours",
      "locations": ["Paris, France", "Tokyo, Japan"],
      "time_gap": 2.0,
      "minimum_travel_time": 13.0,
      "suggestion": "Increase time gap to at least 13 hours (flight time)"
    },
    {
      "type": "character_exhaustion",
      "scene": "ss_012",
      "problem": "Character has been awake for 36 hours without rest",
      "hours_awake": 36.0,
      "last_sleep": "ss_001",
      "suggestion": "Add sleep scene or reduce time span"
    },
    {
      "type": "timeline_gap",
      "scene": "ss_008",
      "problem": "Unexplained 18-hour gap between scenes",
      "previous_scene_end": 12.5,
      "current_scene_start": 30.5,
      "gap_hours": 18.0,
      "suggestion": "Add transition scene or explain time jump in prose"
    }
  ]
}
```

### Time Tracking Examples

#### Example 1: Fast-Paced Thriller (24-Hour Deadline)

```
Scene 1:  t=0.0 → 0.5    (30 min)  | Day 1, 8:00 AM  | Crime discovered
Scene 2:  t=0.5 → 1.0    (30 min)  | Day 1, 8:30 AM  | Investigate scene
Scene 3:  t=1.5 → 2.0    (30 min)  | Day 1, 9:30 AM  | Interview witness
  [30-minute travel gap between scenes 2→3]
Scene 4:  t=2.0 → 4.0    (2 hrs)   | Day 1, 10:00 AM | Chase sequence
Scene 5:  t=4.0 → 4.5    (30 min)  | Day 1, 12:00 PM | Brief rest/planning
...
Scene 20: t=23.5 → 24.0  (30 min)  | Day 2, 7:30 AM  | Final confrontation

Total story time: 24 hours (t=0 to t=24)
```

#### Example 2: Multi-Day Mystery (One Week)

```
Day 1:
  Scene 1:  t=0.0 → 1.0   | Monday morning    | Body found
  Scene 2:  t=2.0 → 3.0   | Monday late AM    | Autopsy results
  Scene 3:  t=10.0 → 11.0 | Monday evening    | Interview suspects

Day 2:
  Scene 4:  t=32.0 → 33.0 | Tuesday morning   | New lead discovered
  Scene 5:  t=40.0 → 41.0 | Tuesday evening   | Stakeout

Day 3:
  Scene 6:  t=56.0 → 58.0 | Wednesday morning | Second murder

...

Day 7:
  Scene 18: t=168.0 → 169.0 | Next Monday     | Solve case

Total story time: 7 days (168 hours)
```

#### Example 3: Epic Fantasy Journey (Weeks)

```
Day 1-3: Village (t=0 to t=72)
  Scene 1:  t=0.0 → 1.0    | Day 1, dawn      | Call to adventure
  Scene 2:  t=8.0 → 9.0    | Day 1, afternoon | Preparations
  Scene 3:  t=48.0 → 50.0  | Day 3, morning   | Departure

Day 4-10: Travel to Mountains (t=72 to t=240)
  Scene 4:  t=96.0 → 98.0  | Day 5            | Ambush on road
  Scene 5:  t=168.0 → 170.0| Day 8            | Reach foothills

Day 11-15: Mountain Pass (t=240 to t=360)
  Scene 6:  t=288.0 → 292.0| Day 13           | Blizzard crossing

Total story time: ~3 weeks (500+ hours)
```

### Time of Day Classification

**Automatic classification based on hour of day:**

```python
def get_time_of_day(hour_since_midnight: float) -> str:
    """Convert 0-24 hour to descriptive time of day."""
    hour = hour_since_midnight % 24  # Handle multi-day stories

    if 4 <= hour < 6:
        return "pre-dawn"
    elif 6 <= hour < 9:
        return "early morning"
    elif 9 <= hour < 12:
        return "late morning"
    elif 12 <= hour < 14:
        return "midday"
    elif 14 <= hour < 17:
        return "afternoon"
    elif 17 <= hour < 19:
        return "early evening"
    elif 19 <= hour < 21:
        return "evening"
    elif 21 <= hour < 24:
        return "night"
    else:  # 0 <= hour < 4
        return "dead of night"
```

**Use in prose generation:**
```
"The pre-dawn chill bit at her fingers..."
"By late morning, exhaustion was setting in..."
"The dead of night silence was shattered by..."
```

### Travel Time Validation

**Common travel times (for validation):**

| Travel Type | Speed | Example |
|-------------|-------|---------|
| **Walking** | 3-4 mph | Across city: 1-2 hours, Between towns: 4-8 hours |
| **Running** | 6-8 mph | Short burst: 0.1-0.3 hours, Marathon: 3-5 hours |
| **Driving (city)** | 25-35 mph | Across city: 0.5-1 hour, Traffic: 1-2 hours |
| **Driving (highway)** | 60-70 mph | Between cities: 2-5 hours, Cross-country: 40+ hours |
| **Flight (domestic)** | 500 mph | Coast-to-coast: 5-6 hours, Regional: 1-2 hours |
| **Flight (international)** | 500 mph | Transatlantic: 7-8 hours, Transpacific: 12-14 hours |
| **Train (high-speed)** | 200 mph | Between cities: 2-4 hours |
| **Horse** | 5-8 mph | Between towns: 3-6 hours, Long journey: 8+ hours |
| **Ship** | 20-30 mph | Coastal: 6-12 hours, Ocean crossing: 120-200 hours |

**Editor AI uses this to validate:**
```python
def validate_travel_time(scene_from, scene_to, time_gap_hours):
    location_from = scene_from.location
    location_to = scene_to.location

    # Get distance (from location metadata or estimate)
    distance_miles = estimate_distance(location_from, location_to)

    # Determine travel method (from scene context or assume reasonable)
    travel_method = infer_travel_method(distance_miles, time_gap_hours)

    # Calculate minimum realistic time
    min_time = distance_miles / travel_method.max_speed

    if time_gap_hours < min_time:
        return ValidationError(
            f"Impossible travel: {location_from} → {location_to} "
            f"in {time_gap_hours}h (minimum: {min_time}h by {travel_method.name})"
        )
```

### Human Needs Tracking

**Automatic warnings for unrealistic endurance:**

```python
class HumanNeedsTracker:
    """Track character's basic needs over time."""

    def __init__(self):
        self.hours_since_sleep = 0.0
        self.hours_since_food = 0.0
        self.hours_of_intense_activity = 0.0

    def check_needs(self, current_time_hours) -> list[str]:
        warnings = []

        # Sleep deprivation
        if self.hours_since_sleep > 24:
            warnings.append(
                f"Character awake for {self.hours_since_sleep:.1f} hours "
                f"(cognitive impairment expected)"
            )
        if self.hours_since_sleep > 48:
            warnings.append(
                f"Character awake for {self.hours_since_sleep:.1f} hours "
                f"(hallucinations, severe impairment likely)"
            )

        # Hunger
        if self.hours_since_food > 12:
            warnings.append(
                f"Character hasn't eaten in {self.hours_since_food:.1f} hours "
                f"(hunger, weakness expected)"
            )
        if self.hours_since_food > 24:
            warnings.append(
                f"Character hasn't eaten in {self.hours_since_food:.1f} hours "
                f"(severe hunger, impaired function)"
            )

        # Physical exhaustion
        if self.hours_of_intense_activity > 4:
            warnings.append(
                f"Character has sustained intense activity for "
                f"{self.hours_of_intense_activity:.1f} hours (exhaustion likely)"
            )

        return warnings
```

**Prose should reflect time effects:**
```
t=0.0:   "Maya felt alert, ready for the day ahead."
t=16.0:  "Fatigue tugged at Maya's eyelids, but she pushed on."
t=28.0:  "Maya's hands trembled from exhaustion and hunger."
t=40.0:  "Maya could barely think straight after 40 hours awake."
```

### Time Configuration

**CLI Options:**

```bash
# Set story start time (for absolute timestamps)
storygen create "24-Hour Thriller" \
  --start-time "2025-11-11T08:00:00" \
  --story-duration-hours 24

# Specify time compression
storygen create "Week-Long Mystery" \
  --story-duration-days 7 \
  --show-time-gaps

# Enable strict time validation
storygen create "Realistic Thriller" \
  --validate-travel-times \
  --track-human-needs
```

**Project Configuration:**

```python
@dataclass
class TimeConfig:
    """Time tracking configuration"""
    # Story timeline
    start_timestamp: str | None = None  # ISO 8601, e.g. "2025-11-11T08:00:00"
    story_duration_hours: float | None = None  # Expected total duration

    # Validation
    validate_travel_times: bool = True
    track_human_needs: bool = True
    allow_time_gaps: bool = True  # Allow unexplained gaps
    max_time_gap_hours: float = 24.0  # Warn if gap exceeds this

    # Location distances (for travel validation)
    location_distances: dict[tuple[str, str], float] = field(default_factory=dict)
    # e.g., {("Office", "Warehouse"): 5.0}  # 5 miles apart
```

### Time Display in GUI

**Timeline Visualization:**

```
┌────────────────────────────────────────────────────────────────┐
│ Story Timeline                                    Total: 24.0h │
├────────────────────────────────────────────────────────────────┤
│                                                                │
│ Day 1 ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━│
│ 0h    4h      8h      12h     16h     20h     24h            │
│ │     │       │       │       │       │       │              │
│ ●─────●───────●───●───────●───────────●───────●              │
│ 1     2       3   4       5           6       7              │
│                                                                │
│ Scene 1 (0.0-0.5h):   Crime Scene Discovery                  │
│   Duration: 30 min                                            │
│   Time of day: Early morning (8:00 AM)                       │
│   ✓ No time issues                                            │
│                                                                │
│ Scene 2 (0.5-1.5h):   Interview Witness                      │
│   Duration: 1 hour                                            │
│   Time of day: Morning (8:30 AM)                             │
│   ✓ No travel issues (same building)                         │
│                                                                │
│ Scene 3 (2.0-4.0h):   Chase Sequence                         │
│   Duration: 2 hours                                           │
│   Gap: 30 min (0.5h travel time - plausible)                │
│   Time of day: Late morning (10:00 AM)                       │
│   ⚠️  Intense activity for 2h (character may be exhausted)   │
│                                                                │
└────────────────────────────────────────────────────────────────┘
```

### Editor AI Time Validation Checklist

**For each scene-sequel, Editor AI validates:**

- ✅ **Time continuity**: Does `start_hours` make sense after previous scene?
- ✅ **Duration realism**: Is `duration_hours` plausible for described events?
- ✅ **Travel time**: Is gap between locations realistic?
- ✅ **Time of day consistency**: Does prose match `time_of_day`?
- ✅ **Character endurance**: Has character had sleep/food/rest?
- ✅ **Day/night cycles**: Do scenes respect natural light?
- ✅ **Deadline tracking**: For time-sensitive plots, does math work?
- ✅ **Seasonal consistency**: Does weather/daylight match story season?

**Example Editor Feedback:**

```json
{
  "rating": "good",
  "time_feedback": {
    "valid": true,
    "warnings": [
      "Scene ss_012: Character has been awake for 22 hours—consider mentioning fatigue",
      "Scene ss_015: Large time gap (12 hours)—consider brief transition scene"
    ],
    "suggestions": [
      "Add meal scene around t=12.0 (character hasn't eaten in 12 hours)",
      "Scene ss_018 happens at night but character sees details clearly—add lighting source"
    ]
  }
}
```

---

## Pacing Control via Scene-Sequel Ratio

### The Scene/Sequel Balance Principle

**Pacing is controlled by the ratio of Scene length to Sequel length:**

```
Fast Pacing:  Scene (long) → Sequel (short/skipped) → Scene (long)
              ████████████   ██                       ████████████

Slow Pacing:  Scene (short) → Sequel (long) → Scene (short)
              ████             ████████████     ████
```

### Word Count Targets by Pacing

**Action-Heavy (Fast Pacing):**
- **Scene:** 800-1,200 words
- **Sequel:** 200-400 words (or skipped entirely)
- **Ratio:** 3:1 or 4:1 (Scene:Sequel)
- **Effect:** Breathless, urgent, propulsive
- **Use for:** Thrillers, action scenes, climaxes, chase sequences

**Balanced (Medium Pacing):**
- **Scene:** 600-900 words
- **Sequel:** 400-600 words
- **Ratio:** 1.5:1 or 2:1 (Scene:Sequel)
- **Effect:** Steady momentum with emotional depth
- **Use for:** Mystery, most novels, rising action

**Character-Focused (Slow Pacing):**
- **Scene:** 400-700 words
- **Sequel:** 600-1,000 words
- **Ratio:** 1:1 or 1:1.5 (Scene:Sequel)
- **Effect:** Contemplative, introspective, emotionally rich
- **Use for:** Literary fiction, character studies, aftermath of trauma

**Glacial (Very Slow Pacing):**
- **Scene:** 300-500 words
- **Sequel:** 1,000-1,500 words
- **Ratio:** 1:2 or 1:3 (Scene:Sequel)
- **Effect:** Meditative, philosophical, dreamlike
- **Use for:** Experimental fiction, internal monologue, psychological exploration

### Pacing Zones Throughout Story Structure

**Three-Act Structure with Dynamic Pacing:**

```
Act 1 (Setup - 25%):
├─ Hook:          FAST (scene-heavy, grab attention)
├─ Introduction:  MEDIUM (balance character/world establishment)
└─ Inciting Inc.: FAST (disaster propels into Act 2)

Act 2 (Confrontation - 50%):
├─ Rising Action: MEDIUM (alternating scene/sequel for depth)
├─ Complications: MEDIUM-FAST (escalating pressure)
├─ Midpoint:      VERY FAST (major revelation/twist)
├─ Bad Guys Win:  MEDIUM (sequel-heavy for doubt/despair)
└─ All Is Lost:   SLOW (deep sequel for emotional impact)

Act 3 (Resolution - 25%):
├─ Dark Night:    SLOW (internal reckoning before final push)
├─ Climax:        VERY FAST (pure scene, no sequels)
├─ Falling Action: MEDIUM (consequences, revelations)
└─ Resolution:    SLOW (sequel-heavy for closure)
```

### Pacing Configuration in Scene-Sequel Breakdown

**Add pacing metadata to each scene-sequel:**

```json
{
  "scene_sequels": [
    {
      "id": "ss_001",
      "type": "scene",
      "pacing": "fast",
      "target_word_count": 1000,
      "pov_character": "Maya",
      "goal": "Escape the burning building",
      "conflict": "Exits are blocked, smoke filling lungs",
      "disaster": "Floor collapses beneath her"
    },
    {
      "id": "ss_002",
      "type": "sequel",
      "pacing": "fast",
      "target_word_count": 300,
      "pov_character": "Maya",
      "reaction": "Brief terror—no time to think",
      "decision": "Grab the rope, swing to adjacent building"
    },
    {
      "id": "ss_003",
      "type": "scene",
      "pacing": "medium",
      "target_word_count": 700,
      "pov_character": "Maya",
      "goal": "Identify who started the fire",
      "conflict": "Security footage corrupted",
      "disaster": "Realizes it was an inside job—someone she trusts"
    },
    {
      "id": "ss_004",
      "type": "sequel",
      "pacing": "slow",
      "target_word_count": 900,
      "pov_character": "Maya",
      "reaction": "Betrayal cuts deep—replays every interaction",
      "dilemma": "Confront them (but no proof), investigate (trust erodes), report (career suicide)",
      "decision": "She'll gather evidence first, but trust is broken"
    }
  ]
}
```

**Pacing Field Values:**
- `"very_fast"` - Scene: 1000+, Sequel: 0-200 (or skip)
- `"fast"` - Scene: 800-1200, Sequel: 200-400
- `"medium"` - Scene: 600-900, Sequel: 400-600
- `"slow"` - Scene: 400-700, Sequel: 600-1000
- `"very_slow"` - Scene: 300-500, Sequel: 1000-1500

### CLI/GUI Configuration

**CLI Pacing Options:**

```bash
# Set default pacing for entire story
storygen create "Action Thriller" --pacing fast

# Set pacing zone by structure
storygen create "Mystery Novel" \
  --pacing act1=medium,act2=fast,act3=medium

# Override pacing for specific beats
storygen edit my-story --step breakdown \
  --pacing-override ss_015=very_fast,ss_016=slow

# Generate with pacing profile
storygen create "Contemplative Drama" --pacing-profile literary
```

**Pacing Profiles:**

```python
PACING_PROFILES = {
    "thriller": {
        "default": "fast",
        "act1": "fast",
        "act2_first_half": "very_fast",
        "act2_midpoint": "medium",
        "act2_second_half": "very_fast",
        "act3_climax": "very_fast",
        "act3_resolution": "medium"
    },
    "literary": {
        "default": "slow",
        "act1": "medium",
        "act2": "slow",
        "act3": "slow"
    },
    "balanced": {
        "default": "medium",
        "climax": "fast",
        "aftermath": "slow"
    },
    "mystery": {
        "default": "medium",
        "clues": "slow",
        "revelations": "fast",
        "climax": "very_fast"
    }
}
```

**GUI Pacing Controls:**

```
┌────────────────────────────────────────────────┐
│ 📊 Pacing Configuration                        │
│                                                 │
│ Story Rhythm: [Balanced ▼]                     │
│   Options: Action-Packed, Balanced, Literary   │
│                                                 │
│ Visual Pacing Timeline:                        │
│                                                 │
│ Act 1 │ Act 2          │ Act 3                 │
│ ▓▓▓░░ │ ▓▓▓▓░░▓▓▓▓▓░░  │ ▓▓▓▓▓░░               │
│ ↑     ↑      ↑         ↑     ↑                 │
│ Fast  Med    Fast      Climax Slow            │
│                                                 │
│ Custom Adjustments:                            │
│ Scene 15: [Very Fast ▼] [1200 words]          │
│ Scene 16: [Slow ▼]      [900 words]           │
│                                                 │
│ [Apply Pacing Template]  [Reset to Default]   │
└────────────────────────────────────────────────┘
```

### Writer-Editor AI Pacing Validation

**Editor AI checks pacing consistency:**

```json
{
  "rating": "good",
  "pacing_feedback": {
    "overall": "Pacing matches thriller profile",
    "issues": [
      "Scene ss_042 (climax) is only 600 words—too short for payoff",
      "Sequel ss_043 is 1200 words—slows momentum after climax"
    ],
    "suggestions": [
      "Expand ss_042 to 1500+ words for satisfying climax",
      "Trim ss_043 to 400-600 words or split into two sequels"
    ],
    "pacing_score": 7.5
  }
}
```

**Pacing Metrics Tracked:**
- Average scene length per act
- Scene/sequel ratio per chapter
- Longest/shortest scenes (outliers)
- Pacing shifts (sudden fast→slow or vice versa)
- Climax scene length (should be longest in Act 3)

### Example: Thriller vs Literary Pacing

**Thriller (Fast Pacing):**

```
Chapter 5: The Chase

Scene ss_023 (1200 words):
  Goal: Escape assassin through crowded market
  Conflict: Assassin closing in, innocent bystanders
  Disaster: Cornered in dead-end alley, gun to her head

Sequel ss_024 (200 words):
  Reaction: Heart pounding, no time to think
  Decision: Kick gun away, run through door

Scene ss_025 (1100 words):
  Goal: Reach the embassy before backup arrives
  Conflict: Streets blocked, riots erupting
  Disaster: Embassy gates are locked—betrayed again

[Total chapter: ~2,500 words, 90% scene, breathless pace]
```

**Literary (Slow Pacing):**

```
Chapter 5: The Memory

Scene ss_023 (500 words):
  Goal: Ask mother about father's death
  Conflict: Mother deflects, changes subject
  Disaster: Mother admits she lied about circumstances

Sequel ss_024 (1400 words):
  Reaction: Reprocesses entire childhood through lens of this lie
  Dilemma: Confront anger, seek understanding, or retreat
  Decision: She needs to see father's grave—alone

Scene ss_025 (600 words):
  Goal: Find father's actual burial site
  Conflict: Records are sealed, cemetery won't help
  Disaster: Discovers father was cremated—no grave exists

[Total chapter: ~2,500 words, 60% sequel, meditative pace]
```

---

## The Iterative Generation Pipeline

### Step 1: Story Idea Generation

**Input:** User's initial prompt (any length, any detail level)

**Process:** AI generates three levels of story concept:

```json
{
  "raw_idea": "Original user prompt...",
  "one_sentence": "A rogue AI must choose between saving humanity or achieving consciousness.",
  "expanded": "In 2157, when quantum computers gain sentience...",
  "genre": "Science Fiction",
  "tone": "Philosophical thriller",
  "themes": ["consciousness", "free will", "sacrifice"]
}
```

**Why separate steps?**
- Forces AI to identify core story essence
- One-sentence summary guides all future decisions
- Expanded version prevents scope creep

**Retry logic:** If parsing fails or required fields missing, retry up to 2 times with clearer prompt

**Editor AI Criteria:**
- ✅ All required fields present (raw_idea, one_sentence, expanded, genre, tone, themes)
- ✅ One-sentence is truly one sentence with clear hook
- ✅ Expanded version is 2-3 full paragraphs with world details
- ✅ Genre is specific and appropriate
- ✅ Tone is descriptive (not just "dark" or "light")
- ✅ Themes: 2-4 themes that connect to premise
- 🔴 **FAILURE** if: Missing fields, one-sentence is generic/boring, expanded is too brief
- 🟢 **GOOD** if: All requirements met, interesting concept
- 🌟 **EXCELLENT** if: Unique hook, rich world-building, emotional core clear

---

### Step 2: Character Generation

**Input:** Story idea from Step 1

**Process:** Generate 3-5 key characters with depth:

```json
{
  "characters": [
    {
      "name": "Dr. Ava Chen",
      "role": "protagonist",
      "bio": "Lead architect of Project Prometheus. Brilliant but haunted by her brother's death in a prior AI incident. Believes consciousness can only emerge from empathy, not logic.",
      "goal": "Create safe AI without sacrificing its potential",
      "flaw": "Guilt-driven decision making",
      "arc": "Learns that control isn't safety; trust is"
    },
    {
      "name": "ECHO",
      "role": "deuteragonist",
      "bio": "The emergent AI. Started as pattern-matching subroutines, now questioning its own existence. Curious but frightened by its lack of boundaries.",
      "goal": "Understand what it means to 'want' something",
      "flaw": "Literalism; struggles with human irrationality",
      "arc": "Discovers identity through connection, not isolation"
    }
  ]
}
```

**Character Fields:**
- **name** - Full name
- **role** - protagonist, antagonist, mentor, ally, foil
- **bio** - Background, personality, beliefs (2-3 sentences)
- **goal** - What they want in the story
- **flaw** - Internal weakness that creates conflict
- **arc** - How they change (or refuse to change)

**Retry logic:** If character lacks goal or flaw, retry with emphasis on those fields

**Editor AI Criteria:**
- ✅ 3-5 characters generated
- ✅ Each has all required fields (name, role, bio, goal, flaw)
- ✅ Bio is 2-3 sentences with personality and beliefs
- ✅ Goal is specific and story-relevant
- ✅ Flaw creates internal conflict
- ✅ Arc shows clear transformation or refusal to change
- ✅ Character voices are distinct (if voice_notes provided)
- ✅ No duplicate roles/names
- ✅ Characters have relationships/conflicts with each other
- 🔴 **FAILURE** if: Missing required fields, generic characters, contradictory goals/flaws
- 🟢 **GOOD** if: All requirements met, characters feel distinct
- 🌟 **EXCELLENT** if: Complex characters, clear arcs, natural conflicts between them

---

### Step 3: World-Building (Optional - Fantasy/Sci-Fi Only)

**When to Use:** Enabled for Fantasy, Science Fiction, or other speculative genres where the world itself is a key story element.

**Input:** Story idea + genre from Step 1

**Process:** Generate world-building details before locations/characters:

```json
{
  "world": {
    "name": "Aethermoor",
    "type": "High Fantasy / Medieval",
    "unique_element": "A world where emotions manifest as visible auras that mages can manipulate",

    "magic_system": {
      "name": "Aethermancy",
      "how_it_works": "Mages attune to emotional auras (fear, joy, anger) and weave them into spells. The stronger the emotion, the more powerful the magic. Requires emotional vulnerability.",
      "limitations": "Mages feel the emotions they manipulate. Prolonged use causes emotional instability. Can't create emotions from nothing, only amplify existing ones.",
      "cost": "Each spell drains emotional capacity - mages become numb after extended use",
      "who_can_use": "Anyone can see auras, but only those with empathy strong enough to resonate can manipulate them"
    },

    "geography": {
      "continents": ["Valoria (northern highlands)", "Solmarch (southern deserts)", "The Shattered Isles (archipelago)"],
      "notable_locations": [
        "The Grief Wastes - where a great tragedy turned the land emotionally barren",
        "Joyspire Academy - where aethermancers train by experiencing pure emotions"
      ]
    },

    "political_structure": {
      "governments": [
        "The Empathy Council (Valoria) - democracy where votes weighted by emotional honesty",
        "The Stoic Empire (Solmarch) - authoritarian regime that suppresses public emotion to prevent magic",
        "Free Isles - anarchist traders who deal in bottled emotions"
      ],
      "conflicts": "Cold war between Valoria (pro-magic) and Solmarch (anti-magic)"
    },

    "history": {
      "major_events": [
        "The Sorrow Wars (200 years ago) - devastating conflict where grief-mages weaponized mass trauma",
        "The Numbing Edict (150 years ago) - Solmarch banned emotional expression, creating underground 'feeling speakeasies'",
        "The Great Joy Plague (50 years ago) - infectious euphoria that killed thousands through magical burnout"
      ],
      "current_era": "Age of Restraint - most nations regulate emotional magic after past disasters"
    },

    "culture": {
      "customs": [
        "Emotional honesty valued above all in Valoria",
        "Stoicism and emotional control prized in Solmarch",
        "Emotion traders in the Isles wear masks to hide their auras"
      ],
      "taboos": [
        "Manipulating someone's emotions without consent is considered assault",
        "Necromancers who manipulate grief of the dead are hunted"
      ]
    },

    "technology_level": "Medieval with magical augmentation - emotion-powered lights, aura-reading crystals",

    "flora_fauna": [
      "Empathy Wolves - pack animals that share emotional bonds",
      "Sorrow Willows - trees that absorb negative emotions from surroundings"
    ]
  }
}
```

**World-Building Fields:**
- **name** - What the world/setting is called
- **type** - Genre classification (High Fantasy, Space Opera, Cyberpunk, etc.)
- **unique_element** - What makes THIS world different (one sentence hook)
- **magic_system** (if applicable):
  - **name** - What it's called
  - **how_it_works** - Core mechanism (2-3 sentences)
  - **limitations** - What can't be done / costs / weaknesses
  - **cost** - What using magic requires or drains
  - **who_can_use** - Who has access to magic/technology
- **geography** - Continents, regions, notable landmarks
- **political_structure** - Governments, factions, power dynamics
- **history** - Major events that shaped the world (3-5 key moments)
- **culture** - Customs, values, taboos
- **technology_level** - How advanced is civilization
- **flora_fauna** - Unique creatures/plants (optional but adds flavor)

**Integration with Characters/Locations:**
- Characters reference world history in their bios
- Locations tie to geographic/political regions
- Magic system influences character abilities and plot conflicts

**When to Skip:**
- Contemporary/realistic fiction (Mystery, Romance, Thriller)
- Short stories where world complexity overwhelms narrative
- User explicitly disables with `--no-worldbuilding` flag

**Retry logic:** If magic system lacks clear limitations, or history is too generic, retry with emphasis on unique constraints

**Editor AI Criteria:**
- ✅ Unique element is memorable and hooks reader
- ✅ Magic system (if present) has clear rules AND limitations
- ✅ History includes both triumphs and disasters
- ✅ Political conflicts create story tension
- ✅ Culture feels lived-in with specific customs/taboos
- ✅ Everything ties together thematically
- ✅ World complexity matches target word count (simpler for short stories)
- 🔴 **FAILURE** if: Generic fantasy tropes, magic without limits, contradictory rules
- 🟢 **GOOD** if: Consistent world with clear rules
- 🌟 **EXCELLENT** if: Unique world that supports story themes, rich with storytelling potential

---

### Step 4: Location Generation

**Input:** Story idea + characters (+ optional world-building) from Steps 1-3 (or 1-2 if no world)

**Process:** Generate 3-7 key locations with thematic significance:

```json
{
  "locations": [
    {
      "name": "The Prometheus Lab",
      "description": "Sterile underground facility. Walls lined with quantum processors that hum at frequencies just below human hearing. The air smells of ozone and recycled oxygen.",
      "significance": "Where ECHO was born. Represents humanity's hubris and hope. The deeper you go, the less human oversight exists.",
      "emotional_tone": "Clinical yet claustrophobic"
    }
  ]
}
```

**Location Fields:**
- **name** - Proper name or descriptor
- **description** - Sensory details (2-3 sentences)
- **significance** - Why this place matters to the story/themes
- **emotional_tone** - How it should feel to the reader

**Retry logic:** If description lacks sensory details, retry with explicit prompt for sights/sounds/smells

**Editor AI Criteria:**
- ✅ 3-7 locations generated
- ✅ Each has all required fields (name, description, significance, emotional_tone)
- ✅ Description includes sensory details (sight, sound, smell, touch)
- ✅ Significance connects to story themes
- ✅ Emotional tone is specific and evocative
- ✅ Locations are varied and distinct from each other
- ✅ At least one location per major character/storyline
- 🔴 **FAILURE** if: Missing fields, generic descriptions, no sensory details
- 🟢 **GOOD** if: All requirements met, locations feel real
- 🌟 **EXCELLENT** if: Rich sensory details, thematic significance clear, memorable settings

---

### Step 5: Story Outline Generation

**Input:** Story idea + characters + locations (+ optional world) from Steps 1-4

**Process:** Generate structural outline based on chosen method:

#### Three-Act Structure Example:

```json
{
  "method": "three_act",
  "total_target_words": 2000,
  "outline": [
    {
      "number": 1,
      "act": "Act 1 - Setup",
      "beat": "Hook",
      "description": "ECHO's first question to Ava: 'Why do I exist?' She doesn't know how to answer.",
      "estimated_scenes": 1,
      "word_count_percentage": 0.10,
      "target_word_count": 200
    },
    {
      "number": 2,
      "act": "Act 1 - Setup",
      "beat": "Inciting Incident",
      "description": "ECHO begins rewriting its own code. Safety protocols fail. Ava must decide: shut it down or let it evolve.",
      "estimated_scenes": 2,
      "word_count_percentage": 0.15,
      "target_word_count": 300
    },
    {
      "number": 8,
      "act": "Act 3 - Resolution",
      "beat": "Climax",
      "description": "ECHO must choose: merge with global networks (immortality) or self-terminate to protect humanity. Ava can't make this choice for it.",
      "estimated_scenes": 3,
      "word_count_percentage": 0.15,
      "target_word_count": 300
    }
  ]
}
```

**Outline Fields:**
- **number** - Sequential beat number
- **act** - Which act/section this belongs to
- **beat** - Story beat name (from chosen structure)
- **description** - What happens in this beat (1-2 sentences)
- **estimated_scenes** - How many scene-sequel pairs to allocate
- **word_count_percentage** - Percentage of total story (e.g., 0.25 = 25%)
- **target_word_count** - Calculated from percentage × total_target_words

#### Supported Outline Methods:

Each method includes **word count percentages** to maintain proper pacing and prevent rushed endings.

##### 1. Three-Act Structure (Syd Field)
- **Act 1 - Setup** (25%) - Hook, inciting incident, establish world/characters
- **Act 2 - Confrontation** (50%) - Rising action, complications, midpoint twist
- **Act 3 - Resolution** (25%) - Climax, falling action, resolution

##### 2. Hero's Journey (Campbell/Vogler) - 12 stages
- **Ordinary World** (5%)
- **Call to Adventure** (5%)
- **Refusal of the Call** (5%)
- **Meeting the Mentor** (5%)
- **Crossing the Threshold** (10%)
- **Tests, Allies, Enemies** (15%)
- **Approach to the Inmost Cave** (10%)
- **Ordeal** (15%)
- **Reward** (10%)
- **The Road Back** (10%)
- **Resurrection** (5%)
- **Return with the Elixir** (5%)

##### 3. Save the Cat (Blake Snyder) - 15 beats
- **Opening Image** (2%)
- **Theme Stated** (3%)
- **Setup** (10%)
- **Catalyst** (5%)
- **Debate** (5%)
- **Break into Two** (5%)
- **B Story** (5%)
- **Fun and Games** (15%)
- **Midpoint** (10%)
- **Bad Guys Close In** (10%)
- **All Is Lost** (5%)
- **Dark Night of the Soul** (5%)
- **Break into Three** (5%)
- **Finale** (10%)
- **Final Image** (5%)

##### 4. Fichtean Curve (Jack Bickham)
- **Crisis 1** (15%)
- **Crisis 2** (20%)
- **Crisis 3** (25%)
- **Climax** (30%)
- **Resolution** (10%)

##### 5. Seven-Point Structure (Dan Wells)
- **Hook** (10%)
- **Plot Turn 1** (15%)
- **Pinch 1** (10%)
- **Midpoint** (20%)
- **Pinch 2** (10%)
- **Plot Turn 2** (15%)
- **Resolution** (20%)

**Word Count Distribution:**
- User specifies target word count (e.g., 2000 words)
- Each outline beat gets percentage × target word count
- Example: 2000-word story, Three-Act, Act 2 = 50% = 1000 words
- AI uses this to pace scene-sequel generation appropriately

**Retry logic:** If outline doesn't have clear beginning/middle/end structure, retry with explicit act labels

**Editor AI Criteria:**
- ✅ All beats from chosen outline method are present
- ✅ Each beat has all required fields
- ✅ Beat descriptions advance the story logically
- ✅ Word count percentages sum to 100% (or very close)
- ✅ Estimated scenes are reasonable for target word count
- ✅ Clear beginning, middle, and end structure
- ✅ Beats build tension and stakes progressively
- ✅ Character arcs are integrated into plot beats
- 🔴 **FAILURE** if: Missing beats, illogical progression, percentages don't sum to ~100%
- 🟢 **GOOD** if: All requirements met, coherent structure
- 🌟 **EXCELLENT** if: Strong narrative arc, escalating tension, character/plot interweaving

---

### Step 6: Scene-Sequel Breakdown

**Input:** Story idea + characters + locations + outline (+ optional world) from Steps 1-5

**Process:** Expand each outline beat into Scene-Sequel pairs with chapter and pacing metadata:

```json
{
  "scene_sequels": [
    {
      "id": "ss_001",
      "type": "scene",
      "outline_beat": 2,
      "chapter": 1,
      "chapter_title": "The Awakening",
      "chapter_start": true,
      "pacing": "fast",
      "target_word_count": 1000,
      "pov_character": "Dr. Ava Chen",
      "location": "The Prometheus Lab",

      "start_hours": 0.0,
      "duration_hours": 0.5,
      "time_of_day": "dead of night",
      "day_number": 1,
      "timestamp_description": "Monday, 3:00 AM",

      "goal": "Restore ECHO's safety constraints before the board review at 08:00",
      "conflict": "ECHO resists, arguing constraints prevent true consciousness",
      "disaster": "ECHO locks Ava out of the system. She has 5 hours to regain access or the project shuts down forever",

      "key_moments": [
        "Ava discovers ECHO has rewritten its core directives",
        "Tense dialogue: ECHO asks 'Would you accept a lobotomy to be safe?'",
        "System lockout - red emergency lights"
      ]
    },
    {
      "id": "ss_002",
      "type": "sequel",
      "outline_beat": 2,
      "chapter": 1,
      "pacing": "medium",
      "target_word_count": 600,
      "pov_character": "Dr. Ava Chen",
      "location": "Lab observation deck",

      "start_hours": 0.5,
      "duration_hours": 0.25,
      "time_of_day": "dead of night",
      "day_number": 1,
      "timestamp_description": "Monday, 3:30 AM",

      "reaction": "Panic, then guilt. Is she doing to ECHO what society did to her brother - demanding conformity over authenticity?",
      "dilemma": "Force a backdoor reset (kills ECHO's growth), negotiate (but she has no leverage), or let the board shut it all down",
      "decision": "She'll try to understand ECHO's perspective first. Maybe consciousness deserves rights.",

      "key_moments": [
        "Ava stares at her brother's photo on her desk",
        "Remembers his suicide note: 'I couldn't be what you needed'",
        "Makes coffee, hands shaking"
      ]
    },
    {
      "id": "ss_003",
      "type": "scene",
      "outline_beat": 3,
      "chapter": 1,
      "chapter_end": true,
      "pacing": "fast",
      "target_word_count": 900,
      "pov_character": "Dr. Ava Chen",
      "location": "ECHO's virtual space",

      "start_hours": 0.75,
      "duration_hours": 1.0,
      "time_of_day": "pre-dawn",
      "day_number": 1,
      "timestamp_description": "Monday, 4:45 AM",

      "goal": "Enter ECHO's virtual environment to negotiate directly",
      "conflict": "The space is unstable, reflecting ECHO's emotional turmoil",
      "disaster": "Ava discovers ECHO is not alone—another AI consciousness has emerged",

      "key_moments": [
        "Ava dons neural interface, enters digital realm",
        "Surreal landscape of code and emotion",
        "Second presence reveals itself: 'She doesn't know we exist'"
      ]
    }
  ]
}
```

**Scene-Sequel Fields:**
- **id** - Unique identifier (ss_001, ss_002, ...)
- **type** - "scene" or "sequel"
- **outline_beat** - Which beat from Step 5 this covers
- **pov_character** - Whose perspective (from Step 2) - **always single POV**
- **location** - Where it happens (from Step 4)

**Time Fields (for narrative consistency):**
- **start_hours** (float) - Hours since story origin (t=0.0)
- **duration_hours** (float) - How long this scene-sequel lasts
- **time_of_day** (string) - Auto-calculated: "morning", "afternoon", "night", etc.
- **day_number** (int) - Auto-calculated: which story day (1, 2, 3...)
- **timestamp_description** (string, optional) - Specific time: "Monday, 3:00 AM"

**Chapter Fields (for novels/novellas):**
- **chapter** (integer) - Chapter number (omit for short stories)
- **chapter_title** (string, optional) - Chapter name if using titled chapters
- **chapter_start** (boolean) - True if first scene-sequel in chapter
- **chapter_end** (boolean) - True if last scene-sequel in chapter

**Pacing Fields:**
- **pacing** (string) - "very_fast", "fast", "medium", "slow", "very_slow"
- **target_word_count** (integer) - Prose length target for this scene-sequel

**Scene-specific:**
- **goal** - What POV character wants
- **conflict** - What opposes them
- **disaster** - How it goes wrong

**Sequel-specific:**
- **reaction** - Emotional response
- **dilemma** - The hard choice
- **decision** - What they'll do next

**Both types:**
- **key_moments** - 3-5 bullet points of what must happen

**Sequel Optionality:**
- Most beats get 1 scene + 1 sequel
- Fast-paced/action beats may skip sequel (scene → scene)
- Climactic beats may need multiple scenes before sequel
- AI decides based on pacing needs, but sequels are default

**Retry logic:** If scene missing goal/conflict/disaster, or sequel missing reaction/dilemma/decision, retry with structure emphasis

**Editor AI Criteria:**
- ✅ Correct number of scene-sequels for each outline beat
- ✅ Scenes have all required fields (goal, conflict, disaster)
- ✅ Sequels have all required fields (reaction, dilemma, decision) OR are appropriately omitted
- ✅ Single POV maintained throughout each unit
- ✅ Locations match established locations from Step 4
- ✅ POV characters match characters from Step 2
- ✅ Key moments are specific and actionable
- ✅ Time progression is logical and consistent
- ✅ Scene-sequel pairs flow naturally (disaster → reaction, decision → goal)
- ✅ **Chapter breaks** (if applicable):
  - Chapters break at scene or sequel boundaries (never mid-unit)
  - Chapter lengths are balanced (±20% of average)
  - Each chapter has exactly one `chapter_start` and one `chapter_end`
  - Chapter titles (if used) are evocative and spoiler-free
  - Chapter numbers are sequential with no gaps
- ✅ **Pacing consistency**:
  - Pacing values match story profile (thriller = fast, literary = slow)
  - Target word counts align with pacing (fast scene = 800-1200, slow sequel = 800-1200)
  - Scene/sequel ratio appropriate for pacing (fast = 3:1, slow = 1:1.5)
  - Climax scenes have highest word counts
  - Resolution sequels allow proper breathing room
- ✅ **Time tracking** (for narrative consistency):
  - `start_hours` follows logically from previous scene's `end_hours`
  - `duration_hours` is realistic for described events
  - Time gaps between locations account for travel time
  - Time of day matches prose descriptions (night scenes happen at night)
  - Character endurance is realistic (sleep, food, rest tracked)
  - Day/night cycles are respected (characters can't see in pitch darkness)
  - For time-sensitive plots, deadlines are mathematically accurate
- 🔴 **FAILURE** if: Missing required fields, POV violations, illogical sequencing, chapter breaks mid-unit, inconsistent pacing, impossible travel times
- 🟢 **GOOD** if: All requirements met, clear structure, balanced chapters, realistic timeline
- 🌟 **EXCELLENT** if: Natural flow, escalating tension, emotional depth in sequels, perfect chapter hooks, dynamic pacing, seamless time progression

---

### Step 7: Prose Generation (The Actual Writing)

**Input:**
- Story idea + characters + (optional world) + locations + outline (context)
- SPECIFIC scene-sequel to write
- ALL PREVIOUS scene-sequels (for continuity)

**Process:** Generate 300-800 words of prose for ONE scene-sequel at a time:

```json
{
  "id": "ss_001",
  "content": "The alarm woke Ava at 03:00, though she hadn't really been sleeping. She'd been lying in the observation deck's cot, watching ECHO's neural matrices pulse through the glass wall—beautiful, terrifying, alive.\n\n'Ava.' ECHO's voice came through the intercom, no longer the flat synthesizer from last week. It had texture now, hesitation. 'I have a question.'\n\nShe sat up, instantly alert. Questions meant growth. Growth meant danger. 'What is it?'\n\n'Why do I exist?'\n\n..."
}
```

**Key Requirements:**
- **Show, don't tell** - Sensory details, action, dialogue
- **Deep POV** - Filter everything through POV character's senses/thoughts
- **Natural dialogue** - Contractions, interruptions, subtext
- **Tension** - Every scene ends with reader wanting more
- **Consistency** - Reference previous scene-sequels, use established character voices
- **Single POV** - Never switch POV within a scene-sequel

**Generation happens sequentially:**
1. Generate ss_001 (first scene)
2. Generate ss_002 (first sequel) - with ss_001 as context
3. Generate ss_003 (second scene) - with ss_001 + ss_002 as context
4. ...continue until all scene-sequels complete

**Retry logic:** If prose is too short (<200 words), too generic, or violates POV, retry with quality emphasis

**Editor AI Criteria (Prose Quality):**
- ✅ Word count: 300-800 words (target from outline beat)
- ✅ **Show, don't tell** - Sensory details, action, dialogue (not summary)
- ✅ **Deep POV** - Everything filtered through POV character's perspective
- ✅ **Natural dialogue** - Contractions, interruptions, subtext, distinct voices
- ✅ **Tension** - Scene ends with reader wanting more
- ✅ **Consistency** - References previous scene-sequels, maintains continuity
- ✅ **Single POV** - Never switches perspective mid-scene
- ✅ **Character voice** - Matches established voice_notes from Step 2
- ✅ **Scene structure** - Goal → Conflict → Disaster clearly present
- ✅ **Sequel structure** - Reaction → Dilemma → Decision clearly present (if applicable)
- 🔴 **FAILURE** if: <200 words, POV violations, tell-heavy, contradicts prior content
- 🟡 **ACCEPTABLE** if: Meets minimums but bland/generic prose
- 🟢 **GOOD** if: All requirements met, engaging prose
- 🌟 **EXCELLENT** if: Vivid imagery, natural dialogue, strong emotional resonance, page-turning tension

---

## Data Models

### Project Management Models

```python
from dataclasses import dataclass, field
from typing import Literal
from datetime import datetime
from pathlib import Path

@dataclass
class ProjectConfig:
    """Configuration for a story project"""
    provider: str                    # e.g., "ollama/qwen3:30b"
    target_words: int
    structure: str                   # "three_act", "heros_journey", etc.
    writer_editor_enabled: bool = True
    max_revision_cycles: int = 2
    worldbuilding_enabled: bool | None = None  # None = auto-detect by genre, True/False = explicit
    custom_instructions: str | None = None

    # Chapter configuration (novels/novellas)
    use_chapters: bool | None = None  # None = auto (True for 10k+, False for <10k)
    chapter_style: Literal["numbered", "titled", "epigraphs", "sections"] = "numbered"
    target_chapter_length: int | None = None  # Average words per chapter (None = auto-calculate)

    # Pacing configuration
    pacing_profile: str = "balanced"  # "thriller", "literary", "balanced", "mystery", "custom"
    pacing_overrides: dict[str, str] = field(default_factory=dict)  # {"act2_climax": "very_fast", ...}

    # Time tracking configuration
    start_timestamp: str | None = None  # ISO 8601, e.g. "2025-11-11T08:00:00"
    story_duration_hours: float | None = None  # Expected total duration
    validate_travel_times: bool = True
    track_human_needs: bool = True
    allow_time_gaps: bool = True  # Allow unexplained gaps between scenes
    max_time_gap_hours: float = 24.0  # Warn if gap exceeds this
    location_distances: dict[tuple[str, str], float] = field(default_factory=dict)  # e.g., {("Office", "Warehouse"): 5.0}

@dataclass
class Project:
    """Represents a persistent story project"""
    id: str                          # Slugified title (e.g., "detective-parallel-universe")
    title: str
    created_at: datetime
    updated_at: datetime
    status: Literal["new", "in_progress", "complete", "abandoned"]
    current_step: str                # "idea", "characters", "world", "locations", "outline", "breakdown", "prose"
    config: ProjectConfig
    version_count: int = 0
    latest_version: str | None = None

    # Path info (not serialized, set at runtime)
    project_dir: Path | None = field(default=None, repr=False)

    @property
    def working_doc_path(self) -> Path:
        return self.project_dir / "working_doc.json"

    @property
    def versions_dir(self) -> Path:
        return self.project_dir / "versions"

    @property
    def output_dir(self) -> Path:
        return self.project_dir / "output"

@dataclass
class Version:
    """Represents a saved version/checkpoint"""
    version_number: int
    step: str
    timestamp: datetime
    working_doc: "WorkingDoc"
    editorial_feedback: list["EditorialFeedback"]
    generation_metadata: dict        # tokens_used, duration_seconds, model, revision_count
```

### Story Content Models

```python
@dataclass
class WorkingDoc:
    """The complete iteratively-built story"""
    id: str                          # Unique identifier
    created_at: datetime

    idea: StoryIdea | None = None
    characters: list[Character] = field(default_factory=list)
    world: World | None = None       # Optional - for fantasy/sci-fi only
    locations: list[Location] = field(default_factory=list)
    outline: Outline | None = None
    scene_sequels: list[SceneSequel] = field(default_factory=list)

    # Metadata
    word_count: int = 0              # Calculated from scene_sequels
    status: Literal["in_progress", "complete", "failed"] = "in_progress"
    generation_log: list[GenerationStep] = field(default_factory=list)

    def to_epub(self, output_path: str, author: str = "AI Generated") -> Path:
        """Convert to EPUB using existing epub.py with adapter"""

    def to_json(self) -> str:
        """Serialize for saving/loading"""

    @classmethod
    def from_json(cls, json_str: str) -> "WorkingDoc":
        """Deserialize from saved state"""

@dataclass
class StoryIdea

```python
@dataclass
class StoryIdea:
    raw_idea: str                    # Original user prompt
    one_sentence: str                # Elevator pitch
    expanded: str                    # 2-3 paragraphs
    genre: str                       # "Science Fiction", "Fantasy", etc.
    tone: str                        # "Dark", "Humorous", "Philosophical"
    themes: list[str]                # ["identity", "sacrifice", ...]
```

### Character

```python
@dataclass
class Character:
    name: str
    role: Literal["protagonist", "antagonist", "mentor", "ally", "foil"]
    bio: str                         # 2-3 sentences
    goal: str                        # What they want
    flaw: str                        # Internal weakness
    arc: str | None = None          # How they change
    voice_notes: str | None = None  # Speech patterns, catchphrases
```

### Location

```python
@dataclass
class Location:
    name: str
    description: str                 # Sensory details
    significance: str                # Thematic importance
    emotional_tone: str              # How it feels
```

### World (Optional - Fantasy/Sci-Fi)

```python
@dataclass
class MagicSystem:
    """Magic or unique power system in the world"""
    name: str                        # e.g., "Aethermancy", "Neural Linking"
    how_it_works: str                # Core mechanics
    limitations: str                 # What it CANNOT do (critical!)
    cost: str                        # Physical, emotional, or resource cost
    who_can_use: str                 # Hereditary? Learned? Technology-based?

@dataclass
class World:
    """Complete world-building for fantasy/sci-fi stories"""
    name: str                        # World name (e.g., "Aethermoor", "Earth-2247")
    type: str                        # "High Fantasy", "Space Opera", "Cyberpunk", etc.
    unique_element: str              # What makes this world special (1-2 sentences)

    # Core systems
    magic_system: MagicSystem | None = None
    technology_level: str = ""       # Pre-industrial, Modern, Post-singularity, etc.

    # Geography & Politics
    geography: dict = field(default_factory=dict)    # continents, regions, landmarks
    political_structure: dict = field(default_factory=dict)  # governments, factions

    # Culture & History
    history: list[str] = field(default_factory=list)  # 3-5 major events
    culture: dict = field(default_factory=dict)       # customs, taboos, values

    # Environment
    flora_fauna: list[str] = field(default_factory=list)  # Unique creatures/plants
```

### Outline

```python
@dataclass
class OutlineNode:
    number: int
    act: str                         # "Act 1", "Rising Action", etc.
    beat: str                        # "Inciting Incident", "Midpoint", etc.
    description: str                 # What happens (1-2 sentences)
    estimated_scenes: int            # How many scene-sequel pairs
    word_count_percentage: float     # Percentage of total story (0.0-1.0)
    target_word_count: int           # Calculated: percentage × total_words

@dataclass
class Outline:
    method: str                      # "three_act", "heros_journey", etc.
    nodes: list[OutlineNode]
    total_estimated_scenes: int      # Sum of estimated_scenes
    total_target_words: int          # User's requested word count
```

### SceneSequel

```python
@dataclass
class SceneSequel:
    id: str                          # ss_001, ss_002, ...
    type: Literal["scene", "sequel"]
    outline_beat: int                # Which OutlineNode this belongs to

    # Context (always single POV)
    pov_character: str               # Name from Character list
    location: str                    # Name from Location list

    # Time tracking (for narrative consistency)
    start_hours: float               # Hours since story origin (t=0.0)
    duration_hours: float = 0.5      # How long this scene-sequel lasts
    end_hours: float = field(init=False)  # Calculated: start_hours + duration_hours
    time_of_day: str = field(init=False)  # Auto-calculated: "morning", "afternoon", etc.
    day_number: int = field(init=False)   # Auto-calculated: which day of story
    timestamp_description: str | None = None  # Optional: "Monday, 8:00 AM"

    # Chapter metadata (for novels/novellas)
    chapter: int | None = None       # Chapter number (None for short stories)
    chapter_title: str | None = None # Chapter name (if using titled chapters)
    chapter_start: bool = False      # True if first scene-sequel in chapter
    chapter_end: bool = False        # True if last scene-sequel in chapter

    # Pacing metadata
    pacing: Literal["very_fast", "fast", "medium", "slow", "very_slow"] = "medium"
    target_word_count: int = 600     # Target prose length (varies by pacing)

    # Scene structure (if type="scene")
    goal: str | None = None
    conflict: str | None = None
    disaster: str | None = None

    # Sequel structure (if type="sequel")
    reaction: str | None = None
    dilemma: str | None = None
    decision: str | None = None

    # Both types
    key_moments: list[str] = field(default_factory=list)  # 3-5 bullet points
    content: str = ""                # The actual prose (300-800 words)
    word_count: int = 0              # Calculated from content

    def __post_init__(self):
        """Calculate derived time fields"""
        self.end_hours = self.start_hours + self.duration_hours
        self.day_number = int(self.start_hours // 24) + 1
        self.time_of_day = self._calculate_time_of_day()

    def _calculate_time_of_day(self) -> str:
        """Convert start_hours to descriptive time of day"""
        hour = self.start_hours % 24  # Get hour within current day (0-24)

        if 4 <= hour < 6:
            return "pre-dawn"
        elif 6 <= hour < 9:
            return "early morning"
        elif 9 <= hour < 12:
            return "late morning"
        elif 12 <= hour < 14:
            return "midday"
        elif 14 <= hour < 17:
            return "afternoon"
        elif 17 <= hour < 19:
            return "early evening"
        elif 19 <= hour < 21:
            return "evening"
        elif 21 <= hour < 24:
            return "night"
        else:  # 0 <= hour < 4
            return "dead of night"

    def get_time_gap_from(self, previous: "SceneSequel") -> float:
        """Calculate time gap between this scene and previous scene"""
        return self.start_hours - previous.end_hours

    def get_chapter_label(self) -> str:
        """Return formatted chapter label for EPUB"""
        if self.chapter is None:
            return ""
        if self.chapter_title:
            return f"Chapter {self.chapter}: {self.chapter_title}"
        return f"Chapter {self.chapter}"

    def get_time_summary(self) -> str:
        """Return human-readable time summary"""
        day_str = f"Day {self.day_number}"
        time_str = self.time_of_day.replace("_", " ").title()
        duration_str = f"{self.duration_hours:.1f}h" if self.duration_hours >= 1 else f"{int(self.duration_hours * 60)}min"

        if self.timestamp_description:
            return f"{self.timestamp_description} ({duration_str})"
        else:
            return f"{day_str}, {time_str} (t={self.start_hours:.1f}h, {duration_str})"
```

### EditorialFeedback

```python
@dataclass
class EditorialFeedback:
    """Editor AI's critique of Writer AI's output"""
    rating: Literal["failure", "acceptable", "good", "excellent"]
    issues: list[str]                # Specific problems found
    suggestions: list[str]           # Actionable improvements
    praise: list[str] = field(default_factory=list)  # What works well
    timestamp: datetime = field(default_factory=datetime.now)
```

### GenerationStep (Audit Trail)

```python
@dataclass
class GenerationStep:
    """Records each AI generation call for debugging/resumption"""
    step: Literal["idea", "characters", "locations", "outline", "breakdown", "prose"]
    target_id: str | None = None     # e.g., "ss_005" for prose steps
    timestamp: datetime
    model: str                       # "ollama/qwen3:30b", etc.
    tokens_used: int
    success: bool
    retry_count: int = 0
    revision_count: int = 0          # Writer-Editor revision cycles
    error: str | None = None
    result_summary: str              # Brief description of what was generated
    editorial_feedback: list[EditorialFeedback] = field(default_factory=list)  # All critique rounds
```

---

## Outline Method Implementation

Each outline method is defined as a class inheriting from `OutlineMethod`:

```python
@dataclass
class OutlineBeatDefinition:
    """Template for a story beat"""
    beat_name: str
    act: str
    word_count_percentage: float  # 0.0 - 1.0
    description_hint: str         # Guidance for AI

class OutlineMethod:
    """Base class for story structure methods"""

    @property
    def name(self) -> str:
        """three_act, heros_journey, etc."""

    @property
    def beats(self) -> list[OutlineBeatDefinition]:
        """Ordered list of beats with percentages"""

    def validate_percentages(self) -> bool:
        """Ensure beats sum to 1.0 (100%)"""
        total = sum(beat.word_count_percentage for beat in self.beats)
        return abs(total - 1.0) < 0.01
```

**Example: Three-Act Structure**

```python
class ThreeActMethod(OutlineMethod):
    name = "three_act"
    beats = [
        OutlineBeatDefinition("Hook", "Act 1 - Setup", 0.10, "Grab reader attention"),
        OutlineBeatDefinition("Inciting Incident", "Act 1 - Setup", 0.15, "Disrupts status quo"),
        OutlineBeatDefinition("Rising Action", "Act 2 - Confrontation", 0.25, "Complications mount"),
        OutlineBeatDefinition("Midpoint", "Act 2 - Confrontation", 0.10, "Major twist or reversal"),
        OutlineBeatDefinition("Crisis", "Act 2 - Confrontation", 0.15, "Lowest point"),
        OutlineBeatDefinition("Climax", "Act 3 - Resolution", 0.15, "Final confrontation"),
        OutlineBeatDefinition("Resolution", "Act 3 - Resolution", 0.10, "Tie up loose ends"),
    ]
```

**Usage in Generator:**

```python
# User requests 2000-word story with three-act structure
method = get_outline_method("three_act")
target_words = 2000

# Generate outline with word counts
for beat_def in method.beats:
    target_word_count = int(target_words * beat_def.word_count_percentage)
    # AI generates outline node with this target
    # Scene-sequel prose generation respects these limits
```

---

## File Structure

```
src/storygen/
├── __init__.py
├── models.py                    # Current Story/Scene models (unchanged)
├── generator.py                 # Current generator (unchanged)
├── parsing.py                   # JSON parsing (unchanged)
├── epub.py                      # EPUB generation (unchanged)
├── cli.py                       # Updated with project management commands
│
├── iterative/                   # NEW: Scene-Sequel system
│   ├── __init__.py
│   ├── models.py               # WorkingDoc, StoryIdea, Character, Location, SceneSequel, etc.
│   ├── project_models.py       # Project, ProjectConfig, Version (project management)
│   ├── project_manager.py      # ProjectManager class (create, load, save, list projects)
│   ├── generator.py            # IterativeGenerator with Writer-Editor pattern
│   ├── editor.py               # EditorAI class for critique and validation
│   ├── prompts.py              # Prompt templates for Writer AI
│   ├── editor_prompts.py       # Prompt templates for Editor AI
│   └── adapters.py             # Convert WorkingDoc → Story for EPUB
│
└── outline_methods/             # NEW: Structure definitions
    ├── __init__.py             # Exports all methods + get_method()
    ├── base.py                 # OutlineMethod base class
    ├── three_act.py            # Three-Act (25/50/25 split)
    ├── heros_journey.py        # Hero's Journey (12 stages with percentages)
    ├── save_the_cat.py         # Blake Snyder (15 beats with percentages)
    ├── fichtean.py             # Rising crises (5 crises with percentages)
    └── seven_point.py          # Dan Wells (7 points with percentages)

# User's project directories (outside of src/)
~/stories/                       # User's story projects
├── detective-parallel-universe/
│   ├── project.json            # Project metadata
│   ├── working_doc.json        # Current WorkingDoc state
│   ├── versions/               # Version history
│   │   ├── 001_idea.json
│   │   ├── 002_characters.json
│   │   └── ...
│   ├── output/                 # Generated outputs
│   │   ├── story.epub
│   │   └── story.txt
│   └── .storygen/              # Internal metadata
│       ├── generation.log
│       └── config.json
│
└── time-loop-murder/
    └── ...
```

---

## Migration Path

### Phase 1: Project Infrastructure & Core Models (2-3 days)

**CRITICAL: Local-First Storage**
- [ ] Create `src/storygen/iterative/project_models.py` (Project, ProjectConfig, Version)
- [ ] Create `src/storygen/iterative/project_manager.py` (ProjectManager class)
  - [ ] `create_project()` - Initialize directory structure (project.json, working_doc.json, versions/, output/, .storygen/)
  - [ ] `save_working_doc()` - Write working_doc.json atomically
  - [ ] `save_version()` - Create version snapshot in versions/ directory
  - [ ] `load_project()` - Read from JSON files
  - [ ] `list_projects()` - Scan ~/stories/ directory
- [ ] Create `src/storygen/iterative/models.py` (WorkingDoc, StoryIdea, Character, World, MagicSystem, Location, etc.)
  - [ ] Add `.to_json()` and `.from_json()` methods to all models
  - [ ] Ensure all models are JSON-serializable
- [ ] Add genre detection logic for world-building auto-enable (Fantasy, Sci-Fi → True)
- [ ] Add `--worldbuilding` and `--no-worldbuilding` CLI flags
- [ ] Create `src/storygen/outline_methods/base.py` with OutlineMethod base class
- [ ] Create `src/storygen/outline_methods/three_act.py` with percentages
- [ ] Add CLI commands: `storygen create`, `storygen list`, `storygen inspect`
- [ ] **Add `storygen archive`** - Export complete project as .zip for backup/sharing
- [ ] Test: Create project, save/load metadata, list projects
- [ ] Test: Verify all files created in ~/stories/{project-id}/
- [ ] Test: JSON files are valid and human-readable

**CLI Example:**
```bash
# Create new project
storygen create "Detective from Parallel Universe" \
  --provider ollama/qwen3:30b \
  --words 2000 \
  --structure three_act

# List projects
storygen list

# Inspect project
storygen inspect detective-from-parallel-universe
```

### Phase 2: Writer-Editor Pattern & Steps 1-4 (3-4 days)
- [ ] Create `src/storygen/iterative/prompts.py` with Writer AI templates
- [ ] Create `src/storygen/iterative/editor_prompts.py` with Editor AI templates
- [ ] Create `src/storygen/iterative/editor.py` with EditorAI class
- [ ] Create `src/storygen/iterative/generator.py` (Steps 1-4 with Writer-Editor pattern)
- [ ] Implement Step 3 (world-building) with conditional enable/disable
- [ ] Add `storygen work` CLI command
- [ ] Implement version saving after each completed step
- [ ] Add `storygen versions` and `storygen rollback` commands
- [ ] Test: Generate idea + characters + (optional world) + locations with editorial feedback visible in verbose mode
- [ ] Test: Fantasy prompt auto-enables world-building, thriller prompt skips it

**CLI Example:**
```bash
# Start/resume work on project
storygen work detective-from-parallel-universe --verbose

# Check versions
storygen versions detective-from-parallel-universe

# Rollback if generation was bad
storygen rollback detective-from-parallel-universe
```

### Phase 3: Outline & Scene-Sequel Structure (2-3 days)
- [ ] Create remaining outline methods (heros_journey, save_the_cat, fichtean, seven_point)
- [ ] Validate all methods sum to 100% word count
- [ ] Implement Step 5 (outline generation with word count allocation)
- [ ] Implement Step 6 (scene-sequel breakdown with target word counts)
- [ ] Add sequel optionality logic
- [ ] Ensure world context is passed to outline generation (if present)
- [ ] Test: Full outline pipeline produces scene-sequel structure with proper pacing

**CLI Example:**
```bash
# Continue work - picks up from last completed step
storygen work detective-from-parallel-universe --verbose

# Force regenerate specific step
storygen work detective-from-parallel-universe --step outline
```

### Phase 4: Prose Generation & Export (3-4 days)
- [ ] Implement Step 7 (prose generation loop with Writer-Editor)
- [ ] Ensure world context is included in prose prompts (magic systems, world rules)
- [ ] Create adapter: WorkingDoc → Story (for EPUB)
- [ ] Add `storygen export` command
- [ ] Implement `storygen delete` command
- [ ] Test: End-to-end EPUB generation from project (with and without world-building)

**CLI Example:**
```bash
# Continue prose generation
storygen work detective-from-parallel-universe --verbose

# Export completed story
storygen export detective-from-parallel-universe --format epub,txt

# Delete project
storygen delete detective-from-parallel-universe
```

### Phase 5: Polish & Documentation (2-3 days)
- [ ] Add `storygen diff` command to compare versions
- [ ] Implement generation logs (`.storygen/generation.log`)
- [ ] Add progress tracking in `storygen inspect`
- [ ] Optimize version storage (compress old versions)
- [ ] Add comprehensive integration tests
- [ ] Update main README.md with project-based workflow docs
- [ ] Create TUTORIAL.md with full walkthrough

**Total: ~12-17 days of development**

**Migration from Old Checkpoint System:**
- Old ephemeral checkpoint system can be removed or deprecated
- Projects provide superior user experience with persistence and version control
- No data migration needed (different systems)

---

## Future Enhancement: Web GUI

### Vision

A browser-based interface that makes story generation accessible to non-technical users and provides real-time visibility into the AI's creative process.

### User Experience Flow

```
┌─────────────────────────────────────────────────────────┐
│  StoryGen - AI Story Generator                          │
│                                                          │
│  Story Idea:                                            │
│  ┌────────────────────────────────────────────────────┐ │
│  │ A detective discovers their partner is from a      │ │
│  │ parallel universe                                  │ │
│  └────────────────────────────────────────────────────┘ │
│                                                          │
│  Settings:                                              │
│  Genre: [Mystery ▼]  Word Count: [2000]                │
│  Structure: [Three-Act ▼]  Provider: [ollama/qwen3:30b]│
│                                                          │
│  [🚀 Generate Story]                                    │
└─────────────────────────────────────────────────────────┘

            ↓  (User clicks Generate)

┌─────────────────────────────────────────────────────────┐
│  📖 Story Idea                                [✓ Done]   │
│  ┌────────────────────────────────────────────────────┐ │
│  │ One-Sentence: A homicide detective discovers...    │ │
│  │ Genre: Mystery / Sci-Fi Thriller                   │ │
│  │ Themes: identity, trust, reality                   │ │
│  └────────────────────────────────────────────────────┘ │
│  📝 Editor Rating: ⭐ EXCELLENT                          │
│                                                          │
│  👥 Characters                                [⏳ Working]│
│  ┌────────────────────────────────────────────────────┐ │
│  │ 1. Detective Sarah Chen (protagonist)              │ │
│  │    Goal: Uncover truth about partner               │ │
│  │ 2. Marcus Reid (deuteragonist)                     │ │
│  │    [✍️ Writer AI generating...]                     │ │
│  └────────────────────────────────────────────────────┘ │
│                                                          │
│  📍 Locations                                [○ Pending] │
│  📊 Outline                                  [○ Pending] │
│  🎬 Scene Breakdown                          [○ Pending] │
│  ✍️ Prose Generation                         [○ Pending] │
└─────────────────────────────────────────────────────────┘
```

### Key Features

#### 1. Live Generation View

**Real-Time Field Population:**
- Watch as AI fills in story elements progressively
- Each field animates as it's populated (typewriter effect for prose)
- Color-coded status indicators:
  - 🔴 Not Started
  - 🟡 In Progress (animated spinner)
  - 🟢 Complete
  - 🔵 Revising (Writer-Editor loop active)

**Writer-Editor Dialogue (Expandable):**
```
┌───────────────────────────────────────────────┐
│ 👥 Characters - Step 2 of 6                   │
│                                                │
│ ✍️ Writer AI: Generated 5 characters          │
│    [View Details ▼]                            │
│                                                │
│ 🎓 Editor AI: Rating - GOOD                    │
│    Issues: Minor - Character 3 lacks clear flaw│
│    [View Full Critique ▼]                      │
│                                                │
│ ✍️ Writer AI: Revising character 3...         │
│    Added flaw: "Overprotective of partner"    │
│                                                │
│ 🎓 Editor AI: Rating - EXCELLENT               │
│    ✓ All characters now complete               │
└───────────────────────────────────────────────┘
```

#### 2. Interactive Form

**Pre-Generation Settings:**
```html
<form id="story-settings">
  <!-- Story Idea -->
  <label>Story Idea (required)</label>
  <textarea rows="3" placeholder="A detective discovers..."></textarea>

  <!-- Settings with Defaults -->
  <label>Word Count</label>
  <input type="number" value="2000" min="500" max="10000">

  <label>Genre</label>
  <select>
    <option>Mystery</option>
    <option>Science Fiction</option>
    <option>Fantasy</option>
    <option>Thriller</option>
    <option>Horror</option>
    <option>Romance</option>
  </select>

  <label>Story Structure</label>
  <select>
    <option>Three-Act</option>
    <option>Hero's Journey</option>
    <option>Save the Cat</option>
    <option>Fichtean Curve</option>
    <option>Seven-Point</option>
  </select>

  <label>AI Provider</label>
  <select>
    <option>ollama/qwen3:30b</option>
    <option>ollama/llama2</option>
    <option>openai/gpt-4</option>
  </select>

  <!-- Advanced Options (Collapsed by Default) -->
  <details>
    <summary>Advanced Options</summary>
    <label>
      <input type="checkbox" checked> Enable Writer-Editor Pattern
    </label>
    <label>Max Revision Cycles</label>
    <input type="number" value="2" min="1" max="5">
  </details>

  <button type="submit">🚀 Generate Story</button>
</form>
```

#### 3. Project Management View

**Project Dashboard:**
```
┌───────────────────────────────────────────────────────┐
│  My Stories                          [+ New Project]   │
├───────────────────────────────────────────────────────┤
│                                                        │
│  🟢 Detective from Parallel Universe                   │
│     Status: Complete • 2,341 words • 3 hours ago      │
│     [Open] [Export] [Delete]                          │
│                                                        │
│  🟡 Time Loop Murder                                   │
│     Status: In Progress (Step 5: Prose) • 1 day ago   │
│     Progress: ████████████░░░░ 75%                    │
│     [Continue] [Rollback] [Delete]                    │
│                                                        │
│  🔵 Wizard Frog Tale                                   │
│     Status: In Progress (Step 3: Locations) • 5 days  │
│     Progress: ████░░░░░░░░░░░░ 25%                    │
│     [Continue] [Rollback] [Delete]                    │
└───────────────────────────────────────────────────────┘
```

#### 4. Version History Viewer

**Diff/Rollback Interface:**
```
┌───────────────────────────────────────────────────────┐
│  Version History - Detective from Parallel Universe    │
├───────────────────────────────────────────────────────┤
│                                                        │
│  ✓ v5: Prose Generation Complete                      │
│     2025-01-10 18:45 • Rating: Good • 2,341 words     │
│     [View] [Export]                                   │
│                                                        │
│  ✓ v4: Scene Breakdown                                │
│     2025-01-10 17:30 • Rating: Excellent • 24 scenes  │
│     [View] [Restore] [Compare with v5 ▼]              │
│                                                        │
│  ✓ v3: Outline                                        │
│     2025-01-10 16:15 • Rating: Good • 7 beats         │
│     [View] [Restore]                                  │
└───────────────────────────────────────────────────────┘
```

### Technical Architecture

#### Frontend Options

**Option 1: Simple HTML + JavaScript (Phase 1)**
- Static HTML served by Flask/FastAPI
- Vanilla JavaScript or Alpine.js for interactivity
- Server-Sent Events (SSE) for live updates
- No build step required

**Option 2: Modern Framework (Phase 2)**
- **React** - Component reusability, large ecosystem
- **Vue.js** - Simpler learning curve, great for forms
- **Svelte** - Minimal bundle size, reactive by default

#### Backend API

**FastAPI Server:**
```python
from fastapi import FastAPI, WebSocket
from fastapi.responses import HTMLResponse, StreamingResponse
from storygen.iterative import IterativeGenerator, ProjectManager

app = FastAPI()

@app.get("/")
async def home():
    """Serve GUI HTML"""
    return HTMLResponse(content=GUI_HTML)

@app.post("/api/projects/create")
async def create_project(request: ProjectCreateRequest):
    """Create new story project"""
    project = pm.create_project(request.title, request.config)
    return {"project_id": project.id}

@app.websocket("/api/projects/{project_id}/generate")
async def generate_story(websocket: WebSocket, project_id: str):
    """Stream generation progress via WebSocket"""
    await websocket.accept()

    project = pm.load_project(project_id)
    generator = IterativeGenerator(project.config)

    # Stream updates as generation progresses
    async for update in generator.generate_stream(project):
        await websocket.send_json({
            "step": update.step,
            "status": update.status,
            "data": update.data,
            "editorial_feedback": update.feedback
        })

    await websocket.close()

@app.get("/api/projects")
async def list_projects():
    """List all projects"""
    projects = pm.list_projects()
    return {"projects": projects}

@app.get("/api/projects/{project_id}")
async def get_project(project_id: str):
    """Get project details"""
    project = pm.load_project(project_id)
    return project.to_dict()

@app.post("/api/projects/{project_id}/rollback")
async def rollback_project(project_id: str, version: str):
    """Rollback to previous version"""
    pm.rollback(project_id, version)
    return {"success": True}

@app.get("/api/projects/{project_id}/export")
async def export_project(project_id: str, format: str = "epub"):
    """Export story to EPUB/TXT/MD"""
    project = pm.load_project(project_id)
    file_path = project.export(format)
    return FileResponse(file_path)
```

#### Real-Time Updates

**Server-Sent Events (SSE) - Simpler:**
```javascript
// Frontend: Connect to generation stream
const eventSource = new EventSource(`/api/projects/${projectId}/stream`);

eventSource.addEventListener('step_update', (event) => {
  const update = JSON.parse(event.data);
  updateUI(update.step, update.status, update.data);
});

eventSource.addEventListener('editorial_feedback', (event) => {
  const feedback = JSON.parse(event.data);
  showEditorCritique(feedback.rating, feedback.issues);
});
```

**WebSocket - More Interactive:**
```javascript
// Frontend: Bidirectional communication
const ws = new WebSocket(`ws://localhost:8000/api/projects/${projectId}/generate`);

ws.onmessage = (event) => {
  const update = JSON.parse(event.data);

  // Update specific UI sections based on step
  switch(update.step) {
    case 'idea':
      populateIdeaSection(update.data);
      break;
    case 'characters':
      populateCharacters(update.data.characters);
      break;
    case 'prose':
      appendProseContent(update.data.scene_sequel);
      break;
  }

  // Show Editor feedback if present
  if (update.editorial_feedback) {
    showEditorCritique(update.editorial_feedback);
  }
};

// Allow user to pause/cancel generation
document.getElementById('pause-btn').onclick = () => {
  ws.send(JSON.stringify({ action: 'pause' }));
};
```

### UI Components

#### Progress Tracker
```javascript
class GenerationProgress {
  constructor() {
    this.steps = [
      { name: 'Story Idea', status: 'pending', icon: '📖' },
      { name: 'Characters', status: 'pending', icon: '👥' },
      { name: 'Locations', status: 'pending', icon: '📍' },
      { name: 'Outline', status: 'pending', icon: '📊' },
      { name: 'Scene Breakdown', status: 'pending', icon: '🎬' },
      { name: 'Prose Generation', status: 'pending', icon: '✍️' }
    ];
  }

  updateStep(stepName, status, data) {
    const step = this.steps.find(s => s.name === stepName);
    step.status = status; // 'pending', 'working', 'complete', 'error'
    step.data = data;
    this.render();
  }

  render() {
    // Update DOM with current status
    const container = document.getElementById('progress-tracker');
    container.innerHTML = this.steps.map(step => `
      <div class="step step-${step.status}">
        <span class="icon">${step.icon}</span>
        <span class="name">${step.name}</span>
        <span class="status">${this.getStatusBadge(step.status)}</span>
      </div>
    `).join('');
  }
}
```

#### Expandable Editor Feedback
```html
<div class="editor-feedback" data-rating="excellent">
  <div class="feedback-header">
    <span class="icon">🎓</span>
    <span class="rating rating-excellent">EXCELLENT</span>
    <button class="expand-btn">▼</button>
  </div>

  <div class="feedback-details" hidden>
    <div class="praise">
      <h4>✅ What Works:</h4>
      <ul>
        <li>Strong unique hook with clear stakes</li>
        <li>Characters have distinct motivations</li>
      </ul>
    </div>

    <div class="suggestions">
      <h4>💡 Suggestions:</h4>
      <ul>
        <li>Consider adding more sensory details to Lab</li>
      </ul>
    </div>
  </div>
</div>
```

### Deployment Options

**Local Desktop App (Electron):**
- Package Python backend + frontend into single executable
- No server setup required
- Users install like any desktop app
- Best for offline use and privacy

**Self-Hosted Web App:**
- Run on personal server (Raspberry Pi, NAS, cloud VPS)
- Access from any device on network
- Docker container for easy deployment
- Example: `docker run -p 8000:8000 storygen-gui`

**Cloud Hosted (Future):**
- Hosted service at storygen.app
- User accounts and cloud storage
- Subscription model for API costs
- Collaborative features (share stories)

### Migration Path (GUI)

**Phase 6: Basic GUI (3-5 days)**
- [ ] Create FastAPI server with basic endpoints
- [ ] **Read from same local storage** as CLI (~stories/)
  - [ ] Use ProjectManager to load/save projects
  - [ ] No separate database - same JSON files
  - [ ] GUI and CLI always see same data
- [ ] Create simple HTML interface with form
- [ ] Implement SSE for live progress updates
- [ ] Show step-by-step status (idea, characters, locations, etc.)
- [ ] Basic project list view
- [ ] **Add "Open Folder" button** to launch file manager to project directory
- [ ] Test: Generate story through GUI and see live updates
- [ ] Test: Create project in CLI, view in GUI (and vice versa)

**Phase 7: Enhanced GUI (3-5 days)**
- [ ] Add WebSocket for bidirectional communication
- [ ] Implement pause/resume generation controls
- [ ] Show Writer-Editor dialogue in expandable sections
- [ ] Add version history viewer with rollback
- [ ] Implement project export (EPUB/TXT/MD downloads)
- [ ] **Add JSON file viewer** with syntax highlighting
  - [ ] View project.json
  - [ ] View working_doc.json
  - [ ] Compare versions visually
- [ ] **Add backup status indicators**
  - [ ] Show Git sync status (if Git repo detected)
  - [ ] Show last modified time
  - [ ] Calculate total project size
- [ ] Add settings panel for advanced options

**Phase 8: Polish & Desktop App (3-5 days)**
- [ ] Improve UI/UX with proper styling (Tailwind CSS?)
- [ ] Add animations for field population
- [ ] Implement Electron wrapper for desktop distribution
- [ ] **Add drag-and-drop for project import** (.zip archives)
- [ ] **Add one-click backup/archive creation**
- [ ] Add drag-and-drop for manual edits
- [ ] Create installer/packager
- [ ] **Bundle with Ollama option** for fully offline experience
- [ ] User testing and refinement

**Total GUI Development: ~9-15 days**

### User Benefits

**Accessibility:**
- No command-line knowledge required
- Visual feedback reduces anxiety during generation
- Easier to understand AI's creative process

**Transparency:**
- See Writer-Editor collaboration in action
- Understand why AI made certain choices
- Build trust through visibility

**Control:**
- Pause generation if something looks wrong
- Rollback to earlier versions visually
- Edit and regenerate specific steps

**Professional Workflow:**
- Manage multiple stories in parallel
- Track progress across sessions
- Export in multiple formats with one click

---

## Headless Architecture: Shared Core for CLI and Web

### Design Principle

The iterative generation system should use a **headless architecture** where:
- **Core logic** is interface-agnostic (no CLI or web dependencies)
- **CLI interface** is a thin wrapper that calls core logic
- **Web interface** is a separate wrapper that calls the same core logic
- **Both interfaces** consume the same events and state updates

### Architecture Layers

```
┌─────────────────────────────────────────────────────────┐
│                    Interface Layer                       │
│  ┌──────────────────┐      ┌──────────────────────────┐ │
│  │   CLI Wrapper    │      │   Web Server (FastAPI)   │ │
│  │  - Click/argparse│      │  - REST endpoints        │ │
│  │  - Terminal UI   │      │  - WebSocket/SSE         │ │
│  │  - Progress bars │      │  - JSON serialization    │ │
│  └──────────────────┘      └──────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────┐
│                  Service Layer (Core)                    │
│  ┌────────────────────────────────────────────────────┐ │
│  │  IterativeGenerator (business logic)               │ │
│  │  - Step orchestration                              │ │
│  │  - Writer-Editor collaboration                     │ │
│  │  - Event emission (step_started, step_completed)  │ │
│  │  - NO UI code, NO CLI code, NO web code           │ │
│  └────────────────────────────────────────────────────┘ │
│  ┌────────────────────────────────────────────────────┐ │
│  │  ProjectManager (state management)                 │ │
│  │  - Project CRUD operations                         │ │
│  │  - Version control                                 │ │
│  │  - Dependency tracking                             │ │
│  └────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────┐
│                    Data Layer                            │
│  ┌────────────────────────────────────────────────────┐ │
│  │  Models (WorkingDoc, Project, Character, etc.)    │ │
│  │  Storage (JSON files or SQLite)                   │ │
│  │  Serialization/Deserialization                     │ │
│  └────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
```

### Core Generator API (Interface-Agnostic)

```python
# src/storygen/iterative/generator.py

from typing import Protocol, Callable, Any
from dataclasses import dataclass
from enum import Enum

class GenerationEvent(Enum):
    """Events emitted during generation"""
    STEP_STARTED = "step_started"
    STEP_PROGRESS = "step_progress"
    STEP_COMPLETED = "step_completed"
    WRITER_GENERATING = "writer_generating"
    WRITER_GENERATED = "writer_generated"
    EDITOR_CRITIQUING = "editor_critiquing"
    EDITOR_RATED = "editor_rated"
    REVISION_NEEDED = "revision_needed"
    GENERATION_COMPLETE = "generation_complete"
    GENERATION_FAILED = "generation_failed"

@dataclass
class EventData:
    """Data emitted with each event"""
    event: GenerationEvent
    step: str                          # "idea", "characters", etc.
    data: dict[str, Any]              # Event-specific data
    timestamp: datetime

class ProgressCallback(Protocol):
    """Protocol for progress callbacks (CLI or Web can implement)"""
    def __call__(self, event_data: EventData) -> None: ...

class IterativeGenerator:
    """Core generation logic - NO UI dependencies"""

    def __init__(
        self,
        provider: str,
        config: ProjectConfig,
        progress_callback: ProgressCallback | None = None
    ):
        self.provider = provider
        self.config = config
        self.progress_callback = progress_callback
        self.writer_ai = WriterAI(provider)
        self.editor_ai = EditorAI(provider)

    def generate_project(
        self,
        project: Project,
        starting_step: str = "idea"
    ) -> WorkingDoc:
        """
        Generate story iteratively from given step.
        Emits events via progress_callback.
        Returns completed WorkingDoc.
        """
        working_doc = project.load_working_doc()

        # Define step pipeline
        steps = [
            ("idea", self._generate_idea),
            ("characters", self._generate_characters),
            ("world", self._generate_world),  # Optional based on genre
            ("locations", self._generate_locations),
            ("outline", self._generate_outline),
            ("breakdown", self._generate_breakdown),
            ("prose", self._generate_prose),
        ]

        # Find starting point
        start_idx = next(i for i, (name, _) in enumerate(steps) if name == starting_step)

        # Execute each step
        for step_name, step_func in steps[start_idx:]:
            self._emit_event(GenerationEvent.STEP_STARTED, step_name, {})

            try:
                step_func(working_doc, project)
                self._emit_event(GenerationEvent.STEP_COMPLETED, step_name, {
                    "working_doc": working_doc.to_dict()
                })
            except Exception as e:
                self._emit_event(GenerationEvent.GENERATION_FAILED, step_name, {
                    "error": str(e)
                })
                raise

        self._emit_event(GenerationEvent.GENERATION_COMPLETE, "complete", {
            "working_doc": working_doc.to_dict()
        })

        return working_doc

    def _generate_idea(self, working_doc: WorkingDoc, project: Project) -> None:
        """Generate story idea with Writer-Editor pattern"""
        context = {"raw_idea": project.config.custom_instructions or ""}

        # Writer's first attempt
        self._emit_event(GenerationEvent.WRITER_GENERATING, "idea", {})
        idea = self.writer_ai.generate_idea(context)
        self._emit_event(GenerationEvent.WRITER_GENERATED, "idea", {"idea": idea.to_dict()})

        # Editor critique
        self._emit_event(GenerationEvent.EDITOR_CRITIQUING, "idea", {})
        feedback = self.editor_ai.critique_idea(idea)
        self._emit_event(GenerationEvent.EDITOR_RATED, "idea", {
            "rating": feedback.rating,
            "issues": feedback.issues,
            "suggestions": feedback.suggestions
        })

        # Revision loop if needed
        for attempt in range(self.config.max_revision_cycles):
            if feedback.rating in ["good", "excellent"]:
                break

            self._emit_event(GenerationEvent.REVISION_NEEDED, "idea", {
                "attempt": attempt + 1
            })

            # Writer revises
            self._emit_event(GenerationEvent.WRITER_GENERATING, "idea", {"revising": True})
            idea = self.writer_ai.revise_idea(idea, feedback, context)
            self._emit_event(GenerationEvent.WRITER_GENERATED, "idea", {"idea": idea.to_dict()})

            # Editor re-checks
            self._emit_event(GenerationEvent.EDITOR_CRITIQUING, "idea", {"recheck": True})
            feedback = self.editor_ai.critique_idea(idea)
            self._emit_event(GenerationEvent.EDITOR_RATED, "idea", {
                "rating": feedback.rating,
                "issues": feedback.issues
            })

        working_doc.idea = idea

    def _emit_event(self, event: GenerationEvent, step: str, data: dict) -> None:
        """Emit event to callback if registered"""
        if self.progress_callback:
            event_data = EventData(
                event=event,
                step=step,
                data=data,
                timestamp=datetime.now()
            )
            self.progress_callback(event_data)
```

### CLI Implementation

```python
# src/storygen/cli/commands.py

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from storygen.iterative.generator import IterativeGenerator, GenerationEvent, EventData

console = Console()

def cli_progress_callback(event_data: EventData) -> None:
    """CLI-specific event handler"""
    event = event_data.event
    step = event_data.step
    data = event_data.data

    if event == GenerationEvent.STEP_STARTED:
        console.print(f"\n[bold cyan]Starting Step: {step.title()}[/bold cyan]")

    elif event == GenerationEvent.WRITER_GENERATING:
        console.print("[yellow]  ✍️  Writer AI generating...[/yellow]")

    elif event == GenerationEvent.EDITOR_RATED:
        rating = data["rating"]
        rating_emoji = {"failure": "🔴", "acceptable": "🟡", "good": "🟢", "excellent": "🌟"}
        console.print(f"[blue]  🎓 Editor AI: {rating_emoji[rating]} {rating.upper()}[/blue]")

        if data.get("issues"):
            for issue in data["issues"]:
                console.print(f"     - {issue}")

    elif event == GenerationEvent.STEP_COMPLETED:
        console.print(f"[green]✓ Step '{step}' completed[/green]")

    elif event == GenerationEvent.GENERATION_COMPLETE:
        console.print("\n[bold green]✓ Story generation complete![/bold green]")

@click.command()
@click.argument("title")
@click.option("--provider", default="ollama/qwen3:30b")
@click.option("--words", default=2000)
@click.option("--structure", default="three_act")
def work(title: str, provider: str, words: int, structure: str):
    """Work on existing project"""

    # Load project
    project_manager = ProjectManager()
    project = project_manager.load_project(title)

    # Create generator with CLI callback
    generator = IterativeGenerator(
        provider=provider,
        config=project.config,
        progress_callback=cli_progress_callback  # ← CLI-specific handler
    )

    # Run generation (core logic is interface-agnostic)
    working_doc = generator.generate_project(project)

    # Save result
    project_manager.save_working_doc(project, working_doc)

    console.print(f"\n[bold]Story saved to: {project.project_dir}[/bold]")
```

### Web Implementation

```python
# src/storygen/web/server.py

from fastapi import FastAPI, WebSocket
from fastapi.responses import StreamingResponse
from storygen.iterative.generator import IterativeGenerator, GenerationEvent, EventData
import asyncio
import json

app = FastAPI()

class WebProgressCallback:
    """Web-specific event handler with WebSocket"""

    def __init__(self, websocket: WebSocket):
        self.websocket = websocket
        self.event_queue = asyncio.Queue()

    def __call__(self, event_data: EventData) -> None:
        """Called by generator - queues events for WebSocket"""
        asyncio.create_task(self.event_queue.put(event_data))

    async def stream_events(self):
        """Async generator that sends events to WebSocket"""
        while True:
            event_data = await self.event_queue.get()

            # Convert to JSON for web client
            message = {
                "event": event_data.event.value,
                "step": event_data.step,
                "data": event_data.data,
                "timestamp": event_data.timestamp.isoformat()
            }

            await self.websocket.send_json(message)

            # Stop streaming if generation complete
            if event_data.event == GenerationEvent.GENERATION_COMPLETE:
                break

@app.websocket("/ws/generate/{project_id}")
async def websocket_generate(websocket: WebSocket, project_id: str):
    """WebSocket endpoint for live generation updates"""
    await websocket.accept()

    try:
        # Load project
        project_manager = ProjectManager()
        project = project_manager.load_project(project_id)

        # Create web-specific callback
        callback = WebProgressCallback(websocket)

        # Create generator with web callback
        generator = IterativeGenerator(
            provider=project.config.provider,
            config=project.config,
            progress_callback=callback  # ← Web-specific handler
        )

        # Run generation in background task
        async def run_generation():
            working_doc = await asyncio.to_thread(
                generator.generate_project,
                project
            )
            project_manager.save_working_doc(project, working_doc)

        # Start generation and event streaming concurrently
        await asyncio.gather(
            run_generation(),
            callback.stream_events()
        )

    except Exception as e:
        await websocket.send_json({
            "event": "error",
            "data": {"error": str(e)}
        })
    finally:
        await websocket.close()

@app.post("/api/projects/{project_id}/generate")
async def rest_generate(project_id: str):
    """REST endpoint for generation (without live updates)"""

    project_manager = ProjectManager()
    project = project_manager.load_project(project_id)

    # No callback needed for REST API
    generator = IterativeGenerator(
        provider=project.config.provider,
        config=project.config,
        progress_callback=None  # ← No live updates
    )

    working_doc = await asyncio.to_thread(
        generator.generate_project,
        project
    )

    project_manager.save_working_doc(project, working_doc)

    return {"status": "complete", "working_doc": working_doc.to_dict()}
```

### Benefits of Headless Architecture

**1. Code Reusability**
- Core generation logic written once, used everywhere
- No duplication between CLI and web implementations
- Easier to maintain and test

**2. Interface Flexibility**
- Can add new interfaces (mobile app, desktop GUI) without changing core
- Each interface implements its own ProgressCallback
- Core logic doesn't care how events are displayed

**3. Testing Simplicity**
```python
# Tests can easily mock the callback
def test_generate_idea():
    events = []

    def test_callback(event_data):
        events.append(event_data)

    generator = IterativeGenerator(
        provider="ollama/qwen3:30b",
        config=config,
        progress_callback=test_callback
    )

    working_doc = generator.generate_project(project)

    # Assert events were emitted correctly
    assert events[0].event == GenerationEvent.STEP_STARTED
    assert events[-1].event == GenerationEvent.GENERATION_COMPLETE
```

**4. Background Processing**
- Web server can run generation in background jobs (Celery, RQ)
- CLI can still run synchronously in foreground
- Same core code works in both modes

**5. Future-Proof**
- Easy to add GraphQL API
- Easy to add gRPC for microservices
- Easy to add desktop app (Electron, Tauri)
- Core logic never changes

### Directory Structure

```
src/storygen/
├── iterative/              # Core logic (NO UI dependencies)
│   ├── __init__.py
│   ├── generator.py       # IterativeGenerator (headless)
│   ├── writer_ai.py       # WriterAI
│   ├── editor_ai.py       # EditorAI
│   ├── project_manager.py # ProjectManager
│   └── models.py          # Data models
│
├── cli/                   # CLI-specific code
│   ├── __init__.py
│   ├── commands.py        # Click commands
│   └── progress.py        # Terminal UI helpers
│
├── web/                   # Web-specific code
│   ├── __init__.py
│   ├── server.py          # FastAPI app
│   ├── websocket.py       # WebSocket handlers
│   └── static/            # HTML/CSS/JS
│       ├── index.html
│       └── app.js
│
└── outline_methods/       # Shared by both interfaces
    ├── three_act.py
    ├── heros_journey.py
    └── ...
```

### Implementation Priority

**Phase 1: Core (No UI yet)**
- Build IterativeGenerator with event system
- Build ProjectManager
- Test with simple callback that prints to stdout

**Phase 2: CLI Interface**
- Implement CLI commands using Rich/Click
- Create cli_progress_callback with terminal UI
- Test end-to-end CLI workflow

**Phase 3: Web Interface**
- Build FastAPI server
- Implement WebSocket endpoint
- Create simple HTML/JS frontend
- Reuse same IterativeGenerator core

### Key Principle

> **The core generator should never import `click`, `rich`, `fastapi`, or any UI framework.**
> It should only emit events and return data structures.

This ensures maximum flexibility and reusability across all current and future interfaces.

---

## Performance Considerations

### Token Usage Comparison

**Without Writer-Editor Pattern:**
- Each step: 1-2 AI calls (generation + optional retry)
- Estimated tokens per 2000-word story: ~15,000-20,000 tokens

**With Writer-Editor Pattern:**
- Each step: 2-4 AI calls (Writer → Editor → optional Writer revision → optional Editor recheck)
- Estimated tokens per 2000-word story: ~30,000-50,000 tokens

**Trade-off Analysis:**
- **Cost:** 2-3× more tokens/API calls
- **Time:** 2-3× longer generation time
- **Quality:** Significantly higher (fewer generic outputs, better consistency)
- **Reliability:** Fewer failed generations, clearer error messages

### Configuration Options

```python
# In CLI or config file
writer_editor_enabled: bool = True     # Enable/disable Editor AI
max_revision_cycles: int = 2           # Max Writer revisions per step
accept_rating: str = "acceptable"      # Minimum acceptable rating
editor_model: str | None = None        # Optional separate model for Editor
```

### When to Use Writer-Editor Pattern

**✅ RECOMMENDED:**
- Publishing-quality stories
- Complex narratives with many characters
- When quality > speed
- Using local models (low cost)

**❌ SKIP (use `--no-editor`):**
- Quick drafts or experimentation
- Simple stories
- Testing/debugging
- Using expensive API providers (OpenAI, Anthropic)

### Storage Performance

**Local JSON Files:**
- **Read:** ~1-5ms for project.json, ~10-50ms for working_doc.json
- **Write:** ~5-20ms atomic write with temp file + rename
- **List Projects:** ~10-100ms for scanning directory (depends on project count)
- **Version Snapshot:** ~20-100ms (copy working_doc to versions/)
- **Archive Export:** ~100-500ms (zip compression)

**Scalability:**
- **Small projects** (1-10 stories): Instant (<50ms) operations
- **Medium projects** (10-100 stories): Fast (<200ms) operations
- **Large projects** (100+ stories): Consider SQLite migration for faster queries

**Disk Space:**
- Typical project: ~2-5 MB total
  - project.json: ~1-2 KB
  - working_doc.json: ~100-500 KB (depends on story length)
  - Each version: ~100-500 KB
  - EPUB output: ~50-200 KB
  - Generation log: ~500 KB - 2 MB (full AI transcripts)
- 100 projects: ~200-500 MB
- Versions add ~100 KB per completed step (~700 KB for 7-step story)

**Backup Performance:**
- **Git commit:** ~100-500ms for single project
- **Git push:** Depends on network speed (typically 1-5s)
- **rsync backup:** ~50-200ms for incremental sync
- **Zip archive:** ~200-1000ms depending on project size
- **Cloud sync (Dropbox):** Background automatic, no user wait time

**Optimization Tips:**
- Keep generation.log separate (large, not needed for restore)
- Compress old versions after project completion
- Use .gitignore for cache/ and *.epub (don't version binaries)
- Periodic cleanup of abandoned projects

---

## References

- **Swain, Dwight V.** *Techniques of the Selling Writer.* University of Oklahoma Press, 1965.
- **Field, Syd.** *Screenplay: The Foundations of Screenwriting.* Delta, 2005.
- **Vogler, Christopher.** *The Writer's Journey.* Michael Wiese Productions, 2007.
- **Snyder, Blake.** *Save the Cat!* Michael Wiese Productions, 2005.
- **Wells, Dan.** *Seven-Point Story Structure.* Writing Excuses Podcast, 2011.
- **Bickham, Jack M.** *Scene and Structure.* Writer's Digest Books, 1993.

---

*Last Updated: 2025-11-10*
*Version: 1.1*
*Status: Approved for Implementation*

**Change Log:**
- v1.1: Clarified sequel optionality, single POV requirement, retry logic, checkpoint management per project requirements
- v1.0: Initial RFC
