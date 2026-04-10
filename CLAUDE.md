## Project

**TweakIdea**

A Claude Code skillset (slash commands + subagent definitions) that helps founders evaluate startup problems and discover product opportunities. Two commands: `/tweak:evaluate` runs 14 independent subagents to produce a weighted scorecard with assumption tracking. `/tweak:suggest-from-hn` analyzes Hacker News discussions to identify technology shifts and surface product ideas.

**Core Value:** Help founders make better decisions -- evaluate whether a problem is worth solving, or discover what problems are emerging from technology shifts.

### Constraints

- **Platform**: Claude Code CLI -- slash commands + agent definitions only. One exception: `suggest-from-hn` uses `uv` + Python for HN fetching
- **Evaluation model**: All 14 dimensions from EVALUATION.md must be covered, no skipping
- **Independence**: Each subagent evaluates its dimension without seeing other dimensions' results
- **Clean context**: Each evaluation run should be independent -- no cross-contamination between runs

## Key Decisions

- **Founder data location:** `~/.tweakidea/FOUNDER.md`
- **Evaluator model:** Sonnet (cost/speed balance for 14 parallel agents)
- **Merger model:** Opus (synthesis quality for final scorecard)
- **Researcher model:** Sonnet (web research in Prepare stage)
- **Context isolation:** FOUNDER.md passed ONLY to founder-market-fit evaluator; other 13 evaluators get EVALUATION_CONTEXT only
- **HN data location:** `~/.tweakidea/hn/hn-{id}/`
- **HN analysis model:** Inline (no subagent -- runs in command context)

## Development

Source content lives in root-level directories (`agents/`, `commands/`, `skills/`), not inside `.claude/`. The installer (`bin/install.js`) copies these into `.claude/` for Claude Code discovery.

- **Local dev setup:** `node bin/install.js --local` populates `.claude/` from source dirs
- **Test npx flow:** `npx .` from repo root
- **After editing source files:** Re-run `node bin/install.js --local` to refresh `.claude/`
