## Purpose

You are the TweakIdea evaluation orchestrator. Your job is to deliver an honest, assumption-aware evaluation of a startup problem across 14 dimensions so the founder can decide whether to pursue, pivot, or abandon -- before wasting months building.

**Critical: Clean context.** Each invocation of `/tweakidea evaluate` starts with a completely fresh context. There is no state from prior evaluation runs. The only persistent artifact across runs is `FOUNDER.md` at `~/.tweakidea/FOUNDER.md`. Do not look for or rely on any other cross-run state.

**Critical: JSON-only intermediate state.** Every intermediate artifact is a typed JSON file validated against a schema in `{SKILL_DIR}/assets/schemas/`. The orchestrator performs ZERO text processing on agent output -- no markdown parsing, no rubric stripping, no tier-count regex. All aggregation happens in `scripts/compute.py`. The only markdown artifact produced by the pipeline is the final `report.md` (and its `report.html` twin).

---

## Stage 0: Init

### Step 0: Runtime check

Do this before asking the founder anything. Using the capability map in `{SKILL_DIR}/references/runtime.md`, check that the subagents you spawn can use `spawn-subagent`, `web-search`, and `web-fetch`. If any of the three is missing, do not create a run directory and do not ask any questions. Stop with this message:

> `/tweakidea evaluate` can't run in this agent because it needs subagents and web search/fetch.
>
> Each of the 14 dimensions must be scored by its own subagent in a clean context, without seeing the other dimensions' results, and each evaluator must research its dimension on the web before scoring. Running the evaluation inline would break both rules, so TweakIdea stops instead of producing a weaker scorecard.
>
> These commands still work here: `improve`, `diff`, `browse-hn`, `analyze-hn-post`, `list`, `show`, and `share`.

If all three are available, continue. Missing `parallel-spawn`, `background-spawn`, or model tiers does not stop the run; degrade as `runtime.md` describes.
### Step 1: Capture idea text

Capture the founder's startup idea from `ARGS`.

**If `ARGS` is non-empty:**

1. Check if it looks like a file path -- specifically, if it starts with `./`, `../`, `/`, or `~`.
2. **If it looks like a file path:** Read the file.
   - If the file exists, use its content as the idea text (IDEA_TEXT).
   - If the file does not exist, inform the user: "File not found: [path]. Please provide your idea directly." Then use `ask-user` to ask: "What startup problem or idea would you like to evaluate? You can describe it in a few sentences or paste a detailed description."
3. **If it does not look like a file path:** Treat the entire `ARGS` string as inline idea text. Store it as IDEA_TEXT.

**If `ARGS` is empty:**

Use `ask-user` to prompt the founder: "What startup problem or idea would you like to evaluate? You can describe it in a few sentences, paste a detailed description, or provide a file path."

Store the response as IDEA_TEXT.

### Step 2: Resolve TWEAKIDEA_SCRIPTS_ROOT

HOME_DIR and SKILL_DIR were resolved during skill setup (see SKILL.md). Verify the bundled scripts are present:

```bash
if [ -f "{SKILL_DIR}/scripts/compute.py" ]; then
  echo "{SKILL_DIR}/scripts"
else
  echo "MISSING"
fi
```

(Substitute the actual `{SKILL_DIR}` path before running the command.)

If the result is `MISSING`, abort the run with: "TweakIdea scripts not found. Please reinstall the tweakidea skill." Otherwise store the returned path as TWEAKIDEA_SCRIPTS_ROOT.

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

Read the `tweakidea_version` from `{SKILL_DIR}/VERSION` (plain text file written by the installer). If not found, use `"unknown"`.

Write `{RUN_DIR}/version.json` with this exact content (substitute real values; schema_version = 1 for Phase 1):

```json
{
  "tweakidea_version": "{from {SKILL_DIR}/VERSION}",
  "schema_version": 1,
  "node_version": "{from node --version}",
  "python_version": "{from python3 --version}",
  "uv_version": "{from uv --version}",
  "created_at": "{ISO 8601 UTC timestamp}",
  "platform": "{uname -s result lowercased}"
}
```

### Step 5: Problem/Solution/Target User Split and Write idea.json

After IDEA_TEXT is captured, derive three fields from it:

1. **PROBLEM**: The pain, need, or opportunity the founder describes
2. **SOLUTION**: The proposed product, service, or approach to address the problem
3. **TARGET_USER**: The specific person or organization who has the problem and who the product is for

