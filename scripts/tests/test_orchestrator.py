"""Regression tests for the Phase 1 orchestrator rewrite (STGE-01, STGE-02)."""
import pathlib
import re
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
EVALUATE_MD = ROOT / "commands" / "tweak" / "evaluate.md"
MANIFEST_JS = ROOT / "bin" / "manifest.js"


class TestOrchestratorFrontmatter(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = EVALUATE_MD.read_text()

    def test_skills_list_uses_ti_report(self):
        # Parse the frontmatter block (between the first and second ---)
        text = self.text
        parts = text.split("---", 2)
        self.assertGreaterEqual(len(parts), 3, "Could not find frontmatter")
        frontmatter = parts[1]
        m = re.search(r"^skills:\n((?:  - .+\n)+)", frontmatter, re.MULTILINE)
        self.assertIsNotNone(m, "No skills block found in frontmatter")
        skills_block = m.group(1)
        self.assertIn("ti-report", skills_block)
        self.assertNotIn("ti-html-report", skills_block)


class TestOrchestratorBody(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.body = EVALUATE_MD.read_text().split("---", 2)[2]

    def test_has_uv_run_compute(self):
        self.assertIn("uv run", self.body)
        self.assertIn("compute.py", self.body)

    def test_has_uv_run_render_report(self):
        self.assertIn("render_report.py", self.body)

    def test_spawns_ti_narrative(self):
        self.assertIn("ti-narrative", self.body)

    def test_no_ti_merger(self):
        self.assertNotIn("ti-merger", self.body)

    def test_no_ti_html_report(self):
        self.assertNotIn("ti-html-report", self.body)

    def test_no_evaluation_results_variable(self):
        self.assertNotIn("EVALUATION_RESULTS", self.body)

    def test_no_rubric_trimming(self):
        self.assertNotIn("Evaluator Output Trimming", self.body)
        self.assertNotIn("Strip the Rubric Assessment", self.body)

    def test_no_legacy_markers(self):
        for marker in ("## EVALUATION COMPLETE", "## EVALUATION FAILED",
                       "## EXTRACTION COMPLETE", "## RESEARCH COMPLETE"):
            with self.subTest(marker=marker):
                self.assertNotIn(marker, self.body)

    def test_no_html_gate(self):
        self.assertNotIn("Would you like an HTML report", self.body)

    def test_stage_order(self):
        """Stages 0, 1, 2, 3a, 3b, 4, 5 appear in the correct order."""
        stages = ["Stage 0", "Stage 1", "Stage 2", "Stage 3a", "Stage 3b", "Stage 4", "Stage 5"]
        positions = []
        for s in stages:
            pos = self.body.find(s)
            self.assertGreater(pos, 0, f"{s} not found in body")
            positions.append(pos)
        self.assertEqual(positions, sorted(positions),
                         f"stages out of order: {positions}")

    def test_version_json_written_in_stage_0(self):
        # Stage 0 section should contain the version.json write
        stage_0_start = self.body.find("Stage 0")
        stage_1_start = self.body.find("Stage 1")
        stage_0_body = self.body[stage_0_start:stage_1_start]
        self.assertIn("version.json", stage_0_body)
        self.assertIn("idea.json", stage_0_body)

    def test_assumptions_json_in_stage_1_lane_b(self):
        stage_1_start = self.body.find("Stage 1")
        stage_2_start = self.body.find("Stage 2")
        stage_1_body = self.body[stage_1_start:stage_2_start]
        self.assertIn("assumptions.json", stage_1_body)

    def test_tweakidea_scripts_root_in_stage_0(self):
        stage_0_start = self.body.find("Stage 0")
        stage_1_start = self.body.find("Stage 1")
        stage_0_body = self.body[stage_0_start:stage_1_start]
        self.assertIn("TWEAKIDEA_SCRIPTS_ROOT", stage_0_body)

    def test_zero_text_processing_statement(self):
        self.assertIn("ZERO text processing", self.body)

    def test_browser_open_question_survives(self):
        self.assertIn("Open the HTML report in your browser", self.body)


class TestManifestJs(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = MANIFEST_JS.read_text()

    def test_agent_files_has_narrative(self):
        self.assertIn("'ti-narrative.md'", self.text)

    def test_agent_files_no_merger(self):
        self.assertNotIn("'ti-merger.md'", self.text)

    def test_skill_dirs_has_ti_report(self):
        self.assertIn("'ti-report'", self.text)

    def test_skill_dirs_no_ti_html_report(self):
        self.assertNotIn("'ti-html-report'", self.text)

    def test_agent_files_count(self):
        """AGENT_FILES must have exactly 4 entries."""
        m = re.search(r"const AGENT_FILES = \[(.*?)\];", self.text, re.DOTALL)
        self.assertIsNotNone(m, "AGENT_FILES array not found")
        entries = [e.strip() for e in m.group(1).split(",") if e.strip()]
        self.assertEqual(len(entries), 4, f"Expected 4 AGENT_FILES entries, got: {entries}")

    def test_skill_dirs_count(self):
        """SKILL_DIRS must have exactly 4 entries."""
        m = re.search(r"const SKILL_DIRS = \[(.*?)\];", self.text, re.DOTALL)
        self.assertIsNotNone(m, "SKILL_DIRS array not found")
        entries = [e.strip() for e in m.group(1).split(",") if e.strip()]
        self.assertEqual(len(entries), 4, f"Expected 4 SKILL_DIRS entries, got: {entries}")


if __name__ == "__main__":
    unittest.main()
