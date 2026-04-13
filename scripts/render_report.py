# /// script
# requires-python = ">=3.11"
# dependencies = ["jsonschema==4.26.0", "jinja2==3.1.6"]
# ///
"""Read full artifact family, render report.md + report.html via Jinja2.

Usage: uv run scripts/render_report.py <run_dir> [--timestamp YYYY-MM-DD]

Writes exactly two files to {RUN_DIR}: report.md and report.html.
No other markdown or HTML files are produced (per RPRT-01).
"""
import argparse
import json
import pathlib
import sys
from datetime import datetime, timezone

from jinja2 import Environment, FileSystemLoader, select_autoescape
from jinja2.exceptions import TemplateError
from jsonschema import ValidationError

from lib import errors, schema

# Locate skills/ti-report relative to this script
_REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
TI_REPORT_DIR = _REPO_ROOT / "skills" / "ti-report"


def load(run_dir, name, schema_name, required=True):
    p = run_dir / name
    if not p.exists():
        if required:
            errors.die(
                errors.MISSING_FILE,
                str(p),
                f"expected {name}",
                f"{name} not found in run directory",
            )
        return None
    try:
        inst = json.loads(p.read_text())
    except json.JSONDecodeError as e:
        errors.die(
            errors.INVALID_JSON,
            str(p),
            str(e),
            f"{name} is not valid JSON",
        )
    try:
        schema.validate(inst, schema_name)
    except ValidationError as e:
        errors.from_validation_error(e, str(p), non_fatal=False)
    return inst


def load_dimensions(run_dir):
    """Load dimensions/*.json into a dict keyed by slug."""
    dims_dir = run_dir / "dimensions"
    result = {}
    if not dims_dir.is_dir():
        return result
    for p in dims_dir.glob("*.json"):
        try:
            inst = json.loads(p.read_text())
            # Skip error placeholders (failed dim files)
            if inst.get("failed"):
                continue
            result[p.stem] = inst
        except json.JSONDecodeError:
            continue
    return result


def build_context(run_dir, timestamp):
    numbers = load(run_dir, "numbers.json", "numbers")
    return {
        "timestamp": timestamp,
        "idea": load(run_dir, "idea.json", "idea"),
        "hypotheses": load(run_dir, "hypotheses.json", "hypotheses", required=False),
        "assumptions": load(run_dir, "assumptions.json", "assumptions", required=False),
        "research": load(run_dir, "research.json", "research", required=False),
        "numbers": numbers,
        "verdict": load(run_dir, "verdict.json", "verdict"),
        "strengths_weaknesses": load(run_dir, "strengths-weaknesses.json", "strengths-weaknesses"),
        "next_steps": load(run_dir, "next-steps.json", "next-steps"),
        "dealbreakers": load(run_dir, "dealbreakers.json", "dealbreakers"),
        "potential": load(run_dir, "potential.json", "potential"),
        "version": load(run_dir, "version.json", "version"),
        "dimensions": load_dimensions(run_dir),
        "radar_svg": numbers["radar_svg"],
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Render report.md + report.html from TweakIdea artifact family"
    )
    parser.add_argument("run_dir", help="Absolute path to RUN_DIR")
    parser.add_argument(
        "--timestamp",
        help="Override timestamp for deterministic tests (e.g. 2026-04-13)",
        default=None,
    )
    args = parser.parse_args()

    run_dir = pathlib.Path(args.run_dir).resolve()
    if not run_dir.is_dir():
        errors.die(
            errors.MISSING_FILE,
            str(run_dir),
            "run directory does not exist",
            f"{run_dir} not found",
        )

    if not TI_REPORT_DIR.is_dir():
        errors.die(
            errors.MISSING_FILE,
            str(TI_REPORT_DIR),
            "skills/ti-report/ not found",
            "template directory missing — is ti-report installed?",
        )

    timestamp = args.timestamp or datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    data = build_context(run_dir, timestamp)

    # Read CSS for inlining
    css_path = TI_REPORT_DIR / "styles.css"
    data["css"] = css_path.read_text() if css_path.exists() else ""

    # Dual Jinja2 environments
    loader = FileSystemLoader(str(TI_REPORT_DIR))
    # HTML env: autoescape=True forces escaping for all templates in this env.
    # Do NOT use select_autoescape(["html","htm"]) alone — template.html.j2 ends
    # in ".j2" not ".html", so select_autoescape would not match it (Pitfall 2).
    html_env = Environment(
        loader=loader,
        autoescape=True,
        trim_blocks=True,
        lstrip_blocks=True,
    )
    md_env = Environment(
        loader=loader,
        autoescape=False,
        trim_blocks=True,
        lstrip_blocks=True,
    )

    try:
        html_tmpl = html_env.get_template("template.html.j2")
        md_tmpl = md_env.get_template("template.md.j2")
        html_output = html_tmpl.render(**data)
        md_output = md_tmpl.render(**data)
    except TemplateError as e:
        errors.die(
            errors.TEMPLATE_RENDER_FAIL,
            str(TI_REPORT_DIR),
            str(e)[:200],
            f"template render failed: {e}",
        )

    # Write exactly two files (per RPRT-01)
    (run_dir / "report.html").write_text(html_output)
    (run_dir / "report.md").write_text(md_output)
    return 0


if __name__ == "__main__":
    sys.exit(main())
