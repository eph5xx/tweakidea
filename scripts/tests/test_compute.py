"""Golden-fixture regression test for scripts/compute.py."""
import json
import pathlib
import shutil
import subprocess
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
FIXTURES = pathlib.Path(__file__).resolve().parent / "fixtures"
GOLDEN = FIXTURES / "golden-run"


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

        # Every ranking has tier_counts
        for r in out["rankings"]:
            self.assertIn("tier_counts", r)
            for t in ("verified", "research", "founder", "assumed"):
                self.assertIn(t, r["tier_counts"])

        # No dealbreakers in golden fixture (no dim scores 1)
        self.assertEqual(out["dealbreaker_dims"], [])

        # Evidence quality percentages sum to ~100
        eq = out["evidence_quality"]
        total = eq["verified_pct"] + eq["research_pct"] + eq["founder_pct"] + eq["assumed_pct"]
        self.assertAlmostEqual(total, 100, delta=2)

        # Assumption impact: willingness-to-pay has UNCONFIRMED → score=3, potential=4
        wtp_impacts = [a for a in out["assumption_impact_math"]
                       if a["dim"] == "Willingness to Pay"]
        self.assertGreaterEqual(len(wtp_impacts), 1)

        # Radar SVG valid
        self.assertTrue(out["radar_svg"].startswith('<svg viewBox="0 0 500 440"'))
        self.assertIn("</svg>", out["radar_svg"])
