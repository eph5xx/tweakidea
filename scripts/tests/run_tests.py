"""Test runner for scripts/tests package.

Usage:
    uv run scripts/tests/run_tests.py          # run all tests
    uv run scripts/tests/run_tests.py -v       # verbose output

Discovers all test_*.py files in scripts/tests/ and runs them via unittest.
"""
import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

if __name__ == "__main__":
    test_dir = pathlib.Path(__file__).resolve().parent
    loader = unittest.TestLoader()
    suite = loader.discover(str(test_dir), pattern="test_*.py")
    verbosity = 2 if "-v" in sys.argv else 1
    runner = unittest.TextTestRunner(verbosity=verbosity)
    result = runner.run(suite)
    sys.exit(0 if result.wasSuccessful() else 1)
