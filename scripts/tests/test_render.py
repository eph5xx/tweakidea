"""Regression tests for scripts/render_report.py."""
import json
import pathlib
import shutil
import subprocess
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
FIXTURES = pathlib.Path(__file__).resolve().parent / "fixtures"
GOLDEN = FIXTURES / "golden-run"


def run_render(run_dir, timestamp="2026-04-13"):
    return subprocess.run(
        [
            "uv",
            "run",
            str(ROOT / "scripts" / "render_report.py"),
            str(run_dir),
            "--timestamp",
            timestamp,
        ],
        capture_output=True,
        text=True,
    )


class TestGoldenRender(unittest.TestCase):
    def setUp(self):
        self.tmpdir = pathlib.Path(tempfile.mkdtemp())
        self.run = self.tmpdir / "run"
        shutil.copytree(GOLDEN, self.run)
        # Clean previous outputs
        for n in ("report.md", "report.html"):
            p = self.run / n
            if p.exists():
                p.unlink()

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_runs_and_produces_two_files(self):
        result = run_render(self.run)
        self.assertEqual(
            result.returncode,
            0,
            f"render exited {result.returncode}; stderr: {result.stderr}",
        )
        self.assertTrue((self.run / "report.md").exists())
        self.assertTrue((self.run / "report.html").exists())

    def test_exactly_two_new_files(self):
        """RPRT-01: render_report.py writes exactly report.md + report.html. No other files."""
        before = set(p.name for p in self.run.iterdir() if p.is_file())
        run_render(self.run)
        after = set(p.name for p in self.run.iterdir() if p.is_file())
        new = after - before
        self.assertEqual(new, {"report.md", "report.html"})

    def test_html_has_inlined_style(self):
        run_render(self.run)
        html = (self.run / "report.html").read_text()
        self.assertIn("<style>", html)
        # CSS content should be present — look for a common selector
        self.assertIn("font-family", html.lower())

    def test_radar_svg_unescaped_in_html(self):
        run_render(self.run)
        html = (self.run / "report.html").read_text()
        self.assertIn('viewBox="0 0 500 440"', html)
        # Pitfall 2 regression: make sure SVG didn't get escaped
        self.assertNotIn("&lt;svg", html)

    def test_md_has_verdict_line(self):
        run_render(self.run)
        md = (self.run / "report.md").read_text()
        self.assertIn("PIVOT", md)
        self.assertIn("Weighted Score", md)

    def test_md_not_escaped(self):
        """Markdown env uses autoescape=False so raw symbols pass through."""
        run_render(self.run)
        md = (self.run / "report.md").read_text()
        # Markdown should have raw | in table rows, not &#124;
        self.assertNotIn("&gt;", md)
        self.assertNotIn("&amp;", md)


class TestHtmlAutoescape(unittest.TestCase):
    """Verify XSS mitigation via auto-escape."""

    def setUp(self):
        self.tmpdir = pathlib.Path(tempfile.mkdtemp())
        self.run = self.tmpdir / "run"
        shutil.copytree(GOLDEN, self.run)
        # Inject a script tag into idea.text
        idea = json.loads((self.run / "idea.json").read_text())
        idea["text"] = "<script>alert(1)</script> " + idea["text"]
        (self.run / "idea.json").write_text(json.dumps(idea))
        for n in ("report.md", "report.html"):
            p = self.run / n
            if p.exists():
                p.unlink()

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_script_tag_escaped_in_html(self):
        run_render(self.run)
        html = (self.run / "report.html").read_text()
        self.assertIn("&lt;script&gt;", html)
        self.assertNotIn("<script>alert(1)", html)


class TestMissingRunDir(unittest.TestCase):
    def test_nonexistent_dir_exits_nonzero(self):
        result = run_render("/tmp/definitely-not-a-dir-xyz999-phase1")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("MISSING_FILE", result.stderr)
