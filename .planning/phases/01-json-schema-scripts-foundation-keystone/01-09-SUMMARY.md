---
phase: 01-json-schema-scripts-foundation-keystone
plan: 09
subsystem: installer
tags: [installer, packaging, uv, legacy-cleanup, testing, shadow-comparison]
dependency_graph:
  requires: [01-06, 01-08]
  provides: [UV-01, SCHE-05, MERG-03]
  affects: [bin/install.js, package.json, scripts/tests/]
tech_stack:
  added: []
  patterns: [spawnSync uv hard-fail, legacyCleanup pattern, PEP 723 test wrapper]
key_files:
  created:
    - scripts/tests/test_packaging.py
    - scripts/tests/test_install_uv.sh
    - scripts/tests/test_install_uv_wrapper.py
    - .planning/phases/01-json-schema-scripts-foundation-keystone/SHADOW-COMPARISON.md
  modified:
    - bin/install.js
    - package.json
    - scripts/tests/test_no_dangling_refs.py
decisions:
  - "SHADOW-COMPARISON.md committed to main repo (eph5xx/json) via force-add since .planning/ is gitignored in worktrees; source code changes committed to worktree branch"
  - "test_no_dangling_refs.py updated to exclude install.js from forbidden-string scan — intentional legacy name references for v1.0 cleanup"
  - "Legacy orphan files (agents/ti-merger.md, skills/ti-html-report/) deleted from worktree — were untracked artifacts from old branch state"
metrics:
  duration: "~20 min"
  completed: "2026-04-13"
  tasks_completed: 3
  files_changed: 7
---

# Phase 1 Plan 9: Installer Hardening + Packaging + MERG-03 Summary

Phase 1 Plan 09 closes the final three Phase 1 requirements: UV-01 (uv hard-fail at install time), SCHE-05 (schemas/scripts ship via npm), and MERG-03 (shadow comparison procedure documented). The installer now hard-fails with a remediation message when `uv` is absent, copies the new `schemas/` and `scripts/` directories into `.claude/`, and removes v1.0 orphan files (`ti-merger.md`, `ti-html-report/`) during upgrade. `npx tweakidea` is now a complete Phase 1 install.

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Update bin/install.js — uv check + schemas/scripts copy + legacy cleanup | `16e9aca` | `bin/install.js` |
| 2 | Update package.json#files + create test_packaging.py + test_install_uv.sh | `c686510` | `package.json`, `scripts/tests/test_packaging.py`, `scripts/tests/test_install_uv.sh`, `scripts/tests/test_install_uv_wrapper.py`, `scripts/tests/test_no_dangling_refs.py` |
| 3 | Document MERG-03 shadow comparison procedure | `9cf5574` (main repo) | `.planning/phases/01-json-schema-scripts-foundation-keystone/SHADOW-COMPARISON.md` |

## What Was Built

### bin/install.js (Task 1)

- `verifyUvOrExit()`: uses `child_process.spawnSync('uv', ['--version'])` to hard-fail with remediation message (exact D-04 text) before any filesystem changes. Called at top of `install()` only — `--help`, `--version`, and `uninstall` paths bypass it.
- `legacyCleanup(targetDir)`: removes `ti-merger.md` from `agents/` and `ti-html-report/` from `skills/` if present. Runs after `cleanupPreviousInstall()` in `install()`.
- `cleanupPreviousInstall()`: extended to also remove `schemas/` and `scripts/` directories from `.claude/` on re-install/upgrade.
- `install()`: now copies `schemas/` and `scripts/` source dirs to `targetDir` after skills copy.
- Summary display: adds `Schemas: N installed` and `Scripts: N installed` lines.
- Old soft uv warning block (`requires 'uv' (Python package runner)`) deleted.

### package.json (Task 2)

`files` array expanded from 4 to 6 entries: `["bin", "agents", "commands", "skills", "schemas", "scripts"]`. This ensures `npx tweakidea` publishes the new schemas and scripts directories.

### Test suite additions (Task 2)

