"""Tests for ti-evaluator agent spawn contract + body contracts.

Validates that references/agents/ti-evaluator.md:
- Has Write in its tools list (EVAL-01)
- References the dimension-evaluation.json schema (EVAL-02)
- Has structured tier fields on criteria (EVAL-03)
- Does NOT contain legacy markdown output markers
- Contains the correct write path pattern
"""
import pathlib
import re
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
AGENT_FILE = ROOT / "skills" / "tweakidea" / "references" / "agents" / "ti-evaluator.md"


from tests.python._fm import parse_spawn_contract  # noqa: E402


class TestEvaluatorAgent(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = AGENT_FILE.read_text()
        cls.fm = parse_spawn_contract(cls.text)
        cls.body = cls.text

    def test_write_in_tools(self):
        """EVAL-01: ti-evaluator must have Write tool to write dimension JSON files."""
        self.assertIn("Write", self.fm.get("tools", []))

    def test_preserves_existing_tools(self):
        """No tools should be removed — Read, Grep, Glob, WebSearch, WebFetch must remain."""
        for t in ("Read", "Grep", "Glob", "WebSearch", "WebFetch"):
            self.assertIn(t, self.fm.get("tools", []), f"Tool {t!r} was removed from the spawn contract")

    def test_schema_reference(self):
        """EVAL-02: Body must reference schemas/dimension-evaluation.json so schema + prompt stay in sync."""
        self.assertIn("schemas/dimension-evaluation.json", self.body)

    def test_no_legacy_markers(self):
        """D-11: Legacy markdown output wrappers must be deleted."""
        self.assertNotIn("## EVALUATION COMPLETE", self.body)
        self.assertNotIn("## EVALUATION FAILED", self.body)

    def test_write_path(self):
        """D-10: Evaluator must write to {RUN_DIR}/dimensions/{slug}.json."""
        self.assertIn("{RUN_DIR}/dimensions/{slug}.json", self.body)

    def test_hybrid_prose_fields(self):
        """D-12: Hybrid schema requires analysis_narrative, key_finding, score_explanation."""
        self.assertIn("analysis_narrative", self.body)
        self.assertIn("key_finding", self.body)
        self.assertIn("score_explanation", self.body)

    def test_no_research_context_section(self):
        """Research is read from research.json, not injected as a prompt section."""
        self.assertNotIn("## Research Context", self.body)

    def test_two_round_research_minimum(self):
        self.assertIn("at least 4 WebSearch calls and at least 2 WebFetch calls", self.body)
        self.assertIn("Round 2", self.body)

    def test_model_still_sonnet(self):
        """Evaluator model must remain sonnet per project key decisions."""
        self.assertEqual(self.fm.get("model"), "sonnet")

    def test_evidence_tier_classification_heading(self):
        """EVAL-03: Structured tier field requires Evidence Tier Classification section."""
        self.assertIn("Evidence Tier Classification", self.body)

    def test_all_four_tier_names_present(self):
        """EVAL-03: All four tier names must appear in the body."""
        for tier in ("both_confirmed", "research_only", "founder_only", "assumed"):
            self.assertIn(tier, self.body, f"Tier name {tier!r} missing from body")

    def test_critical_rules_section(self):
        """Evaluator must retain a Critical Rules section with at least 6 numbered rules."""
        self.assertIn("## Critical Rules", self.body)
        # Count numbered list entries in the critical rules section
        rules_match = re.search(r"## Critical Rules(.*?)(?=\n##|\Z)", self.body, re.DOTALL)
        self.assertIsNotNone(rules_match, "Could not find Critical Rules section content")
        rules_text = rules_match.group(1)
        rule_count = len(re.findall(r"^\d+\.", rules_text, re.MULTILINE))
        self.assertGreaterEqual(rule_count, 6, f"Expected >= 6 numbered rules, found {rule_count}")


if __name__ == "__main__":
    unittest.main()
