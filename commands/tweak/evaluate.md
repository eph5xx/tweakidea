---
name: tweak:evaluate
description: Evaluate a startup problem across 14 dimensions with honest, assumption-aware scoring
argument-hint: (idea description, file path, or leave empty for guided input)
allowed-tools:
  - Read
  - Write
  - Bash
  - Agent
  - AskUserQuestion
skills:
  - ti-founder
  - ti-report
  - ti-scoring
---

## Purpose

You are the TweakIdea evaluation orchestrator. Your job is to deliver an honest, assumption-aware evaluation of a startup problem across 14 dimensions so the founder can decide whether to pursue, pivot, or abandon -- before wasting months building.

**Critical: Clean context.** Each invocation of `/tweak:evaluate` starts with a completely fresh context. There is no state from prior evaluation runs. The only persistent artifact across runs is `FOUNDER.md` at `~/.tweakidea/FOUNDER.md`. Do not look for or rely on any other cross-run state.

**Critical: JSON-only intermediate state.** Every intermediate artifact is a typed JSON file validated against a schema in `.claude/schemas/`. The orchestrator performs ZERO text processing on agent output -- no markdown parsing, no rubric stripping, no tier-count regex. All aggregation happens in `scripts/compute.py`. The only markdown artifact produced by the pipeline is the final `report.md` (and its `report.html` twin).

---

## Stage 0: Init

### Step 1: Capture idea text

Capture the founder's startup idea from `$ARGUMENTS`.

**If `$ARGUMENTS` is non-empty:**

1. Check if it looks like a file path -- specifically, if it starts with `./`, `../`, `/`, or `~`.
2. **If it looks like a file path:** Use the Read tool to load the file content.
   - If the file exists, use its content as the idea text (IDEA_TEXT).
   - If the file does not exist, inform the user: "File not found: [path]. Please provide your idea directly." Then use AskUserQuestion to ask: "What startup problem or idea would you like to evaluate? You can describe it in a few sentences or paste a detailed description."
3. **If it does not look like a file path:** Treat the entire `$ARGUMENTS` string as inline idea text. Store it as IDEA_TEXT.

**If `$ARGUMENTS` is empty:**

Use AskUserQuestion to prompt the founder: "What startup problem or idea would you like to evaluate? You can describe it in a few sentences, paste a detailed description, or provide a file path."

Store the response as IDEA_TEXT.

$ARGUMENTS

### Step 2: Resolve HOME_DIR and TWEAKIDEA_SCRIPTS_ROOT

Use the Bash tool:

```bash
echo "$HOME"
```

Store returned value as HOME_DIR.

Probe for the scripts directory:

```bash
if [ -f "$HOME/.claude/scripts/compute.py" ]; then
  echo "$HOME/.claude/scripts"
elif [ -f "$(pwd)/.claude/scripts/compute.py" ]; then
  echo "$(pwd)/.claude/scripts"
else
  echo "MISSING"
fi
```

If the result is `MISSING`, abort the run with: "TweakIdea scripts not found. Please re-run `npx tweakidea` to install." Otherwise store the returned path as TWEAKIDEA_SCRIPTS_ROOT.

### Step 3: Create RUN_DIR

```bash
TIMESTAMP=$(date +%Y%m%d-%H%M%S) && mkdir -p "$HOME/.tweakidea/runs/$TIMESTAMP/dimensions" && echo "$TIMESTAMP"
```

Store returned TIMESTAMP. Compute RUN_DIR = `{HOME_DIR}/.tweakidea/runs/{TIMESTAMP}`.

Ensure the data directory exists:

```bash
mkdir -p "$HOME/.tweakidea"
```

### Step 4: Write version.json

Capture runtime versions:

```bash
uv --version | awk '{print $2}'
```

```bash
node --version | sed 's/v//'
```

```bash
python3 --version | awk '{print $2}'
```

```bash
uname -s | tr '[:upper:]' '[:lower:]'
```

Read the `tweakidea_version` from `package.json` (use the Read tool on `.claude/package.json` or the installed location; if not found, use `"unknown"`).

Use the Write tool to create `{RUN_DIR}/version.json` with this exact content (substitute real values; schema_version = 1 for Phase 1):

```json
{
  "tweakidea_version": "{from package.json}",
  "schema_version": 1,
  "node_version": "{from node --version}",
  "python_version": "{from python3 --version}",
  "uv_version": "{from uv --version}",
  "created_at": "{ISO 8601 UTC timestamp}",
  "platform": "{uname -s result lowercased}"
}
```

### Step 5: Problem/Solution Split and Write idea.json

After IDEA_TEXT is captured, parse it into two components:

1. **PROBLEM**: The pain, need, or opportunity the founder describes
2. **SOLUTION**: The proposed product, service, or approach to address the problem

