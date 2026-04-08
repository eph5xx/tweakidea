## Project

**TweakIdea**

A Claude Code skillset (slash commands + subagent definitions) that helps founders evaluate whether a startup problem is worth solving. The system runs 14 independent subagents -- one per problem dimension -- in parallel, then merges results into a weighted scorecard. It emphasizes honest evaluation by detecting unverified assumptions, debating hypotheses with the founder, and incorporating founder-market fit analysis.

**Core Value:** Deliver an honest, assumption-aware evaluation of a startup problem across 14 dimensions so founders can decide whether to pursue, pivot, or abandon -- before wasting months building.

### Constraints

- **Platform**: Claude Code CLI -- slash commands + agent definitions only, no external runtime
- **Evaluation model**: All 14 dimensions from EVALUATION.md must be covered, no skipping
- **Independence**: Each subagent evaluates its dimension without seeing other dimensions' results
- **Clean context**: Each evaluation run should be independent -- no cross-contamination between runs

## Key Decisions

- **Founder data location:** `~/.tweakidea/FOUNDER.md`
- **Evaluator model:** Sonnet (cost/speed balance for 14 parallel agents)
- **Merger model:** Opus (synthesis quality for final scorecard)
- **Researcher model:** Sonnet (web research in Prepare stage)
- **Context isolation:** FOUNDER.md passed ONLY to founder-market-fit evaluator; other 13 evaluators get EVALUATION_CONTEXT only

## Development

Source content lives in root-level directories (`agents/`, `commands/`, `skills/`), not inside `.claude/`. The installer (`bin/install.js`) copies these into `.claude/` for Claude Code discovery.

- **Local dev setup:** `node bin/install.js --local` populates `.claude/` from source dirs
- **Test npx flow:** `npx .` from repo root
- **After editing source files:** Re-run `node bin/install.js --local` to refresh `.claude/`
