"""Shared minimal YAML frontmatter parser for TweakIdea agent test files.

Handles the subset of YAML used by TweakIdea agent files:
- `key: value` scalars
- `key:` followed by `  - item` lists (2-space indent)
- `key: []` empty list shorthand

Does NOT support YAML flow style, anchors, multi-line strings — TweakIdea agents don't use those.
"""
import re


def parse_frontmatter(md_text: str) -> dict:
    """Parse YAML frontmatter from a markdown file.

    Returns a dict of key -> value (scalar string) or key -> list[str].
    Raises ValueError if no frontmatter block is found.
    """
    m = re.match(r"^---\n(.*?)\n---\n", md_text, re.DOTALL)
    if not m:
        raise ValueError("no frontmatter found")
    block = m.group(1)
    result: dict = {}
    current_key: str | None = None
    current_list: list | None = None
    for raw in block.split("\n"):
        if not raw.strip():
            continue
        if raw.startswith("  - "):
            if current_list is None:
                result[current_key] = []
                current_list = result[current_key]
            current_list.append(raw[4:].strip())
            continue
        if ":" in raw:
            key, _, val = raw.partition(":")
            key = key.strip()
            val = val.strip()
            if val == "" or val == "[]":
                result[key] = [] if val == "[]" else None
                current_key = key
                current_list = result[key] if val == "[]" else None
            else:
                result[key] = val
                current_key = key
                current_list = None
    return result
