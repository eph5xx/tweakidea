"""Tests for scripts.lib.errors module."""
import io
import json
import pathlib
import sys
import unittest
from contextlib import redirect_stderr
from unittest.mock import patch

from scripts.tests import _SKIP_MSG

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from lib import errors  # noqa: E402


class TestEmit(unittest.TestCase):
    def test_emit_produces_single_line_json(self):
        buf = io.StringIO()
        with redirect_stderr(buf):
            errors.emit("TEST_CODE", "/path/to/file", "hint text", "something broke")
        line = buf.getvalue().strip()
        self.assertEqual(line.count("\n"), 0, "emit must produce exactly one line")
        parsed = json.loads(line)
        self.assertEqual(parsed["code"], "TEST_CODE")
        self.assertEqual(parsed["path"], "/path/to/file")
        self.assertEqual(parsed["hint"], "hint text")
        self.assertEqual(parsed["error"], "something broke")

    def test_emit_does_not_exit(self):
        buf = io.StringIO()
        with redirect_stderr(buf):
            errors.emit("X", "y", "z", "w")
        # Reached this line = did not exit
        self.assertTrue(True)


class TestDie(unittest.TestCase):
    def test_die_calls_sys_exit_1(self):
        buf = io.StringIO()
        with redirect_stderr(buf):
            with self.assertRaises(SystemExit) as ctx:
                errors.die("FATAL", "/path", "hint", "boom")
        self.assertEqual(ctx.exception.code, 1)

    def test_die_custom_exit_code(self):
        with redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit) as ctx:
                errors.die("X", "y", "z", "w", exit_code=42)
        self.assertEqual(ctx.exception.code, 42)


class TestFromValidationError(unittest.TestCase):
    def test_deque_absolute_path_serializes(self):
        try:
            from jsonschema import Draft202012Validator
        except ImportError:
            self.skipTest(_SKIP_MSG)
        v = Draft202012Validator({"type": "object", "required": ["x"]})
        errs = list(v.iter_errors({}))
        self.assertTrue(errs)

        buf = io.StringIO()
        with redirect_stderr(buf):
            with self.assertRaises(SystemExit):
                errors.from_validation_error(errs[0], "test.json")
        parsed = json.loads(buf.getvalue().strip())
        self.assertEqual(parsed["code"], "SCHEMA_VIOLATION")
        self.assertIn("test.json", parsed["path"])
