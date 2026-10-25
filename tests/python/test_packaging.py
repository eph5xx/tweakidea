"""Tests for package.json#files and the shipped skill layout (SCHE-05)."""
import json
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
PACKAGE_JSON = ROOT / "package.json"
SKILL = ROOT / "skills" / "tweakidea"


class TestPackageJson(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pkg = json.loads(PACKAGE_JSON.read_text())

    def test_files_ships_only_bin_and_skills(self):
        self.assertEqual(self.pkg.get("files"), ["bin", "skills", "!**/__pycache__"])

    def test_bin_entry(self):
        self.assertEqual(self.pkg.get("bin", {}).get("tweakidea"), "bin/install.js")

    def test_test_script(self):
        self.assertEqual(self.pkg.get("scripts", {}).get("test"), "node tests/run-tests.cjs")


class TestSkillLayout(unittest.TestCase):
    def test_top_level_entries(self):
        entries = sorted(p.name for p in SKILL.iterdir() if p.name != ".DS_Store")
        self.assertEqual(entries, ["SKILL.md", "assets", "references", "scripts"])

    def test_schemas_has_ten_files(self):
        self.assertEqual(len(list((SKILL / "assets" / "schemas").glob("*.json"))), 10)

    def test_scripts_present(self):
        for name in ("compute.py", "render_report.py", "hnparse.py", "hnsearch.py"):
            with self.subTest(name=name):
                self.assertTrue((SKILL / "scripts" / name).exists())

    def test_scripts_has_lib(self):
        for name in ("schema.py", "registry.py", "errors.py"):
            with self.subTest(name=name):
                self.assertTrue((SKILL / "scripts" / "lib" / name).exists())

    def test_no_tests_inside_skill(self):
        self.assertEqual([p for p in SKILL.rglob("tests") if p.is_dir()], [])

    def test_old_top_level_dirs_gone(self):
        for name in ("agents", "commands", "schemas", "scripts"):
            with self.subTest(name=name):
                self.assertFalse((ROOT / name).exists())


if __name__ == "__main__":
    unittest.main()
