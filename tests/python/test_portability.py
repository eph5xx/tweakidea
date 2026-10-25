"""Portability guard: Claude Code tool names live only in references/runtime.md.

Every other file in the skill names capabilities (`ask-user`, `spawn-subagent`,
`web-search`, ...) so the skill works in any Agent Skills-compatible agent.
SKILL.md may keep Claude Code identifiers only on a few known lines.
"""
import pathlib
import re
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
SKILL = ROOT / "skills" / "tweakidea"
RUNTIME_MD = SKILL / "references" / "runtime.md"

FORBIDDEN = [
    ("AskUserQuestion", re.compile(r"AskUserQuestion")),
    ("general-purpose", re.compile(r"general-purpose")),
    ("run_in_background", re.compile(r"run_in_background")),
    ("ToolSearch", re.compile(r"ToolSearch")),
    ("WebSearch", re.compile(r"WebSearch")),
    ("WebFetch", re.compile(r"WebFetch")),
    ("sonnet", re.compile(r"\bsonnet\b", re.IGNORECASE)),
    ("opus", re.compile(r"\bopus\b", re.IGNORECASE)),
    (".claude/", re.compile(r"\.claude/")),
    ("the X tool", re.compile(r"\b(?:Read|Write|Edit|Bash|Glob|Grep|Agent)`? tool\b")),
    ("Agent()", re.compile(r"\bAgent\(\)")),
]

# SKILL.md lines that may name Claude Code identifiers, keyed by line prefix.
SKILL_MD_ALLOWED_PREFIXES = (
    "allowed-tools:",
    "compatibility:",
    "$ARGUMENTS",
    "1. **SKILL_DIR**",
)


def iter_text_files():
    for p in sorted(SKILL.rglob("*")):
        if not p.is_file() or "__pycache__" in p.parts:
            continue
        if p.suffix not in {".md", ".py", ".j2", ".json", ".css"}:
            continue
        yield p


class TestPortability(unittest.TestCase):
    def test_claude_code_identifiers_only_in_runtime_md(self):
        hits = []
        for p in iter_text_files():
            if p == RUNTIME_MD:
                continue
            is_skill_md = p == SKILL / "SKILL.md"
            for lineno, line in enumerate(p.read_text().splitlines(), 1):
                if is_skill_md and line.startswith(SKILL_MD_ALLOWED_PREFIXES):
                    continue
                for label, rx in FORBIDDEN:
                    if rx.search(line):
                        hits.append(f"{p.relative_to(ROOT)}:{lineno}: {label}")
        self.assertEqual(hits, [], "Claude Code identifiers outside runtime.md:\n" + "\n".join(hits))

    def test_runtime_md_maps_every_capability(self):
        text = RUNTIME_MD.read_text()
        for capability, tool in (
            ("ask-user", "AskUserQuestion"),
            ("spawn-subagent", "Agent"),
            ("parallel-spawn", "Agent"),
            ("background-spawn", "run_in_background"),
            ("web-search", "WebSearch"),
            ("web-fetch", "WebFetch"),
            ("read-file", "Read"),
            ("write-file", "Write"),
            ("find-files", "Glob"),
            ("search-text", "Grep"),
            ("shell", "Bash"),
        ):
            with self.subTest(capability=capability):
                row = re.search(rf"^\| `{capability}` \|.*$", text, re.MULTILINE)
                self.assertIsNotNone(row, f"runtime.md has no row for {capability}")
                self.assertIn(tool, row.group(0))

    def test_references_use_ask_user(self):
        for name in ("evaluate", "browse-hn", "diff", "improve", "show", "share"):
            with self.subTest(command=name):
                self.assertIn("`ask-user`", (SKILL / "references" / "commands" / f"{name}.md").read_text())
        for path in (SKILL / "references" / "commands" / "analyze-hn-post.md", SKILL / "references" / "founder.md"):
            with self.subTest(path=path.name):
                self.assertIn("ask in chat", path.read_text().lower())

    def test_no_batched_questions_outside_runtime_md(self):
        forbidden = ("multiSelect", "up to 4 questions", "chunks of up to 4", "single `ask-user` call", "Pack up to")
        hits = []
        for p in iter_text_files():
            if p == RUNTIME_MD:
                continue
            for lineno, line in enumerate(p.read_text().splitlines(), 1):
                for phrase in forbidden:
                    if phrase in line:
                        hits.append(f"{p.relative_to(ROOT)}:{lineno}: {phrase}")
        self.assertEqual(hits, [], "Batched question wording outside runtime.md:\n" + "\n".join(hits))

    def test_runtime_md_defines_question_protocol(self):
        section = RUNTIME_MD.read_text().split("## Asking questions", 1)[1]
        self.assertIn("exactly one question per call", section)
        self.assertIn("Ask in chat", section)
        self.assertIn("Never put several items that each need their own answer into one question", section)

    def test_no_installer_specific_reinstall_hint(self):
        for p in iter_text_files():
            with self.subTest(path=str(p.relative_to(ROOT))):
                self.assertNotIn("npx tweakidea", p.read_text())


if __name__ == "__main__":
    unittest.main()
