---
name: tweak:browse-hn
description: Browse HN posts via Algolia search to find candidates for /tweak:analyze-hn-post
argument-hint: "[topic] [today|week|month|all]"
allowed-tools:
  - Bash
  - Read
  - AskUserQuestion
skills:
  - ti-hnparse
---

## Purpose

Discover HN posts worth feeding into `/tweak:analyze-hn-post`. Takes an optional topic + time window from `$ARGUMENTS` (or one follow-up question), searches HN via `hnsearch.py`, scores each result as an idea seed, and prints a ranked table inline. Read-only.

$ARGUMENTS

## Phase 1 — Parse `$ARGUMENTS`

`$ARGUMENTS` carries an optional topic and an optional time window, in any order.

**Time keywords** (case-insensitive, stripped from the string before setting QUERY):

- `today` / `24h` / `1 day` / `1d` → DAYS = `1`
- `week` / `7 days` / `7d` → DAYS = `7`
- `month` / `30 days` / `30d` → DAYS = `30`
- `all` / `all time` / `ever` → DAYS = `0`

If no time keyword is present, leave DAYS unset — Phase 2 will ask.

**QUERY** is whatever remains after stripping the time phrase (trimmed). An empty QUERY is a valid "browse everything" search and must proceed silently.

**Unintelligible-query guard.** Only if the residual QUERY is obvious nonsense (random characters, contradictory, clearly off-HN like "make me a coffee"), ask once via AskUserQuestion: `"I couldn't parse '{ARGUMENTS}' as an HN topic. What should I search for? (leave blank to browse all recent stories)"` (header `HN query`, single option `Enter topic`). A blank answer means QUERY = "". When in doubt, pass the query through.

## Phase 2 — Time range (only if DAYS unset)

Skip this phase if Phase 1 set DAYS. Otherwise ask once via AskUserQuestion:

- question: `"Over what time window should I browse HN{for_query_phrase}?"` where `for_query_phrase` is ` for "{QUERY}"` when QUERY is non-empty, otherwise blank.
- header: `Time window`
- options: `Last 24 hours (Recommended)` → 1, `Last 7 days` → 7, `Last 30 days` → 30, `All time` → 0.

## Phase 3 — Locate script and run

Verify `uv` is on PATH (`which uv`). If missing, tell the user to install it (`brew install uv` or `curl -LsSf https://astral.sh/uv/install.sh | sh`) and stop.

Find `hnsearch.py` at `.claude/skills/ti-hnparse/hnsearch.py` then `$HOME/.claude/skills/ti-hnparse/hnsearch.py`. If neither exists, tell the user to run `npx tweakidea` and stop.

Run:

```bash
uv run "{SCRIPT_PATH}" --query "{QUERY}" --days {DAYS} --limit 20
```

Stdout is a JSON array with fields `id`, `title`, `url`, `points`, `num_comments`, `author`, `created_at_i`, `relative_age`, `hn_url`. On non-zero exit, surface stderr and stop.

## Phase 4 — Score, sort, render

### Zero results

If the array is empty, tell the user nothing matched{query_phrase} in the selected window and suggest broadening the query or widening the window. Stop.

### Score

For each hit, assign SCORE 1–5 answering: **"how likely is this thread to yield a real startup-idea seed when `/tweak:analyze-hn-post` reads its article and comments?"** Use only the JSON fields — this is a triage signal, not a verdict. Apply these steps in order; later steps cannot override earlier ones.

**1. Topic gate (hard filter).** Is this thread about technology, tools, products, workflows, or practices a founder can build on? If no — politics, legal drama, consumer outrage, celebrity news, obituaries, memes, sports, culture-war, corporate gossip, non-tech finance — the score is **1**, regardless of points or comments. If QUERY is non-empty, also collapse clearly off-query hits to 1.

**2. Shift signal.** Does the title or URL name something that *changed* — a new capability, a cost/access threshold crossed, closed → open, a technique or measurement that did not exist a year ago? Positive examples: `Show HN: [novel capability]`, "now runs on-device", "we replaced N with M at $Y", open-sourcings, benchmark releases with concrete numbers.

**3. Practitioner density.** Are the commenters likely builders, not opinionators?
- Signal: Show HN / Ask HN; github / gitlab / arxiv / personal-blog URLs; specific tools, frameworks, or benchmarks named in the title; "how we built X".
- Anti-signal: major news-site URLs, corporate PR, vague editorial headlines.

**4. Assign.**
- **5** — passes gate AND clear shift signal AND high practitioner density.
- **4** — passes gate AND one of (shift signal OR practitioner density).
- **3** — passes gate, on-topic for builders, but neither signal is clear.
- **2** — passes gate but reads as news / opinion / shallow coverage.
- **1** — fails gate, or clearly off-query.

**5. `num_comments` is a tiebreaker only.** It does not decide the bucket. A 5 with 30 comments beats a 4 with 500; a political thread with 500 comments is still a 1. Aim for visible spread across the table — if every row lands on 3, tighten the gate.

### Sort

`score` desc → `num_comments` desc → `points` desc.

### Render

Header: `Found {N} HN candidates{query_phrase} over {window label}. Sorted by usefulness.` — `query_phrase` is ` for "{QUERY}"` when non-empty, else blank; `window label` is `last 24 hours` / `last 7 days` / `last 30 days` / `all time`.

Table (post-sort order):

| # | ID | Title | Score | Pts | Cmts | Age |
|---|----|-------|-------|-----|------|-----|

- `ID` — markdown link `[{id}]({hn_url})`.
- `Title` — trim to ~70 chars with trailing `…`; escape `|` as `\|`.
- `Score` — `{n}/5`; wrap the cell in `**…**` when `n ≥ 4`.

After the table:

> Run `/tweak:analyze-hn-post <id>` on any candidate to analyze tech shifts and product opportunities.

Never write under `~/.tweakidea/`. Never spawn agents. Never call `/tweak:analyze-hn-post` on the user's behalf.
