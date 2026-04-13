"""Tests for package.json#files and related packaging invariants (SCHE-05)."""
import json
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
PACKAGE_JSON = ROOT / "package.json"


class TestPackageJson(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pkg = json.loads(PACKAGE_JSON.read_text())

    def test_files_array_shape(self):
        self.assertIn("files", self.pkg)
        self.assertIsInstance(self.pkg["files"], list)

    def test_files_includes_schemas(self):
        self.assertIn("schemas", self.pkg["files"])

    def test_files_includes_scripts(self):
        self.assertIn("scripts", self.pkg["files"])

    def test_files_includes_existing_dirs(self):
        for entry in ("bin", "agents", "commands", "skills"):
            with self.subTest(entry=entry):
                self.assertIn(entry, self.pkg["files"])

    def test_files_has_six_entries(self):
        self.assertEqual(len(self.pkg["files"]), 6)

    def test_bin_entry(self):
        self.assertEqual(self.pkg.get("bin", {}).get("tweakidea"), "bin/install.js")


class TestRealDirectories(unittest.TestCase):
    """Assert the directories referenced in package.json#files actually exist."""

    def test_schemas_directory_exists(self):
        self.assertTrue((ROOT / "schemas").is_dir())

    def test_scripts_directory_exists(self):
        self.assertTrue((ROOT / "scripts").is_dir())

    def test_schemas_has_twelve_files(self):
        count = len(list((ROOT / "schemas").glob("*.json")))
        self.assertEqual(count, 12)

    def test_scripts_has_compute_and_render(self):
        self.assertTrue((ROOT / "scripts" / "compute.py").exists())
        self.assertTrue((ROOT / "scripts" / "render_report.py").exists())

    def test_scripts_has_lib(self):
        for name in ("schema.py", "registry.py", "radar.py", "errors.py"):
            with self.subTest(name=name):
                self.assertTrue((ROOT / "scripts" / "lib" / name).exists())
