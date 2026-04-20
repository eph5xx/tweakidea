---
name: tweak:share
description: Upload a run's report.html to a secret GitHub gist and print the gist + rendered preview URLs
argument-hint: <timestamp | latest | keyword | query>
allowed-tools:
  - Bash
  - Read
  - AskUserQuestion
---

## Purpose

Publish a run's `report.html` as a secret GitHub gist and print both the gist URL and a `htmlpreview.github.io` rendered URL for sharing.

$ARGUMENTS

## Argument handling

Resolve `$ARGUMENTS` to a single run under `~/.tweakidea/runs/`. Accept: empty or `latest` → newest run; a timestamp or prefix (`20260419`, `20260419-202954`); a keyword matched against `idea.json` across the 50 newest runs; or a ranked query (`best ideas`, `top 3 GO`, `potential > 4`) — pick the top hit.

Runs only. If the query looks like an HN id (`hn-<id>`, `hn <id>`, or a bare numeric id) or `founder`/`me`, print one line — `/tweak:share is for evaluation runs only — HN and founder artifacts have no report.html.` — and stop.

If a keyword or prefix matches 2–5 runs, use `AskUserQuestion` to pick; if more than 5, render the 5 newest matches and stop without uploading.

## Preflight

Require `gh`: `command -v gh >/dev/null && gh auth status >/dev/null 2>&1`. On failure, print exactly one line — `gh CLI not available or not logged in — install at https://cli.github.com and run \`gh auth login\`, then retry.` — and stop before any network call.

## Upload

Read `idea.json` from the resolved run to build the gist description:

- Present and populated: `TweakIdea: <codename> — <subtitle>` (if `codename`/`subtitle` are empty, use the first ~80 chars of `problem`).
- Missing (legacy runs without `idea.json`): `TweakIdea evaluation (<timestamp>)`.

Then run `gh gist create "<run>/report.html" --desc "<description>"`. Secret by default; no `--public` flag. Capture stdout, take the last non-empty line, and trim surrounding whitespace — that's the gist URL, of the form `https://gist.github.com/<user>/<id>`.

## Output

On the success path, print exactly this — two sections, each a bold label on its own line followed by the URL on the next line in markdown autolink syntax (angle brackets), with one blank line between the sections. No surrounding prose, no commentary.

    **Code**
    <https://gist.github.com/<user>/<id>>

    **Preview**
    <https://htmlpreview.github.io/?https://gist.githubusercontent.com/<user>/<id>/raw/report.html>

Derive `<user>/<id>` by stripping the `https://gist.github.com/` prefix from the trimmed upload URL.

Never write under `~/.tweakidea/`. Never spawn agents. Each invocation creates a new gist — do not attempt to update or reuse prior ones.
