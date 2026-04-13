# Contributing to TweakIdea

Thanks for your interest in contributing! TweakIdea is a set of Claude Code markdown files — there's no compiled code and no build step, but there is a `package.json` for npm distribution and a Node.js installer (`bin/install.js`). "Development" means editing markdown files that contain natural language instructions.

## Project Structure

```
tweakidea/
  bin/
    install.js            # Installer: copies source into .claude/ for Claude Code
  commands/tweak/
    evaluate.md           # Evaluation pipeline (6 stages)
    suggest-from-hn.md    # HN opportunity discovery (7 phases)
  agents/
    ti-extractor.md       # Hypothesis extractor (Sonnet)
    ti-evaluator.md       # Dimension evaluator (spawned 14x with Sonnet)
    ti-narrative.md       # Cross-dimensional narrative author (Opus)
    ti-researcher.md      # Web research agent (Sonnet)
  skills/
    ti-scoring/
      SKILL.md            # Skill metadata (auto-loaded, not user-invocable)
      EVALUATION.md       # Scoring algorithm, weights, evidence tiers
      dimensions/         # 14 dimension definition files
    ti-founder/
      SKILL.md            # Founder profile template and fit question guidance
    ti-report/
      SKILL.md            # Report skill metadata
      template.md.j2      # Markdown report template (Jinja2)
      template.html.j2    # HTML report template (Jinja2)
      styles.css          # Embedded CSS for HTML report
    ti-hnparse/
      SKILL.md            # Skill metadata (not user-invocable)
      hnparse.py          # HN fetcher script (Python, runs via uv)
  package.json            # npm package metadata (name, version, bin entry)
```

Source files live in the root-level directories above. The installer (`bin/install.js`) copies them into `.claude/` where Claude Code discovers them. **Edit the root-level files, not the `.claude/` copies.**

- **Commands** (`commands/tweak/`): Slash command entry points invoked by users. `evaluate.md` is the evaluation orchestrator (6-stage pipeline). `suggest-from-hn.md` is the HN opportunity discovery orchestrator (7-phase pipeline).

- **Agents** (`agents/`): Subagent definitions spawned by the evaluate orchestrator. Each runs in an independent context window. `ti-extractor.md` extracts testable hypotheses from idea text. `ti-evaluator.md` is spawned 14 times (once per dimension) on Sonnet. `ti-narrative.md` authors the cross-dimensional narrative prose on Opus. `ti-researcher.md` gathers web research on Sonnet.

- **Skills** (`skills/`): Reference knowledge auto-loaded into agent context. `ti-scoring/` contains the evaluation framework (14 dimensions + weights), scoring rubrics, and individual dimension definitions. `ti-founder/` contains the founder profile template and fit question guidance. `ti-report/` contains Jinja2 report templates (markdown + HTML) and embedded CSS. `ti-hnparse/` contains the Python script that fetches HN posts via the Algolia API.

## Evaluation Pipeline

The `/tweak:evaluate` command runs a 6-stage pipeline (Stage 0 through Stage 5):

0. **Init** — Capture idea, resolve script paths, create run directory, write `version.json` + `idea.json`
1. **Parallel Research + Extraction** — (Lane A) ti-researcher writes `research.json`; (Lane B) ti-extractor writes `hypotheses.json`, founder confirms, orchestrator writes `assumptions.json`
2. **Parallel Dimension Evaluation** — Spawn 14 independent evaluator agents in parallel; each writes its own `dimensions/{slug}.json`
3. **Compute + Narrative** — (Stage 3a) `scripts/compute.py` reads dimension JSONs and writes `numbers.json`; (Stage 3b) ti-narrative reads numbers.json and writes 5 prose JSON files
4. **Render** — `scripts/render_report.py` writes `report.md` + `report.html` via Jinja2
5. **Confirm** — Display artifact summary and offer browser open

Each evaluator agent gets its own context window and never sees other dimensions' results. This prevents anchoring bias. The orchestrator performs zero text processing on evaluator output -- all math is in `scripts/compute.py`.

## Suggest-from-HN Pipeline

The `/tweak:suggest-from-hn` command runs a 7-phase pipeline (no subagents — analysis runs inline):

1. **Capture** — Parse HN URL or item ID from arguments (or prompt interactively)
2. **Fetch** — Run `hnparse.py` via `uv` to download the post, article, and comment tree
3. **Read** — Load the full `content.md` (all chunks — late comments often have the strongest signals)
4. **Analyze** — Identify 3-6 technology shifts with evidence-grounded product opportunities
5. **Write Shifts** — Save analysis to `~/.tweakidea/hn/hn-{id}/shifts.md`
6. **Confirm** — Present opportunities for user selection via multi-select prompts
7. **Write Ideas** — Save confirmed opportunities as detailed problem/solution writeups to `ideas.md`

## Dimension Files

Each dimension in `skills/ti-scoring/dimensions/` defines:
- **Signals table**: What the evaluator looks for (strong/moderate/weak indicators)
- **Rubric criteria**: 5-level binary scoring (each level has PASS/FAIL criteria)
- **Weight**: How much this dimension contributes to the final score

To modify a dimension's scoring behavior, edit its dimension file. To add a new dimension, create a new file following the existing pattern and update EVALUATION.md to include it in the framework.

## Making Changes

### What to change where

| Change | Files to edit |
|--------|--------------|
| Scoring criteria for a dimension | `skills/ti-scoring/dimensions/{name}.md` |
| Dimension weights | `skills/ti-scoring/EVALUATION.md` |
| Scoring algorithm | `skills/ti-scoring/EVALUATION.md` |
| Evaluate pipeline behavior | `commands/tweak/evaluate.md` |
| Scorecard computation | `scripts/compute.py` |
| Cross-dimensional narrative | `agents/ti-narrative.md` |
| Research strategy | `agents/ti-researcher.md` |
| Evaluator behavior | `agents/ti-evaluator.md` |
| Founder profile template | `skills/ti-founder/SKILL.md` |
| Report templates | `skills/ti-report/` |
| Hypothesis extraction | `agents/ti-extractor.md` |
| Suggest pipeline behavior | `commands/tweak/suggest-from-hn.md` |
| HN fetch/parse logic | `skills/ti-hnparse/hnparse.py` |

### PR conventions

1. **One concern per PR** — don't mix dimension changes with pipeline changes
2. **Describe the "why"** — explain what behavior you're changing and why the current behavior is wrong or insufficient
3. **Test with a real idea** — run `/tweak:evaluate` with a real startup idea and confirm the output makes sense
4. **Keep dimension files consistent** — if you change the structure of one dimension file, update all 14 to match

## User Data

TweakIdea stores user data outside the repository:

- `~/.tweakidea/FOUNDER.md` — Persistent founder profile
- `~/.tweakidea/runs/{timestamp}/` — Evaluation run outputs
- `~/.tweakidea/hn/hn-{id}/` — HN suggest outputs (content.md, shifts.md, ideas.md)

These paths are never committed to the repository. If you're testing, your personal data stays in your home directory.

## Development Workflow

Source files live in root-level directories (`agents/`, `commands/`, `skills/`). The installer copies them into `.claude/` for Claude Code discovery.

1. **Setup:** `node bin/install.js --local` — populates `.claude/` from source dirs
2. **Edit:** Change files in `agents/`, `commands/`, or `skills/`
3. **Refresh:** Re-run `node bin/install.js --local` to update `.claude/`
4. **Test npx flow:** `npx .` from repo root
