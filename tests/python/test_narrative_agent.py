"""Tests for references/agents/ti-narrative.md spawn contract + body contract (NARR-01..03)."""
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
AGENT_FILE = ROOT / "skills" / "tweakidea" / "references" / "agents" / "ti-narrative.md"

from tests.python._fm import parse_spawn_contract  # noqa: E402


class TestNarrativeAgentContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = AGENT_FILE.read_text()
        cls.fm = parse_spawn_contract(cls.text)
        cls.body = cls.text

    def test_file_exists(self):
        self.assertTrue(AGENT_FILE.exists())

    def test_no_frontmatter(self):
        self.assertFalse(self.text.startswith("---"))

    def test_model_is_opus(self):
        self.assertEqual(self.fm.get("model"), "opus")

    def test_max_turns(self):
        # Read phase + 3 writes + reasoning headroom
        self.assertEqual(self.fm.get("maxTurns"), "15")

    def test_has_read_and_write_tools(self):
        tools = self.fm.get("tools", [])
        self.assertIn("Read", tools)
        self.assertIn("Write", tools)

    def test_references_evaluation_md(self):
        self.assertIn("references/scoring/EVALUATION.md", self.body)


class TestNarrativeAgentBody(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.body = AGENT_FILE.read_text()

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
        self.assertIn("WROTE {RUN_DIR}/strengths-weaknesses.json", self.body)

    def test_no_evaluator_markers(self):
        # Narrative is NOT an evaluator; must not have these markers
        self.assertNotIn("## EVALUATION COMPLETE", self.body)
        self.assertNotIn("## EVALUATION FAILED", self.body)
        self.assertNotIn("## NARRATIVE COMPLETE", self.body)

    def test_files_to_read_block(self):
        self.assertIn("<files_to_read>", self.body)
        self.assertIn("</files_to_read>", self.body)

    def test_missing_input_handling_section(self):
        self.assertIn("Missing Input Handling", self.body)
