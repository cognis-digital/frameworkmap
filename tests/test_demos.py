"""Guard tests: the shipped demo catalogs load and produce documented numbers.

Keeps demos/ honest — if the catalog or engine drifts, these fail.
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from frameworkmap import load_catalog, coverage_report, find_gaps  # noqa: E402

DEMOS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "demos")


class TestDemoCatalogs(unittest.TestCase):
    def test_every_demo_dir_has_scenario(self):
        for name in os.listdir(DEMOS):
            d = os.path.join(DEMOS, name)
            if os.path.isdir(d):
                self.assertTrue(
                    os.path.exists(os.path.join(d, "SCENARIO.md")),
                    f"{name} missing SCENARIO.md",
                )

    def test_demo01_catalog_loads(self):
        path = os.path.join(DEMOS, "01-basic", "catalog_extra.json")
        cat = load_catalog(path)
        self.assertTrue(any(c.id == "SC-13" for c in cat))

    def test_demo05_startup_catalog_coverage(self):
        path = os.path.join(DEMOS, "05-custom-catalog-startup", "catalog.json")
        cat = load_catalog(path)
        rep = coverage_report("NIST", "SOC2", cat)
        # SCENARIO.md documents 66.7% (6 of 9) — keep it honest.
        self.assertEqual(rep["total_controls"], 9)
        self.assertEqual(rep["covered"], 6)
        self.assertEqual(rep["coverage_pct"], 66.7)
        gap_ids = {g["id"] for g in find_gaps("NIST", "SOC2", cat)}
        self.assertEqual(gap_ids, {"RA-5", "IR-4", "AT-2"})


if __name__ == "__main__":
    unittest.main()
