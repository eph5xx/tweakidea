"""Schema validation wrapper for TweakIdea Phase 1 pipeline.

This module is imported by scripts/compute.py and scripts/render_report.py.
It is NOT a PEP 723 entry point — its jsonschema dependency is resolved
by whichever caller script declares it in its inline metadata.
"""
import json
import pathlib
from functools import lru_cache

from jsonschema import Draft202012Validator, ValidationError  # noqa: F401

_SCHEMAS_DIR = (
    pathlib.Path(__file__).resolve().parent.parent.parent / "schemas"
)


def _schema_path(name: str) -> pathlib.Path:
    if "/" in name or ".." in name or "\\" in name:
        raise ValueError(f"invalid schema name: {name!r}")
    return _SCHEMAS_DIR / f"{name}.json"


@lru_cache(maxsize=None)
def _schema(name: str) -> dict:
    p = _schema_path(name)
    if not p.exists():
        raise FileNotFoundError(f"schema not found: {name} (expected {p})")
    return json.loads(p.read_text())


def validate(instance, schema_name: str) -> None:
    """Validate instance against the named schema.

    Raises jsonschema.ValidationError on failure (first error only).
    """
    v = Draft202012Validator(_schema(schema_name))
    errors = sorted(v.iter_errors(instance), key=lambda e: list(e.absolute_path))
    if errors:
        raise errors[0]


def validate_file(path, schema_name: str) -> None:
    """Read JSON file at path and validate against the named schema."""
    with open(path) as f:
        instance = json.load(f)
    validate(instance, schema_name)
