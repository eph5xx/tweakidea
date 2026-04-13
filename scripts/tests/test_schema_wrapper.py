"""Tests for scripts.lib.schema wrapper."""
import json
import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from lib import schema  # noqa: E402
from jsonschema import ValidationError  # noqa: E402

FIXTURES = pathlib.Path(__file__).resolve().parent / "fixtures"
GOLDEN = FIXTURES / "golden-run"
FAIL = FIXTURES / "schema_fail"


class TestValidatePass(unittest.TestCase):
    """Every golden-run fixture should pass its schema."""
    CASES = [
        ("idea.json", "idea"),
        ("hypotheses.json", "hypotheses"),
        ("assumptions.json", "assumptions"),
        ("research.json", "research"),
        ("numbers.json", "numbers"),
        ("verdict.json", "verdict"),
        ("strengths-weaknesses.json", "strengths-weaknesses"),
        ("next-steps.json", "next-steps"),
        ("dealbreakers.json", "dealbreakers"),
        ("potential.json", "potential"),
        ("version.json", "version"),
    ]

    def test_golden_run_artifacts_pass(self):
        for file_name, schema_name in self.CASES:
            with self.subTest(file=file_name):
                schema.validate_file(GOLDEN / file_name, schema_name)

    def test_all_dimensions_pass(self):
        for p in (GOLDEN / "dimensions").glob("*.json"):
            with self.subTest(dim=p.name):
                schema.validate_file(p, "dimension-evaluation")


class TestValidateFail(unittest.TestCase):
    """Every schema_fail fixture should raise ValidationError."""
    CASES = [
        ("dimension-bad-score.json", "dimension-evaluation"),
        ("dimension-extra-field.json", "dimension-evaluation"),
        ("dimension-missing-required.json", "dimension-evaluation"),
        ("numbers-bad-bucket.json", "numbers"),
        ("verdict-too-long.json", "verdict"),
        ("sw-wrong-count.json", "strengths-weaknesses"),
        ("idea-missing-text.json", "idea"),
        ("hypotheses-bad-status.json", "hypotheses"),
        ("research-missing-available.json", "research"),
        ("assumptions-bad-status.json", "assumptions"),
        ("next-steps-empty-task.json", "next-steps"),
        ("version-missing-schema.json", "version"),
        ("dealbreakers-wrong-shape.json", "dealbreakers"),
        ("potential-missing-dims.json", "potential"),
    ]

    def test_fail_fixtures_reject(self):
        for file_name, schema_name in self.CASES:
            with self.subTest(file=file_name):
                with self.assertRaises(ValidationError):
                    schema.validate_file(FAIL / file_name, schema_name)


class TestPathTraversalGuard(unittest.TestCase):
    def test_rejects_parent_traversal(self):
        with self.assertRaises(ValueError):
            schema.validate({}, "../etc/passwd")

    def test_rejects_slash(self):
        with self.assertRaises(ValueError):
            schema.validate({}, "subdir/foo")

    def test_missing_schema_raises(self):
        with self.assertRaises(FileNotFoundError):
            schema.validate({}, "definitely-not-a-real-schema-name")
