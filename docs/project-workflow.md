# Project-Based Workflow

## Overview

The project-based workflow provides an organized way to manage story generation by keeping all related files in a dedicated project directory.

## Quick Start

### Create a New Project

```bash
# With pitch
storygen-iter new necromancer-duel --pitch "Two necromancers fight to the death over shared love"

# Interactive (will prompt for pitch)
storygen-iter new my-story
```

This creates:
```
projects/
  necromancer-duel/
    metadata.json  # Contains pitch and other project info
```

### List All Projects

```bash
storygen-iter projects
```

Shows all projects with their completion status.

### Check Project Status

```bash
storygen-iter status necromancer-duel
```

Shows which pipeline stages are complete and suggests next steps.

### Generate Story (Project Mode)

```bash
# Generate idea (uses saved pitch from metadata.json)
storygen-iter idea necromancer-duel --model ollama/qwen3:30b

# TODO: Remaining commands to be updated
# storygen-iter characters necromancer-duel
# storygen-iter locations necromancer-duel
# storygen-iter outline necromancer-duel
# storygen-iter breakdown necromancer-duel --words 4000
# storygen-iter prose necromancer-duel
# storygen-iter epub necromancer-duel
```

### Current Workaround (Manual Paths)

Until all commands support project mode, you can use explicit paths:

```bash
# Create project structure
storygen-iter new necromancer-duel --pitch "Two necromancers duel"

# Generate with explicit paths
storygen-iter idea necromancer-duel --model ollama/qwen3:30b  # ✅ Works!
storygen-iter characters -i projects/necromancer-duel/idea.json -o projects/necromancer-duel/characters.json --model ollama/qwen3:30b
storygen-iter locations -i projects/necromancer-duel/idea.json -o projects/necromancer-duel/locations.json --model ollama/qwen3:30b
storygen-iter outline -i projects/necromancer-duel/idea.json -c projects/necromancer-duel/characters.json -l projects/necromancer-duel/locations.json -o projects/necromancer-duel/outline.json --model ollama/qwen3:30b
# ... and so on
```

## Project Structure

Each project has a standardized structure:

```
projects/
  <project-name>/
    metadata.json      # Pitch and project info
    idea.json          # Story idea (hook, description, themes)
    characters.json    # Generated characters
    locations.json     # Generated locations
    outline.json       # Scene outline (acts and scenes)
    breakdown.json     # Detailed scene-sequel breakdown
    prose.json         # Generated prose for all scenes
    story.epub         # Final EPUB file
```

## Benefits

- **Organization**: All files for a story in one place
- **Clarity**: Standardized file names (always `idea.json`, never `necromancer_idea_v2_final.json`)
- **Progress Tracking**: Easy to see what's done with `status` command
- **Multiple Projects**: Work on several stories in parallel
- **Incremental Save**: Resume failed prose generation automatically

## Implementation Status

### ✅ Completed
- `ProjectManager` class for managing project directories
- `new` command - create project with pitch
- `projects` command - list all projects with status
- `status` command - show detailed project progress
- `idea` command - generate idea in project mode
- Projects directory added to `.gitignore`

### 🚧 In Progress
- Update remaining commands (`characters`, `locations`, `outline`, `breakdown`, `prose`, `epub`) to accept project names
- Helper function `resolve_project_or_path()` created for easy integration

### 📋 Planned
- `generate` command to run full pipeline in one go
- Project templates (different structures for different story types)
- Project export/import for sharing
- Project metadata expansion (author, tags, creation date)
