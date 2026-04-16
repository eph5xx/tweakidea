"""Golden-fixture regression test for scripts/compute.py."""
import json
import pathlib
import shutil
import subprocess
import sys
import tempfile
import unittest

from scripts.tests import requires_jsonschema

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
FIXTURES = pathlib.Path(__file__).resolve().parent / "fixtures"
GOLDEN = FIXTURES / "golden-run"

try:
    sys.path.insert(0, str(ROOT / "scripts"))
    from compute import grade_from_counts, grade_from_points, points_from_counts  # noqa: E402
except ImportError:
    pass

VALID_GRADES = {"A+", "A", "A-", "B+", "B", "B-", "C", "D", "F"}
TIER_KEYS = ("both_confirmed", "research_only", "founder_only", "assumed")


@requires_jsonschema
class TestComputeGolden(unittest.TestCase):
    """Run compute.py on the golden fixture and assert math."""

    def setUp(self):
        # Copy golden-run to a temp dir so we can run compute.py without clobbering fixture
        self.tmpdir = pathlib.Path(tempfile.mkdtemp())
        shutil.copytree(GOLDEN, self.tmpdir / "run", dirs_exist_ok=True)
        # Delete numbers.json from temp copy so compute.py produces it fresh
        numbers = self.tmpdir / "run" / "numbers.json"
        if numbers.exists():
            numbers.unlink()

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_golden_run(self):
        result = subprocess.run(
            ["uv", "run", str(ROOT / "scripts" / "compute.py"), str(self.tmpdir / "run")],
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0,
                         f"compute.py exited {result.returncode}, stderr: {result.stderr}")
        out = json.loads((self.tmpdir / "run" / "numbers.json").read_text())

        self.assertEqual(out["verdict_bucket"], "PIVOT")
        self.assertAlmostEqual(out["weighted_total"], 3.2, delta=0.15)
        self.assertAlmostEqual(out["potential_total"], 3.5, delta=0.15)
        self.assertEqual(len(out["rankings"]), 14)

        # Index order preserved
        self.assertEqual(out["rankings"][0]["slug"], "pain-intensity")
        self.assertEqual(out["rankings"][-1]["slug"], "incumbent-indifference")

        # Every ranking has evidence_strength with counts + grade
        for r in out["rankings"]:
            self.assertIn("evidence_strength", r)
            es = r["evidence_strength"]
            for t in TIER_KEYS:
                self.assertIn(t, es)
                self.assertIsInstance(es[t], int)
            self.assertIn("grade", es)
            self.assertIn(es["grade"], VALID_GRADES)

        # Overall grade present and valid
        self.assertIn("overall_grade", out)
        self.assertIn(out["overall_grade"], VALID_GRADES)

        # Assumption impact: willingness-to-pay has UNCONFIRMED → score=3, potential=4
        wtp_impacts = [a for a in out["assumption_impact_math"]
                       if a["dim"] == "Willingness to Pay"]
        self.assertGreaterEqual(len(wtp_impacts), 1)

        # Every ranking exposes its registry weight (drives the dim-grid percentage)
        for r in out["rankings"]:
            self.assertIn("weight", r)
            self.assertGreater(r["weight"], 0)
            self.assertLessEqual(r["weight"], 1)

        # Evidence totals aggregate per-dim counts
        self.assertIn("evidence_totals", out)
        totals = out["evidence_totals"]
        for t in TIER_KEYS:
            self.assertIn(t, totals)
            self.assertEqual(
                totals[t],
                sum(r["evidence_strength"][t] for r in out["rankings"] if not r.get("failed")),
            )

        # Reach-potential blocks grouped per dimension where potential > score
        self.assertIn("reach_potential_blocks", out)
        for block in out["reach_potential_blocks"]:
            self.assertGreater(block["to"], block["from"])
            self.assertGreater(len(block["assumption_texts"]), 0)
        # Willingness to Pay should appear in the blocks (score=3, potential=4)
        wtp_blocks = [b for b in out["reach_potential_blocks"] if b["dim"] == "Willingness to Pay"]
        self.assertEqual(len(wtp_blocks), 1)


def c(bc=0, ro=0, fo=0, a=0):
    return {"both_confirmed": bc, "research_only": ro, "founder_only": fo, "assumed": a}


@requires_jsonschema
class TestGradeFormula(unittest.TestCase):
    """Unit tests for the points→grade formula."""

    def test_zero_evidence_is_F(self):
        self.assertEqual(grade_from_counts(c()), "F")

    def test_all_assumed_is_F(self):
        # Assumed contributes 0 points regardless of count.
        self.assertEqual(grade_from_counts(c(a=10)), "F")

    def test_research_only_does_not_penalize(self):
        # 5 research_only = 10 points → B-, same as 5 mixed confirmed+research of similar weight.
        self.assertEqual(grade_from_counts(c(ro=5)), "B-")

    def test_grade_boundaries(self):
        # Exact threshold hits
        self.assertEqual(grade_from_points(24), "A+")
        self.assertEqual(grade_from_points(23), "A")
        self.assertEqual(grade_from_points(21), "A")
        self.assertEqual(grade_from_points(20), "A-")
        self.assertEqual(grade_from_points(18), "A-")
        self.assertEqual(grade_from_points(17), "B+")
        self.assertEqual(grade_from_points(15), "B+")
        self.assertEqual(grade_from_points(14), "B")
        self.assertEqual(grade_from_points(12), "B")
        self.assertEqual(grade_from_points(11), "B-")
        self.assertEqual(grade_from_points(9), "B-")
        self.assertEqual(grade_from_points(8), "C")
        self.assertEqual(grade_from_points(6), "C")
        self.assertEqual(grade_from_points(5), "D")
        self.assertEqual(grade_from_points(3), "D")
        self.assertEqual(grade_from_points(2), "F")
        self.assertEqual(grade_from_points(0), "F")

    def test_typical_strong_dim(self):
        # 2 both + 3 research + 1 founder + 0 assumed = 6+6+1 = 13 → B
        self.assertEqual(grade_from_counts(c(bc=2, ro=3, fo=1)), "B")

    def test_typical_weak_dim(self):
        # 0 both + 0 research + 2 founder + 2 assumed = 0+0+2 = 2 → F
        self.assertEqual(grade_from_counts(c(fo=2, a=2)), "F")

    def test_high_volume_strong(self):
        # 4 both + 4 research + 2 founder = 12+8+2 = 22 → A
        self.assertEqual(grade_from_counts(c(bc=4, ro=4, fo=2)), "A")

    def test_heavy_research_A_minus(self):
        # 2 both + 6 research = 6+12 = 18 → A-
        self.assertEqual(grade_from_counts(c(bc=2, ro=6)), "A-")

    def test_single_both_confirmed_is_D(self):
        # 1 both = 3 points → D (count participation: not enough volume for higher)
        self.assertEqual(grade_from_counts(c(bc=1)), "D")

    def test_points_weighting(self):
        self.assertEqual(points_from_counts(c(bc=1)), 3)
        self.assertEqual(points_from_counts(c(ro=1)), 2)
        self.assertEqual(points_from_counts(c(fo=1)), 1)
        self.assertEqual(points_from_counts(c(a=1)), 0)
