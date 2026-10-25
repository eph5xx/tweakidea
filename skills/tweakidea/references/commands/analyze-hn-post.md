## Purpose

You analyze Hacker News discussions to identify technology shifts and product opportunities. You fetch the full post (article + comments), identify what has changed in capability, cost, or access, and surface specific product ideas grounded in evidence from the discussion.

**Critical: Clean context.** Each invocation starts fresh. Results are saved to `~/.tweakidea/hn/hn-{item_id}/`.

---

## Phase 1: Capture Input

1. Extract the numeric item ID from `ARGS`:
   - If it contains `id=`, extract the number after it
   - If it is purely numeric, use it directly
   - If `ARGS` is empty, ask in chat: "Paste a Hacker News URL or item ID to analyze."

2. Resolve the home directory:
   ```bash
   echo $HOME
   ```
   Store this as HOME_DIR.

3. Set OUT_DIR = `{HOME_DIR}/.tweakidea/hn/hn-{item_id}`

4. Create the output directory:
   ```bash
   mkdir -p {OUT_DIR}
   ```

---

## Phase 2: Fetch HN Data

### Pre-check: uv

Run:
```bash
which uv
```

If this fails (exit code non-zero), tell the user:

> The `/tweakidea analyze-hn-post` command requires `uv` (Python package runner).
>
> Install it:
> - `curl -LsSf https://astral.sh/uv/install.sh | sh`
> - Or: `brew install uv`

Then stop. Do not continue.

### Locate the script

The `hnparse.py` script ships in the skill's `scripts/` folder at `{SKILL_DIR}/scripts/hnparse.py` (usage notes in `{SKILL_DIR}/references/hn.md`). Run `ls` to check it exists and store it as SCRIPT_PATH. If it does not exist, tell the user: "Cannot find hnparse.py. Please reinstall the tweakidea skill." and stop.

### Run the script

```bash
uv run {SCRIPT_PATH} '{item_id_or_url}' -o '{OUT_DIR}'
```

The last line of stdout is the absolute path to `content.md`. Capture it as CONTENT_PATH. All progress messages are on stderr.

If the script fails, inform the user and stop.

---

## Phase 3: Read All Content

1. Read CONTENT_PATH in full, starting at line 1.

2. If your file reader returns the file in chunks, keep reading the next chunk until you reach the end of the file. Do not stop after the first chunk.

3. You MUST read ALL content before starting analysis. Do not begin writing the report after only the first chunk. Late comments often contain the strongest practitioner signals -- people building things, reporting real-world experience, citing costs, or describing pain points.

4. While reading, pay attention to:
   - What capabilities are new or newly accessible?
   - What cost or access thresholds have shifted?
   - What are commenters building, struggling with, or requesting?
   - What existing workflows are being disrupted?
   - Where do commenters identify gaps between what is now possible and what products exist?
   - Specific data points: prices, timelines, user counts, adoption rates

---

## Phase 4: Analyze

### What counts as a technology shift

A technology shift is a specific change in capability, cost structure, or access model that makes something possible or economical that was not before. It must be grounded in evidence from the article and comments, not speculation.

Good: "AI models can now find zero-day vulnerabilities at commodity cost -- $20K vs $300K/yr for a human researcher"
Bad: "AI is getting better at coding"

Good: "OSS maintainers went from 2-3 vuln reports/week to 5-10/day, all real and high-quality"
Bad: "Security is becoming more important"

### What counts as a product opportunity

Each opportunity must name: the specific product, who it serves, and why the timing is right. Ground it in evidence from the discussion -- cite specific comments, quotes, or data points where relevant.

Good: "Vulnerability triage platform for OSS maintainers -- curl's Daniel Stenberg is spending hours/day on incoming reports, Linux kernel list went from 3/week to 10/day. No tooling exists for this new volume."
Bad: "A platform for security stuff"

### What counts as a topical opportunity

Same test as a product opportunity, but "why now" comes from the topic or discussion (pain points, workflows, requests, domain dynamics) rather than a recent capability, cost, or access change.

Good (topical): "Peer-support platform for parents of kids with rare conditions -- commenters describe spending months finding each other on scattered Facebook groups and Reddit threads; no domain-specific hub exists."

### Analysis steps

1. Identify **up to 3** technology shifts evidenced by the article and comments. Each shift must satisfy ALL of:
   - It describes a specific capability, cost reduction, or access change (not a vague trend)
   - There is evidence from the article or comments that this shift is real and recent
   - It creates at least one concrete product opportunity that did not exist before

