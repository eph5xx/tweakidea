"""Tests for agents/ti-narrative.md frontmatter + body contract (NARR-01..03)."""
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
AGENT_FILE = ROOT / "agents" / "ti-narrative.md"

try:
    from ._fm import parse_frontmatter  # shared helper from Plan 04
except ImportError:
    # Fallback: inline the minimal parser
    import re

    def parse_frontmatter(md_text: str) -> dict:
        m = re.match(r"^---\n(.*?)\n---\n", md_text, re.DOTALL)
        if not m:
            raise ValueError("no frontmatter")
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


class TestNarrativeAgentFrontmatter(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = AGENT_FILE.read_text()
        cls.fm = parse_frontmatter(cls.text)
        cls.body = cls.text.split("---", 2)[2]

    def test_file_exists(self):
        self.assertTrue(AGENT_FILE.exists())

    def test_name_is_ti_narrative(self):
        self.assertEqual(self.fm.get("name"), "ti-narrative")

    def test_model_is_opus(self):
        self.assertEqual(self.fm.get("model"), "opus")

    def test_permission_mode(self):
        self.assertEqual(self.fm.get("permissionMode"), "dontAsk")

    def test_max_turns(self):
        # Per RESEARCH.md §Q6c analysis + planner judgment: maxTurns: 15 (read phase + 5 writes + reasoning headroom)
        self.assertEqual(self.fm.get("maxTurns"), "15")

    def test_has_read_and_write_tools(self):
        tools = self.fm.get("tools", [])
        self.assertIn("Read", tools)
        self.assertIn("Write", tools)

    def test_has_ti_scoring_skill(self):
        skills = self.fm.get("skills", [])
        self.assertIn("ti-scoring", skills)


class TestNarrativeAgentBody(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.body = AGENT_FILE.read_text().split("---", 2)[2]

    def test_references_all_three_schemas(self):
        for name in (
            "schemas/strengths-weaknesses.json",
            "schemas/next-steps.json",
            "schemas/potential.json",
        ):
            with self.subTest(schema=name):
                self.assertIn(name, self.body)

    def test_does_not_reference_dropped_schemas(self):
        for name in ("schemas/verdict.json", "schemas/dealbreakers.json"):
            with self.subTest(schema=name):
                self.assertNotIn(name, self.body)

    def test_references_all_three_output_paths(self):
        for path in (
            "{RUN_DIR}/strengths-weaknesses.json",
            "{RUN_DIR}/next-steps.json",
            "{RUN_DIR}/potential.json",
        ):
            with self.subTest(path=path):
                self.assertIn(path, self.body)

    def test_reads_numbers_json(self):
        self.assertIn("numbers.json", self.body)

    def test_reads_dimensions_directory(self):
        self.assertIn("dimensions/", self.body)

    def test_prohibition_on_numeric_computation(self):
        # NARR-02: agent does NOT compute weights, rankings, verdict, uplift math
        self.assertIn("Do NOT", self.body)
        # At least one of these keywords should appear near the Do NOT
        lowered = self.body.lower()
        self.assertTrue(
            "compute" in lowered or "math" in lowered,
            "no computation-prohibition language found",
        )

    def test_completion_marker(self):
        self.assertIn("## NARRATIVE COMPLETE", self.body)

    def test_no_evaluator_markers(self):
        # Narrative is NOT an evaluator; must not have these markers
        self.assertNotIn("## EVALUATION COMPLETE", self.body)
        self.assertNotIn("## EVALUATION FAILED", self.body)

    def test_files_to_read_block(self):
        self.assertIn("<files_to_read>", self.body)
        self.assertIn("</files_to_read>", self.body)

    def test_partial_failure_section(self):
        # Should mention partial failure handling even if brief
        self.assertIn("Partial Failure", self.body)
