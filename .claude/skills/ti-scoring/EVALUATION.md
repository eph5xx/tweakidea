# Startup Problem Evaluation Dimensions

> Per-dimension signal tables and rubrics are in the `dimensions/` subdirectory. Each evaluator agent receives its assigned dimension file via prompt injection.

---

## Scoring Algorithm

Score = highest level where ALL criteria pass. If any criterion at a level fails, score drops to the previous level.

For criteria depending on an [UNCONFIRMED] hypothesis: mark as CONDITIONAL. CONDITIONAL criteria are treated as FAIL for actual score, PASS for potential score.

## Evidence Tier Classification

| Condition | Tier |
|-----------|------|
| Founder confirmed AND research supports | Verified |
| Research supports, founder did not confirm | Research-Backed |
| Founder confirmed, no research support | Founder-Asserted |
| Inferred from reasoning, no direct support | Assumed |

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

## Scoring Template

Rate each dimension 1-5, weight by importance for your context:

| Dimension | Score (1-5) | Weight | Weighted Score |
|-----------|-------------|--------|----------------|
| Pain Intensity | | 12% | |
| Urgency | | 8% | |
| Frequency | | 8% | |
| Willingness to Pay | | 12% | |
| Mandatory Nature | | 2% | |
| Market Size | | 8% | |
| Market Growth | | 4% | |
| Solution Gap | | 12% | |
| Founder-Market Fit | | 12% | |
| Defensibility | | 8% | |
| Incumbent Indifference | | 2% | |
| Scalability | | 4% | |
| Clarity of Target Customer | | 4% | |
| Behavior Change Required | | 4% | |
| **Total** | | **100%** | |

**Interpretation:**
- 4.0-5.0: GO -- Strong problem, worth pursuing
- 3.0-3.99: PIVOT -- Promising, address weak areas
- 2.0-2.99: STOP -- Significant concerns, reconsider
- 1.0-1.99: STOP -- Likely not worth pursuing