2. For each shift, identify **up to 3** product opportunities. Every opportunity must pass this test: would a competent engineer reading this know what to build and for whom?

3. Separately, identify 0 or 1 topical opportunities section with **up to 3** topical opportunities. Include it only when the discussion surfaces genuinely interesting product ideas not explained by any tech shift.

4. Do NOT pad with weak opportunities. Omit a shift or the topical section entirely if nothing qualifies.

---

## Phase 5: Write Shifts Report

Write the analysis to `{OUT_DIR}/shifts.md` using this exact format:

```
# Product Opportunities from HN #{item_id} -- {Post Title}

Source: https://news.ycombinator.com/item?id={item_id}

---

## 1. [Technology shift title]

**The shift:** [What changed -- the capability, cost structure, or access model that is new. Be specific and cite evidence.]

**Why now, not earlier?** [What specific technical threshold was crossed that makes this viable now, not 2 years ago?]

**Product opportunities:** (max 3 bullets)
- **[Opportunity name].** [Description: what it is, who it serves, why the timing is right. Ground this in evidence from the discussion -- quote or cite specific commenters where relevant.]
- **[Another opportunity].** [...]

---

[Repeat for each shift]

---

## Topical opportunities

[One short paragraph on why this topic is an interesting product space. Ground in the discussion.]

**Opportunities:** (max 3 bullets)
- **[Opportunity name].** [Description: what it is, who it serves, why it is interesting now. Cite commenters where relevant.]
- **[Another opportunity].** [...]

---

## Meta-pattern

[One paragraph tying the shifts (and topical opportunities, if any) together. What common dynamic connects them? What does this suggest about where value is migrating? This should be a genuine insight, not a generic summary.]
```

Omit the `## Topical opportunities` section entirely if Phase 4 identified none.

### Show the report in chat

After writing `shifts.md`, print to the user:

1. A clickable markdown link to the file: `[shifts.md]({OUT_DIR}/shifts.md)`
2. The full contents of `shifts.md` pasted directly into chat (verbatim, no summarization).

This gives the user the context they need before answering the Phase 6 confirmation questions.

---

## Phase 6: Confirm Opportunities

Ask in chat with every product opportunity, grouped under a heading per shift (plus `Topical`, if present) and numbered continuously across groups:

```
Which opportunities do you want to develop into full ideas?

[Shift 1 Title]
1. [Opportunity name]: [one-sentence summary]
2. [Opportunity name]: [one-sentence summary]

[Shift 2 Title]
3. [Opportunity name]: [one-sentence summary]

Topical
4. [Opportunity name]: [one-sentence summary]

Reply with the numbers to develop (like "1, 3"), or "none".
```

The picked numbers are the confirmed opportunities. If none, skip to Phase 7.

---

## Phase 7: Write Ideas and Close

### Write confirmed ideas

If the user confirmed any opportunities, write them to `{OUT_DIR}/ideas.md` using this exact format:

```
# Product Ideas from HN #{item_id} -- {Post Title}

Source: https://news.ycombinator.com/item?id={item_id}

---

## 1. [Idea Title]

**Problem:** [Problem statement grounded in evidence from the article and comments. Cite specific commenters, data points, and quotes. Explain the pain point and what the current alternatives are. Soft limit: 6-10 sentences.]

**Solution:** [Solution: what the product is, how it works, pricing model, go-to-market angle, and why the timing is right. Include competitive positioning and evidence from the discussion. Soft limit: 6-10 sentences.]

**Target User:** [Who the product is for: segment, role, firmographics or demographics, and where they gather. Ground it in evidence from the thread (which commenters fit this profile and what they said). Soft limit: 2-4 sentences.]

---
```

Number ideas sequentially starting from 1, regardless of which shift, topical section, or opportunity position they came from.

### Close

Tell the user, using clickable markdown links:
- `[shifts.md]({OUT_DIR}/shifts.md)`
- `[ideas.md]({OUT_DIR}/ideas.md)` (if created)
- Counts: shifts identified, topical opportunities (if any), total opportunities presented, confirmed ideas
- Do NOT summarize or repeat the report contents -- the user has already seen shifts.md in chat and can open ideas.md.

Then suggest:

> To evaluate any of these ideas, run `/tweakidea evaluate` and paste the Problem + Solution + Target User text from ideas.md.
