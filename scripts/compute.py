# /// script
# requires-python = ">=3.11"
# dependencies = ["jsonschema==4.26.0"]
# ///
"""Read dimension/*.json files + parse EVALUATION.md, produce numbers.json.

Usage: uv run scripts/compute.py <run_dir>

Reads:
    {run_dir}/dimensions/*.json  (14 files per schemas/dimension-evaluation.json)
    skills/ti-scoring/EVALUATION.md  (Dimension Registry table)

Writes:
    {run_dir}/numbers.json  (validated against schemas/numbers.json)

Exit codes:
    0 = success (any number of non-fatal warnings may have been emitted)
    1 = fatal (missing RUN_DIR, all 14 dims failed validation, or output schema violation)
"""
import argparse
import json
import pathlib
import sys

from lib import errors, registry, radar, schema
from jsonschema import ValidationError

# Verdict bucket thresholds (from EVALUATION.md lines 58-63)
VERDICT_THRESHOLDS = [
    (4.0, "GO", "GO — Strong problem, worth pursuing"),
    (3.0, "PIVOT", "PIVOT — Promising, address weak areas"),
    (2.0, "STOP", "STOP — Significant concerns, reconsider"),
    (0.0, "STOP", "STOP — Likely not worth pursuing"),
]


def verdict_for(total: float) -> tuple[str, str]:
    for threshold, bucket, label in VERDICT_THRESHOLDS:
        if total >= threshold:
            return bucket, label
    return "STOP", "STOP — Likely not worth pursuing"


def count_tiers(criteria: list) -> dict:
    """Count evidence tiers across a dimension's criteria array."""
    counts = {"verified": 0, "research": 0, "founder": 0, "assumed": 0}
    for c in criteria:
        t = c.get("tier", "")
        if t == "Verified":
            counts["verified"] += 1
        elif t == "Research-Backed":
            counts["research"] += 1
        elif t == "Founder-Asserted":
            counts["founder"] += 1
        elif t == "Assumed":
            counts["assumed"] += 1
    return counts


