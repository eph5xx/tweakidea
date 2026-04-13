"""Unit tests for scripts.lib.radar."""
import math
import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from lib import radar  # noqa: E402


DIM_NAMES = [
    "Pain Intensity", "Willingness to Pay", "Solution Gap",
    "Founder-Market Fit", "Urgency", "Frequency", "Market Size",
    "Defensibility", "Market Growth", "Scalability",
    "Clarity of Target Customer", "Behavior Change Required",
    "Mandatory Nature", "Incumbent Indifference",
]


class TestScorePolygon(unittest.TestCase):
    def test_all_threes_at_mid_radius(self):
        pts_str = radar.score_polygon_points([3] * 14)
        points = [tuple(map(float, p.split(","))) for p in pts_str.split()]
        self.assertEqual(len(points), 14)
        # (3/5)*150 = 90 — distance from (250, 210) should be 90
        for x, y in points:
            dist = math.hypot(x - 250, y - 210)
            self.assertAlmostEqual(dist, 90.0, places=1)

    def test_wrong_length_raises(self):
        with self.assertRaises(ValueError):
            radar.score_polygon_points([3] * 13)


class TestGridPolygon(unittest.TestCase):
    def test_level_5_at_max_radius(self):
        pts_str = radar.grid_polygon_points(5)
        points = [tuple(map(float, p.split(","))) for p in pts_str.split()]
        self.assertEqual(len(points), 14)
        for x, y in points:
            dist = math.hypot(x - 250, y - 210)
            self.assertAlmostEqual(dist, 150.0, places=1)

    def test_level_out_of_range(self):
        with self.assertRaises(ValueError):
            radar.grid_polygon_points(0)
        with self.assertRaises(ValueError):
            radar.grid_polygon_points(6)


class TestLabelCoords(unittest.TestCase):
    def test_index_0_is_top(self):
        x, y, anchor = radar.label_coords(0)
        # Top of radar: angle = -90°, so label at (250, 210-175) = (250, 35)
        self.assertAlmostEqual(x, 250.0, places=1)
        self.assertAlmostEqual(y, 35.0, places=1)
        self.assertEqual(anchor, "middle")

    def test_index_1_is_middle(self):
        """Index 1 (Willingness to Pay) is near top — should be 'middle'."""
        _, _, anchor = radar.label_coords(1)
        self.assertEqual(anchor, "middle")

    def test_index_2_is_start(self):
        """Index 2 (Solution Gap) is on the right — should be 'start'."""
        _, _, anchor = radar.label_coords(2)
        self.assertEqual(anchor, "start")

    def test_index_9_is_end(self):
        """Index 9 (Scalability) is on the left — should be 'end'."""
        _, _, anchor = radar.label_coords(9)
        self.assertEqual(anchor, "end")

    def test_index_7_is_bottom_middle(self):
        """Index 7 (Defensibility) is at the bottom — should be 'middle'."""
        _, _, anchor = radar.label_coords(7)
        self.assertEqual(anchor, "middle")

    def test_index_13_is_middle(self):
        """Index 13 (Incumbent Indifference) is near top-left — should be 'middle'."""
        _, _, anchor = radar.label_coords(13)
        self.assertEqual(anchor, "middle")


class TestBuildSvg(unittest.TestCase):
    def test_svg_envelope(self):
        svg = radar.build_svg([3] * 14, DIM_NAMES)
        self.assertTrue(svg.startswith('<svg viewBox="0 0 500 440"'))
        self.assertTrue(svg.endswith("</svg>"))

    def test_svg_deterministic(self):
        a = radar.build_svg([3] * 14, DIM_NAMES)
        b = radar.build_svg([3] * 14, DIM_NAMES)
        self.assertEqual(a, b)

    def test_svg_contains_all_abbreviated_labels(self):
        svg = radar.build_svg([3] * 14, DIM_NAMES)
        # Abbreviations from SKILL.md line 351
        self.assertIn("Founder Fit", svg)
        self.assertIn("Target Customer", svg)
        self.assertIn("Behavior Change", svg)
        self.assertIn("Incumbent", svg)
        # Unabbreviated names
        self.assertIn("Pain Intensity", svg)
        self.assertIn("Willingness to Pay", svg)

    def test_svg_has_score_polygon(self):
        svg = radar.build_svg([4, 3, 2, 3, 5, 4, 3, 2, 3, 4, 3, 3, 2, 3], DIM_NAMES)
        self.assertIn('polygon points="', svg)
        self.assertIn('fill="rgba(66,153,225,0.3)"', svg)

    def test_svg_has_five_grid_rings(self):
        svg = radar.build_svg([3] * 14, DIM_NAMES)
        # 5 rings + 1 score polygon = 6 <polygon> tags
        self.assertEqual(svg.count("<polygon"), 6)

    def test_svg_has_14_spokes(self):
        svg = radar.build_svg([3] * 14, DIM_NAMES)
        self.assertEqual(svg.count("<line "), 14)

    def test_svg_has_14_labels(self):
        svg = radar.build_svg([3] * 14, DIM_NAMES)
        self.assertEqual(svg.count("<text "), 14)


if __name__ == "__main__":
    unittest.main()