- `test_packaging.py`: asserts `package.json#files` has 6 entries including `schemas` and `scripts`, verifies `schemas/` and `scripts/` dirs exist on disk, checks 12 schema files present and key script files exist.
- `test_install_uv.sh`: shell integration test that scrubs `uv` from PATH, runs `node bin/install.js --local`, asserts non-zero exit code and correct remediation message in stderr. Uses exit-77 skip convention for environments where PATH scrubbing is impossible.
- `test_install_uv_wrapper.py`: Python unittest wrapper for the shell test — handles skip-77 convention, integrates into `uv run scripts/tests/run_tests.py` suite.
- `test_no_dangling_refs.py`: updated to exclude `install.js` from the forbidden-string scan (intentional legacy name references in `LEGACY_AGENTS`/`LEGACY_SKILL_DIRS`).

All 134 tests pass.

### SHADOW-COMPARISON.md (Task 3)

Manual procedure for MERG-03 verification before Phase 1 merges to main. Covers:
- Prerequisites (Plan 08 + Plan 09 merged, at least one v1.0 baseline run)
- Step-by-step comparison: pick baseline, re-run on same idea, apply 3 tolerance rules
- Tolerance 1: weighted-total delta ≤ 0.2
- Tolerance 2: verdict bucket unchanged
- Tolerance 3: top-3 strengths/weaknesses overlap ≥ 2 of 3
- Investigation guide for tolerance failures including Pitfall 6 (research noise)

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] test_no_dangling_refs.py flagged install.js as containing forbidden strings**
- **Found during:** Task 2 test run
- **Issue:** The plan requires `LEGACY_AGENTS = ['ti-merger.md']` and `LEGACY_SKILL_DIRS = ['ti-html-report']` in install.js, but the existing `test_no_dangling_refs.py` (from Plan 08) forbids `ti-merger` and `ti-html-report` strings in any live source file in `bin/`.
- **Fix:** Added `"install.js"` to `EXCLUDED_TEST_FILES` in `test_no_dangling_refs.py` with an explanatory comment that these are intentional legacy references for cleanup.
- **Files modified:** `scripts/tests/test_no_dangling_refs.py`
- **Commit:** `c686510`

**2. [Rule 3 - Blocking] Legacy orphan untracked files in worktree**
- **Found during:** Task 2 test run
- **Issue:** `agents/ti-merger.md` and `skills/ti-html-report/SKILL.md` were untracked in the worktree (left over from main branch state before reset). They caused the dangling refs test to fail.
- **Fix:** Deleted both files from the worktree. These files are exactly what `legacyCleanup()` in install.js is designed to remove from user installs.
- **Files modified:** (deleted untracked files, no commit needed)

**3. [Rule 3 - Blocking] SHADOW-COMPARISON.md cannot be committed to worktree (.planning/ gitignored)**
- **Found during:** Task 3
- **Issue:** `.planning/` is gitignored in the worktree branch. The SHADOW-COMPARISON.md is a planning artifact that belongs in the main repo.
- **Fix:** Committed SHADOW-COMPARISON.md directly to the `eph5xx/json` main repo branch via `git add -f`. The worktree also has a copy for local verification.
- **Commit:** `9cf5574` (on `eph5xx/json` branch, not worktree branch)

## Known Stubs

None.

## Threat Flags

None. No new network endpoints, auth paths, or schema changes at trust boundaries introduced.

## Self-Check: PASSED

- `bin/install.js` exists and contains `verifyUvOrExit`, `LEGACY_AGENTS`, `LEGACY_SKILL_DIRS`, `copyDirSync.*schemas`, `copyDirSync.*scripts` — verified via grep
- `package.json#files` has 6 entries including `schemas` and `scripts` — verified via python3
- `scripts/tests/test_packaging.py` exists — verified
- `scripts/tests/test_install_uv.sh` exists and is executable — verified
- `scripts/tests/test_install_uv_wrapper.py` exists — verified
- All 134 tests pass — verified via `uv run scripts/tests/run_tests.py`
- `SHADOW-COMPARISON.md` exists in `.planning/phases/01-json-schema-scripts-foundation-keystone/` — verified
- Old soft warning `requires 'uv' (Python package runner)` deleted — verified via grep
- Commits `16e9aca` and `c686510` exist in worktree branch — verified via `git log`
