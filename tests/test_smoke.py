"""Smoke tests for FRAMEWORKMAP. No network. Standard library only."""
import io
import json
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from frameworkmap import (  # noqa: E402
    TOOL_NAME,
    TOOL_VERSION,
    FRAMEWORKS,
    load_catalog,
    map_control,
    crosswalk_framework,
    coverage_report,
    find_gaps,
)
from frameworkmap.cli import main  # noqa: E402


class TestCore(unittest.TestCase):
    def test_metadata(self):
        self.assertEqual(TOOL_NAME, "frameworkmap")
        self.assertTrue(TOOL_VERSION)
        self.assertIn("NIST", FRAMEWORKS)

    def test_catalog_loads(self):
        cat = load_catalog()
        self.assertGreater(len(cat), 30)
        self.assertTrue(all(c.framework in FRAMEWORKS for c in cat))

    def test_map_control_crosses_frameworks(self):
        cw = map_control("AC-2")
        self.assertEqual(cw.source["framework"], "NIST")
        # AC-2 carries AC + IA objectives; must reach SOC2 and ISO27001.
        self.assertTrue(cw.mappings["SOC2"])
        self.assertTrue(cw.mappings["ISO27001"])
        soc2_ids = {m["id"] for m in cw.mappings["SOC2"]}
        self.assertIn("CC6.1", soc2_ids)
        # source framework is never a mapping target
        self.assertNotIn("NIST", cw.mappings)

    def test_map_case_insensitive(self):
        cw = map_control("ac-2")
        self.assertEqual(cw.source["id"], "AC-2")

    def test_map_unknown_raises(self):
        with self.assertRaises(KeyError):
            map_control("ZZ-999")

    def test_crosswalk_and_coverage(self):
        rows = crosswalk_framework("NIST", "ISO27001")
        self.assertTrue(any(r["matches"] for r in rows))
        rep = coverage_report("NIST", "ISO27001")
        self.assertEqual(rep["total_controls"], len(rows))
        self.assertGreater(rep["coverage_pct"], 0)
        self.assertLessEqual(rep["coverage_pct"], 100)

    def test_gaps_are_uncovered(self):
        gaps = find_gaps("NIST", "PCI")
        gap_ids = {g["id"] for g in gaps}
        # NIST RA-3 (risk assessment) and CP-9 (backup/contingency) have no PCI
        # equivalent in the catalog spine — PCI carries no RA or CP objective.
        self.assertIn("RA-3", gap_ids)
        self.assertIn("CP-9", gap_ids)

    def test_bad_framework_raises(self):
        with self.assertRaises(ValueError):
            crosswalk_framework("NIST", "NOPE")


class TestCLI(unittest.TestCase):
    def _run(self, argv):
        buf = io.StringIO()
        old = sys.stdout
        sys.stdout = buf
        try:
            code = main(argv)
        finally:
            sys.stdout = old
        return code, buf.getvalue()

    def test_map_json(self):
        code, out = self._run(["--format", "json", "map", "AC-2"])
        self.assertEqual(code, 0)
        data = json.loads(out)
        self.assertEqual(data["source"]["id"], "AC-2")
        self.assertIn("mappings", data)

    def test_coverage_table(self):
        code, out = self._run(["coverage", "SOC2", "ISO27001"])
        self.assertEqual(code, 0)
        self.assertIn("coverage", out)

    def test_unknown_control_nonzero(self):
        code, _ = self._run(["map", "ZZ-999"])
        self.assertEqual(code, 1)

    def test_frameworks_json(self):
        code, out = self._run(["--format", "json", "frameworks"])
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(out), FRAMEWORKS)


class TestExportFormats(unittest.TestCase):
    """csv / md tabular export formats (added in this release)."""

    def _run(self, argv):
        buf = io.StringIO()
        old = sys.stdout
        sys.stdout = buf
        try:
            code = main(argv)
        finally:
            sys.stdout = old
        return code, buf.getvalue()

    def test_csv_map_has_header_and_rows(self):
        import csv as _csv
        code, out = self._run(["--format", "csv", "map", "AC-2"])
        self.assertEqual(code, 0)
        rows = list(_csv.reader(io.StringIO(out)))
        self.assertEqual(rows[0],
                         ["source_framework", "source_id", "source_title",
                          "target_framework", "target_id", "target_title", "via"])
        # at least one real mapping row to SOC2 CC6.1
        body = rows[1:]
        self.assertTrue(any(r[3] == "SOC2" and r[4] == "CC6.1" for r in body))
        # every data row carries the source control id
        self.assertTrue(all(r[1] == "AC-2" for r in body))

    def test_csv_coverage_single_row(self):
        import csv as _csv
        code, out = self._run(["--format", "csv", "coverage", "NIST", "PCI"])
        self.assertEqual(code, 0)
        rows = list(_csv.reader(io.StringIO(out)))
        self.assertEqual(rows[0],
                         ["source", "target", "total_controls", "covered",
                          "uncovered", "coverage_pct"])
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[1][0], "NIST")
        self.assertEqual(rows[1][1], "PCI")

    def test_csv_gaps_names_frameworks(self):
        import csv as _csv
        code, out = self._run(["--format", "csv", "gaps", "NIST", "PCI"])
        self.assertEqual(code, 0)
        rows = list(_csv.reader(io.StringIO(out)))
        ids = {r[1] for r in rows[1:]}
        self.assertIn("CP-9", ids)
        self.assertIn("RA-3", ids)
        # source/target framework columns are populated
        self.assertTrue(all(r[0] == "NIST" and r[3] == "PCI" for r in rows[1:]))

    def test_md_crosswalk_is_table(self):
        code, out = self._run(["--format", "md", "crosswalk", "NIST", "ISO27001"])
        self.assertEqual(code, 0)
        lines = out.splitlines()
        self.assertTrue(lines[0].startswith("|"))
        self.assertTrue(set(lines[1].replace("|", "").replace(" ", "")) <= {"-"})
        self.assertIn("via", lines[0])

    def test_md_objectives_table(self):
        code, out = self._run(["--format", "md", "objectives"])
        self.assertEqual(code, 0)
        self.assertIn("| objective | label |", out)
        self.assertIn("Access control", out)

    def test_md_escapes_pipes(self):
        # No catalog title currently contains a pipe; assert the escaper itself.
        from frameworkmap.cli import _to_md
        rendered = _to_md(["a"], [["x | y"]])
        self.assertIn("x \\| y", rendered)


if __name__ == "__main__":
    unittest.main()
