"""Tests for ti-evaluator agent frontmatter + body contracts.

Validates that agents/ti-evaluator.md:
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
AGENT_FILE = ROOT / "agents" / "ti-evaluator.md"


def parse_frontmatter(md_text: str) -> dict:
    """Minimal YAML frontmatter parser — handles the subset used by TweakIdea agent files.

    Supports: `key: value` scalars, `key:` followed by `  - item` lists, nested blocks.
    Does NOT support YAML flow style, anchors, multi-line strings — TweakIdea agents don't use those.
    """
    m = re.match(r"^---\n(.*?)\n---\n", md_text, re.DOTALL)
    if not m:
        raise ValueError("no frontmatter found")
    block = m.group(1)
    result = {}
    current_key = None
    current_list = None
    for raw in block.split("\n"):
        if not raw.strip():
            continue
        if raw.startswith("  - "):
            if current_list is None:
                result[current_key] = []
                current_list = result[current_key]
            current_list.append(raw[4:].strip())
            continue
        if ":" in raw:
            key, _, val = raw.partition(":")
            key = key.strip()
            val = val.strip()
            if val == "" or val == "[]":
                result[key] = [] if val == "[]" else None
                current_key = key
                current_list = result[key] if val == "[]" else None
            else:
                result[key] = val
                current_key = key
                current_list = None
    return result


class TestEvaluatorAgent(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = AGENT_FILE.read_text()
        cls.fm = parse_frontmatter(cls.text)
        cls.body = cls.text.split("---", 2)[2]

    def test_write_in_tools(self):
        """EVAL-01: ti-evaluator must have Write tool to write dimension JSON files."""
        self.assertIn("Write", self.fm.get("tools", []))

    def test_preserves_existing_tools(self):
        """No tools should be removed — Read, Grep, Glob, WebSearch, WebFetch must remain."""
        for t in ("Read", "Grep", "Glob", "WebSearch", "WebFetch"):
            self.assertIn(t, self.fm.get("tools", []), f"Tool {t!r} was removed from frontmatter")

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
