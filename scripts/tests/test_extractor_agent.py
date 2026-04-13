"""Tests for ti-extractor agent frontmatter + body contracts.

Validates that agents/ti-extractor.md:
- Has Write in its tools list (EXTR-01)
- References the hypotheses.json schema
- Contains the correct write path {RUN_DIR}/hypotheses.json
- Does NOT contain legacy ## EXTRACTION COMPLETE marker
"""
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
AGENT_FILE = ROOT / "agents" / "ti-extractor.md"

from scripts.tests._fm import parse_frontmatter  # noqa: E402


class TestExtractorAgent(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = AGENT_FILE.read_text()
        cls.fm = parse_frontmatter(cls.text)
        cls.body = cls.text.split("---", 2)[2]

    def test_write_in_tools(self):
        """EXTR-01: ti-extractor must have Write tool to write hypotheses.json."""
        tools = self.fm.get("tools", [])
        # tools may be None (parsed as None for empty `tools:`) or a list
        if tools is None:
            tools = []
        self.assertIn("Write", tools)

    def test_schema_reference(self):
        """Body must reference schemas/hypotheses.json so schema + prompt stay in sync."""
        self.assertIn("schemas/hypotheses.json", self.body)

    def test_write_path(self):
        """D-20: Extractor must write to {RUN_DIR}/hypotheses.json."""
        self.assertIn("{RUN_DIR}/hypotheses.json", self.body)

    def test_no_legacy_markers(self):
        """Legacy ## EXTRACTION COMPLETE marker must be deleted."""
        self.assertNotIn("## EXTRACTION COMPLETE", self.body)

    def test_model_still_sonnet(self):
        """Extractor model must remain sonnet per project key decisions."""
        self.assertEqual(self.fm.get("model"), "sonnet")

    def test_status_pending_in_schema_example(self):
        """Extractor must emit status: PENDING for all extracted hypotheses."""
        self.assertIn("PENDING", self.body)

    def test_zero_hypothesis_edge_case_documented(self):
        """Zero-hypothesis edge case must still be handled (write empty array)."""
        # The body should mention writing [] or empty array for the zero case
        self.assertTrue(
            "[]" in self.body or "zero" in self.body.lower() or "empty" in self.body.lower(),
            "Zero-hypothesis edge case not documented in body"
        )


if __name__ == "__main__":
    unittest.main()
