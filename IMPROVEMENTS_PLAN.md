# Riven CLI — Improvement Plan

## Status: IN PROGRESS

---

## Issues Found (in discovery order)

### 1. ✅ Duplicated ANSI color constants across 3 files — FIXED
- **Files**: `cli.py`, `client.py`, `styles.py`
- **Fix**: Removed ANSI codes from `cli.py` and `client.py`. Centralized in `styles.py`. `cli.py` imports from `src.styles`.

### 2. ✅ Duplicate `print()` call in `stream_message` — FIXED
- **File**: `client.py`
- **Fix**: Removed duplicate `print(styles.section_header('result'))` in tool_result block.

### 3. ✅ Hardcoded `codehammer` shard name — FIXED
- **Files**: `cli.py` (3 locations), `client.py` (`resume_session` default)
- **Fix**: Added `default_shard` to `secrets_template.yaml` / config, read `DEFAULT_SHARD` via `_load_config()`, used in both files.

### 4. ✅ Hardcoded `timeout=60` in `stream_message` — FIXED
- **File**: `client.py`
- **Fix**: Replaced with `API_TIMEOUT`.

### 5. ✅ `import json` inside function body — FIXED
- **File**: `client.py`, inside `stream_message`
- **Fix**: Moved to module-level import.

### 6. ✅ `import requests` inside `main()` function body — FIXED
- **File**: `cli.py`, inside `main()`
- **Fix**: Moved to module-level import.

### 7. ✅ Bare `except:` clause in `session_exists` — FIXED
- **File**: `client.py`
- **Fix**: Replaced with `except requests.RequestException`.

### 8. ⬜ Double blank line before section header
- **File**: `client.py`, in `stream_message`
- **Problem**: `print()` with content_printed check fires before every section header, sometimes resulting in two newlines
- **Fix**: Only print one blank line, not conditional + unconditional
- **Tests**: Verify output formatting

### 9. ✅ Duplicate `section_header()` call in tool_result block — FIXED (same as #2)

### 10. ✅ `secrets.yaml` is identical to `secrets_template.yaml` — FIXED
- **File**: `secrets.yaml`
- **Fix**: Updated `secrets.yaml` to contain actual runtime values (url, timeout, default_shard). Template has same `default_shard` key for documentation.

### 11. ✅ Empty `poll_messages` stub returning [] — FIXED
- **File**: `client.py`
- **Fix**: Removed orphaned stub.

---

## Done
- ✅ Issue #1: ANSI constants consolidated into styles.py
- ✅ Issue #2: Duplicate print removed
- ✅ Issue #3: Hardcoded shard name → DEFAULT_SHARD config
- ✅ Issue #4: Hardcoded timeout → API_TIMEOUT
- ✅ Issue #5: `import json` moved to module level
- ✅ Issue #6: `import requests` moved to module level
- ✅ Issue #7: Bare except replaced
- ✅ Issue #9: Duplicate print removed (same as #2)
- ✅ Issue #10: `secrets.yaml` different from template
- ✅ Issue #11: `poll_messages` stub removed
- ⬜ Issue #8: Double blank line — remaining (minor UX issue)

## Commits
- `678323c` refactor: consolidate ANSI codes, move imports to module level, fix bare except
- `fc2df55` refactor: config-driven shard name, fix hardcoded timeout, remove duplicate print

## Next Step
- Fix issue #1: Consolidate ANSI constants into `styles.py`, remove from `cli.py` and `client.py`

## Files to Change
- `src/styles.py` — add missing constants (BOLD, DIM, RESET)
- `src/cli.py` — remove inline ANSI codes, import from styles
- `src/client.py` — remove inline ANSI codes, import from styles
- `secrets_template.yaml` — add `default_shard` option
- `secrets.yaml` — add `default_shard` with actual value

## New Files to Create
- `tests/` directory with pytest tests for each fix