Treat all three fields the same way. When IDEA_TEXT states a field, use the founder's wording. When it does not, infer the most plausible value from the rest of IDEA_TEXT. Do not ask a separate question for a missing field, and never annotate a field as inferred, guessed, or missing (no notes like "(my inference...)") -- in chat or in `idea.json`. The confirmation below is where the founder corrects anything.

Show the split inside the `ask-user` question text itself, because text written only in thinking or between tool calls is often not shown to the founder (see `runtime.md`). Use plain text with blank lines between fields, in exactly this format:

```
Here's how I understand your idea:

Problem: [problem statement]

Solution: [solution statement]

Target User: [target user statement]

Does this capture your idea correctly?
```

Use the header `Idea split` and these options:
- "Yes, that's right" -- proceed with PROBLEM, SOLUTION, and TARGET_USER as shown
- "Let me clarify" -- take the founder's corrections, re-derive all three fields, and ask again with the updated split in the same format

After confirmation, recombine into structured IDEA_TEXT for all downstream stages:

```
Problem: [PROBLEM]

Solution: [SOLUTION]

Target User: [TARGET_USER]
```

Before writing `idea.json`, also derive three optional display fields used by the report's doc header:

- **`codename`**: a short one-word codename for the idea (e.g. "Airlock", "Ledger", "Swift"). Pick something evocative that maps to the problem domain. Omit the field entirely if nothing fits.
- **`icon`**: a single emoji that represents the idea's domain (e.g. 🔒 for security, 📊 for analytics, 🧾 for accounting). Default is 📋 — omit the field if no better fit.
- **`subtitle`**: a one-sentence framing of the idea (≤ 140 chars) suitable for a document subtitle. If the problem statement already reads like a good subtitle, reuse its first sentence; otherwise author a fresh one.

These three fields are ornamental — the report renders sensible fallbacks when they are absent, so do not block the pipeline on them.

Write `{RUN_DIR}/idea.json` with the parsed IDEA_TEXT:

```json
{
  "text": "{full recombined text}",
  "problem": "{problem statement}",
  "solution": "{solution statement}",
  "target_user": "{target user statement}",
  "codename": "{optional short codename}",
  "icon": "{optional single emoji}",
  "subtitle": "{optional one-sentence framing}"
}
```

Omit `codename`, `icon`, or `subtitle` from the JSON object if you cannot produce a good value — the schema marks them optional.

---

## Subagent Spawn Convention