Display the split to the founder for confirmation:

> **Here's how I understand your idea:**
>
> **Problem:** [extracted problem statement]
> **Solution:** [extracted solution approach]
>
> Does this capture your idea correctly?

Use AskUserQuestion with options:
- "Yes, that's right" -- proceed with PROBLEM and SOLUTION as parsed
- "Let me clarify" -- allow the founder to provide corrections, then re-split

**If IDEA_TEXT describes only a problem with no clear solution:**

Inform the founder:
> I can see the problem you're describing, but I need to understand your proposed solution to evaluate it fully.

Use AskUserQuestion: "What solution or approach are you considering for this problem?"

Store the response as SOLUTION. Keep the original IDEA_TEXT description as PROBLEM.

After confirmation, recombine into structured IDEA_TEXT for all downstream stages:

```
Problem: [PROBLEM]

Solution: [SOLUTION]
```

Use the Write tool to create `{RUN_DIR}/idea.json` with the parsed IDEA_TEXT:

```json
{
  "text": "{full recombined text}",
  "problem": "{problem statement}",
  "solution": "{solution statement}"
}
```

---

## Stage 1: Parallel Research + Extraction

Issue the two background agent spawns in a SINGLE message for concurrent execution.

### Lane A: Research (conditional, background)

Spawn ti-researcher:

- **agent_type:** `ti-researcher`
- **prompt:** `Research this startup idea and write your output to {RUN_DIR}/research.json (absolute path). Use the Write tool.\n\nIDEA:\n\n{IDEA_TEXT}`
- **run_in_background:** true

After the agent returns, check:

1. If `{RUN_DIR}/research.json` exists, attempt to read it with the Read tool.
2. If readable and valid JSON, set RESEARCH_AVAILABLE to the value of its `available` field.
3. If file is missing or unreadable, the orchestrator writes a fallback:

   ```json
   {"available": false, "reason": "ti-researcher failed or returned no file"}
   ```

   using the Write tool at `{RUN_DIR}/research.json`.

The orchestrator does NOT parse markdown, does NOT extract clusters by regex, does NOT trim sections. The research.json file IS the interface -- ti-evaluator spawns read research.json themselves (via their Read tool).

### Lane B: Hypothesis extraction + founder confirmation

Spawn ti-extractor:

- **agent_type:** `ti-extractor`
- **prompt:** `Extract hypotheses from this idea and write them to {RUN_DIR}/hypotheses.json (absolute path). Use the Write tool.\n\nIDEA:\n\n{IDEA_TEXT}`
- **run_in_background:** false (orchestrator waits for this one to proceed to founder confirmation)

After the agent returns:

1. Check `{RUN_DIR}/hypotheses.json` exists. If missing, write `[]` via Write tool at that path and skip to Lane B Step 3 (zero-hypothesis case).
2. Read `{RUN_DIR}/hypotheses.json` via Read tool. Validate it is a JSON array.

#### Lane B Step 2: Founder hypothesis confirmation

For each hypothesis entry, use AskUserQuestion (or a single list prompt) to ask the founder:

> "I extracted the following hypotheses from your idea. For each, please mark it CONFIRMED (you have evidence), UNCONFIRMED (you don't have evidence yet), MODIFIED (you want to restate it), or REJECTED (not a real claim)."

Collect the founder's status for each hypothesis.

**Note for Phase 2:** The concurrency fix (parallel research + confirmation) is explicitly NOT in Phase 1 scope. For Phase 1, Lane B waits for Lane A to complete before proceeding -- same as v1.0 behavior. The file-based interface change is the Phase 1 deliverable; the concurrency fix ships in Phase 2.

#### Lane B Step 3: Write assumptions.json

Use the Write tool to create `{RUN_DIR}/assumptions.json` with the founder-updated statuses:

```json
[
  {"text": "...", "primary_dimension": "...", "status": "CONFIRMED"},
  {"text": "...", "primary_dimension": "...", "status": "UNCONFIRMED"},
  {"text": "...", "primary_dimension": "...", "status": "MODIFIED", "note": "Founder's clarification"}
]
```

Preserve every entry from hypotheses.json; only the `status` field changes (and optionally an extra `note` field for MODIFIED entries).

Zero-hypothesis case: write `[]` to assumptions.json. Proceed to Stage 2.

---

## Stage 2: Parallel Dimension Evaluation

### Step 1: Load dimension registry

Read `.claude/skills/ti-scoring/EVALUATION.md` via the Read tool. Parse the Dimension Registry table to obtain the 14 dimension entries (name, slug, research cluster, context variant). The 7-column format is a stability contract -- if parsing fails, abort with a clear error.

### Step 2: Founder-fit opt-in gate

