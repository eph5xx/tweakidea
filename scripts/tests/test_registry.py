"""Unit tests for scripts.lib.registry."""
import pathlib
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from lib import registry  # noqa: E402


class TestLoadRegistry(unittest.TestCase):
    def test_fourteen_dimensions(self):
        dims = registry.load_registry()
        self.assertEqual(len(dims), 14)

    def test_index_order(self):
        dims = registry.load_registry()
        for i, d in enumerate(dims, start=1):
            self.assertEqual(d.index, i, f"dim at position {i} has index {d.index}")

    def test_weight_sum_is_one(self):
        dims = registry.load_registry()
        total = registry.total_weight(dims)
        self.assertAlmostEqual(total, 1.00, places=3,
                               msg=f"weights sum to {total}, expected 1.00")

    def test_pain_intensity_first(self):
        dims = registry.load_registry()
        d = dims[0]
        self.assertEqual(d.name, "Pain Intensity")
        self.assertEqual(d.slug, "pain-intensity")
        self.assertAlmostEqual(d.weight, 0.12, places=3)
        self.assertEqual(d.research_cluster, "USER_CLUSTER")
        self.assertEqual(d.context_variant, "EVALUATION_CONTEXT")

    def test_founder_market_fit_has_no_cluster(self):
        dims = registry.load_registry()
        fmf = next(d for d in dims if d.slug == "founder-market-fit")
        self.assertIsNone(fmf.research_cluster)
        self.assertEqual(fmf.context_variant, "FOUNDER_EVALUATION_CONTEXT")

    def test_incumbent_indifference_last(self):
        dims = registry.load_registry()
        last = dims[-1]
        self.assertEqual(last.index, 14)
        self.assertEqual(last.slug, "incumbent-indifference")
        self.assertAlmostEqual(last.weight, 0.02, places=3)

    def test_all_14_slugs_present(self):
        dims = registry.load_registry()
        expected = {
            "pain-intensity", "willingness-to-pay", "solution-gap",
            "founder-market-fit", "urgency", "frequency", "market-size",
            "defensibility", "market-growth", "scalability",
            "clarity-of-target-customer", "behavior-change-required",
            "mandatory-nature", "incumbent-indifference",
        }
        self.assertEqual(set(d.slug for d in dims), expected)

    def test_custom_path(self):
        """load_registry() accepts a custom path parameter."""
        # Passing the real EVALUATION.md via explicit path should work identically
        real_path = ROOT / "skills" / "ti-scoring" / "EVALUATION.md"
        dims = registry.load_registry(path=real_path)
        self.assertEqual(len(dims), 14)


class TestMalformedRegistry(unittest.TestCase):
    def test_missing_rows_raises(self):
        bad = tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False)
        bad.write("| # | Name | Weight | File Slug | Output Filename | Research Cluster | Context Variant |\n")
        bad.write("|---|------|--------|-----------|-----------------|------------------|-----------------|\n")
        bad.write("| 01 | Pain Intensity | 12% | pain-intensity | 01-pain-intensity.md | USER_CLUSTER | EVALUATION_CONTEXT |\n")
        bad.close()
        with self.assertRaises(ValueError):
            registry.load_registry(pathlib.Path(bad.name))


if __name__ == "__main__":
    unittest.main()
