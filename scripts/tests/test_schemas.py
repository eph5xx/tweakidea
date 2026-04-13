"""Schema structural integrity + FAIL fixture validation."""
import json
import pathlib
import unittest

SCHEMAS_DIR = pathlib.Path(__file__).resolve().parent.parent.parent / "schemas"
FIXTURES = pathlib.Path(__file__).resolve().parent / "fixtures"


class TestSchemaPresence(unittest.TestCase):
    EXPECTED_SCHEMAS = [
        "idea", "hypotheses", "assumptions", "research",
        "dimension-evaluation", "numbers", "verdict",
        "strengths-weaknesses", "next-steps", "dealbreakers",
        "potential", "version",
    ]

    def test_twelve_schemas_exist(self):
        files = sorted(p.stem for p in SCHEMAS_DIR.glob("*.json"))
        self.assertEqual(len(files), 12, f"expected 12 schemas, got {len(files)}: {files}")
        self.assertEqual(sorted(self.EXPECTED_SCHEMAS), files)

    def test_config_json_deferred(self):
        self.assertFalse((SCHEMAS_DIR / "config.json").exists(),
                         "config.json must not exist in Phase 1 (deferred to Phase 6)")


class TestAdditionalPropertiesReject(unittest.TestCase):
    def test_every_schema_has_additional_properties_false(self):
        for p in SCHEMAS_DIR.glob("*.json"):
            with self.subTest(schema=p.name):
                content = p.read_text()
                self.assertIn('"additionalProperties": false', content,
                              f"{p.name} missing additionalProperties: false")


class TestVersionShape(unittest.TestCase):
    def test_version_schema_requires_schema_version(self):
        s = json.loads((SCHEMAS_DIR / "version.json").read_text())
        self.assertIn("schema_version", s.get("required", []))
