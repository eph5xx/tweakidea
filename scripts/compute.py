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


TIER_KEYS = ("both_confirmed", "research_only", "founder_only", "assumed")


def count_tiers(criteria: list) -> dict:
    """Count evidence tiers across a dimension's criteria array."""
    counts = {k: 0 for k in TIER_KEYS}
    for c in criteria:
        t = c.get("tier", "")
        if t in counts:
            counts[t] += 1
    return counts


def points_from_counts(counts: dict) -> int:
    """Weighted evidence points: both_confirmed=3, research_only=2, founder_only=1, assumed=0."""
    return (
        3 * counts["both_confirmed"]
        + 2 * counts["research_only"]
        + 1 * counts["founder_only"]
    )


def grade_from_points(points: int) -> str:
    """Map weighted evidence points to a letter grade."""
    if points >= 24:
        return "A+"
    if points >= 21:
        return "A"
    if points >= 18:
        return "A-"
    if points >= 15:
        return "B+"
    if points >= 12:
        return "B"
    if points >= 9:
        return "B-"
    if points >= 6:
        return "C"
    if points >= 3:
        return "D"
    return "F"


def grade_from_counts(counts: dict) -> str:
    return grade_from_points(points_from_counts(counts))


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
    total_points = 0
    rankings = []
    for d in dims:
        result = dim_results.get(d.slug)
        if result is None:
            empty_counts = {k: 0 for k in TIER_KEYS}
            rankings.append({
                "dim": d.name,
                "slug": d.slug,
                "score": None,
                "potential": None,
                "weighted_score": 0.0,
                "evidence_strength": {**empty_counts, "grade": "F"},
                "failed": True,
            })
            continue
        norm_w = d.weight / total_valid_weight
        score = result["score"]
        potential = result["potential"]
        weighted_total += score * norm_w
        potential_total += potential * norm_w
        counts = count_tiers(result.get("criteria", []))
        points = points_from_counts(counts)
        total_points += points
        rankings.append({
            "dim": d.name,
            "slug": d.slug,
            "score": score,
            "potential": potential,
            "weighted_score": round(score * norm_w, 3),
            "evidence_strength": {**counts, "grade": grade_from_points(points)},
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

    # Overall grade: average weighted-points across valid dims, then grade.
    avg_points = round(total_points / len(valid_slugs))
    overall_grade = grade_from_points(avg_points)

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
        "overall_grade": overall_grade,
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
