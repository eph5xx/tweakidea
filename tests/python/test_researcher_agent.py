"""Tests for ti-researcher agent spawn contract + body contracts.

Validates that references/agents/ti-researcher.md:
- Has write-file in its tools list (RSRC-01)
- Still retains web-search, web-fetch, read-file (nothing removed)
- References the research.json schema
- Contains the correct write path {RUN_DIR}/research.json
- Does NOT contain legacy ## RESEARCH COMPLETE marker
"""
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
AGENT_FILE = ROOT / "skills" / "tweakidea" / "references" / "agents" / "ti-researcher.md"

from tests.python._fm import claude_model_for_tier, parse_spawn_contract  # noqa: E402


class TestResearcherAgent(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = AGENT_FILE.read_text()
        cls.fm = parse_spawn_contract(cls.text)
        cls.body = cls.text

    def test_write_in_tools(self):
        """RSRC-01: ti-researcher must have write-file to write research.json."""
        self.assertIn("write-file", self.fm.get("tools", []))

    def test_preserves_existing_tools(self):
        """web-search, web-fetch, read-file must all remain — no capabilities removed."""
        for t in ("web-search", "web-fetch", "read-file"):
            self.assertIn(t, self.fm.get("tools", []), f"Tool {t!r} was removed from the spawn contract")

    def test_four_tools_total(self):
        """Researcher should have exactly 4 capabilities: web-search, web-fetch, read-file, write-file."""
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

    def test_per_cluster_research_minimum(self):
        self.assertIn("at least 3 targeted search queries per cluster", self.body)
        self.assertIn("Fetch at least 3", self.body)

    def test_model_still_sonnet(self):
        """Researcher runs on the fast tier, which maps to sonnet per project key decisions."""
        self.assertEqual(self.fm.get("tier"), "fast")
        self.assertEqual(claude_model_for_tier("fast"), "sonnet")

    def test_available_false_case_documented(self):
        """available: false case must be documented for when research is disabled."""
        self.assertIn("available", self.body)
        self.assertTrue(
            "false" in self.body.lower() or "disabled" in self.body.lower() or "unavailable" in self.body.lower(),
            "available:false / research disabled case not documented in body"
        )


if __name__ == "__main__":
    unittest.main()
