---
name: tweak:show
description: Find and open any artifact in ~/.tweakidea/ — by timestamp, keyword, HN id, founder, or natural query
argument-hint: <timestamp | latest | hn-id | founder | keyword | query>
allowed-tools:
  - Bash
  - Read
  - AskUserQuestion
---

## Purpose

Resolve a free-form query into one (or a few) artifacts under `~/.tweakidea/` and open them. Read-only.

$ARGUMENTS

## Data layout

Everything lives under `$HOME/.tweakidea/`: `runs/<timestamp>/` (with `idea.json`, `numbers.json`, `strengths-weaknesses.json`, `report.html`, and older `scorecard.md`), `hn/hn-<id>/` (with some of `content.md`, `shifts.md`, `ideas.md`), and either `FOUNDER.md` or `founders/*.md`. Read the smallest thing that answers the query — you do not need to crawl every dimension or every run. `numbers.json` carries the quantitative fields (`weighted_total`, `potential_total`, `verdict_bucket`, `verdict_label`, `rankings[]`); `idea.json` carries the idea text for keyword matching.

## Query handling

The query may be `latest`, a run timestamp or prefix, an HN id (`hn-<id>`, `hn <id>`, or a bare numeric id), `founder`/`me`, a keyword to match against `idea.json`, or a quantitative query like `best ideas`, `top 3 GO`, `potential > 4`, `pain intensity 5`, `with dealbreakers` (dimensions where `rankings[].score == 1`). Interpret it against whatever file actually answers it (usually `numbers.json` for quantitative, `idea.json` for keyword). Cap keyword/ranking scans at the 50 newest runs, and read per-run files (`idea.json`, `numbers.json`, …) in parallel rather than serially.

If `$ARGUMENTS` is empty, ask with `AskUserQuestion` what to open. If the query is ambiguous between 2–5 targets, use `AskUserQuestion` to pick. If it resolves to more than 5, render the 5 best matches (newest-first for keywords, metric-sorted for ranked queries) and stop — do not blind-pick.

## Output

**Exactly one target resolved.** Render a compact summary, then open the artifact:

- **Run** — print problem, solution, verdict label + weighted/potential, top 3 strengths, and bottom 3 weaknesses (sourced from `idea.json`, `numbers.json`, `strengths-weaknesses.json` — skip any missing section). Then `open "{run}/report.html" 2>/dev/null || xdg-open "{run}/report.html" 2>/dev/null`. Older runs without `numbers.json`: print the head of `scorecard.md` and note `_Pre-JSON run._`.
- **HN** — print title (first line of `content.md`) and path, then inline `ideas.md` in full (or `shifts.md` if no ideas file, or note that only `content.md` exists).
- **Founder** — print the resolved profile file inline in full.

**Ranked-list query** (`best ideas`, `top 3 GO`, `potential > 4`, etc.): render the top 5 matches as a compact table with a metric column inline (timestamp, idea trimmed to ~80 chars, metric), then auto-open the top result's `report.html` using the same `open`/`xdg-open` pattern as above. Append `_Interpreted as: …_` if the query was ambiguous.

Never write under `~/.tweakidea/`. Never spawn agents. No second-arg escape hatch.
