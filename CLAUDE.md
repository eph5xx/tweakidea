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

<!-- GSD:project-start source:PROJECT.md -->
## Project

**TweakIdea**

TweakIdea is a Claude Code skillset (slash commands + subagent definitions) that helps founders evaluate startup problems and discover product opportunities. The evaluate pipeline spawns 14 independent dimension agents to produce a weighted scorecard with assumption tracking; a second command (`suggest-from-hn`) analyzes Hacker News discussions for emerging opportunities. Users are solo and small-team founders making go/pivot/stop decisions on ideas.

**Core Value:** Help founders make better decisions — evaluate whether a problem is worth solving, or discover what problems are emerging from technology shifts.

### Constraints

- **Platform:** Claude Code CLI — all orchestration stays in slash commands + agent definitions; `ti-hnparse` is the sole exception (Python via `uv`)
- **Evaluation model:** All 14 dimensions from EVALUATION.md must remain covered — no skipping even in `quick` tier
- **Independence:** Each subagent evaluates its dimension without seeing other dimensions' results — parallelism + context isolation must be preserved
- **Clean context:** Each evaluation run remains independent — no cross-contamination between runs
- **Node.js:** Installer/scripts stay on Node 18+ built-ins only (no external npm deps introduced)
- **Founder data:** Persistent data lives under `~/.tweakidea/` — do not relocate
- **Backwards compatibility:** Existing `FOUNDER.md` single-file installs must migrate cleanly to `founders/` folder (or keep working until founder runs a migration)
- **Scope:** This milestone touches `/tweak:evaluate` surface only; `/tweak:suggest-from-hn` is off-limits
<!-- GSD:project-end -->

<!-- GSD:stack-start source:codebase/STACK.md -->
## Technology Stack

