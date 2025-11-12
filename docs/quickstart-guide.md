# Quick Start Guide

## Basic Workflow

### Option 1: Full Pipeline (One Command)

```bash
# Create project and generate everything
storygen-iter new my-story --pitch "A detective who can see ghosts"
storygen-iter generate my-story --model ollama/qwen3:30b --words 4000 -v
```

That's it! This will:
1. Generate story idea from pitch
2. Create 1-3 core characters (genre-appropriate names)
3. Generate 3-7 locations
4. Create story outline
5. Break down into scene-sequels
6. Generate prose (with incremental save/resume)
7. Create EPUB with AI-generated title

### Option 2: Step-by-Step

```bash
# Create project
storygen-iter new necromancer-duel --pitch "Two necromancers duel over shared love"

# Check status
storygen-iter status necromancer-duel

# Run each stage manually
storygen-iter idea necromancer-duel --model ollama/qwen3:30b
storygen-iter characters necromancer-duel --model ollama/qwen3:30b
storygen-iter locations necromancer-duel --model ollama/qwen3:30b --timeout 300
storygen-iter outline necromancer-duel --model ollama/qwen3:30b
storygen-iter breakdown necromancer-duel --words 4000 --model ollama/qwen3:30b
storygen-iter prose necromancer-duel --model ollama/qwen3:30b --writing-style "Clark Ashton Smith: baroque, ornate"
storygen-iter epub necromancer-duel --author "Your Name"
```

### Option 3: Smart Regeneration

If you edit source files (like modifying a character), regenerate dependencies:

```bash
# Edit characters.json manually
# Then regenerate everything that depends on it
storygen-iter generate necromancer-duel --check-deps -v
```

This will:
- Detect that characters.json changed
- Backup affected files (outline.json.backup-20251112-143500, etc.)
- Regenerate only what needs updating

### Resume from Stage

If generation fails midway (timeout, crash), resume:

```bash
# Resume from breakdown stage
storygen-iter generate my-story --from-stage breakdown --model ollama/qwen3:30b
```

Prose generation automatically resumes from last completed scene if interrupted.

## Project Management

```bash
# List all projects
storygen-iter projects

# Check specific project
storygen-iter status necromancer-duel

# View all files
ls projects/necromancer-duel/
```

## Common Options

- `--model ollama/qwen3:30b` - Use local Ollama model
- `--words 4000` - Target word count (default: 2000)
- `--structure hero-journey` - Use different outline template
- `--writing-style "Description"` - Override auto-detected style
- `--timeout 300` - Increase timeout for slow models (default: 60s)
- `-v` - Verbose output to see what's happening
- `--check-deps` - Regenerate files if sources changed
- `--backup` - Create backups before overwriting (default: on)

## Tips

1. **Character Names**: The system now generates genre-appropriate names:
   - Clark Ashton Smith style: "Malygris", "Namirrha" (not "Elara")
   - Contemporary: "Maya Chen", "Dr. Aris Thorne"
   - Historical: Period-appropriate names

2. **Incremental Save**: Prose generation saves after each scene. If it crashes, just run again:
   ```bash
   storygen-iter prose necromancer-duel --model ollama/qwen3:30b
   # Crashes after 10 scenes
   # Run again - resumes from scene 11
   storygen-iter prose necromancer-duel --model ollama/qwen3:30b
   ```

3. **Timeouts**: Local models need more time:
   - Locations: `--timeout 300`
   - Breakdown: `--timeout 600`
   - Prose: `--timeout 300` (per scene)

4. **Backup Files**: Check `projects/your-story/` for `.backup-*` files if you need to revert changes

5. **AI Title Generation**: EPUB command analyzes your complete story to generate a resonant title, not just the pitch

## Example Full Command

```bash
storygen-iter generate necromancer-duel \
  --model ollama/qwen3:30b \
  --words 8000 \
  --structure three-act \
  --writing-style "Clark Ashton Smith: baroque, ornate, archaic language with cosmic horror undertones" \
  --author "Mark Cromwell" \
  --check-deps \
  -v
```
