"""Python wrapper for the shell-based uv install check (UV-01)."""
import pathlib
import subprocess
import unittest

SHELL_TEST = pathlib.Path(__file__).resolve().parent / "test_install_uv.sh"


class TestInstallUvCheck(unittest.TestCase):
    def test_install_hard_fails_without_uv(self):
        if not SHELL_TEST.exists():
            self.skipTest(f"{SHELL_TEST} not found")
        result = subprocess.run(
            ["bash", str(SHELL_TEST)],
            capture_output=True,
            text=True,
        )
        if result.returncode == 77:
            self.skipTest(result.stdout.strip() or "test environment cannot scrub uv from PATH")
        self.assertEqual(
            result.returncode,
            0,
            f"shell test failed: stdout={result.stdout!r}, stderr={result.stderr!r}",
        )
