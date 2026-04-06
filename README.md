# TweakIdea

A Claude Code skillset that evaluates whether a startup problem is worth solving. It runs 14 independent subagents in parallel -- one per problem dimension -- then merges results into a weighted scorecard with assumption tracking and evidence tiers.

## How It Works

1. **Capture** -- Describe your startup idea (inline, from a file, or interactively)
2. **Prepare** -- In parallel: extract testable hypotheses, run web research on competitors/market/users, load your founder profile
3. **Question** -- Confirm which hypotheses you can verify; answer 2-4 founder-idea fit questions
4. **Evaluate** -- 14 independent evaluators (Sonnet) score your idea on separate dimensions, each with targeted web searches
5. **Merge** -- A synthesis agent (Opus) produces a weighted scorecard with verdict, strengths, weaknesses, and next steps
6. **Store** -- Report displayed inline and saved to `~/.tweakidea/runs/`

The pipeline optionally asks if you want an HTML report alongside the markdown scorecard.

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

## Installation

```bash
git clone https://github.com/eph5xx/tweakidea.git
cd tweakidea
claude
```

Type `/tweak:` and you should see `evaluate` in the autocomplete.

## Quickstart

```
/tweak:evaluate "A mobile app that lets restaurants sell unsold food at a discount 30 minutes before closing"
```

First run takes 5-10 minutes (includes founder profile creation). Subsequent runs are faster.

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

MIT -- see [LICENSE](LICENSE) for details.
