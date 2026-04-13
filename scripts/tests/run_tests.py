# /// script
# requires-python = ">=3.11"
# dependencies = ["jsonschema==4.26.0"]
# ///
"""Entry point for TweakIdea Phase 1 tests via uv run.

Usage: uv run scripts/tests/run_tests.py [-v]
"""
import sys
import unittest

if __name__ == "__main__":
    loader = unittest.TestLoader()
    suite = loader.discover(
        start_dir="scripts/tests",
        pattern="test_*.py",
        top_level_dir=".",
    )
    runner = unittest.TextTestRunner(verbosity=2 if "-v" in sys.argv else 1)
    result = runner.run(suite)
    sys.exit(0 if result.wasSuccessful() else 1)