def load_dimension(run_dir: pathlib.Path, slug: str):
    """Load + validate one dimension file. Returns dict or None on failure.

    On failure emits non-fatal stderr error and returns None — caller handles
    partial-failure re-normalization.
    """
    fpath = run_dir / "dimensions" / f"{slug}.json"
    if not fpath.exists():
        errors.emit(
            errors.INVALID_DIMENSION,
            str(fpath),
            "no file produced by evaluator",
            f"dimension file missing: {slug}",
        )
        return None
    try:
        inst = json.loads(fpath.read_text())
    except json.JSONDecodeError as e:
        errors.emit(
            errors.INVALID_JSON,
            str(fpath),
            str(e),
            f"malformed JSON in {fpath.name}",
        )
        return None
    try:
        schema.validate(inst, "dimension-evaluation")
    except ValidationError as e:
        errors.from_validation_error(e, str(fpath), non_fatal=True)
        return None
    return inst


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Aggregate dimension JSONs into numbers.json"
    )
    parser.add_argument("run_dir", help="Absolute path to RUN_DIR")
    args = parser.parse_args()

    run_dir = pathlib.Path(args.run_dir).resolve()
    if not run_dir.is_dir():
        errors.die(
            errors.MISSING_FILE,
            str(run_dir),
            "run directory does not exist",
            f"{run_dir} not found",
        )

    # Load registry
    try:
        dims = registry.load_registry()
    except Exception as e:
        errors.die(
            errors.REGISTRY_PARSE_FAIL,
            "skills/ti-scoring/EVALUATION.md",
            str(e),
            f"failed to parse Dimension Registry: {e}",
        )

    # Load + validate each dim file
    dim_results = {}
    for d in dims:
        dim_results[d.slug] = load_dimension(run_dir, d.slug)

    # Count valid dims
    valid_slugs = [d.slug for d in dims if dim_results[d.slug] is not None]
    if len(valid_slugs) == 0:
        errors.die(
            errors.INVALID_DIMENSION,
            str(run_dir),
            "all 14 dimensions failed validation",
            "cannot compute weighted total with zero valid dimensions",
        )

    # Re-normalize weights over valid dims only
    total_valid_weight = sum(d.weight for d in dims if dim_results[d.slug] is not None)

    weighted_total = 0.0
    potential_total = 0.0
    rankings = []
    for d in dims:
        result = dim_results.get(d.slug)
        if result is None:
            rankings.append({
                "dim": d.name,
                "slug": d.slug,
                "score": None,
                "potential": None,
                "weighted_score": 0.0,
                "tier_counts": {"verified": 0, "research": 0, "founder": 0, "assumed": 0},
                "failed": True,
            })
            continue
        norm_w = d.weight / total_valid_weight
        score = result["score"]
        potential = result["potential"]
        weighted_total += score * norm_w
        potential_total += potential * norm_w
        rankings.append({
            "dim": d.name,
            "slug": d.slug,
            "score": score,
            "potential": potential,
            "weighted_score": round(score * norm_w, 3),
            "tier_counts": count_tiers(result.get("criteria", [])),
        })

    weighted_total = round(weighted_total, 1)
    potential_total = round(potential_total, 1)

    bucket, label = verdict_for(weighted_total)

    # Dealbreakers: any valid dim with score == 1
    dealbreaker_dims = [
        d.slug for d in dims
        if dim_results.get(d.slug) is not None
        and dim_results[d.slug]["score"] == 1
    ]

    # Aggregate evidence quality across all valid criteria
    tier_totals = {"verified": 0, "research": 0, "founder": 0, "assumed": 0}
    total_criteria = 0
    for slug in valid_slugs:
        for c in dim_results[slug].get("criteria", []):
            t = c.get("tier")
            if t == "Verified":
                tier_totals["verified"] += 1
            elif t == "Research-Backed":
                tier_totals["research"] += 1
            elif t == "Founder-Asserted":
                tier_totals["founder"] += 1
            elif t == "Assumed":
                tier_totals["assumed"] += 1
            total_criteria += 1
    denom = max(total_criteria, 1)
    evidence_quality = {
        "verified_pct": round(tier_totals["verified"] / denom * 100),
        "research_pct": round(tier_totals["research"] / denom * 100),
        "founder_pct": round(tier_totals["founder"] / denom * 100),
        "assumed_pct": round(tier_totals["assumed"] / denom * 100),
    }

    # Assumption impact math
    assumption_impact_math = []
    for d in dims:
        result = dim_results.get(d.slug)
        if result is None or result["potential"] <= result["score"]:
            continue
        norm_w = d.weight / total_valid_weight
        for a in result.get("assumptions_relied_on", []):
            if a.get("status") == "UNCONFIRMED":
                assumption_impact_math.append({
                    "assumption_text": a["text"],
                    "dim": d.name,
                    "score_delta": result["potential"] - result["score"],
                    "weighted_uplift": round(
                        (result["potential"] - result["score"]) * norm_w, 2
                    ),
                })

    # Radar SVG — use raw scores (0 for failed dims) in registry index order
    scores_in_order = [
        (dim_results[d.slug]["score"] if dim_results.get(d.slug) else 0)
        for d in dims
    ]
    labels = [d.name for d in dims]
    radar_svg = radar.build_svg(scores_in_order, labels)

    numbers = {
        "weighted_total": weighted_total,
        "potential_total": potential_total,
        "verdict_bucket": bucket,
        "verdict_label": label,
        "rankings": rankings,
        "dealbreaker_dims": dealbreaker_dims,
        "evidence_quality": evidence_quality,
        "assumption_impact_math": assumption_impact_math,
        "radar_svg": radar_svg,
    }

    # Validate before write
    try:
        schema.validate(numbers, "numbers")
    except ValidationError as e:
        errors.die(
            errors.SCHEMA_VIOLATION,
            "numbers.json",
            str(e)[:200],
            "computed numbers.json does not match schema — this is a compute.py bug",
        )

    out_path = run_dir / "numbers.json"
    out_path.write_text(json.dumps(numbers, indent=2, ensure_ascii=False) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
