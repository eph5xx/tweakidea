---
name: tweak:improve
description: Generate three idea tweaks — small, medium, and big — to address evaluation weaknesses
argument-hint: <run timestamp, prefix, or `latest`>
allowed-tools:
  - Bash
  - Read
  - Glob
  - AskUserQuestion
skills:
  - ti-scoring
---

## Purpose

Read a completed `/tweak:evaluate` run and generate three concrete idea rewrites at escalating scales of change — small reframe, medium reshape, big reimagine. Each tweak is a rewritten problem + solution statement the founder can paste directly into `/tweak:evaluate`.

Read-only. Never write files under `~/.tweakidea/`. Never spawn agents.

$ARGUMENTS

## Data layout

Everything lives under `$HOME/.tweakidea/runs/<YYYYMMDD-HHMMSS>/`. Files needed:

- `idea.json` — `problem`, `solution`, `codename`, `icon`, `subtitle`
- `numbers.json` — `weighted_total`, `potential_total`, `verdict_bucket`, `verdict_label`, `overall_grade`, `rankings[]` (per-dimension `dim`, `slug`, `weight`, `score`, `potential`, `evidence_strength.grade`), `assumption_impact_math[]`
- `strengths-weaknesses.json` — 6 entries: `[{kind, dim, score, why}]`
- `potential.json` — `{dimensions[], assumptions[], narrative}`
- `next-steps.json` — `[{task, dim, from, to, weighted_uplift, rationale}]`
- `dimensions/<slug>.json` — `analysis_narrative`, `key_finding`, `score_explanation`, `assumptions_relied_on[]`

## Argument handling

Parse `$ARGUMENTS` for a run identifier. Accept any of:

- **Timestamp or prefix** → resolve via `ls $HOME/.tweakidea/runs/` and prefix-match
- **`latest`** → the most recent run
- **Empty** → use `AskUserQuestion` to ask which run

If a prefix matches multiple runs, use `AskUserQuestion` to disambiguate.

## Steps

Follow these steps IN ORDER.

### Step 1: Resolve run directory

Resolve the argument to a single run directory under `$HOME/.tweakidea/runs/`. Use `ls $HOME/.tweakidea/runs/` and prefix-match.

### Step 2: Load run data

Read these files **in parallel**:

1. `{RUN}/idea.json`
2. `{RUN}/numbers.json`
3. `{RUN}/strengths-weaknesses.json`
4. `{RUN}/potential.json`
5. `{RUN}/next-steps.json`

If `numbers.json` is missing, stop: `Run {timestamp} has no scores. Was the evaluation completed?`

The other files are optional — degrade gracefully if missing.

### Step 3: Compute priority ranking

For each dimension in `numbers.json → rankings[]`:

- `weighted_gap = weight × (5 − score)`
- `is_dealbreaker = score == 1`

Sort by: dealbreakers first, then `weighted_gap` descending, then `evidence_strength.grade` ascending (F before D before C).

Identify the **bottom 5 dimensions by score** (break ties by weight descending). These are the attack targets.

### Step 4: Load rubrics and dimension details

For the bottom 5 dimensions, read **in parallel** (up to 10 reads):

- **Rubric file:** `.claude/skills/ti-scoring/dimensions/{slug}.md` — contains the scoring rubric (what earns each score level 1–5) and signal table
- **Evaluation file:** `{RUN}/dimensions/{slug}.json` — contains `analysis_narrative`, `key_finding`, `score_explanation`, `assumptions_relied_on`

If a file is missing, proceed without it — note "(detail unavailable)" where needed.

### Step 5: Generate three tweaks and render output

Using the priority ranking, rubric criteria, and dimension analyses, generate three independent idea rewrites. Each tweak targets different dimensions at a different scale of change.

**Critical constraints for tweak generation:**

1. **Grounded in rubrics.** Each rationale must cite a specific rubric criterion — e.g., "Defensibility Score 4 requires a durable barrier that strengthens over time — the data flywheel from API integrations provides this."
2. **Three are independent branches**, not nested. Small is NOT a subset of Medium. Medium is NOT a subset of Big. A founder picks one path, not all three in sequence.
3. **Never duplicate next-steps.** Next-steps are validation tasks ("interview 10 customers"). Tweaks are idea changes ("reposition as a compliance tool"). Check `next-steps.json` and avoid generating validation tasks dressed up as tweaks.
4. **Trade-offs are mandatory.** Every tweak must acknowledge what it might weaken. Narrowing the target helps Clarity but may hurt Market Size. Introducing compliance features helps Mandatory Nature but may increase Behavior Change.
5. **Pasteable output.** The Problem/Solution text must be complete, self-contained, and written in the same style as the original `idea.json` — ready to paste into `/tweak:evaluate`.