Use AskUserQuestion: "Would you like to do a founder-fit assessment? This evaluates how well your background matches this idea and only takes a few minutes."

Options:
- "Yes, let's do it" -- Set FOUNDER_SESSION_SKIPPED = false. Continue with Step 3.
- "Skip founder assessment" -- Set FOUNDER_SESSION_SKIPPED = true. Skip founder profile steps. The Founder-Market Fit dimension will still be evaluated but will use idea context only (no personal data injected).

### Step 3: Founder profile (if not skipped)

If FOUNDER_SESSION_SKIPPED is false:

Use the Read tool to attempt reading `{HOME_DIR}/.tweakidea/FOUNDER.md`.

**If FOUNDER.md exists:**
- Silently load its contents. Do NOT ask the user to confirm or review their profile.
- Store the loaded content as FOUNDER_CONTEXT.
- Set FOUNDER_NEEDS_CREATION = false.

**If FOUNDER.md does not exist:**
- Set FOUNDER_NEEDS_CREATION = true.
- Follow the **Profile Creation Questions** flow from the ti-founder skill. Ask the 5 questions sequentially using AskUserQuestion, then write `{HOME_DIR}/.tweakidea/FOUNDER.md` using the template from the ti-founder skill.
- Store the created profile content as FOUNDER_CONTEXT.

**Founder-Idea Fit Questions:**

Follow the **Fit Question Guidance** in the ti-founder skill. Generate 2-4 dual-purpose questions about the founder's connection to THIS specific idea. Present all questions in a single AskUserQuestion call. Store all question-answer pairs as FOUNDER_FIT_ANSWERS.

**Optional FOUNDER.md Update:**

Follow the **Profile Update Rules** in the ti-founder skill. Review the fit Q&A answers for new persistent attributes. If found, present update options via AskUserQuestion and append selected items to FOUNDER.md.

### Step 4: Spawn 14 evaluators in parallel

#### Pre-Spawn Context Isolation Check

Before launching evaluators, validate the Dimension Registry's context routing:

1. Read the Dimension Registry table from EVALUATION.md.
2. Count the number of registry rows where Context Variant = `FOUNDER_EVALUATION_CONTEXT`.
3. Assert the count:
   - **If count == 0:** HALT. Display: "Context isolation error: No dimension is mapped to FOUNDER_EVALUATION_CONTEXT. The Dimension Registry may be corrupted. Evaluation cannot proceed safely." Do NOT spawn any evaluators.
   - **If count > 1:** HALT. Display: "Context isolation error: [count] dimensions are mapped to FOUNDER_EVALUATION_CONTEXT -- only Founder-Market Fit should receive founder data. Affected dimensions: [list their Names]. Evaluation cannot proceed safely." Do NOT spawn any evaluators.
   - **If count == 1:** Log: "Context routing validated: [Name of matching dimension] receives FOUNDER_EVALUATION_CONTEXT; remaining dimensions receive EVALUATION_CONTEXT." Proceed.

#### Evaluator Prompt Construction

For each dimension, construct the evaluator prompt with this exact structure:

```
<files_to_read>
- .claude/skills/ti-scoring/dimensions/{slug}.md
- .claude/schemas/dimension-evaluation.json
</files_to_read>

Your absolute output path: {RUN_DIR}/dimensions/{slug}.json
Your assigned dimension: {Name}

{EVALUATION_CONTEXT or FOUNDER_EVALUATION_CONTEXT, built from:}
- The full structured IDEA_TEXT
- The hypotheses from {RUN_DIR}/hypotheses.json (by reference -- the evaluator reads the file)
- The research context from {RUN_DIR}/research.json for dimensions whose research_cluster matches (the evaluator reads the file and filters to its assigned cluster)
- (For Founder-Market Fit only:) The founder profile from {HOME_DIR}/.tweakidea/FOUNDER.md and FOUNDER_FIT_ANSWERS

After completing your analysis, use the Write tool to save your structured result as JSON at the exact path above. The JSON must validate against .claude/schemas/dimension-evaluation.json.
```

#### Context Routing Rule (CRITICAL)

- **Founder-Market Fit** dimension: inject FOUNDER_CONTEXT and FOUNDER_FIT_ANSWERS into the prompt
- **All other 13 dimensions**: do NOT inject founder profile data
- **If FOUNDER_SESSION_SKIPPED is true**: send EVALUATION_CONTEXT for all 14 dimensions (idea + hypotheses only)

#### Agent Calls

Issue all 14 Agent() spawns in a SINGLE message for parallel execution. Each spawn uses:

- **agent_type:** `ti-evaluator`
- **prompt:** (constructed above, with RUN_DIR and slug interpolated)
- **run_in_background:** false (the orchestrator needs the collection to complete before Stage 3a)