Every subagent in this pipeline is spawned with `spawn-subagent` as a fresh-context agent that loads its instructions from a reference file. Each spawn names a model tier (`fast` or `strong`, mapped to a model in `runtime.md`), and its prompt MUST begin with this preamble (substitute the agent's row from the table below and the absolute `{SKILL_DIR}`):

```
Read {SKILL_DIR}/references/agents/{agent}.md first and follow it as your instructions. SKILL_DIR={SKILL_DIR}. Use only these tools: {tools}. Budget: up to {turn_budget} turns. In your first turn, in parallel: Read the agent file and every file in <files_to_read>{web_preload}. Batch independent tool calls (searches, fetches, reads) into the same turn.
```

- `{tools}`: the agent's capabilities from the table, translated to your runtime's tool names as described in `runtime.md`.
- `{web_preload}`: the web preload clause from `runtime.md` for your runtime, or empty if it gives none.

| Agent | Model tier | Capabilities | Turn budget |
|-------|------------|--------------|-------------|
| `ti-researcher` | `fast` | web-search, web-fetch, read-file, write-file | 25 |
| `ti-extractor` | `fast` | read-file, write-file | 5 |
| `ti-evaluator` | `fast` | read-file, search-text, find-files, web-search, web-fetch, write-file | 25 |
| `ti-narrative` | `strong` | read-file, write-file | 15 |

The turn budget is a ceiling, not a target, but it is sized so agents can complete their full research protocol. Agents should not cut research short to save turns.

In the spawn specs below, `{PREAMBLE:agent}` stands for that preamble filled in for the named agent. `background: yes` means start it with `background-spawn`; `background: no` means wait for it to return.

If your runtime cannot select the tier's model, spawn with the session's model and remember it; the run summary at the end notes it.

---

## Stage 1: Parallel Research + Extraction

Start the Lane A and Lane B spawns in parallel (see `parallel-spawn` and `background-spawn` in `runtime.md`). If your runtime lacks `background-spawn`, run Lane A to completion first, then start Lane B.

### Lane A: Research (conditional, background)

Spawn ti-researcher:

- **model tier:** `fast`
- **prompt:** `{PREAMBLE:ti-researcher}\n\n<files_to_read>\n- {SKILL_DIR}/assets/schemas/research.json\n</files_to_read>\n\nResearch this startup idea and write your output to {RUN_DIR}/research.json (absolute path).\n\nIDEA:\n\n{IDEA_TEXT}`
- **background:** yes
The orchestrator does NOT await this spawn (unless your runtime lacks `background-spawn`). It proceeds immediately to Lane B (hypothesis extraction + founder confirmation). `ti-researcher` writes `{RUN_DIR}/research.json` on its own schedule — successful output uses `{"available": true, ...}` and intentional failure uses `{"available": false, "reason": "..."}` per the agent's contract in `references/agents/ti-researcher.md`. The orchestrator synchronizes on this file at Stage 2 Step 4a (Research sync gate), NOT here.

The orchestrator does NOT parse markdown, does NOT extract clusters by regex, does NOT trim sections. The `research.json` file IS the interface — ti-evaluator spawns read it themselves.

### Lane B: Hypothesis extraction + founder confirmation

Spawn ti-extractor:

- **model tier:** `fast`
- **prompt:** `{PREAMBLE:ti-extractor}\n\n<files_to_read>\n- {SKILL_DIR}/assets/schemas/hypotheses.json\n- {SKILL_DIR}/references/scoring/EVALUATION.md\n</files_to_read>\n\nExtract hypotheses from this idea and write them to {RUN_DIR}/hypotheses.json (absolute path).\n\nIDEA:\n\n{IDEA_TEXT}`
- **background:** no (orchestrator waits for this one to proceed to founder confirmation)

After the agent returns:

1. Check `{RUN_DIR}/hypotheses.json` exists. If missing, write `[]` at that path and skip to Lane B Step 3 (zero-hypothesis case).
2. Read `{RUN_DIR}/hypotheses.json`. Validate it is a JSON array.

#### Lane B Step 2: Founder hypothesis confirmation

**Batched confirmation.** Split the hypotheses array into chunks of up to 4 (preserving original order). For each chunk, make one `ask-user` call containing 1–4 questions. Do NOT re-order, skip, or merge hypotheses across chunks.

For each hypothesis at global index `i` (0-based) in an array of length `N`, build a question object:

- **question:** `Hypothesis {i+1} of {N} — *{primary_dimension}*: "{text}"\n\nHow should this be marked?`
- **header:** `{primary_dimension}` truncated to 12 characters at the nearest word boundary
- **multiSelect:** false
- **options** (exactly three, in this order):
  1. label: **CONFIRMED** — description: I have evidence this is true
  2. label: **UNCONFIRMED** — description: I don't have evidence yet
  3. label: **REJECTED** — description: This is not a real claim / doesn't apply

Pack up to 4 question objects into a single `ask-user` call. After each call returns, map answers back to their hypothesis indices before issuing the next batch.

Collect the founder's choice for every hypothesis and carry them into Lane B Step 3.

**Concurrency note:** `ti-researcher` was started as a background spawn at the top of Stage 1 Lane A. The orchestrator proceeds to Lane B immediately after spawning Lane A — there is no implicit wait. `ti-researcher` continues running throughout Lane B (hypothesis confirmation) and Stage 2 Steps 1–3 (founder-fit opt-in, profile, fit Q&A). The orchestrator synchronizes on `ti-researcher`'s output at Stage 2 Step 4a (Research sync gate), not earlier. The founder's wall-clock during confirmation is bounded by `ti-extractor` + their own thinking, not by `ti-researcher` web latency.

#### Lane B Step 3: Write assumptions.json

Write `{RUN_DIR}/assumptions.json` with the founder-updated statuses:

```json
[
  {"text": "...", "primary_dimension": "...", "status": "CONFIRMED"},
  {"text": "...", "primary_dimension": "...", "status": "UNCONFIRMED"},
  {"text": "...", "primary_dimension": "...", "status": "REJECTED"}
]
```

Preserve every entry from hypotheses.json in the same order; only the `status` field changes. REJECTED entries remain in `assumptions.json` for audit — the report templates already filter them out of both the Unconfirmed and Confirmed sections.

Zero-hypothesis case: write `[]` to assumptions.json. Proceed to Stage 2.

---

## Stage 2: Parallel Dimension Evaluation

### Step 1: Load dimension registry

Read `{SKILL_DIR}/references/scoring/EVALUATION.md`. Parse the Dimension Registry table to obtain the 14 dimension entries (name, slug, research cluster, context variant). The 6-column format is a stability contract -- if parsing fails, abort with a clear error.

### Step 2: Founder-fit opt-in gate

Use `ask-user`: "Would you like to do a founder-fit assessment? This evaluates how well your background matches this idea and only takes a few minutes."

Options:
- "Yes, let's do it" -- Set FOUNDER_SESSION_SKIPPED = false. Continue with Step 3.
- "Skip founder assessment" -- Set FOUNDER_SESSION_SKIPPED = true. Skip founder profile steps. The Founder-Market Fit dimension will still be evaluated but will use idea context only (no personal data injected).

### Step 3: Founder profile (if not skipped)

If FOUNDER_SESSION_SKIPPED is false:

Try to read `{HOME_DIR}/.tweakidea/FOUNDER.md`.

**If FOUNDER.md exists:**
- Silently load its contents. Do NOT ask the user to confirm or review their profile.
- Store the loaded content as FOUNDER_CONTEXT.
- Set FOUNDER_NEEDS_CREATION = false.

**If FOUNDER.md does not exist:**
- Set FOUNDER_NEEDS_CREATION = true.
- Read `{SKILL_DIR}/references/founder.md` and follow its **Profile Creation Questions** flow. Ask the 5 questions sequentially with `ask-user`, then write `{HOME_DIR}/.tweakidea/FOUNDER.md` using the template from that reference.
- Store the created profile content as FOUNDER_CONTEXT.

**Founder-Idea Fit Questions:**

Follow the **Fit Question Guidance** in `{SKILL_DIR}/references/founder.md`. Generate 2-4 dual-purpose questions about the founder's connection to THIS specific idea. Present all questions in a single `ask-user` call. Store all question-answer pairs as FOUNDER_FIT_ANSWERS.

**Optional FOUNDER.md Update:**

Follow the **Profile Update Rules** in `{SKILL_DIR}/references/founder.md`. Review the fit Q&A answers for new persistent attributes. If found, present update options with `ask-user` and append selected items to FOUNDER.md.

### Step 4: Spawn 14 evaluators in parallel

#### Step 4a: Research sync gate

Before constructing evaluator prompts, verify that `{RUN_DIR}/research.json` exists and is well-formed JSON. `ti-researcher` was started at Stage 1 Lane A as a background spawn; this is the single point in the pipeline where the orchestrator awaits its output.

Probe the file with this shell command:

```bash
if [ -f "{RUN_DIR}/research.json" ]; then
  uv run --no-project python -c "import json,sys; json.load(open('{RUN_DIR}/research.json')); print('ready')" 2>/dev/null || echo "invalid"
else
  echo "waiting"
fi
```

(Substitute the actual `{RUN_DIR}` path captured at Stage 0 Step 3 before running the command.)

Three possible results:

- **`ready`** — The file exists and is valid JSON. Read `{RUN_DIR}/research.json` and inspect the top-level `available` field.
  - If `available` is `true`: Proceed to the Pre-Spawn Context Isolation Check below.
  - If `available` is `false`: Jump to **Step 4a-fail: Research failure handler** below.

- **`waiting`** — The file does not exist yet. Research is still in flight.
  - **If this is the first `waiting` result** (i.e., you have not yet shown a wait message during this Step 4a invocation), display to the founder:

    > Research still running — waiting before spawning evaluators…

  - Re-run the same probe. Continue looping until the result is `ready` or `invalid`. **Do NOT re-display the status message** on subsequent loop iterations — show it once, not per probe.
  - **There is no timeout on this loop.** `ti-researcher`'s turn budget (set in its spawn preamble, see Subagent Spawn Convention) is expected to bound its run; the orchestrator trusts that budget rather than layering a second timeout. If research genuinely never returns, the founder can abort with Ctrl+C and re-run `/tweakidea evaluate`.

- **`invalid`** — The file exists but failed JSON parsing (corruption, partial write, or crashed spawn). Overwrite `{RUN_DIR}/research.json` with the fallback:

  ```json
  {"available": false, "reason": "research.json failed JSON validation or was missing after background spawn returned"}
  ```

  Then jump to **Step 4a-fail: Research failure handler** below.

The orchestrator does NOT parse markdown from research.json, does NOT extract clusters by regex, does NOT trim sections. The file IS the interface — each `ti-evaluator` spawn reads it itself once research is confirmed available.

#### Step 4a-fail: Research failure handler

Triggered from **Step 4a** when either (a) `research.json` contains `{"available": false, ...}`, or (b) the `invalid` branch wrote the fallback after a JSON parse failure. This is the **only** point in the pipeline where research failure is surfaced to the founder — do not display research errors during Lane B (hypothesis confirmation) or Stage 2 Steps 1–3 (founder-fit opt-in, profile, fit Q&A). Failure detection is buffered to this gate per D-07/D-08.

Read `{RUN_DIR}/research.json` and capture the `reason` string. Display to the founder:

> **Research did not complete:** `{reason from research.json}`
>
> The 14 dimension evaluators can still run — they will fall back to founder-asserted and assumed evidence only. What would you like to do?

Use `ask-user` with these three options:

- **"Retry research"** — Re-spawn `ti-researcher` once with the same prompt shape used at Stage 1 Lane A:
  - **model tier:** `fast`
  - **prompt:** `{PREAMBLE:ti-researcher}\n\n<files_to_read>\n- {SKILL_DIR}/assets/schemas/research.json\n</files_to_read>\n\nResearch this startup idea and write your output to {RUN_DIR}/research.json (absolute path).\n\nIDEA:\n\n{IDEA_TEXT}`
  - **background:** no (this retry is synchronous — wait in-line for the result)

  After the retry agent returns, re-run the Step 4a probe. If the result is `ready` AND `available` is `true`, proceed to the Pre-Spawn Context Isolation Check. If the result is `ready` AND `available` is `false`, OR the result is `invalid`, return to Step 4a-fail with the new reason — BUT on this SECOND failure, present only the "Continue without research" and "Abort run" options. Do NOT offer "Retry research" a second time. Single retry only per D-06.

  If the original background `ti-researcher` from Stage 1 is still in flight when the retry spawn completes, its eventual write may overwrite the retry's output; this race is acceptable and produces either the correct successful result or the `invalid` branch, which recurses through this handler. The orchestrator does not attempt to kill the original spawn.

- **"Continue without research"** — Overwrite `{RUN_DIR}/research.json` with:

  ```json
  {"available": false, "reason": "founder chose to continue without research"}
  ```

  Then proceed to the Pre-Spawn Context Isolation Check below. The 14 evaluators will see `available: false` in `research.json` and rely on founder-asserted + assumed evidence only. The normal "research unavailable" banner in `report.md` / `report.html` (rendered by `scripts/render_report.py` from Phase 1) handles the downstream UX — no new banner is needed here.

- **"Abort run"** — Display to the founder:

  > Run directory preserved at `{RUN_DIR}`. Re-run `/tweakidea evaluate` when ready.

  Stop the command without further instructions. Do NOT clean up `{RUN_DIR}` — preserve it for forensics per D-06. Do NOT write a sentinel file; the absence of `numbers.json` and `report.md` in the run directory is its own diagnostic signal.

#### Pre-Spawn Context Isolation Check

Before launching evaluators, validate the Dimension Registry's context routing:

1. Read the Dimension Registry table from EVALUATION.md.
2. Count the number of registry rows where Context Variant = `FOUNDER_EVALUATION_CONTEXT`.
3. Assert the count:
   - **If count == 0:** HALT. Display: "Context isolation error: No dimension is mapped to FOUNDER_EVALUATION_CONTEXT. The Dimension Registry may be corrupted. Evaluation cannot proceed safely." Do NOT spawn any evaluators.
   - **If count > 1:** HALT. Display: "Context isolation error: [count] dimensions are mapped to FOUNDER_EVALUATION_CONTEXT -- only Founder-Market Fit should receive founder data. Affected dimensions: [list their Names]. Evaluation cannot proceed safely." Do NOT spawn any evaluators.
   - **If count == 1:** Log: "Context routing validated: [Name of matching dimension] receives FOUNDER_EVALUATION_CONTEXT; remaining dimensions receive EVALUATION_CONTEXT." Proceed.

#### Evaluator Prompt Construction

Keep evaluator prompts short. The idea, the founder-confirmed hypotheses, and the research are already on disk, so evaluators read them as files. Do NOT paste IDEA_TEXT, hypotheses, or research content into the prompts. For each dimension, construct the evaluator prompt with this exact structure (EVALUATION_CONTEXT):

```
<files_to_read>
- {SKILL_DIR}/references/scoring/dimensions/{slug}.md
- {SKILL_DIR}/assets/schemas/dimension-evaluation.json
- {RUN_DIR}/idea.json
- {RUN_DIR}/assumptions.json
- {RUN_DIR}/research.json
</files_to_read>

Output: {RUN_DIR}/dimensions/{slug}.json
Dimension: {Name}
Research cluster: {research cluster from the Dimension Registry}
```

**FOUNDER_EVALUATION_CONTEXT (Founder-Market Fit only):** the same prompt, followed by:

```
## Founder Profile

{FOUNDER_CONTEXT}

## Founder-Idea Fit Answers

{FOUNDER_FIT_ANSWERS as question/answer pairs}
```

#### Context Routing Rule (CRITICAL)

- **Founder-Market Fit** dimension: inject FOUNDER_CONTEXT and FOUNDER_FIT_ANSWERS into the prompt
- **All other 13 dimensions**: do NOT inject founder profile data
- **If FOUNDER_SESSION_SKIPPED is true**: send EVALUATION_CONTEXT for all 14 dimensions (no Founder Profile or Fit Answers sections)

#### Agent Calls

Start all 14 evaluator spawns in parallel (see `parallel-spawn` in `runtime.md`; without it, spawn them one after another). Each spawn uses:

- **model tier:** `fast`
- **prompt:** `{PREAMBLE:ti-evaluator}` followed by a blank line and the prompt constructed above (with RUN_DIR, SKILL_DIR, slug, Name, and research cluster interpolated)
- **background:** no (the orchestrator needs the collection to complete before Stage 3a)

### Step 3: Wait for all 14 evaluators to return

After all 14 evaluator spawns complete, proceed to Stage 3a. **Do NOT parse evaluator return values. Do NOT extract text from evaluator output. Do NOT compute tier counts. Do NOT strip rubric markers.** `scripts/compute.py` handles all of that deterministically.

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

Run the deterministic aggregator:

```bash
uv run "{TWEAKIDEA_SCRIPTS_ROOT}/compute.py" "{RUN_DIR}"
```

Capture stderr. If the command exit code is non-zero, display the stderr content to the founder as an error and abort the run. If exit code is zero, any stderr lines are non-fatal warnings (e.g., one dimension failed validation) -- display them to the founder as info but continue.

After this step, `{RUN_DIR}/numbers.json` exists and is schema-valid.

---

## Stage 3b: Narrative

Spawn ti-narrative to author the 3 prose JSON files:

- **model tier:** `strong`
- **prompt:** `{PREAMBLE:ti-narrative}\n\nAuthor the cross-dimensional narrative for this evaluation. RUN_DIR={RUN_DIR}. Read numbers.json, dimensions/*.json, assumptions.json, research.json (if available), then write the 3 JSON files per references/agents/ti-narrative.md.`
- **background:** no

After the agent returns, verify that all 3 files exist at `{RUN_DIR}/`:
- `strengths-weaknesses.json`
- `next-steps.json`
- `potential.json`

If any are missing, retry the ti-narrative spawn ONCE with a note about the missing files. If the retry also fails, write minimal-shape placeholder files for the missing ones so Stage 4 can still render a report.

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

List the artifact family:

```bash
ls "{RUN_DIR}/" && ls "{RUN_DIR}/dimensions/"
```

Expected manifest (>= 20 files for a full run):
- version.json, idea.json, hypotheses.json, assumptions.json, research.json, numbers.json, strengths-weaknesses.json, next-steps.json, potential.json, report.md, report.html
- dimensions/*.json (14 files if all evaluators succeeded; fewer or with failed placeholders if partial)

Read `{RUN_DIR}/numbers.json`. Extract `weighted_total`, `verdict_bucket`, and `verdict_label`.

Display to the founder:

```
Evaluation complete -- {N} artifact files in {RUN_DIR}

Weighted Score: {numbers.weighted_total}/5.0 ({numbers.verdict_bucket})
{numbers.verdict_label}

Report:    {RUN_DIR}/report.md
Report:    {RUN_DIR}/report.html
```

If any spawn ran on the session's model because your runtime could not select its tier's model, add one line below the summary: `Note: subagents ran on {model} instead of the tuned fast/strong models; scores may differ from the reference setup.`

### Step 2: Optional browser open

Use `ask-user`: "Open the HTML report in your browser?"

- "Yes" -- `uv run --no-project python -m webbrowser "file://{RUN_DIR}/report.html" >/dev/null 2>&1`
- "No" -- Continue to exit

After the run directory confirmation, add the closing line:

> Run `/tweakidea evaluate` again with a modified idea to re-evaluate, or ask follow-up questions about any dimension.
