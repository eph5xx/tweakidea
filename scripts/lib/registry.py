"""Parse the Dimension Registry table from skills/ti-scoring/EVALUATION.md.

Reads the 7-column pipe-delimited table and returns a list of Dimension
NamedTuples in registry index order (1..14). This is a stability contract —
the 7-column format is the canonical source of truth for dimension metadata
in the Phase 1 pipeline (D-26).
"""
import pathlib
from typing import List, NamedTuple, Optional


class Dimension(NamedTuple):
    index: int
    name: str
    weight: float
    slug: str
    output_filename: str  # Dead metadata in Phase 1 — preserved per D-26 stability contract
    research_cluster: Optional[str]
    context_variant: str


_REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
_EVALUATION_MD = _REPO_ROOT / "skills" / "ti-scoring" / "EVALUATION.md"


def load_registry(path: Optional[pathlib.Path] = None) -> List[Dimension]:
    """Parse EVALUATION.md and return 14 Dimension NamedTuples in index order.

    Raises ValueError if the registry doesn't contain exactly 14 rows or if
    any row doesn't have 7 pipe-delimited columns.
    """
    src_path = path or _EVALUATION_MD
    lines = src_path.read_text().splitlines()
    dims: List[Dimension] = []
    in_table = False
    for line in lines:
        line = line.rstrip()
        if not in_table:
            if line.startswith("| # |"):
                in_table = True
            continue
        if line.startswith("|---") or not line.startswith("|"):
            if dims and not line.startswith("|"):
                break  # exited the table
            continue
        parts = [c.strip() for c in line.strip("|").split("|")]
        if len(parts) != 7:
            continue  # tolerate blank rows
        try:
            idx = int(parts[0])
        except ValueError:
            break  # first non-int row = end of data rows
        weight = float(parts[2].rstrip("%")) / 100
        cluster = None if parts[5] in ("—", "-", "") else parts[5]
        dims.append(Dimension(
            index=idx,
            name=parts[1],
            weight=weight,
            slug=parts[3],
            output_filename=parts[4],
            research_cluster=cluster,
            context_variant=parts[6],
        ))
    if len(dims) != 14:
        raise ValueError(
            f"expected 14 dimensions in registry, got {len(dims)} from {src_path}"
        )
    return dims


def total_weight(dims: List[Dimension]) -> float:
    """Return sum of weights across all dimensions."""
    return sum(d.weight for d in dims)
