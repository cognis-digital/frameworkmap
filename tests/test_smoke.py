"""Smoke tests for FRAMEWORKMAP. No network. Standard library only."""
import io
import json
import os
import sys
import tempfile
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
        # NIST CP-9 (backup/contingency) has no PCI equivalent in the catalog spine;
        # PCI covers MP+PE via 9.4 but has no CP-objective control.
        self.assertIn("CP-9", gap_ids)

    def test_bad_framework_raises(self):
        with self.assertRaises(ValueError):
            crosswalk_framework("NIST", "NOPE")

    def test_map_control_empty_id_raises(self):
        with self.assertRaises(ValueError):
            map_control("")

    def test_crosswalk_same_framework_raises(self):
        with self.assertRaises(ValueError):
            crosswalk_framework("NIST", "NIST")

    def test_catalog_missing_file_raises(self):
        with self.assertRaises(FileNotFoundError):
            load_catalog("/nonexistent/path/catalog.json")

    def test_catalog_invalid_json_raises(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write("this is not json {{{")
            fname = f.name
        try:
            with self.assertRaises(ValueError) as ctx:
                load_catalog(fname)
            self.assertIn("not valid JSON", str(ctx.exception))
        finally:
            os.unlink(fname)

    def test_catalog_missing_framework_field_raises(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump([{"id": "X-1", "title": "Missing framework", "objectives": ["AC"]}], f)
            fname = f.name
        try:
            with self.assertRaises(ValueError) as ctx:
                load_catalog(fname)
            self.assertIn("missing required field 'framework'", str(ctx.exception))
        finally:
            os.unlink(fname)

    def test_catalog_objectives_not_list_raises(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump([{"framework": "NIST", "id": "X-1", "title": "bad", "objectives": "AC"}], f)
            fname = f.name
        try:
            with self.assertRaises(ValueError) as ctx:
                load_catalog(fname)
            self.assertIn("must be a list", str(ctx.exception))
        finally:
            os.unlink(fname)

    def test_catalog_empty_list_raises(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump([], f)
            fname = f.name
        try:
            with self.assertRaises(ValueError) as ctx:
                load_catalog(fname)
            self.assertIn("empty", str(ctx.exception))
        finally:
            os.unlink(fname)


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

    def test_missing_catalog_file_returns_2(self):
        buf = io.StringIO()
        old_err = sys.stderr
        sys.stderr = buf
        try:
            code = main(["--catalog", "/nonexistent/file.json", "map", "AC-2"])
        finally:
            sys.stderr = old_err
        self.assertEqual(code, 2)
        self.assertIn("error", buf.getvalue())

    def test_malformed_catalog_json_returns_1(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write("{not json}")
            fname = f.name
        buf = io.StringIO()
        old_err = sys.stderr
        sys.stderr = buf
        try:
            code = main(["--catalog", fname, "map", "AC-2"])
        finally:
            sys.stderr = old_err
            os.unlink(fname)
        self.assertEqual(code, 1)
        self.assertIn("error", buf.getvalue())

    def test_same_framework_crosswalk_returns_1(self):
        buf = io.StringIO()
        old_err = sys.stderr
        sys.stderr = buf
        try:
            code = main(["crosswalk", "NIST", "NIST"])
        finally:
            sys.stderr = old_err
        self.assertEqual(code, 1)
        self.assertIn("error", buf.getvalue())


if __name__ == "__main__":
    unittest.main()
