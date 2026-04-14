# Startup Problem Evaluation Dimensions

> Per-dimension signal tables and rubrics are in the `dimensions/` subdirectory. Each evaluator agent receives its assigned dimension file via prompt injection.

---

## Scoring Algorithm

Score = highest level where ALL criteria pass. If any criterion at a level fails, score drops to the previous level.

For criteria depending on an [UNCONFIRMED] hypothesis: mark as CONDITIONAL. CONDITIONAL criteria are treated as FAIL for actual score, PASS for potential score.

## Evidence Tier Classification

| Condition | Tier |
|-----------|------|
| Founder confirmed AND research supports | `both_confirmed` |
| Research supports, founder did not confirm | `research_only` |
| Founder confirmed, no research support | `founder_only` |
| Inferred from reasoning, no direct support | `assumed` |

Counts feed `scripts/compute.py` which maps each dimension to a letter grade (A+/A/A−/B+/B/B−/C/D/F) via `points = 3·both_confirmed + 2·research_only + 1·founder_only`. See `agents/ti-evaluator.md` for the canonical classification rules.

---

## Problem Type Matrix

Categorize problems by intensity vs. breadth:

| Type | Description | Strategy |
|------|-------------|----------|
| **Type 1**: Many people, intense pain | Mass-market painkiller | Scale fast, network effects |
| **Type 2**: Many people, mild pain | Mass-market vitamin | Elevate urgency, make seamless |
| **Type 3**: Few people, intense pain | Niche painkiller | Deep value, high price, strong loyalty |
| **Type 4**: Few people, mild pain | Avoid | Hard to monetize, hard to find customers |

---

## Dimension Registry

> **Canonical source of truth.** All dimension metadata lives in this table. Agents receive registry values via orchestrator prompt injection at spawn time (D-06). Do not duplicate this data elsewhere.

| # | Name | Weight | File Slug | Output Filename | Research Cluster | Context Variant |
|---|------|--------|-----------|-----------------|------------------|-----------------|
| 01 | Pain Intensity | 12% | pain-intensity | 01-pain-intensity.md | USER_CLUSTER | EVALUATION_CONTEXT |
| 02 | Willingness to Pay | 12% | willingness-to-pay | 02-willingness-to-pay.md | USER_CLUSTER | EVALUATION_CONTEXT |
| 03 | Solution Gap | 12% | solution-gap | 03-solution-gap.md | COMPETITIVE_CLUSTER | EVALUATION_CONTEXT |
| 04 | Founder-Market Fit | 12% | founder-market-fit | 04-founder-market-fit.md | — | FOUNDER_EVALUATION_CONTEXT |
| 05 | Urgency | 8% | urgency | 05-urgency.md | USER_CLUSTER | EVALUATION_CONTEXT |
| 06 | Frequency | 8% | frequency | 06-frequency.md | — | EVALUATION_CONTEXT |
| 07 | Market Size | 8% | market-size | 07-market-size.md | MARKET_CLUSTER | EVALUATION_CONTEXT |
| 08 | Defensibility | 8% | defensibility | 08-defensibility.md | COMPETITIVE_CLUSTER | EVALUATION_CONTEXT |
| 09 | Market Growth | 4% | market-growth | 09-market-growth.md | MARKET_CLUSTER | EVALUATION_CONTEXT |
| 10 | Scalability | 4% | scalability | 10-scalability.md | — | EVALUATION_CONTEXT |
| 11 | Clarity of Target Customer | 4% | clarity-of-target-customer | 11-clarity-of-target-customer.md | — | EVALUATION_CONTEXT |
| 12 | Behavior Change Required | 4% | behavior-change-required | 12-behavior-change-required.md | — | EVALUATION_CONTEXT |
| 13 | Mandatory Nature | 2% | mandatory-nature | 13-mandatory-nature.md | — | EVALUATION_CONTEXT |
| 14 | Incumbent Indifference | 2% | incumbent-indifference | 14-incumbent-indifference.md | COMPETITIVE_CLUSTER | EVALUATION_CONTEXT |

## Interpretation

- 4.0-5.0: GO -- Strong problem, worth pursuing
- 3.0-3.99: PIVOT -- Promising, address weak areas
- 2.0-2.99: STOP -- Significant concerns, reconsider
- 1.0-1.99: STOP -- Likely not worth pursuing
