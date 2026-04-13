---
phase: 01-json-schema-scripts-foundation-keystone
plan: 07
subsystem: agents
tags: [ti-narrative, prose-agent, json-output, opus, tdd]
dependency_graph:
  requires: [01-01, 01-02, 01-05]
  provides: [agents/ti-narrative.md]
  affects: [agents/ti-merger.md (coexists until Plan 08 cutover)]
tech_stack:
  added: []
  patterns: [single-spawn prose agent, sequential Write tool calls, maxTurns budget for multi-file writes]
key_files:
  created:
    - agents/ti-narrative.md
    - scripts/tests/test_narrative_agent.py
  modified: []
decisions:
  - "maxTurns set to 15 per plan spec (read phase + 5 sequential writes + reasoning headroom; RESEARCH.md Q6c started at 5 as conservative [ASSUMED] — plan pre-bumped to 15 to avoid mid-run truncation)"
  - "ti-merger.md NOT deleted — Plan 08 cutover responsibility; both agents coexist in Wave 3"
  - "prohibition clause 'Do NOT compute' explicitly in body — enforces script/LLM boundary (T-01-07-02)"
metrics:
  duration: "~5 min"
  completed: "2026-04-13"
  tasks_completed: 2
  files_created: 2
---

# Phase 01 Plan 07: ti-narrative Agent Summary

**One-liner:** New prose-only opus agent writes 5 narrative JSON files per spawn from pre-computed numbers.json, replacing ti-merger's LLM-computed scorecard role with a focused synthesis-only mandate.

## What Was Built

`agents/ti-narrative.md` is the LLM half of the script/LLM boundary established in Phase 1. It:

- Reads `{RUN_DIR}/numbers.json` (pre-computed by `compute.py`) for all numeric values
- Reads 14 `{RUN_DIR}/dimensions/*.json` files for evaluator prose (analysis_narrative, key_finding, key_signals, assumptions_relied_on)
- Reads `{RUN_DIR}/assumptions.json` and optionally `{RUN_DIR}/research.json`
- Writes exactly 5 narrative JSON files in sequence via Write tool calls
- Returns `## NARRATIVE COMPLETE` and nothing else

The agent explicitly prohibits any numeric computation — weights, rankings, verdict buckets, and uplift math are all pre-computed by `compute.py` and only cited here.

**Frontmatter diff vs ti-merger.md:**

| Field | ti-merger | ti-narrative |
|-------|-----------|--------------|
| model | opus | opus |
| maxTurns | 3 | 15 |
| tools | Read, Write | Read, Write |
| skills | ti-scoring | ti-scoring |
| permissionMode | dontAsk | dontAsk |

**LOC comparison:** ti-narrative.md = 126 lines; ti-merger.md = 179 lines (53 lines shorter — merger had inline scorecard computation instructions that are now in compute.py).

**Body sections:**
1. Input description (numbers.json, dimensions/, assumptions.json, research.json)
2. `<files_to_read>` block (5 schema files)
3. Five Sequential File Writes (verdict → strengths-weaknesses → next-steps → dealbreakers → potential)
4. Per-file schema + content instructions (Files 1-5)
5. Partial Failure Handling
6. Critical Rules (7 rules, prohibition clause #1 and #5)

## Test Results

`uv run scripts/tests/run_tests.py -v` — 98 tests, all pass.

`test_narrative_agent.py` adds 16 tests across 2 classes:
- `TestNarrativeAgentFrontmatter` (7 tests): file_exists, name, model, permissionMode, maxTurns, tools, skills
- `TestNarrativeAgentBody` (9 tests): 5 schema refs, 5 output paths, numbers.json input, dimensions/ input, prohibition clause, completion marker, no evaluator markers, files_to_read block, partial failure section

Requirements verified:
- NARR-01: ti-narrative.md exists, Write tool, model opus, single spawn — PASS
- NARR-02: reads numbers.json + dimensions/, no computation — PASS
- NARR-03: writes 5 JSON files in one invocation — PASS

## Deviations from Plan

None — plan executed exactly as written.

## Known Stubs

None. Agent definition is complete. Actual prose quality verified at runtime when spawned by Plan 08 orchestrator.

## Threat Flags

No new security-relevant surface introduced. Agent writes to `{RUN_DIR}/` (user's home directory run folder, trusted path). Schema validation at read time handled by render_report.py (Plan 06) per T-01-07-01.

## Self-Check: PASSED

- `agents/ti-narrative.md` — FOUND
- `scripts/tests/test_narrative_agent.py` — FOUND
- Commit `30da7db` (RED tests) — FOUND
- Commit `340fb82` (GREEN agent + test) — FOUND
- `agents/ti-merger.md` still exists — FOUND
- 98/98 tests pass — VERIFIED
