# Riven CLI — Improvement Plan

## Status: IN PROGRESS

---

## Issues Found (in discovery order)

### 1. ⬜ Duplicated ANSI color constants across 3 files
- **Files**: `cli.py`, `client.py`, `styles.py`
- **Problem**: `RED`, `RESET`, `CYAN`, `MAGENTA`, `GREEN`, `YELLOW`, `WHITE`, `GREY`, `BOLD`, `DIM` defined in BOTH `cli.py` AND `styles.py`. `client.py` also defines `RED` and `RESET` again.
- **Fix**: Remove all ANSI codes from `cli.py` and `client.py`. Centralize them in `styles.py`. `cli.py` imports from `src.styles`.
- **Tests**: Verify no NameErrors after removal

### 2. ⬜ Duplicate `print()` call in `stream_message`
- **File**: `client.py` line ~the `tool_result` block
- **Problem**: `print(styles.section_header('result'))` called twice in a row
- **Fix**: Remove one
- **Tests**: Verify output still correct

### 3. ⬜ Hardcoded `codehammer` shard name
- **Files**: `cli.py` (appears ~3 times), `client.py` (in `resume_session` default)
- **Problem**: Shard name should come from config.yaml, not hardcoded
- **Fix**: Move `default_shard: codehammer` to `secrets_template.yaml` / `secrets.yaml`, read via `_load_config()`, use in both files
- **Tests**: Verify CLI still works with configurable shard

### 4. ⬜ Hardcoded `timeout=60` in `stream_message`
- **File**: `client.py`
- **Problem**: Uses hardcoded 60 instead of `API_TIMEOUT` constant defined 3 lines above
- **Fix**: Use `API_TIMEOUT` instead
- **Tests**: Verify still works

### 5. ⬜ `import json` inside function body
- **File**: `client.py`, inside `stream_message`
- **Problem**: Should be at module level
- **Fix**: Move to module-level import
- **Tests**: Verify still works

### 6. ⬜ `import requests` inside `main()` function body
- **File**: `cli.py`, inside `main()`
- **Problem**: Should be at module level
- **Fix**: Move to module-level import
- **Tests**: Verify CLI still boots

### 7. ⬜ Bare `except:` clause in `session_exists`
- **File**: `client.py`, `session_exists` method
- **Problem**: Catches ALL exceptions including KeyboardInterrupt, SystemExit
- **Fix**: Use `except requests.RequestException`
- **Tests**: Write unit test for this

### 8. ⬜ Double blank line before section header
- **File**: `client.py`, in `stream_message`
- **Problem**: `print()` with content_printed check fires before every section header, sometimes resulting in two newlines
- **Fix**: Only print one blank line, not conditional + unconditional
- **Tests**: Verify output formatting

### 9. ⬜ Duplicate `section_header()` call in tool_result block
- **File**: `client.py`, tool_result handling in `stream_message`
- **Problem**: `print(styles.section_header('result'))` called twice consecutively
- **Fix**: Remove duplicate call
- **Tests**: Verify

### 10. ⬜ `secrets.yaml` is identical to `secrets_template.yaml`
- **File**: `secrets.yaml`
- **Problem**: The actual config file is identical to the template — this means it was likely committed accidentally
- **Fix**: `secrets.yaml` should contain only actual runtime values (url, timeout, and add default_shard). Template stays as reference.
- **Tests**: N/A (config only)

### 11. ⬜ Empty `poll_messages` stub returning []
- **File**: `client.py`
- **Problem**: Stub method that always returns empty list, never called
- **Fix**: Remove it, or replace with `NotImplementedError` comment
- **Tests**: Verify nothing breaks

---

## Done
- (none yet)

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
