"""Filesystem assertions for skills/ti-report/ rename (RNME-01)."""
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent


class TestTiReportLayout(unittest.TestCase):
    def test_ti_report_directory_exists(self):
        self.assertTrue((ROOT / "skills" / "ti-report").is_dir())

    def test_ti_report_has_four_files(self):
        files = sorted(p.name for p in (ROOT / "skills" / "ti-report").iterdir() if p.is_file())
        expected = ["SKILL.md", "styles.css", "template.html.j2", "template.md.j2"]
        self.assertEqual(files, expected)

    def test_skill_md_has_frontmatter(self):
        content = (ROOT / "skills" / "ti-report" / "SKILL.md").read_text()
        self.assertTrue(content.startswith("---"))
        self.assertIn("name: ti-report", content)

    def test_templates_have_jinja_syntax(self):
        html = (ROOT / "skills" / "ti-report" / "template.html.j2").read_text()
        md = (ROOT / "skills" / "ti-report" / "template.md.j2").read_text()
        self.assertIn("{{", html)
        self.assertIn("{%", html)
        self.assertIn("{{", md)
