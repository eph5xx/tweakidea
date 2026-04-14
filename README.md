# TweakIdea

A Claude Code skillset that helps founders evaluate startup problems and discover product opportunities. Four commands: **evaluate** an idea across 14 weighted dimensions, **suggest** new ideas from Hacker News discussions, **list** your accumulated runs and profiles, or **show** any saved artifact.

## Evaluate: `/tweak:evaluate`

Runs 14 independent subagents in parallel — one per problem dimension — then merges results into a weighted scorecard with assumption tracking and evidence tiers.

1. **Capture** — Describe your startup idea (inline, from a file, or interactively)
2. **Prepare** — Two parallel tracks: extract hypotheses + web research in background; interactive founder profile + fit questions
3. **Assemble** — Display research brief, confirm hypotheses, build evaluation context
4. **Evaluate** — 14 independent evaluators (Sonnet) score your idea on separate dimensions, each with targeted web searches
5. **Merge** — A synthesis agent (Opus) produces a weighted scorecard with verdict, strengths, weaknesses, and next steps
6. **Confirm** — Report displayed inline and saved to `~/.tweakidea/runs/`

The pipeline optionally asks if you want an HTML report alongside the markdown scorecard.

## Suggest: `/tweak:suggest-from-hn`

Fetches a Hacker News post (article + full comment tree), identifies technology shifts, and surfaces product opportunities grounded in evidence from the discussion.

1. **Fetch** — Download the HN post, linked article, and all comments
2. **Analyze** — Identify 3-6 technology shifts (specific changes in capability, cost, or access)
3. **Suggest** — Surface 1-3 product opportunities per shift, each with a named product, target customer, and timing rationale
4. **Confirm** — Select which opportunities to develop into full ideas
5. **Write** — Detailed problem/solution writeups saved to `~/.tweakidea/hn/hn-{id}/`

Confirmed ideas can be fed directly into `/tweak:evaluate` for a full 14-dimension assessment.

## List: `/tweak:list`

Lists what you have accumulated under `~/.tweakidea/`: evaluation runs, HN analyses, and founder profiles. Read-only.

- `/tweak:list` — default (all categories, 5 most recent per section)
- `/tweak:list runs 20` — the 20 most recent evaluation runs
- `/tweak:list best ideas` — runs ranked by weighted score
- `/tweak:list hn` — just HN analyses

Arguments are a free-form hint; use whatever phrasing feels natural. Use `/tweak:show` to open any item.

## Show: `/tweak:show`

Opens any artifact under `~/.tweakidea/` by timestamp, keyword, HN id, founder name, or natural query.

- `/tweak:show latest` — most recent evaluation run
- `/tweak:show 20260412-143022` — a specific run by timestamp
- `/tweak:show restaurant food waste` — keyword match on idea text
- `/tweak:show hn 43374458` — an HN analysis by id
- `/tweak:show best ideas` — ranked query over saved runs

Run reports open in the browser; HN and founder artifacts are inlined.

## The 14 Dimensions

| Weight | Dimension | What it measures |
|--------|-----------|-----------------|
| 12% | Pain Intensity | Painkiller vs. vitamin vs. candy |
| 12% | Willingness to Pay | Budget exists and buyer is reachable |
| 12% | Solution Gap | Why this hasn't been solved yet |
| 12% | Founder-Market Fit | Founder's domain, network, capabilities |
| 8% | Urgency | Forcing functions and active revenue loss |
| 8% | Frequency | How often the problem occurs |
| 8% | Market Size | TAM/SAM/SOM viability |
| 8% | Defensibility | Moats: network effects, switching costs, data |
| 4% | Market Growth | Sector CAGR trajectory |
| 4% | Scalability | Margins, self-serve, automation potential |
| 4% | Clarity of Target Customer | ICP specificity and findability |
| 4% | Behavior Change Required | Drop-in (5) vs. massive change (1) |
| 2% | Mandatory Nature | Regulatory or contractual forcing |
| 2% | Incumbent Indifference | Risk of being in the kill zone |

## Prerequisites

- [Claude Code](https://claude.ai/download) installed
- Model access: **Claude Sonnet** (evaluators + researcher) and **Claude Opus** (merge agent)
- [`uv`](https://docs.astral.sh/uv/) — needed by `/tweak:suggest-from-hn` for Python script execution. Install: `curl -LsSf https://astral.sh/uv/install.sh | sh` or `brew install uv`

## Installation

```bash
npx tweakidea
```

The installer prompts for global (`~/.claude`) or local (`./.claude`) placement.

To uninstall:

```bash
npx tweakidea -u
```

After install, open Claude Code and type `/tweak:` — you should see `evaluate`, `suggest-from-hn`, `list`, and `show` in the autocomplete.

For better article extraction from JS-heavy sites, optionally run `uv run playwright install chromium` once. Without it, the script falls back to plain HTTP which works fine for most sites.

## Quickstart

**Evaluate an idea:**

```
/tweak:evaluate "A mobile app that lets restaurants sell unsold food at a discount 30 minutes before closing"
```

First run takes 30-40 minutes (includes founder profile creation). Subsequent runs are faster.

**Discover opportunities from HN:**

```
/tweak:suggest-from-hn https://news.ycombinator.com/item?id=43374458
```

## Example Output

```
PIVOT -- Promising, address weak areas | Weighted Score: 3.4/5.0 | Potential: 4.0/5.0

| Dimension              | Score | Potential | Evidence        | Key Finding                                    |
|------------------------|-------|-----------|-----------------|------------------------------------------------|
| Pain Intensity         | 4/5   | 4/5       | 2V 3R 1F 0A     | Clear pain with existing demand signals        |
| Willingness to Pay     | 3/5   | 4/5*      | 0V 1R 2F 2A     | Budget exists but price sensitivity unknown    |
| Solution Gap           | 2/5   | 2/5       | 1V 4R 0F 1A     | Crowded market with strong incumbents          |
| Founder-Market Fit     | 4/5   | 4/5       | 0V 0R 3F 1A     | Strong domain expertise and network            |
| ...                    | ...   | ...       | ...             | ...                                            |

V=Verified R=Research-Backed F=Founder-Asserted A=Assumed

Evidence Quality: 8% Verified | 32% Research-Backed | 35% Founder-Asserted | 25% Assumed

### Top 3 Strengths
1. **Pain Intensity** (4/5): Active workarounds and food waste regulations driving urgency
2. **Founder-Market Fit** (4/5): 6 years in restaurant operations with direct customer access
3. **Urgency** (4/5): Perishable inventory creates daily forcing function

### Top 3 Weaknesses
1. **Solution Gap** (2/5): Too Good To Go, Flashfood already well-established
2. **Defensibility** (2/5): Low switching costs, no network effects at launch
3. **Incumbent Indifference** (2/5): Incumbents actively competing in this space

### Next Steps
1. Interview 10 restaurant owners about switching costs from Too Good To Go -- **Solution Gap**: 2/5 -> 3/5 (+0.12)
2. Test pricing with 5 restaurants to validate willingness to pay -- **Willingness to Pay**: 3/5 -> 4/5 (+0.12)
3. Identify a defensible niche incumbents ignore -- **Defensibility**: 2/5 -> 3/5 (+0.08)
```

Full report includes all 14 dimensions with rubric assessments, assumption tracking, and evidence citations.

## License

MIT — see [LICENSE](LICENSE) for details.
