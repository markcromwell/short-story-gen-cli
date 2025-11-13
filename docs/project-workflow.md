# Project-Based Workflow

## Overview

The current system uses a flexible file-based approach where you can generate stories directly and save them as JSON files for further processing. Projects are managed through file organization rather than dedicated project directories.

## Quick Start

### Generate and Save a Story

```bash
# Generate a structured story and save as JSON
storygen generate "A detective who can see ghosts" --structured --format json > ghost-detective.json

# Generate with specific parameters
storygen generate "A space adventure" --structured --format json --min-words 3000 --pov first_person > space-adventure.json
```

### Editorial Analysis and Improvement

```bash
# Analyze story structure
storygen job start --prose ghost-detective.json --output structural-feedback.json

# Check job progress
storygen job status <job-id>

# Apply AI-driven improvements
storygen edit revise --feedback structural-feedback.json --input ghost-detective.json --output improved-ghost-detective.json
```

### Generate EPUB

```bash
# Create EPUB from JSON story
storygen generate "A detective who can see ghosts" --structured --epub ghost-detective.epub
```

## File Organization

While not enforced, a recommended structure for managing multiple stories:

```
stories/
  ghost-detective/
    story.json          # Original generated story
    feedback.json       # Editorial analysis results
    improved.json       # AI-revised version
    story.epub          # Final EPUB file
  space-adventure/
    story.json
    feedback.json
    improved.json
    story.epub
```

## Complete Workflow Example

```bash
# 1. Create directory for organization
mkdir -p stories/cyberpunk-hacker

# 2. Generate initial story
storygen generate "A cyberpunk hacker discovers a conspiracy" --structured --format json > stories/cyberpunk-hacker/story.json

# 3. Start editorial analysis
storygen job start --prose stories/cyberpunk-hacker/story.json --output stories/cyberpunk-hacker/feedback.json

# 4. Monitor progress
storygen job status <job-id>

# 5. Apply improvements when ready
storygen edit revise --feedback stories/cyberpunk-hacker/feedback.json --input stories/cyberpunk-hacker/story.json --output stories/cyberpunk-hacker/improved.json

# 6. Generate final EPUB
storygen generate "A cyberpunk hacker discovers a conspiracy" --structured --epub stories/cyberpunk-hacker/story.epub
```

## Benefits

- **Flexibility**: Generate stories directly without project setup
- **File-Based**: Easy to version control and share individual files
- **Iterative**: Apply multiple rounds of editorial improvement
- **Background Processing**: Long analyses run asynchronously
- **Cost Control**: Track and limit AI API usage

## Command Reference

### Story Generation
```bash
storygen generate [PROMPT] [OPTIONS]

Options:
  --provider MODEL      AI provider (gpt-4, claude-3-sonnet, ollama/llama2)
  --structured          Generate with title, scenes, metadata
  --format json|text    Output format
  --epub FILENAME       Generate EPUB file
  --min-words COUNT     Minimum word count
  --pov POV             Point of view
  --structure TYPE      Story structure
  --verbose             Show progress
```

### Editorial Commands
```bash
# Analyze story idea
storygen edit idea --idea file.json --output feedback.json

# Apply AI revisions
storygen edit revise --feedback feedback.json --input story.json --output revised.json
```

### Job Management
```bash
# Start background analysis
storygen job start --prose story.json --output feedback.json

# Monitor and control
storygen job status <job-id>
storygen job list
storygen job pause <job-id>
storygen job resume <job-id>
storygen job cancel <job-id>
```

## Tips

1. **File Naming**: Use descriptive names for your JSON files
2. **Version Control**: Commit story files to track changes
3. **Backup Important Work**: Save versions before major revisions
4. **Batch Processing**: Use job commands for multiple stories
5. **Cost Monitoring**: Check costs with `--verbose` or config settings

## Migration from Old System

If you have old project directories from `storygen-iter`:

```bash
# Convert old project to new format
# 1. Extract the story data from old files
# 2. Generate new story with current system
# 3. Use editorial commands for improvements

# Example migration
storygen generate "Your old story pitch" --structured --format json > migrated-story.json
storygen job start --prose migrated-story.json --output feedback.json
```

## Implementation Status

### ✅ Completed
- Direct story generation with JSON output
- AI-driven editorial revision system
- Background job processing
- EPUB generation
- Comprehensive CLI with all commands working
- Full test coverage (242 tests passing)

### 📋 Future Enhancements
- Project directory management (optional)
- Story templates and presets
- Batch processing for multiple stories
- Advanced export options
- Story comparison and diff tools
