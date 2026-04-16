import unittest

_SKIP_MSG = "jsonschema not installed — run via uv run scripts/tests/run_tests.py"

try:
    import jsonschema  # noqa: F401
    HAS_JSONSCHEMA = True
except ImportError:
    HAS_JSONSCHEMA = False

requires_jsonschema = unittest.skipUnless(HAS_JSONSCHEMA, _SKIP_MSG)
