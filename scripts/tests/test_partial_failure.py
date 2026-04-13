"""Partial-failure regression test — 13-of-14 dims present."""
import json
import pathlib
import shutil
import subprocess
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
FIXTURES = pathlib.Path(__file__).resolve().parent / "fixtures"
GOLDEN = FIXTURES / "golden-run"
PARTIAL_DIMS = FIXTURES / "dimensions-partial"


class TestPartialFailure(unittest.TestCase):
    def setUp(self):
        # Build a synthetic RUN_DIR: top-level artifacts from golden-run,
        # but dimensions/ subfolder from dimensions-partial/
        self.tmpdir = pathlib.Path(tempfile.mkdtemp())
        run = self.tmpdir / "run"
        run.mkdir()
        # Copy all top-level golden files except dimensions/
        for p in GOLDEN.iterdir():
            if p.is_dir():
                continue
            shutil.copy(p, run / p.name)
        # Copy dimensions-partial as dimensions/
        shutil.copytree(PARTIAL_DIMS, run / "dimensions")
        # Remove numbers.json so compute produces it
        (run / "numbers.json").unlink(missing_ok=True)
        self.run_dir = run

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_partial_failure_survives(self):
        result = subprocess.run(
            ["uv", "run", str(ROOT / "scripts" / "compute.py"), str(self.run_dir)],
            capture_output=True,
            text=True,
        )
        # Exit 0: partial failure is non-fatal
        self.assertEqual(result.returncode, 0,
                         f"compute.py exited {result.returncode}, stderr: {result.stderr}")

        # stderr should contain at least one INVALID_DIMENSION warning
        self.assertIn("INVALID_DIMENSION", result.stderr)

        out = json.loads((self.run_dir / "numbers.json").read_text())
        self.assertIn(out["verdict_bucket"], ("GO", "PIVOT", "STOP"))

        # Rankings still has 14 entries (1 marked failed)
        self.assertEqual(len(out["rankings"]), 14)
        failed = [r for r in out["rankings"] if r.get("failed")]
        self.assertEqual(len(failed), 1)
        self.assertEqual(failed[0]["slug"], "founder-market-fit")

        # The failed dim's ranking has score=None, weighted_score=0
        self.assertIsNone(failed[0]["score"])
        self.assertEqual(failed[0]["weighted_score"], 0.0)


class TestFatalFailures(unittest.TestCase):
    def test_nonexistent_run_dir(self):
        result = subprocess.run(
            ["uv", "run", str(ROOT / "scripts" / "compute.py"), "/tmp/definitely-not-a-dir-xyz123"],
            capture_output=True,
            text=True,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("MISSING_FILE", result.stderr)
