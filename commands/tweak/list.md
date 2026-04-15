---
name: tweak:list
description: List runs, HN analyses, and founder profiles stored under ~/.tweakidea/
argument-hint: (optional category, limit, or filter — e.g. `runs 20`, `best ideas`)
allowed-tools:
  - Bash
  - Read
---

## Purpose

List what the founder has accumulated under `~/.tweakidea/`: evaluation runs from `/tweak:evaluate`, HN analyses from `/tweak:suggest-from-hn`, and founder profiles. Read-only.

$ARGUMENTS

## Data layout

Everything lives under `$HOME/.tweakidea/`: `runs/YYYYMMDD-HHMMSS/` (each with `idea.json`, `numbers.json`, `report.html`, and other artifacts), `hn/hn-<id>/` (with some of `content.md`, `shifts.md`, `ideas.md`), and either `FOUNDER.md` or `founders/*.md`. When you need a row's title or idea text, read `runs/*/idea.json`. When the caller's args imply ranking or filtering, read `runs/*/numbers.json` (has `weighted_total`, `potential_total`, `verdict_bucket`/`verdict_label`, and per-dimension `rankings[]`). Cap any fanout scan at the 50 newest runs, and read per-run files in parallel rather than serially. Do not read `report.html`, `report.md`, dimension files, or scorecards from this command — that is `/tweak:show`'s job.

## Argument handling

Arguments are a free-form hint, not a strict grammar. Extract what you can and ignore nothing:

- Category words (`runs`/`run`/`evaluations`, `hn`/`hacker-news`, `founder`/`founders`/`profile`/`me`, `all`) set CATEGORY.
- A bare integer sets LIMIT.
- Anything else (`best`, `top`, `GO`, `pain intensity 5`, `potential > 4`, etc.) is a filter or sort hint — apply it against `numbers.json` on the runs section.

Defaults: CATEGORY = `all`, LIMIT = `5`. Never reject an argument. If you had to guess at intent, add a single `_Interpreted as: …_` line at the very bottom of the output.

## Output

Render sections in order Runs → HN → Founders, skipping any that CATEGORY excludes. Within each section, newest-first, and cap at LIMIT rows. If the total exceeds LIMIT, append `_Showing {LIMIT} of {TOTAL}. Pass a number to widen._` below the section.

- **Runs** — table with `#`, timestamp, idea (trimmed to ~80 chars). If the args imply ranking/filtering, add one metric column (score / potential / verdict) sourced from `numbers.json` and sort accordingly instead of by timestamp.
- **HN** — table with `id` and which of `content.md`/`shifts.md`/`ideas.md` exist (`✓`/`–`). No titles — they are not cheap to fetch.
- **Founders** — one row per profile file (`FOUNDER.md` or `founders/*.md`) with file size. Do not dump contents.

Close with one tip line: `_Use /tweak:show <timestamp | latest | hn-id | founder | query> to open any item._`

Never write under `~/.tweakidea/`. Never spawn agents.
