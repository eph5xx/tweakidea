"""Filesystem assertions for the report templates in assets/report/."""
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
SKILL = ROOT / "skills" / "tweakidea"
REPORT_DIR = SKILL / "assets" / "report"


class TestReportAssetsLayout(unittest.TestCase):
    def test_report_directory_exists(self):
        self.assertTrue(REPORT_DIR.is_dir())

    def test_report_has_three_files(self):
        files = sorted(p.name for p in REPORT_DIR.iterdir() if p.is_file())
        self.assertEqual(files, ["styles.css", "template.html.j2", "template.md.j2"])

    def test_report_reference_exists_without_frontmatter(self):
        content = (SKILL / "references" / "report.md").read_text()
        self.assertFalse(content.startswith("---"))
        self.assertIn("assets/report/styles.css", content)

    def test_templates_have_jinja_syntax(self):
        html = (REPORT_DIR / "template.html.j2").read_text()
        md = (REPORT_DIR / "template.md.j2").read_text()
        self.assertIn("{{", html)
        self.assertIn("{%", html)
        self.assertIn("{{", md)