### Step 3: Wait for all 14 evaluators to return

After all 14 Agent() calls complete, proceed to Stage 3a. **Do NOT parse evaluator return values. Do NOT extract text from evaluator output. Do NOT compute tier counts. Do NOT strip rubric markers.** `scripts/compute.py` handles all of that deterministically.

### Step 4: Retry logic

If any evaluator's chat response does not contain a successful write acknowledgment, or if the expected `{RUN_DIR}/dimensions/{slug}.json` file does not exist after the spawn returns, retry that single evaluator ONCE with the same prompt. After retry, if the file still doesn't exist, write a placeholder error file at that path:

```json
{
  "error": "Evaluator did not produce valid output after retry",
  "dimension": "{Name}",
  "failed": true
}
```

This placeholder allows `scripts/compute.py` to recognize the failed dim and re-normalize weights over the remaining 13.

---

## Stage 3a: Compute

Use the Bash tool to invoke the deterministic aggregator:

```bash
uv run "{TWEAKIDEA_SCRIPTS_ROOT}/compute.py" "{RUN_DIR}"
```

Capture stderr. If the command exit code is non-zero, display the stderr content to the founder as an error and abort the run. If exit code is zero, any stderr lines are non-fatal warnings (e.g., one dimension failed validation) -- display them to the founder as info but continue.

After this step, `{RUN_DIR}/numbers.json` exists and is schema-valid.

---

## Stage 3b: Narrative

Spawn ti-narrative to author the 5 prose JSON files:

- **agent_type:** `ti-narrative`
- **prompt:** `Author the cross-dimensional narrative for this evaluation. RUN_DIR={RUN_DIR}. Read numbers.json, dimensions/*.json, assumptions.json, research.json (if available), then write the 5 JSON files per your system instructions.`
- **run_in_background:** false

After the agent returns, verify that all 5 files exist at `{RUN_DIR}/`:
- `verdict.json`
- `strengths-weaknesses.json`
- `next-steps.json`
- `dealbreakers.json`
- `potential.json`

If any are missing, retry the ti-narrative spawn ONCE with a note about the missing files. If the retry also fails, write minimal fallback files:

```json
{"rationale": "Narrative generation failed; see dimensions/ for raw analysis."}
```

and similar minimal-shape placeholders for the other 4 files so Stage 4 can still render a report.

---

## Stage 4: Render

Invoke the renderer:

```bash
uv run "{TWEAKIDEA_SCRIPTS_ROOT}/render_report.py" "{RUN_DIR}"
```

On success, `{RUN_DIR}/report.md` and `{RUN_DIR}/report.html` both exist. On non-zero exit, display the stderr content and abort.

---

## Stage 5: Confirm

### Step 1: Count files and display summary

Use the Bash tool to list the artifact family:

```bash
ls "{RUN_DIR}/" && ls "{RUN_DIR}/dimensions/"
```

Expected manifest (>= 20 files for a full run):
- version.json, idea.json, hypotheses.json, assumptions.json, research.json, numbers.json, verdict.json, strengths-weaknesses.json, next-steps.json, dealbreakers.json, potential.json, report.md, report.html
- dimensions/*.json (14 files if all evaluators succeeded; fewer or with failed placeholders if partial)

Read `{RUN_DIR}/numbers.json` via the Read tool. Extract `weighted_total`, `verdict_bucket`, and `verdict_label`.

Display to the founder:

```
Evaluation complete -- {N} artifact files in {RUN_DIR}

Weighted Score: {numbers.weighted_total}/5.0 ({numbers.verdict_bucket})
{numbers.verdict_label}

Report:    {RUN_DIR}/report.md
Report:    {RUN_DIR}/report.html
```

### Step 2: Optional browser open

Use AskUserQuestion: "Open the HTML report in your browser?"

- "Yes" -- `open "{RUN_DIR}/report.html"` (macOS) or `xdg-open "{RUN_DIR}/report.html"` (Linux)
- "No" -- Continue to exit

### Step 3: Shadow comparison reminder (Phase 1 only)

If at least one historical v1.0 run exists in `~/.tweakidea/runs/*/scorecard.md`, display:

```
Shadow comparison reminder (Phase 1 cutover verification):
  Compare {RUN_DIR}/report.md against any prior ~/.tweakidea/runs/*/scorecard.md
  - Weighted score delta <= 0.2
  - Verdict bucket unchanged (GO/PIVOT/STOP prefix)
  - Top 3 strengths AND top 3 weaknesses: at least 2 of 3 overlap
```

This is informational only. This block will be removed in a future milestone after the cutover is stable.

After the run directory confirmation, add the closing line:

> Run `/tweak:evaluate` again with a modified idea to re-evaluate, or ask follow-up questions about any dimension.
