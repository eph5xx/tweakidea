"""Structured stderr error emission for TweakIdea pipeline scripts.

Every script calls emit() for non-fatal errors and die() for fatal.
Output contract: single-line JSON with keys error, code, path, hint.
"""
import json
import sys

# Error code constants
SCHEMA_VIOLATION = "SCHEMA_VIOLATION"
MISSING_FILE = "MISSING_FILE"
REGISTRY_PARSE_FAIL = "REGISTRY_PARSE_FAIL"
INVALID_JSON = "INVALID_JSON"
INVALID_DIMENSION = "INVALID_DIMENSION"  # non-fatal: hard-fail one dim, continue
TEMPLATE_RENDER_FAIL = "TEMPLATE_RENDER_FAIL"
REGISTRY_WEIGHT_MISMATCH = "REGISTRY_WEIGHT_MISMATCH"


def emit(code: str, path: str, hint: str, message: str) -> None:
    """Emit a structured error to stderr. Does NOT exit."""
    print(
        json.dumps(
            {"error": message, "code": code, "path": path, "hint": hint},
            ensure_ascii=False,
        ),
        file=sys.stderr,
    )


def die(code: str, path: str, hint: str, message: str, exit_code: int = 1) -> None:
    """Emit a structured error and exit with the given code."""
    emit(code, path, hint, message)
    sys.exit(exit_code)


def from_validation_error(e, file_path: str, non_fatal: bool = False) -> None:
    """Serialize a jsonschema.ValidationError into our structured format.

    absolute_path is a collections.deque; list() it for JSON-serializable output.
    """
    code = INVALID_DIMENSION if non_fatal else SCHEMA_VIOLATION
    path_in_instance = ".".join(str(p) for p in list(e.absolute_path))
    schema_path_str = ".".join(str(p) for p in list(e.schema_path))
    hint = f"validator={e.validator}, schema_path={schema_path_str}"
    location = f"{file_path}:{path_in_instance}" if path_in_instance else file_path
    if non_fatal:
        emit(code, location, hint, e.message)
    else:
        die(code, location, hint, e.message)