## Tweak scales

### Small — "Reframe"

- **Constraint:** Same core product, same target market segment.
- **Allowed changes:** Positioning, pricing model, target customer specificity, urgency framing, go-to-market narrative.
- **Targets:** 1–2 dimensions movable through framing alone. Typical candidates: Clarity of Target Customer, Urgency, Willingness to Pay, Pain Intensity, Mandatory Nature.
- **Example:** Narrowing "small SaaS teams" to "seed-stage SaaS teams doing their first SOC 2 audit" could lift Urgency and Mandatory Nature by introducing a compliance forcing function.

### Medium — "Reshape"

- **Constraint:** Same core problem space.
- **Allowed changes:** Solution approach, delivery model, scope expansion/contraction, distribution channel, revenue model, market segment shift.
- **Targets:** 3–5 dimensions, including at least one high-weight dimension (≥8%).
- **Example:** Pivoting from "dashboard" to "embedded API that payment processors white-label" could lift Defensibility (switching costs), Market Size (platform economics), and Behavior Change (zero-change for end users).

### Big — "Reimagine"

- **Constraint:** Thematic connection to the founder's domain/interest only. Can change the problem, the market, and the solution.
- **Targets:** The entire weakness profile. Must address all dealbreakers if any exist.
- **Example:** Moving from "SaaS invoice reconciliation" to "AI-powered financial close automation for mid-market companies with SOX compliance requirements" changes the problem, the market, and introduces Mandatory Nature (SOX) and Urgency (audit deadlines).

## Output format

Print the markdown below. Do NOT wrap it in a code fence — output it as rendered markdown.

### Title + original idea

```
## {Icon} {Codename} — Improvement Tweaks
```

Use `icon` and `codename` from `idea.json` if present, else omit and just print `## Improvement Tweaks`.

Then the original idea summary:

```
**Original idea** ({date}, weighted {weighted_total}/5.0, {verdict_bucket}):
**Problem:** {problem}
**Solution:** {solution}

**Weakest dimensions:** {bottom 5 with scores, e.g. "Urgency (2), Defensibility (2), Mandatory Nature (2), WTP (3), Founder-Market Fit (3)"}
```

If any dimension in `rankings[]` has `score == 1`, add: `**Dealbreakers:** {list of those dimension names}`

Then a horizontal rule `---`.

### Each tweak

For each of the three tweaks, render:

```
### Tweak 1: Small — {2-4 word label}

**What changes:** {1 sentence describing the reframe}

**Problem:** {rewritten problem statement}

**Solution:** {rewritten solution statement}

**Why this helps:**

| Dimension | Now | Direction | Rationale |
|---|---:|---|---|
| {dim} | {score} | likely up | {1-sentence citing rubric criteria} |
| {dim} | {score} | risk: down | {1-sentence explaining the trade-off} |

**Trade-offs:** {1 sentence summarizing what this might weaken}
```

Direction values:
- `likely up` — the tweak directly addresses what the rubric requires for a higher score
- `steady` — no expected change
- `risk: down` — the tweak may weaken this dimension

Only include dimensions where the direction is NOT steady. Focus the table on what moves.

Separate tweaks with `---`.

### Footer

```
### What's next

Pick any tweak (or combine elements) and run:

> `/tweak:evaluate {paste the rewritten problem + solution}`

Then compare with `/tweak:diff latest` to see what moved.
```

## Edge cases

- **All 14 dimensions scored 4+** — tweaks become refinements, not rescues. Acknowledge the idea is strong. Focus on the gap from 4 to 5 (which typically requires deeper evidence or structural moats, not just reframing).
- **Dealbreakers exist** (any dimension scores 1) — the Big Tweak must address all dealbreakers. The Small Tweak should acknowledge it cannot address structural dealbreakers. The Medium Tweak should address at least one.
- **Missing dimension evaluation files** — use `numbers.json` rankings data only. Note "(detail unavailable)" in rationale where needed.
- **Missing optional files** (`strengths-weaknesses.json`, `potential.json`, `next-steps.json`) — degrade gracefully. Priority ranking is computed entirely from `numbers.json`.
- **Score of 1 on a high-weight dimension** — signal that the idea may need a Big Tweak to be viable. The Small Tweak should explicitly note it cannot rescue a fundamental weakness at this scale.
- **Missing `codename`/`icon`/`subtitle`** — degrade gracefully (no icon, no codename, use problem text).
