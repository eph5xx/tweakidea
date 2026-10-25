"""Shared parser for the spawn contract line at the top of each agent reference.

Agent references are plain markdown (no frontmatter). Each one starts with:

    > **Tools and budget:** Model: sonnet. Tools: Read, Write. Turn budget: 15 turns. ...
"""
import re

_CONTRACT_RE = re.compile(
    r"^> \*\*Tools and budget:\*\* Model: (\w+)\. Tools: ([^.]+)\. Turn budget: (\d+) turns\.",
    re.MULTILINE,
)


def parse_spawn_contract(md_text: str) -> dict:
    """Return {"model": str, "tools": list[str], "maxTurns": str}.

    Raises ValueError if the contract line is missing.
    """
    m = _CONTRACT_RE.search(md_text)
    if not m:
        raise ValueError("no 'Tools and budget' line found")
    return {
        "model": m.group(1),
        "tools": [t.strip() for t in m.group(2).split(",")],
        "maxTurns": m.group(3),
    }