## Languages
- JavaScript (Node.js) — CLI tooling, installer, command/agent definitions (YAML frontmatter + markdown)
- Python 3.11+ — HN data fetching and parsing (`hnparse.py`)
- Markdown — Command definitions, agent prompts, skill documentation
## Runtime
- Node.js 18.0.0 or higher (per `package.json` engines field in `package.json`)
- Python 3.11+ (via `uv` package runner)
- npm (for Node.js packages)
- `uv` (Python script runner for HN fetching)
- Lockfile: Not present (minimal npm dependencies)
## Frameworks
- Claude Code CLI — Slash command + agent framework for orchestrating multi-agent evaluation workflows (`commands/tweak/evaluate.md`, `commands/tweak/suggest-from-hn.md`)
- Agent definitions (4 agents): Evaluator, Extractor, Researcher, Merger — spawned in parallel during evaluation (`agents/ti-evaluator.md`, `agents/ti-extractor.md`, `agents/ti-researcher.md`, `agents/ti-merger.md`)
- None detected — evaluation framework is the product, not tested separately
- Node.js installer script (`bin/install.js`) — copies source files to `.claude/` for Claude Code discovery
- `uv run` — Executes Python script with inline dependency declarations
## Key Dependencies
- `playwright` — Browser automation for JavaScript-rendered article pages
- `httpx` — HTTP client for Algolia HN API and fallback article fetching
- `trafilatura` — Article content extraction (HTML to markdown)
- Built-in only: `fs`, `path`, `os`, `readline`
- No external npm packages required (pure Node.js implementation)
## Configuration
- `.claude/` directory — Installed agent and command definitions (auto-generated by `bin/install.js`)
- Source directories — `agents/`, `commands/`, `skills/` (populated by developer, installed by script)
- Persistent data stored in `~/.tweakidea/` (user's home directory):
- `package.json` — Minimal metadata, only specifies Node engine requirement and bin entry point
## Platform Requirements
- macOS, Linux, or Windows with Node.js ≥18.0.0 installed
- `uv` installed for Python script execution (`curl -LsSf https://astral.sh/uv/install.sh | sh` or `brew install uv`)
- Claude Code CLI installed and configured
- Claude Code CLI environment
- Node.js ≥18.0.0 runtime
- `uv` for HN analysis feature (`/tweak:suggest-from-hn`)
- Network access:
- Claude Sonnet — 14 evaluators + researcher + extractor (cost/speed balance)
- Claude Opus — Merger agent (synthesis quality)
<!-- GSD:stack-end -->

<!-- GSD:conventions-start source:CONVENTIONS.md -->
## Conventions

## Project Overview
## Markdown File Structure
- `agents/ti-evaluator.md`: `model: sonnet`, spawned independently 14 times
- `agents/ti-merger.md`: `model: opus`, synthesis of multiple inputs
- `commands/tweak/evaluate.md`: No model specified (orchestrator context)
## Naming Patterns
- Agents: `ti-[function].md` (e.g., `ti-evaluator.md`, `ti-merger.md`)
- Commands: `[verb]-[noun].md` (e.g., `evaluate.md`, `suggest-from-hn.md`)
- Skills: `ti-[purpose]/` (e.g., `ti-scoring/`, `ti-hnparse/`)
- Dimensions: `[descriptor].md` (e.g., `pain-intensity.md`, `market-size.md`)
- `agents/`: Subagent definitions
- `commands/tweak/`: Command entry points
- `skills/`: Reference knowledge and framework definitions
- `skills/ti-scoring/dimensions/`: Individual dimension rubrics
- `bin/`: Installation and build tooling
## Content Style
- `## Section Title` — major phases/steps (Stage, Phase, Lane)
- `### Subsection Title` — actions within phases (Step)
- `#### Detailed Section` — fine-grained guidance (Evidence tiers, algorithm details)
- Bash commands enclosed in triple backticks with `bash` lang identifier
- Output examples use indentation or separate fenced blocks
- Include stderr/stdout separation when relevant for script execution
- Use bullet lists (`-`) for unordered content
- Use numbered lists (`1.`, `2.`) for sequential steps
- Use definition lists (`**Term:**`) for concept definitions
- **Bold** for terms of art, critical instructions, and defined keywords
- `code font` for file paths, variable names, technical identifiers
- > blockquotes for critical constraints or context notes
## Agent Behavior Specifications
- Use explicit ordering: "Follow these steps IN ORDER. Step 0 is optional -- skip it if..."
- Mark optional steps clearly: `### Step 0: Targeted Research (Optional)`
- Mandatory steps marked as "mandatory and must not be skipped"
- `[PASS|Verified]` — Both founder confirmation AND research data support the claim
- `[PASS|Research-Backed]` — Research data exists without explicit founder statement
- `[PASS|Founder-Asserted]` — Founder stated it but no research data supports
- `[PASS|Assumed]` — Inferred from context or unconfirmed hypotheses
## Hypothesis Handling
- `[CONFIRMED]` hypothesis: Treat as evidence with full weight
- `[UNCONFIRMED]` hypothesis: Withhold scoring credit but note as CONDITIONAL
- Hypotheses tagged by dimension (e.g., `(Primary dimension: Pain Intensity)`)
## Pipeline Context Flow
- "Each invocation of `/tweak:evaluate` starts with a completely fresh context"
- "No state from prior evaluation runs"
- "Only persistent artifact across runs is `FOUNDER.md` at `~/.tweakidea/FOUNDER.md`"
- "All intermediate state stays in-memory during evaluation"
- "No intermediate temp files" during stage transitions
- Agents pass context via prompts, not file writes
- Final artifacts written progressively as each stage completes
## File Path References
- `agents/ti-evaluator.md` (source file location)
- `.claude/skills/ti-scoring/EVALUATION.md` (installed location in Claude Code)
- `~/.tweakidea/FOUNDER.md` (user data location)
## JavaScript/Node.js Conventions
- `camelCase` for variables and functions: `wantGlobal`, `getSourceDir()`, `copyFileSync()`
- `CONSTANT_CASE` for flags and static values: `AGENT_FILES`, `SKILL_DIRS`
- Descriptive function names: `getGlobalDir()`, `resolveTargetDir()`, `cleanupPreviousInstall()`
- ANSI color constants at top (cyan, green, yellow, red, dim, bold, reset)
- Utility functions grouped by concern: file utilities, cleanup, settings, version tracking
- Main logic in `async main()` function
- Error handling via try-catch with informative console output
- Separator comments: `// ── ANSI helpers ────────────────────────────────────────────────────────────────`
- Inline comments minimal; code self-documents via function names
- No JSDoc or TypeScript type annotations (not TypeScript codebase)
- Flag parsing: `hasFlag(...flags)` helper accepts multiple flag variants (e.g., `--global`, `-g`)
- Directory creation: `mkdirp()` wraps `fs.mkdirSync` with `{ recursive: true }`
- Version comparison: Semantic versioning strings parsed as-is (no semver library)
- CLI feedback: ANSI color wrapping for success, warning, and error messages
## Python Conventions
- Uses Python 3.11+ union syntax: `str | None` instead of `Optional[str]`
- Type hints on function parameters and return types
- `# type: ignore` comments on external library imports (Playwright, trafilatura, httpx)
- `snake_case` for functions and variables: `parse_hn_id()`, `fetch_hn_data()`, `article_text`
- `snake_case` for constants: `item_id`, `out_dir`
- Descriptive function names: `clean_comment_html()`, `relative_time()`, `count_comments()`
- Script header with PEP 723 dependency declaration
- Imports grouped: stdlib, then third-party
- Pure functions for data transformation
- Recursive helpers: `count_comments()` and `format_comments()` handle tree structures
- Regex for HTML parsing: `re.sub()` with lambda fallbacks for complex replacements
- Fallback error handling: Try Playwright → fall back to HTTP if JS rendering fails
- String formatting: f-strings for interpolation, `str.join()` for list concatenation
- HTML entity decoding: `html.unescape()` for safety
- Structured markdown generation via `build_markdown()` function
- Relative time formatting for user-friendly timestamps
- Nested blockquote prefixes for recursive comments (`">" * (depth + 1)`)
## Data Format Patterns
- `## EXTRACTION COMPLETE` — Signals successful completion
- `## EVALUATION COMPLETE` — Dimension evaluator success marker
- `## EVALUATION FAILED` — Evaluator failure (handled as missing dimension)
- `## RESEARCH COMPLETE` — Researcher completion marker
### Dimension: [name]
### Analysis
### Evidence Tier Counts: {count}V {count}R {count}F {count}A
### Score: [X]/5
### Potential: [Y]/5 (if [assumptions] confirmed)
### Assumptions Relied On
- [Assumption]: [CONFIRMED/UNCONFIRMED] -- [impact]
### Key Signals
- [Signal observed]
### Evidence Basis: [Research/Founder]
- [Hypothesis text] (Primary dimension: [dimension name])
## Error Handling
- Silent handling of missing input: "If zero hypotheses extracted... do NOT block or fail -- this is a valid outcome"
- Graceful degradation: When extraction fails, use zero-hypothesis edge case format
- Evidence absence treated as evidence itself: "no evidence supports this criterion" is a valid assessment
- Try-catch with user-facing error messages
- Warnings for invalid JSON without halting: `catch { console.log(...); return; }`
- Exit codes: `process.exit(1)` for critical errors
- ANSI colored error output for clarity
- Exception handling with fallbacks: Playwright errors → HTTP fallback
- Stderr for progress messages, stdout for file path (parseable for calling scripts)
- `raise ValueError` for invalid input parsing
## Testing
- "Test with a real idea" — run `/tweak:evaluate` with a real startup idea per CONTRIBUTING.md
- Dimension file consistency checks: "if you change the structure of one dimension file, update all 14 to match"
- Integration testing via full pipeline execution (Capture → Prepare → Assemble → Evaluate → Merge → Confirm)
- PR convention: "One concern per PR — don't mix dimension changes with pipeline changes"
- Evidence consistency: Evaluators must verify hypothesis handling aligns with rubric assessment
## Documentation Conventions
- `# [Dimension Name]` — title
- `**Weight:** X%` — scalar weight
- `**Core Question:** [Key question]` — evaluator focus
- `## Signal Table` — strong/weak indicators
- `## Scoring Rubric` — Score 5 (highest) down to Score 1 (lowest)
- Optional: `### B2B/B2C Nuance` — context-dependent guidance
- `EVALUATION.md` — Dimension registry, weights, indexes, clusters
- `SKILL.md` — Metadata-only skill definitions
<!-- GSD:conventions-end -->

<!-- GSD:architecture-start source:ARCHITECTURE.md -->
## Architecture

## Pattern Overview
- **Command-centric entry points**: Two primary slash commands (`/tweak:evaluate`, `/tweak:suggest-from-hn`) define user interactions
- **Parallel agent execution**: Independent dimension evaluators run concurrently (no cross-contamination)
- **Modular skill system**: Shared reference data (scoring framework, dimensions, templates) injected at runtime
- **Persistent founder profile**: Single source of truth at `~/.tweakidea/FOUNDER.md` persists across evaluation runs
- **Clean context isolation**: Each run is independent; intermediate state stays in-memory; final artifacts written progressively to `~/.tweakidea/runs/{TIMESTAMP}/`
## Layers
- Purpose: Command dispatch, stage coordination, prompt construction for downstream agents
- Location: `commands/tweak/evaluate.md`, `commands/tweak/suggest-from-hn.md`
- Contains: Multi-stage pipelines (Capture, Prepare, Evaluate, Merge, Report)
- Depends on: Skills (ti-scoring, ti-founder, ti-html-report, ti-hnparse), agents (ti-extractor, ti-researcher, ti-evaluator, ti-merger)
- Used by: Claude Code slash command runtime
- Purpose: Independent evaluation specialists; each spawned via Agent() tool with isolated prompts
- Location: `agents/ti-*.md`
- Contains: Four agent definitions with model selection, tools, permissions
- Depends on: Skills (ti-scoring, ti-founder)
- Used by: Orchestrators via Agent() tool spawning
- Purpose: Shared framework data, templates, and generation rules
- Location: `skills/ti-*/` directories
- Contains:
- Depends on: None (pure reference)
- Used by: All agents and orchestrators via skill preloading
- Purpose: Store founder profiles and evaluation run artifacts
- Location: `~/.tweakidea/` (user home directory, outside repo)
- Contains:
- Purpose: npm package, installer, discovery integration
- Location: `bin/install.js`, `package.json`
- Contains: Installer logic for local (`.claude/`) and global (`~/.claude/`) deployment
- Depends on: Source directories (agents/, commands/, skills/)
- Used by: `npx tweakidea` CLI for installation
## Data Flow
- **In-Memory State** (per command execution):
- **Persistent State** (cross-run):
- **Transient State** (discarded after run):
## Key Abstractions
- Purpose: Single axis of startup evaluation with signal table and scoring rubric
- Examples: `skills/ti-scoring/dimensions/pain-intensity.md`, `solution-gap.md`, `founder-market-fit.md`
- Pattern: Each dimension file contains:
- Purpose: Testable claim extracted from founder's idea text
- Pattern: Formatted as "Claim text (Primary dimension: name)"
- Examples: "Small accounting firms struggle with client onboarding (Pain Intensity)", "Market is $500M+ (Market Size)"
- Usage: Passed to all 14 evaluators; tagged [CONFIRMED] or [UNCONFIRMED] based on evidence
- Purpose: Dimension assessment output from single evaluator
- Pattern: Analysis narrative + rubric walkthrough + score + potential + assumptions + key signals
- Structure: Between `## EVALUATION COMPLETE` / `## EVALUATION FAILED` markers
- Consumption: Parsed by merger agent to extract scores, findings, evidence tier counts
- Purpose: Grouped market intelligence targeted to specific dimensions
- Three clusters:
- Generation: ti-researcher agent produces all three
- Injection: Orchestrator injects cluster into dimension evaluator prompts matching the dimension's research context
- Purpose: Persistent record of founder attributes across evaluation runs
- Sections: Expertise & Domain Knowledge, Relevant Experience, Network & Market Access, Build Capabilities, Drive & Commitment
- Usage: 
- File: `~/.tweakidea/FOUNDER.md` (YAML-like tagged list format)
- Purpose: Executive summary of evaluation outcome
- Scale: 4.0-5.0 (GO), 3.0-3.99 (PIVOT), 2.0-2.99 (STOP), 1.0-1.99 (STOP)
- Calculation: Weighted average of 14 dimension scores using percentages from registry
- Display: Color-coded banner (green/yellow/orange/red) in report
## Entry Points
- Location: `commands/tweak/evaluate.md`
- Triggers: User invokes `/tweak:evaluate "idea description"` or `/tweak:evaluate` (empty → guided input)
- Arguments: Optional idea text or file path (checked via Read tool)
- Responsibilities:
- Location: `commands/tweak/suggest-from-hn.md`
- Triggers: User invokes `/tweak:suggest-from-hn <hn-url-or-id>`
- Arguments: Hacker News URL or numeric item ID
- Responsibilities:
- `ti-scoring`: Reference data only; accessed via prompt injection by agents
- `ti-founder`: Profile template and Q&A guidance; accessed by orchestrator
- `ti-html-report`: Generation rules; accessed by orchestrator for HTML rendering
- `ti-hnparse`: Python utility; executed as subprocess via Bash tool
## Error Handling
- **Evaluator failure** (ti-evaluator returns `## EVALUATION FAILED`): Merger treats as missing dimension; marks evidence unavailable in scorecard; verdict still computed with 13 dimensions.
- **Research not available** (ti-researcher returns no data): Orchestrator sets RESEARCH_AVAILABLE=false; HTML template omits research highlights card; evaluators proceed with founder context only.
- **Hypothesis extraction zero-case** (ti-extractor returns zero hypotheses): Marked as valid outcome; evaluators proceed with idea text only, no hypothesis tags.
- **Missing founder profile** (first-time user): Profile creation triggered; 5 questions asked; profile written before evaluation proceeds.
- **File not found** (idea text is file path, file missing): User notified; fallback to AskUserQuestion for inline input.
- **HN fetch failure** (hnparse.py fails): User shown error; suggested remedies (uv not installed, invalid item ID, network error).
- **Verdict edge case** (no dimensions available): Weighted total defaults to 0; verdict = "STOP -- Unable to evaluate".
## Cross-Cutting Concerns
- Console output (status messages, findings)
- Markdown reports (structured evaluation output)
- HTML report (styled final artifact)
- Rubric validation: Each evaluator validates their assigned dimension's criteria against evidence
- Dimension registry validation: Merger validates all 14 dimensions present and weighted correctly
- Founder profile validation: Profile creation ensures all 5 sections captured; fit questions confirm idea-specific fit
- **Safe patterns**: Parallel dimension evaluators (no shared state); each receives independent prompt copy
- **Ordering constraints**: Profile must be loaded/created before founder-market-fit evaluator spawns (Stage 2 Lane B before Stage 3)
- **No mutexes/locks**: Each run uses unique RUN_TIMESTAMP directory; no cross-run collision risk
<!-- GSD:architecture-end -->

<!-- GSD:skills-start source:skills/ -->
## Project Skills

No project skills found. Add skills to any of: `.claude/skills/`, `.agents/skills/`, `.cursor/skills/`, or `.github/skills/` with a `SKILL.md` index file.
<!-- GSD:skills-end -->

<!-- GSD:workflow-start source:GSD defaults -->
## GSD Workflow Enforcement

Before using Edit, Write, or other file-changing tools, start work through a GSD command so planning artifacts and execution context stay in sync.

Use these entry points:
- `/gsd-quick` for small fixes, doc updates, and ad-hoc tasks
- `/gsd-debug` for investigation and bug fixing
- `/gsd-execute-phase` for planned phase work

Do not make direct repo edits outside a GSD workflow unless the user explicitly asks to bypass it.
<!-- GSD:workflow-end -->

<!-- GSD:profile-start -->
## Developer Profile

> Profile not yet configured. Run `/gsd-profile-user` to generate your developer profile.
> This section is managed by `generate-claude-profile` -- do not edit manually.
<!-- GSD:profile-end -->
