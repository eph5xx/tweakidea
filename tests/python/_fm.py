"""Shared parsers for the agent spawn contract and the runtime capability map.

Agent references are plain markdown (no frontmatter). Each one starts with:

    > **Tools and budget:** Model tier: fast. Tools: read-file, write-file. Turn budget: 15 turns. ...

`references/runtime.md` maps each model tier to a Claude Code model.
"""
import pathlib
import re

RUNTIME_MD = (
    pathlib.Path(__file__).resolve().parent.parent.parent
    / "skills" / "tweakidea" / "references" / "runtime.md"
)

_CONTRACT_RE = re.compile(
    r"^> \*\*Tools and budget:\*\* Model tier: (\w+)\. Tools: ([^.]+)\. Turn budget: (\d+) turns\.",
    re.MULTILINE,
)


def parse_spawn_contract(md_text: str) -> dict:
    """Return {"tier": str, "tools": list[str], "maxTurns": str}.

    Raises ValueError if the contract line is missing.
    """
    m = _CONTRACT_RE.search(md_text)
    if not m:
        raise ValueError("no 'Tools and budget' line found")
    return {
        "tier": m.group(1),
        "tools": [t.strip() for t in m.group(2).split(",")],
        "maxTurns": m.group(3),
    }


def claude_model_for_tier(tier: str) -> str:
    """Return the Claude Code model that runtime.md maps a model tier to."""
    m = re.search(
        rf"^\| `{re.escape(tier)}` \| [^|]+ \| `(\w+)` \|", RUNTIME_MD.read_text(), re.MULTILINE
    )
    if not m:
        raise ValueError(f"no model tier row for {tier!r} in runtime.md")
    return m.group(1)
