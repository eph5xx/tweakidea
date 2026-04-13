"""Tests for ti-researcher agent frontmatter + body contracts.

Validates that agents/ti-researcher.md:
- Has Write in its tools list (RSRC-01)
- Still retains WebSearch, WebFetch, Read tools (nothing removed)
- References the research.json schema
- Contains the correct write path {RUN_DIR}/research.json
- Does NOT contain legacy ## RESEARCH COMPLETE marker
"""
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
AGENT_FILE = ROOT / "agents" / "ti-researcher.md"

from scripts.tests._fm import parse_frontmatter  # noqa: E402


class TestResearcherAgent(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = AGENT_FILE.read_text()
        cls.fm = parse_frontmatter(cls.text)
        cls.body = cls.text.split("---", 2)[2]

    def test_write_in_tools(self):
        """RSRC-01: ti-researcher must have Write tool to write research.json."""
        self.assertIn("Write", self.fm.get("tools", []))

    def test_preserves_existing_tools(self):
        """WebSearch, WebFetch, Read must all remain — no tools removed."""
        for t in ("WebSearch", "WebFetch", "Read"):
            self.assertIn(t, self.fm.get("tools", []), f"Tool {t!r} was removed from frontmatter")

    def test_four_tools_total(self):
        """Researcher should have exactly 4 tools: WebSearch, WebFetch, Read, Write."""
        tools = self.fm.get("tools", [])
        self.assertEqual(len(tools), 4, f"Expected 4 tools, got {len(tools)}: {tools}")

    def test_schema_reference(self):
        """Body must reference schemas/research.json so schema + prompt stay in sync."""
        self.assertIn("schemas/research.json", self.body)

    def test_write_path(self):
        """D-21: Researcher must write to {RUN_DIR}/research.json."""
        self.assertIn("{RUN_DIR}/research.json", self.body)

    def test_no_legacy_markers(self):
        """Legacy ## RESEARCH COMPLETE marker must be deleted."""
        self.assertNotIn("## RESEARCH COMPLETE", self.body)

    def test_model_still_sonnet(self):
        """Researcher model must remain sonnet per project key decisions."""
        self.assertEqual(self.fm.get("model"), "sonnet")

    def test_available_false_case_documented(self):
        """available: false case must be documented for when research is disabled."""
        self.assertIn("available", self.body)
        self.assertTrue(
            "false" in self.body.lower() or "disabled" in self.body.lower() or "unavailable" in self.body.lower(),
            "available:false / research disabled case not documented in body"
        )


if __name__ == "__main__":
    unittest.main()
