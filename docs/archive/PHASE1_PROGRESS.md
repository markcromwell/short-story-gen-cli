# Phase 1 CLI Refactoring - Progress Report

## Status: IN PROGRESS (30% Complete)

### Completed Tasks ✅

1. **Created CLI Package Structure**
   - `src/storygen/iterative/cli/__init__.py` - Package exports
   - `src/storygen/iterative/cli/commands/__init__.py` - Command modules
   - Directory structure ready for modular commands

2. **Created Utils Module** (`cli/commands/utils.py`)
   - `resolve_project_or_path()` - Project name/path resolution
   - `get_default_word_count()` - Story type defaults
   - `format_word_count()` - Number formatting
   - `format_list()` - List truncation for display
   - `setup_logging()` - Logging configuration
   - **Logging Strategy**: Using Python's `logging` module with DEBUG/INFO levels

3. **Created Project Commands Module** (`cli/commands/project.py`)
   - `new` command - Create new story projects with interactive prompts
   - `projects` command - List all projects with completion status
   - `status` command - Show detailed project pipeline status
   - **Changes**: Added `logger` calls for debugging, kept `click.echo()` for user output
   - **Lines**: ~310 lines (migrated from original ~200 lines due to logging)

### Remaining Tasks 🔨

4. **Generate Commands Module** (`cli/commands/generate.py`) - NOT STARTED
   - `idea` command - Generate story ideas
   - `characters` command - Generate characters
   - `locations` command - Generate locations
   - `outline` command - Generate story outlines
   - Estimated: ~450 lines

5. **Prose Commands Module** (`cli/commands/prose.py`) - NOT STARTED
   - `breakdown` command - Break outline into scene-sequels
   - `prose` command - Generate prose from breakdown
   - `continue-prose` command (if exists)
   - Estimated: ~450 lines

6. **Export Commands Module** (`cli/commands/export.py`) - NOT STARTED
   - `title` command - Generate story titles
   - `epub` command - Format EPUB output
   - Estimated: ~250 lines

7. **Main CLI Entry Point** (`cli/main.py`) - NOT STARTED
   - Import all command modules
   - Set up click.Group to combine commands
   - Configure logging at startup
   - Handle environment variables (dotenv)
   - Estimated: ~50 lines

8. **Update Entry Point** (`pyproject.toml`) - NOT STARTED
   - Change from `storygen.iterative.cli:cli` → `storygen.iterative.cli.main:cli`

9. **Verification** - NOT STARTED
   - Run full test suite: `pytest`
   - Manual testing of key commands
   - Verify all imports work

10. **Cleanup** - NOT STARTED
    - Delete old `src/storygen/iterative/cli.py` (1,700 lines)
    - Update any documentation

### Key Design Decisions

**Logging Strategy**:
- Use `logging.getLogger(__name__)` in each module
- User-facing output: `click.echo()` to stderr
- Debug/internal: `logger.debug()`, `logger.info()`, `logger.error()`
- Setup in `cli/main.py` based on `--verbose` flag

**Import Strategy**:
- Kept heavy imports (generators, models) local to command functions
- Faster CLI startup time
- Only load what's needed for each command

**Type Safety**:
- Added `# type: ignore[arg-type]` where Click's dynamic typing conflicts with mypy
- Maintained strict typing for core logic

### File Size Comparison

**Before** (monolithic):
- `cli.py`: 1,700 lines

**After** (modular):
- `cli/__init__.py`: 10 lines
- `cli/main.py`: ~50 lines (to be created)
- `cli/commands/__init__.py`: 3 lines
- `cli/commands/utils.py`: 109 lines
- `cli/commands/project.py`: 310 lines
- `cli/commands/generate.py`: ~450 lines (to be created)
- `cli/commands/prose.py`: ~450 lines (to be created)
- `cli/commands/export.py`: ~250 lines (to be created)
- **Total**: ~1,632 lines (68 lines saved) + better organization

### Next Steps

**Recommended Approach**:
1. Create `generate.py` with idea, characters, locations, outline commands
2. Create `prose.py` with breakdown, prose commands
3. Create `export.py` with title, epub commands
4. Create `main.py` to wire everything together
5. Update `pyproject.toml` entry point
6. Run tests (`pytest`)
7. Manual verification of key commands
8. Delete old `cli.py`

**Time Estimate**: 2-3 hours remaining

### Testing Plan

**Commands to Test**:
```bash
# Project management
storygen-iter new test-cli-refactor --pitch "test story" --type short-story
storygen-iter status test-cli-refactor
storygen-iter projects

# Generation
storygen-iter idea test-cli-refactor "detective story"
storygen-iter characters test-cli-refactor
storygen-iter locations test-cli-refactor
storygen-iter outline test-cli-refactor

# Prose & Export
storygen-iter breakdown test-cli-refactor --words 4000
storygen-iter prose test-cli-refactor
storygen-iter epub test-cli-refactor
```

**Automated Tests**:
```bash
pytest tests/ -v
```

### Benefits Achieved So Far

✅ **Separation of Concerns**: Each command type in its own module
✅ **Logging Infrastructure**: Proper logging instead of print statements
✅ **Type Safety**: Maintained with minimal type ignores
✅ **Maintainability**: Easier to find and modify specific commands
✅ **Testability**: Each module can be tested independently

---

*Last Updated: In Progress*
*Next Action: Create generate.py module*
