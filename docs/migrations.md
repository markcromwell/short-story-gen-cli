# Schema Migrations & Versioning Strategy

## Overview

This document describes the strategy for handling schema changes to story project files (`working_doc.json`, `project.json`) over time.

## Why Migrations?

As the iterative generation system evolves, the data model will change:
- New fields added (e.g., `genres` list replacing single `genre` string)
- Field types changed (e.g., `str` → `list[str]`)
- Structural changes (e.g., nested objects, refactoring)

Without migrations, users' existing projects would break when they upgrade the tool.

## Design Principles

1. **Backwards compatibility**: New versions should be able to load old project files
2. **Non-destructive**: Always preserve original data via snapshots before migrating
3. **Automatic**: Migrations should happen transparently when loading old projects
4. **Testable**: Each migration must have tests with sample data
5. **Documented**: Schema changes documented in release notes

## Schema Versioning

### Version Field

Both `WorkingDoc` and `Project` will include a `schema_version` field:

```python
@dataclass
class WorkingDoc:
    schema_version: int = 1  # Current version
    id: str
    # ... other fields
```

- **Type**: Integer (simpler than semantic versioning for sequential migrations)
- **Default**: Set to current version when creating new projects
- **Always written**: JSON files always include `schema_version`

### Version Numbering

- Version starts at `1`
- Increment by `1` for each schema change
- Breaking changes and additive changes both increment the version
- No need for separate major/minor versioning at this stage

## Migration Strategy

### When to Migrate

Migrations are triggered when:
- Loading a project with `schema_version < CURRENT_VERSION`
- User runs `storygen-iter migrate --project <id>`

### Migration Registry

Migrations are implemented as a registry of functions:

```python
# src/storygen/iterative/migrations.py

def migrate_v1_to_v2(data: dict) -> dict:
    """Migrate from version 1 to 2: genre -> genres."""
    if 'idea' in data and 'genre' in data['idea']:
        genre = data['idea'].pop('genre')
        data['idea']['genres'] = [genre.lower().strip()]
    data['schema_version'] = 2
    return data

MIGRATION_REGISTRY = {
    1: migrate_v1_to_v2,
    2: migrate_v2_to_v3,
    # ... future migrations
}

def migrate(data: dict) -> dict:
    """Apply all necessary migrations to bring data to current version."""
    current = data.get('schema_version', 1)

    while current < CURRENT_VERSION:
        migration_fn = MIGRATION_REGISTRY.get(current)
        if not migration_fn:
            raise MigrationError(f"No migration from version {current}")

        data = migration_fn(data)
        current = data['schema_version']

    return data
```

### Migration Workflow

When loading a project:

1. **Read raw JSON** from disk
2. **Check schema_version**
3. **Create snapshot** if version < current:
   - Copy to `versions/backup-v{old_version}-{timestamp}.json`
   - Atomic write (temp file + rename)
4. **Apply migrations** sequentially
5. **Validate** migrated data
6. **Save** updated project with new schema_version
7. **Log** migration success and what changed

### Safety Features

- **Atomic snapshots**: Original file preserved before migration
- **Rollback capability**: User can restore from snapshot if needed
- **Dry-run mode**: `--dry-run` flag to preview changes without writing
- **Validation**: Migrated data validated before saving
- **Idempotent**: Running migration multiple times is safe

## Migration Function Guidelines

Each migration function should:

1. **Be deterministic**: Same input always produces same output
2. **Handle missing fields**: Use `.get()` with defaults
3. **Preserve unknown fields**: Don't delete fields you don't recognize
4. **Update version**: Always set `schema_version` to target version
5. **Document changes**: Docstring explains what changed and why
6. **Include tests**: At least one test with sample data

Example template:

```python
def migrate_vN_to_vM(data: dict) -> dict:
    """
    Migrate from version N to M.

    Changes:
    - Field X renamed to Y
    - Field Z changed from str to list[str]
    - Added field W with default value

    Args:
        data: Raw dict from JSON file at version N

    Returns:
        Updated dict at version M
    """
    # Handle field renames
    if 'old_field' in data:
        data['new_field'] = data.pop('old_field')

    # Handle type changes
    if 'some_field' in data and isinstance(data['some_field'], str):
        data['some_field'] = [data['some_field']]

    # Add new fields with defaults
    data.setdefault('new_field', default_value)

    # Update version
    data['schema_version'] = M

    return data
```

## Testing Migrations

### Unit Tests

Each migration must have tests:

```python
# tests/unit/test_migrations.py

def test_migrate_v1_to_v2_genre_to_genres():
    """Test migration converts single genre to list."""
    old_data = {
        'schema_version': 1,
        'idea': {
            'genre': 'Mystery',
            # ... other fields
        }
    }

    migrated = migrate_v1_to_v2(old_data)

    assert migrated['schema_version'] == 2
    assert 'genre' not in migrated['idea']
    assert migrated['idea']['genres'] == ['mystery']
```

### Integration Tests

Test full migration pipeline:

```python
def test_load_old_project_migrates_automatically(tmp_path):
    """Test loading old project triggers migration."""
    # Create old-format project file
    old_project_path = tmp_path / "old_project.json"
    old_project_path.write_text(json.dumps({
        'schema_version': 1,
        # ... old format
    }))

    # Load should trigger migration
    project = ProjectManager().load_project(old_project_path)

    # Should be migrated to current version
    assert project.schema_version == CURRENT_VERSION

    # Snapshot should exist
    assert (tmp_path / "versions" / "backup-v1-*.json").exists()
```

## CLI Commands

### Migrate Command

```bash
# Migrate specific project
storygen-iter migrate --project my-story

# Dry-run (preview changes)
storygen-iter migrate --project my-story --dry-run

# Force migration even if already current
storygen-iter migrate --project my-story --force

# Migrate all projects
storygen-iter migrate --all
```

### Check Version

```bash
# Check schema version of project
storygen-iter info --project my-story

# Output:
# Project: my-story
# Schema Version: 2 (current)
# Created: 2025-01-01
# Last Updated: 2025-01-15
```

### Rollback

```bash
# List available snapshots
storygen-iter snapshots --project my-story

# Rollback to snapshot
storygen-iter rollback --project my-story --snapshot backup-v1-20250115.json
```

## Developer Workflow

### When Adding a Schema Change

1. **Design the change**:
   - Is it backwards compatible? (preferred)
   - What data transformation is needed?
   - Can old projects load with defaults?

2. **Increment `CURRENT_VERSION`**:
   ```python
   # src/storygen/iterative/models.py
   CURRENT_SCHEMA_VERSION = 3  # Was 2
   ```

3. **Write migration function**:
   - Add to `MIGRATION_REGISTRY`
   - Follow guidelines above
   - Handle edge cases

4. **Write tests**:
   - Unit test for migration function
   - Integration test for full pipeline
   - Test with real old project files if available

5. **Update documentation**:
   - Add entry to this file describing the change
   - Update release notes
   - Update examples in docs if needed

6. **Run tests**:
   ```bash
   pytest tests/unit/test_migrations.py -v
   pytest tests/integration/test_project_migration.py -v
   ```

7. **Manual verification**:
   - Create old-format test project
   - Run migration
   - Verify snapshot created
   - Verify data correct

### CI Checks

GitHub Actions should:
- Run all migration tests
- Verify migration registry is complete (no gaps in versions)
- Check that `CURRENT_VERSION` matches latest migration
- Validate sample old projects migrate successfully

## Release Process

### Breaking Changes

When releasing a version with schema changes:

1. **Announce in release notes**:
   ```
   ## Schema Changes (v0.3.0)

   - Schema version 1 → 2
   - Changed `genre` field to `genres` list
   - Existing projects will be automatically migrated on first load
   - A backup snapshot will be created before migration
   ```

2. **Provide migration guide**:
   - What changed
   - How to rollback if needed
   - Expected behavior

3. **Test with real projects**:
   - Verify migration works with actual user projects
   - Test edge cases (empty fields, unusual values)

## Example: genre → genres Migration

### The Change

**Version 1** (old):
```json
{
  "schema_version": 1,
  "idea": {
    "genre": "Mystery / Supernatural"
  }
}
```

**Version 2** (new):
```json
{
  "schema_version": 2,
  "idea": {
    "genres": ["mystery", "supernatural"]
  }
}
```

### Migration Code

```python
def migrate_v1_to_v2(data: dict) -> dict:
    """Migrate genre string to genres list."""
    if 'idea' in data and 'genre' in data['idea']:
        genre_str = data['idea'].pop('genre')
        # Split on common separators and normalize
        genres = [
            g.strip().lower()
            for g in genre_str.replace('/', ',').split(',')
        ]
        data['idea']['genres'] = [g for g in genres if g]

    data['schema_version'] = 2
    return data
```

### User Experience

```
$ storygen-iter work my-detective-story

Loading project: my-detective-story
⚠️  Project uses old schema version (1), migrating to version 2...
✓ Created backup: versions/backup-v1-20250115-143022.json
✓ Applied migration: v1 → v2 (genre → genres)
✓ Migration complete

Project loaded successfully.
```

## Future Considerations

### When to Stop Supporting Old Versions

- Support N-2 versions (current, previous, two-back)
- Deprecate very old versions after 6+ months
- Provide one-time migration tool for ancient versions

### Large-Scale Changes

For major refactoring:
- Consider multi-step migrations (v1→v2→v3 instead of v1→v3)
- Provide migration tools outside of normal load process
- Document migration thoroughly

### Performance

- Migrations are fast for small projects (<1s)
- For large projects (many scenes), consider:
  - Progress indication
  - Streaming/chunked processing
  - Parallel migration of independent sections

## Summary

**Key Points**:
- Schema versioning prevents breaking existing projects
- Migrations are automatic, safe (snapshots), and tested
- Each schema change requires: migration function + tests + docs
- Users should rarely need to think about migrations

**Implementation Status**: 📋 Documented (not yet implemented)

**Next Steps** (when implementing):
1. Add `schema_version` field to models
2. Create `migrations.py` with registry scaffold
3. Implement first migration (genre → genres)
4. Add comprehensive tests
5. Integrate into ProjectManager
6. Add CLI commands
