# Quick Start Guide

## Basic Workflow

### Generate a Story

```bash
# Generate a structured story with AI
storygen generate "A detective who can see ghosts" --structured --epub ghost-detective.epub

# Or generate and save as JSON for further processing
storygen generate "A space adventure" --structured --format json > space-adventure.json
```

### Editorial Analysis & Improvement

```bash
# Analyze a story idea
storygen edit idea --idea idea.json --output feedback.json

# Apply AI-driven revisions based on editorial feedback
storygen edit revise --feedback feedback.json --input story.json --output improved-story.json

# Start background editorial analysis
storygen job start --prose story.json --output analysis.json
storygen job status <job-id>
```

## Complete Workflow Example

### Option 1: Automated Iterative Workflow (Recommended)

```bash
# Run the complete editorial workflow automatically
storygen edit all "A cyberpunk hacker discovers a conspiracy" --iterations 3 --quality-threshold 8.0 --verbose

# This will:
# 1. Generate initial story
# 2. Analyze quality and provide feedback
# 3. Apply AI-driven revisions
# 4. Repeat until quality threshold met or max iterations reached
# 5. Save final result to iterative_story_YYYYMMDD_HHMMSS.json
```

### Option 2: Manual Step-by-Step

```bash
# Generate initial story
storygen generate "A cyberpunk hacker discovers a conspiracy" --structured --format json > hacker-story.json

# Analyze the story structure
storygen job start --prose hacker-story.json --output structural-feedback.json

# Check job progress
storygen job status <job-id>

# Apply AI improvements (when feedback is ready)
storygen edit revise --feedback structural-feedback.json --input hacker-story.json --output improved-hacker-story.json

# Generate final EPUB
storygen generate "A cyberpunk hacker discovers a conspiracy" --structured --epub hacker-story.epub
```

## Command Reference

### Story Generation
```bash
storygen generate [PROMPT] [OPTIONS]

Options:
  --provider MODEL      AI provider (gpt-4, claude-3-sonnet, ollama/llama2)
  --structured          Generate with title, scenes, metadata
  --format json|text    Output format for structured stories
  --epub FILENAME       Generate EPUB file
  --min-words COUNT     Minimum word count
  --pov POV             Point of view (first_person, third_person_deep, etc.)
  --structure TYPE      Story structure (three_act, hero_journey, etc.)
  --verbose             Show detailed progress
```

### Editorial Commands
```bash
# Automated iterative workflow (recommended)
storygen edit all "Your story prompt" --iterations 3 --quality-threshold 8.0

# Manual step-by-step
storygen edit idea --idea file.json --output feedback.json
storygen edit revise --feedback feedback.json --input story.json --output revised.json
```

### Job Management
```bash
# Start analysis job
storygen job start --prose story.json --output feedback.json

# Monitor progress
storygen job status <job-id>
storygen job list

# Control jobs
storygen job pause <job-id>
storygen job resume <job-id>
storygen job cancel <job-id>
```

## Tips

1. **Start Simple**: Begin with basic generation, then add editorial analysis
2. **Use Local Models**: Ollama models are free and work offline
3. **Iterative Improvement**: Use the revise command to let AI improve its own work
4. **Background Processing**: Long analyses can run in background with job commands
5. **Cost Control**: Use `--max-cost` to limit API spending

## Model Recommendations

- **Free/Local**: `ollama/llama2`, `ollama/mistral`
- **Fast/Cheap**: `xai/grok-2-1212`
- **High Quality**: `gpt-4`, `claude-3-opus`

## Troubleshooting

- **Model Not Found**: Install Ollama and run `ollama pull llama2`
- **API Errors**: Check your API keys in `.env` file
- **Long Wait Times**: Use `--verbose` to see progress
- **Job Stuck**: Use `job cancel` then restart
