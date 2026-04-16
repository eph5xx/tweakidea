---
name: tweak:diff
description: Compare two evaluation runs — score changes, potential shifts, and what moved
argument-hint: <run1> <run2> (timestamps, prefixes, or `latest`)
allowed-tools:
  - Bash
  - Read
  - AskUserQuestion
---

## Purpose

Compare two `/tweak:evaluate` runs side-by-side. Show what got better, what got worse, and why — in chat, as markdown. Read-only.

$ARGUMENTS

## Data layout

Everything lives under `$HOME/.tweakidea/runs/<YYYYMMDD-HHMMSS>/`. Files needed per run:

- `idea.json` — `problem`, `solution`, `codename`, `icon`, `subtitle`
- `numbers.json` — `weighted_total`, `potential_total`, `verdict_bucket`, `verdict_label`, `overall_grade` (may be absent in older runs), `rankings[]` with per-dimension `dim`, `slug`, `weight`, `score`, `potential`, `weighted_score`, `evidence_strength.grade`
- `dimensions/<slug>.json` — `key_finding` (read only for movers, not all 14)

## Argument handling

Parse `$ARGUMENTS` for two run identifiers. Accept any of:

- **Two timestamps or prefixes** → resolve both
- **One timestamp + `latest`** → resolve the timestamp + the most recent run
- **Just `latest`** → the two most recent runs (latest = Run B, second-latest = Run A)
- **Empty** → use `AskUserQuestion` to ask which runs to compare

If a prefix matches multiple runs, use `AskUserQuestion` to disambiguate. Resolve run directories via `ls $HOME/.tweakidea/runs/` and prefix-match.

**Convention:** the earlier run is always **Run A**, the later is **Run B** — swap if the user passed them in reverse chronological order.

## Comparison logic

Follow these steps IN ORDER.

### Step 1: Load data

Read `idea.json` and `numbers.json` from both runs **in parallel** (4 reads). If `numbers.json` is missing for either run, stop and print: `Run {timestamp} has no scores. Was the evaluation completed?`

If both arguments resolve to the same run directory, stop and print: `Both arguments resolve to the same run ({timestamp}).`

### Step 2: Compute deltas

For each of the 14 dimensions, match by `slug` across both `numbers.json → rankings[]`:

- `Δ_score = B.score − A.score`
- `Δ_potential = B.potential − A.potential`
- `Δ_weighted = (B.score − A.score) × weight`

Classify each dimension:
- **Mover** if `Δ_score ≠ 0` OR `Δ_potential ≠ 0`
- **Unchanged** otherwise

Sort movers by `|Δ_weighted|` descending. Break ties by `|Δ_potential × weight|` descending.

### Step 3: Load mover details

For movers only: read `dimensions/<slug>.json` from **both** runs in parallel. Extract `key_finding` from each. If a dimension file is missing, note "(detail unavailable)" for that dimension's "why" entry.

### Step 4: Render output

Print the markdown below. Do not wrap it in a code fence — output it as rendered markdown.

## Output format

### Title + Intro

```
## [Icon] Codename — Run diff
```

Use Run B's `icon` and `codename` if present, else Run A's, else omit them and just print `## Run diff`.

Then two intro lines — one sentence per idea. Use `subtitle` from `idea.json` if present, otherwise use the first sentence of `problem`:

```
**Run A** (Mon DD): [one-sentence summary of Run A's idea]
**Run B** (Mon DD): [one-sentence summary of Run B's idea]
```

Then a *Difference* line. Compare the two `problem` + `solution` texts:
- If both are identical: `*Same idea text — differences come from updated evidence or profile.*`
- If the same core idea but rewritten: synthesize a one-liner about what changed, e.g. `*Run B sharpens the target customer and repositions as sidecar middleware.*`
- If entirely different ideas: `*Different ideas — this is a cross-idea comparison.*`

### Summary table

```
### Summary

|  | Run A | Run B | Δ |
|---|---|---|---|
| Weighted | {A.weighted_total} | **{B.weighted_total}** | {signed delta} {▲ or ▼} |
| Potential | {A.potential_total} | **{B.potential_total}** | {signed delta} {▲ or ▼} |
| Verdict | {A.verdict_bucket} | **{B.verdict_bucket}** | {▲ or ▼ or blank} |
| Evidence | {A.overall_grade} | **{B.overall_grade}** | {▲ or ▼ or blank} |
```

Omit the Evidence row if either run lacks `overall_grade`. Bold the Run B value when it is better than Run A; bold the Run A value when it is better. If equal, bold neither.

Direction symbols: `▲` = improved (higher score, or verdict upgrade), `▼` = declined, blank = no change.

### Movers table

```
### Movers ({count} of 14)

| Dimension | W | Score | Potential | Δ Weight |
|---|---:|---|---|---|
| {dim} | {weight as %}  | {A.score} → **{B.score}** ▲ | {A.pot} → **{B.pot}** ▲ | +{Δ_weighted} |
```

For each column:
- **Score**: if changed, show `{old} → **{new}** {▲ or ▼}`. If unchanged, show just the number.
- **Potential**: same pattern.
- **Δ Weight**: show signed value to 2 decimal places. Use `+0.36`, `-0.12`, or `0.00` for potential-only movers.

If zero movers: skip this section entirely and print `*All 14 dimensions scored identically across both runs.*`

### Why they moved

```
**Why they moved**

- **{Dimension}** — {one sentence comparing Run A's key_finding vs Run B's key_finding — what specifically changed}
```

One bullet per mover. Keep each to one sentence. If the dimension file was missing for either run, write `(detail unavailable)`.

### Unchanged table

```
### Unchanged ({count} of 14)

| Dimension | W | Score | Potential |
|---|---:|---:|---:|
| {dim} | {weight as %} | {score} | {potential} |
```

### Problem + Solution

```
### Problem

**Run A:** {A.problem}

**Run B:** {B.problem}

### Solution

**Run A:** {A.solution}

**Run B:** {B.solution}
```

## Edge cases

- **Missing `numbers.json`** → stop early with a clear message.
- **Same run twice** → stop early with a clear message.
- **Zero movers** → skip Movers section and "Why they moved"; print note.
- **All 14 moved** → skip Unchanged section.
- **Missing dimension files** → still show the mover row (scores come from `numbers.json`); note "(detail unavailable)" in the why-they-moved bullet.
- **Missing `overall_grade`** → omit Evidence row from summary table.
- **Missing `codename`/`icon`/`subtitle`** → degrade gracefully (no icon, no codename, use first sentence of problem).

Never write under `~/.tweakidea/`. Never spawn agents.
