# Phase 1 Shadow Comparison — MERG-03 Procedure

**Purpose:** Verify that the Phase 1 cutover (ti-merger → ti-narrative + scripts/compute.py + scripts/render_report.py) does not regress scoring behavior versus v1.0. This is a manual eyeball comparison because:

1. `/tweak:evaluate` runs cost ~$50 and ~40 minutes each — a locked-fixture harness was explicitly deferred after founder scope review.
2. Top-3 strengths/weaknesses overlap requires human synonym handling (e.g., "pricing uncertainty" ≈ "willingness to pay concern").

Per D-39, the baseline is the founder's existing v1.0 runs already on disk in `~/.tweakidea/runs/`. No pre-capture step is required.

## Prerequisites

1. **At least one existing v1.0 run** in `~/.tweakidea/runs/*/scorecard.md`. If none exist, this is an OPEN question per RESEARCH.md A7 — the founder must either run `/tweak:evaluate` once on v1.0 BEFORE Phase 1 merges (to capture a baseline) or accept that shadow comparison cannot run and the merge ships with higher risk.

2. **Plan 08 merged** (big-bang cutover complete — ti-merger.md deleted, ti-narrative.md live).

3. **Plan 09 merged** (installer updated — `npx tweakidea` works with the new schemas/scripts).

4. **Fresh `npx tweakidea` run** to refresh `.claude/` with the Phase 1 files.

## Procedure

### Step 1: Pick a baseline run

Choose one or more existing runs from `~/.tweakidea/runs/` where `scorecard.md` exists. Note the idea text from that run (open `idea.md` in the same directory). Example:

```
~/.tweakidea/runs/20260215-142300/
  idea.md
  scorecard.md      ← baseline file
  dimensions/*.md
  report.html
```

### Step 2: Run Phase 1 evaluation on the SAME idea

Invoke `/tweak:evaluate` with the exact text from `idea.md`. Note the new timestamp:

```
~/.tweakidea/runs/20260413-093500/
  version.json      ← new: Phase 1 run marker
  idea.json         ← JSON, not .md
  hypotheses.json
  assumptions.json
  research.json
  dimensions/*.json ← JSON, not .md
  numbers.json      ← script-computed
  verdict.json
  strengths-weaknesses.json
  next-steps.json
  dealbreakers.json
  potential.json
  report.md         ← single markdown artifact
  report.html
```

### Step 3: Compare against tolerance rules

Open both files side by side:

```bash
open ~/.tweakidea/runs/20260215-142300/scorecard.md  # baseline
open ~/.tweakidea/runs/20260413-093500/report.md     # new
```

Apply these three tolerance rules:

#### Tolerance 1: Weighted-Total Delta ≤ 0.2

- Baseline: first line contains `Weighted Score: X.X/5.0` (extract X.X)
- New: `jq '.weighted_total' ~/.tweakidea/runs/20260413-*/numbers.json`
- **PASS** if `|new - baseline| ≤ 0.2`
- **FAIL** if `|new - baseline| > 0.2`

#### Tolerance 2: Verdict Bucket Unchanged

- Baseline: first line prefix is `GO`, `PIVOT`, or `STOP`
- New: `jq -r '.verdict_bucket' ~/.tweakidea/runs/20260413-*/numbers.json`
- **PASS** if both prefixes are identical
- **FAIL** if they differ (e.g., baseline is `PIVOT`, new is `STOP`)

#### Tolerance 3: Top-3 Strengths/Weaknesses Overlap ≥ 2 of 3

- Baseline: read the `### Top 3 Strengths` and `### Top 3 Weaknesses` sections in `scorecard.md`
- New: `jq -r '.[] | select(.kind=="strength") | .dim' ~/.tweakidea/runs/20260413-*/strengths-weaknesses.json` (repeat for `"weakness"`)
- **PASS** if at least 2 of 3 strengths appear in both lists AND at least 2 of 3 weaknesses appear in both lists
- **FAIL** if fewer than 2 overlap in either list

Note: Human synonym handling is acceptable. "Willingness to Pay" in the baseline matching "Willingness to Pay" in the new is exact. "Pricing Uncertainty" in the baseline matching "Willingness to Pay" in the new is ALSO acceptable if the founder recognizes the semantic equivalence.

### Step 4: Record outcome

- **ALL THREE TOLERANCES PASS** → merge is safe. Update `.planning/phases/01-json-schema-scripts-foundation-keystone/01-09-SUMMARY.md` with a `Shadow comparison: PASS` note.

- **ANY TOLERANCE FAILS** → investigate before merging. Options:

  1. **Research noise** (Pitfall 6 in RESEARCH.md): web search results may have changed between baseline date and new run, producing different evidence tiers. If the per-dimension delta is spread evenly across dimensions, this is the likely cause.
  2. **compute.py bug**: check the score math in `numbers.json.rankings` against a hand-computed weighted total from the 14 dimension files.
  3. **ti-narrative misinterprets rankings**: compare `strengths-weaknesses.json` entries against `numbers.json.rankings` sorted by score — if the narrative agent picked the wrong top/bottom 3, that's a bug in the agent prompt (fix in Plan 07 or an out-of-phase follow-up).
  4. **Prompt drift**: if the evaluator prompts changed meaning subtly (e.g., new prose fields altered scoring behavior), roll back agent frontmatter changes in Plan 04 and re-run.

  Record the investigation outcome. Do NOT merge until all three tolerances pass OR the founder explicitly accepts the drift (with written justification).

## Handling Multiple Baselines

If more than one v1.0 run is available on disk, repeat Steps 2-4 for each one. A Phase 1 cutover should pass shadow comparison on ALL of them.

If only 1 baseline exists, 1 comparison is sufficient. This is explicitly what D-39 specifies: "one or more existing v1.0 run(s) from ~/.tweakidea/runs/ as baseline(s)".

## Why Manual

Per D-39 and Phase 0 deferral: a dedicated locked-fixture regression harness was scoped and explicitly removed due to `/tweak:evaluate` runtime cost (~$50 × 5 fixtures × N phases = untenable). The manual procedure above is the agreed-upon substitute for Phase 1, Phase 3, and Phase 4 (each of which touches scoring behavior).

---

*Document created: 2026-04-13 as part of Phase 1 Plan 09.*
*This procedure is Phase 1-specific. Phase 3 and Phase 4 will reference similar but lightly adapted procedures.*
