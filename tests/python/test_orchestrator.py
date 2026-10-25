"""Regression tests for the evaluate orchestrator reference and installer manifest."""
import pathlib
import re
import unittest

from tests.python._fm import parse_spawn_contract

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
SKILL = ROOT / "skills" / "tweakidea"
EVALUATE_MD = SKILL / "references" / "commands" / "evaluate.md"
AGENTS_DIR = SKILL / "references" / "agents"
RUNTIME_MD = SKILL / "references" / "runtime.md"
MANIFEST_JS = ROOT / "bin" / "manifest.js"

AGENTS = ("ti-researcher", "ti-extractor", "ti-evaluator", "ti-narrative")


class TestOrchestratorSpawns(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = EVALUATE_MD.read_text()

    def test_no_frontmatter(self):
        self.assertFalse(self.text.startswith("---"))

    def test_no_named_agent_types(self):
        self.assertNotRegex(self.text, r"agent_type:\*\*\s*`ti-")
        self.assertNotIn("agent_type", self.text)

    def test_all_spawns_name_a_model_tier(self):
        spawns = re.findall(r"- \*\*model tier:\*\* `(\w+)`\n\s*- \*\*prompt:\*\*", self.text)
        # researcher, extractor, retry researcher, evaluator, narrative
        self.assertEqual(len(spawns), 5, spawns)
        self.assertEqual(spawns.count("strong"), 1, spawns)
        for tier in spawns:
            self.assertIn(tier, ("fast", "strong"))

    def test_spawns_declare_background(self):
        flags = re.findall(r"- \*\*background:\*\* (yes|no)\b", self.text)
        self.assertEqual(len(flags), 5, flags)
        self.assertEqual(flags.count("yes"), 1, flags)

    def test_spawn_table_matches_agent_contracts(self):
        self.assertIn("| Agent | Model tier | Capabilities | Turn budget |", self.text)
        for agent in AGENTS:
            with self.subTest(agent=agent):
                contract = parse_spawn_contract((AGENTS_DIR / f"{agent}.md").read_text())
                row = re.search(
                    rf"^\| `{agent}` \| `(\w+)` \| ([^|]+) \| (\d+) \|$", self.text, re.MULTILINE
                )
                self.assertIsNotNone(row, f"no spawn table row for {agent}")
                self.assertEqual(row.group(1), contract["tier"])
                self.assertEqual([t.strip() for t in row.group(2).split(",")], contract["tools"])
                self.assertEqual(row.group(3), contract["maxTurns"])

    def test_every_spawn_uses_preamble(self):
        for agent in AGENTS:
            with self.subTest(agent=agent):
                self.assertIn(f"{{PREAMBLE:{agent}}}", self.text)

    def test_preamble_points_at_agent_references(self):
        self.assertIn("Read {SKILL_DIR}/references/agents/{agent}.md first", self.text)

    def test_preamble_has_web_preload_slot(self):
        self.assertIn("every file in <files_to_read>{web_preload}.", self.text)

    def test_runtime_md_holds_claude_code_web_preload(self):
        self.assertIn(
            ', and if WebSearch/WebFetch are in your tool list, load them with ToolSearch query "select:WebSearch,WebFetch"',
            RUNTIME_MD.read_text(),
        )

    def test_runtime_check_stops_before_questions(self):
        stage_0 = self.text[self.text.find("## Stage 0"):self.text.find("## Stage 1")]
        start = stage_0.find("### Step 0: Runtime check")
        self.assertGreaterEqual(start, 0, "Stage 0 must start with a runtime check")
        self.assertLess(start, stage_0.find("### Step 1"))
        section = stage_0[start:stage_0.find("### Step 1")]
        for capability in ("spawn-subagent", "web-search", "web-fetch"):
            with self.subTest(capability=capability):
                self.assertIn(capability, section)
        self.assertIn("can't run in this agent", section)
        self.assertIn("clean context", section)
        for cmd in ("improve", "diff", "browse-hn", "analyze-hn-post", "list", "show", "share"):
            with self.subTest(cmd=cmd):
                self.assertIn(f"`{cmd}`", section)
    def test_evaluator_prompt_reads_inputs_from_run_dir(self):
        start = self.text.find("#### Evaluator Prompt Construction")
        end = self.text.find("#### Context Routing Rule")
        section = self.text[start:end]
        for path in ("{RUN_DIR}/idea.json", "{RUN_DIR}/assumptions.json", "{RUN_DIR}/research.json"):
            with self.subTest(path=path):
                self.assertIn(path, section)
        self.assertNotIn("The full structured IDEA_TEXT", section)
        self.assertNotIn("hypotheses.json", section)


class TestOrchestratorBody(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.body = EVALUATE_MD.read_text()

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

    def _stage_0(self):
        start = self.body.find("## Stage 0")
        end = self.body.find("## Stage 1")
        return self.body[start:end]

    def test_version_json_written_in_stage_0(self):
        stage_0_body = self._stage_0()
        self.assertIn("version.json", stage_0_body)
        self.assertIn("idea.json", stage_0_body)
        self.assertIn("{SKILL_DIR}/VERSION", stage_0_body)

    def test_assumptions_json_in_stage_1_lane_b(self):
        stage_1_start = self.body.find("## Stage 1")
        stage_2_start = self.body.find("## Stage 2")
        stage_1_body = self.body[stage_1_start:stage_2_start]
        self.assertIn("assumptions.json", stage_1_body)

    def test_tweakidea_scripts_root_in_stage_0(self):
        stage_0_body = self._stage_0()
        self.assertIn("TWEAKIDEA_SCRIPTS_ROOT", stage_0_body)
        self.assertIn("{SKILL_DIR}/scripts/compute.py", stage_0_body)

    def test_target_user_in_stage_0(self):
        stage_0_body = self._stage_0()
        self.assertIn("target_user", stage_0_body)
        self.assertIn("Target User:", stage_0_body)

    def test_zero_text_processing_statement(self):
        self.assertIn("ZERO text processing", self.body)

    def test_browser_open_question_survives(self):
        self.assertIn("Open the HTML report in your browser", self.body)


class TestManifestJs(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = MANIFEST_JS.read_text()

    def _array(self, name):
        m = re.search(rf"const {name} = \[(.*?)\];", self.text, re.DOTALL)
        self.assertIsNotNone(m, f"{name} array not found")
        return [e.strip().strip("'") for e in m.group(1).split(",") if e.strip()]

    def test_skill_name(self):
        self.assertIn("const SKILL_NAME = 'tweakidea';", self.text)
        self.assertIn("const SKILL_SOURCE = 'skills/tweakidea';", self.text)

    def test_agents(self):
        self.assertEqual(sorted(self._array("AGENTS")), sorted(AGENTS))

    def test_commands_match_references(self):
        on_disk = sorted(p.stem for p in (SKILL / "references" / "commands").glob("*.md"))
        self.assertEqual(sorted(self._array("COMMANDS")), on_disk)

    def test_no_legacy_names(self):
        self.assertNotIn("ti-merger", self.text)
        self.assertNotIn("ti-html-report", self.text)


if __name__ == "__main__":
    unittest.main()
