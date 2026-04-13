"""Sanity test: confirms scripts.tests package is importable and unittest discovery works.

This test MUST exist before any Wave 1 production code lands so that downstream tasks
can rely on `uv run python -m unittest discover -s scripts/tests` returning exit 0.
"""
import unittest


class TestSanity(unittest.TestCase):
    def test_package_importable(self):
        import scripts.tests  # noqa: F401
        self.assertTrue(True, "scripts.tests package imports cleanly")


if __name__ == "__main__":
    unittest.main()
