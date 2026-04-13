"""SVG radar chart math for TweakIdea dimension scorecard.

Ported verbatim from skills/ti-report/SKILL.md lines 166-217 + line 351.
Uniform 360/14 angular wedges; score vertex at radius (score/5)*150 from center.

This module is called by scripts/compute.py; output stored in numbers.json.radar_svg.
scripts/render_report.py interpolates the stored string via Jinja2 {{ radar_svg|safe }}
— no math at render time.
"""
import math
from typing import List, Tuple

CENTER_X = 250
CENTER_Y = 210
MAX_RADIUS = 150
VIEWBOX_W = 500
VIEWBOX_H = 440
LABEL_RADIUS = 175
NUM_DIMS = 14

# Long dimension names get abbreviated labels on the radar (from SKILL.md line 351).
DIMENSION_ABBREVIATIONS = {
    "Founder-Market Fit": "Founder Fit",
    "Clarity of Target Customer": "Target Customer",
    "Behavior Change Required": "Behavior Change",
    "Incumbent Indifference": "Incumbent",
}


def _angle_rad(i: int) -> float:
    """Angle for dimension index i (0-based), with index 0 at top (-90°)."""
    return math.radians(i * (360 / NUM_DIMS) - 90)


def _vertex(i: int, radius: float) -> Tuple[float, float]:
    a = _angle_rad(i)
    return (CENTER_X + radius * math.cos(a),
            CENTER_Y + radius * math.sin(a))


def score_polygon_points(scores: List[int]) -> str:
    """Return 'x1,y1 x2,y2 ...' for 14-vertex polygon at (score/5)*MAX_RADIUS."""
    if len(scores) != NUM_DIMS:
        raise ValueError(f"expected {NUM_DIMS} scores, got {len(scores)}")
    pts = [_vertex(i, (s / 5) * MAX_RADIUS) for i, s in enumerate(scores)]
    return " ".join(f"{x:.1f},{y:.1f}" for x, y in pts)


def grid_polygon_points(level: int) -> str:
    """level 1..5 → 'x1,y1 ...' for a grid ring at radius level*30."""
    if not 1 <= level <= 5:
        raise ValueError(f"level must be 1-5, got {level}")
    radius = level * 30
    pts = [_vertex(i, radius) for i in range(NUM_DIMS)]
    return " ".join(f"{x:.1f},{y:.1f}" for x, y in pts)


def spoke_coords(i: int) -> Tuple[float, float]:
    """Outer endpoint of spoke i (inner endpoint is always center)."""
    return _vertex(i, MAX_RADIUS)


def label_coords(i: int) -> Tuple[float, float, str]:
    """Return (x, y, text_anchor) for the label of dimension index i.

    Text anchor rules (derived from canonical SKILL.md lines 203-216):
    - "middle" when the label is near the top (270°) or bottom (90°) poles,
      within 2 angular steps (2 * 360/14 ≈ 51.4°) of either pole.
    - "end" when on the left half (outside the polar bands).
    - "start" when on the right half (outside the polar bands).
    """
    a_deg = (i * (360 / NUM_DIMS) - 90) % 360
    x, y = _vertex(i, LABEL_RADIUS)

    # Distance to top pole (270°) and bottom pole (90°), in [0, 180]
    dist_top = min(abs(a_deg - 270), 360 - abs(a_deg - 270))
    dist_bot = min(abs(a_deg - 90), 360 - abs(a_deg - 90))
    threshold = 2 * (360 / NUM_DIMS)  # ≈ 51.43°

    if dist_top < threshold or dist_bot < threshold:
        anchor = "middle"
    elif 90 < a_deg < 270:
        anchor = "end"
    else:
        anchor = "start"

    return (x, y, anchor)


def _label_for(full_name: str) -> str:
    return DIMENSION_ABBREVIATIONS.get(full_name, full_name)


def build_svg(scores: List[int], labels: List[str]) -> str:
    """Build the complete <svg>...</svg> string.

    scores: 14 integers in registry index order (Pain Intensity first).
    labels: 14 full dimension names (will be abbreviated via DIMENSION_ABBREVIATIONS).
    """
    if len(scores) != NUM_DIMS:
        raise ValueError(f"expected {NUM_DIMS} scores, got {len(scores)}")
    if len(labels) != NUM_DIMS:
        raise ValueError(f"expected {NUM_DIMS} labels, got {len(labels)}")

    parts: List[str] = []
    parts.append(
        f'<svg viewBox="0 0 {VIEWBOX_W} {VIEWBOX_H}" xmlns="http://www.w3.org/2000/svg">'
    )
    # 5 concentric grid rings
    for level in range(1, 6):
        pts = grid_polygon_points(level)
        parts.append(
            f'  <polygon points="{pts}" fill="none" stroke="#ddd" stroke-width="1"/>'
        )
    # 14 spokes from center to outer ring
    for i in range(NUM_DIMS):
        ex, ey = spoke_coords(i)
        parts.append(
            f'  <line x1="{CENTER_X}" y1="{CENTER_Y}" x2="{ex:.1f}" y2="{ey:.1f}" '
            f'stroke="#ddd" stroke-width="1"/>'
        )
    # Score polygon
    score_pts = score_polygon_points(scores)
    parts.append(
        f'  <polygon points="{score_pts}" fill="rgba(66,153,225,0.3)" '
        f'stroke="#3182ce" stroke-width="2"/>'
    )
    # Labels (abbreviated for long names)
    for i, full in enumerate(labels):
        label_text = _label_for(full)
        lx, ly, anchor = label_coords(i)
        parts.append(
            f'  <text x="{lx:.1f}" y="{ly:.1f}" text-anchor="{anchor}" '
            f'font-size="11" fill="#2d3748">{label_text}</text>'
        )
    parts.append("</svg>")
    return "\n".join(parts)
