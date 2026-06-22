"""Offline tests for the data-feed enrichment layer.

These tests NEVER hit the network. They point ``COGNIS_FEEDS_CACHE`` at the
committed trimmed fixtures under ``tests/fixtures/feeds_cache`` and call the
feed accessors with ``offline=True`` so the bundled ``datafeeds`` module serves
the cache and refuses any fetch.
"""
import io
import json
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))

# Point the feed cache at the committed fixtures BEFORE importing datafeeds use.
FIXTURE_CACHE = os.path.join(HERE, "fixtures", "feeds_cache")
os.environ["COGNIS_FEEDS_CACHE"] = FIXTURE_CACHE

from frameworkmap import datafeeds, feeds  # noqa: E402
from frameworkmap.cli import main  # noqa: E402


class TestFixtureCache(unittest.TestCase):
    def test_fixture_cache_present(self):
        self.assertTrue(os.path.isdir(FIXTURE_CACHE))
        for fid in feeds.FEED_IDS:
            self.assertTrue(os.path.exists(os.path.join(FIXTURE_CACHE, fid + ".data")),
                            f"missing fixture for {fid}")

    def test_offline_get_serves_cache(self):
        doc = datafeeds.get("oscal-800-53-rev5-catalog", offline=True)
        self.assertIn("catalog", doc)

    def test_offline_get_unknown_raises(self):
        with self.assertRaises(FileNotFoundError):
            datafeeds.get("attack-enterprise", offline=True)


class TestOscalTitles(unittest.TestCase):
    def test_resolve_authoritative_title(self):
        # Authoritative OSCAL title for AC-2 is "Account Management".
        self.assertEqual(feeds.resolve_title("AC-2", offline=True), "Account Management")

    def test_title_index_normalises_ids(self):
        titles = feeds.control_titles(offline=True)
        # zero-padded / lowercase inputs all resolve
        self.assertEqual(titles.get("RA-5"), feeds.resolve_title("ra-05", offline=True))
        self.assertTrue(feeds.resolve_title("RA-5", offline=True).startswith("Vulnerability"))

    def test_title_is_more_specific_than_builtin(self):
        # OSCAL gives the full IA-2 title that the curated spine abbreviates.
        self.assertIn("Organizational Users", feeds.resolve_title("IA-2", offline=True))


class TestAttackMappings(unittest.TestCase):
    def test_techniques_for_control(self):
        techs = feeds.techniques_for("AC-2", offline=True)
        self.assertTrue(techs)
        ids = {t["technique"] for t in techs}
        self.assertIn("T1003", ids)  # OS Credential Dumping is mitigated by AC-2
        self.assertTrue(all(t["mapping_type"] == "mitigates" for t in techs))

    def test_zero_padded_capability_id_normalised(self):
        # the feed stores AC-02; we must find it under AC-2
        idx = feeds.technique_index(offline=True)
        self.assertIn("AC-2", idx)
        self.assertNotIn("AC-02", idx)

    def test_unmapped_control_returns_empty(self):
        # AU-2 carries no completed ATT&CK mapping in the fixture
        self.assertEqual(feeds.techniques_for("AU-2", offline=True), [])


class TestEnrichment(unittest.TestCase):
    def test_enrich_joins_title_and_techniques(self):
        d = feeds.enrich_nist_control("ac-2", offline=True)
        self.assertEqual(d["control_id"], "AC-2")
        self.assertEqual(d["authoritative_title"], "Account Management")
        self.assertGreater(d["technique_count"], 0)
        self.assertEqual(d["technique_count"], len(d["techniques_mitigated"]))

    def test_threat_informed_crosswalk(self):
        from frameworkmap.core import crosswalk_framework
        rows = crosswalk_framework("NIST", "SOC2")
        enriched = feeds.threat_informed_crosswalk(rows, offline=True)
        self.assertEqual(len(enriched), len(rows))
        ac2 = next(r for r in enriched if r["source"]["id"] == "AC-2")
        # carries both compliance mapping AND threat coverage
        self.assertTrue(ac2["matches"])
        self.assertTrue(ac2["techniques"])
        self.assertEqual(ac2["authoritative_title"], "Account Management")


class TestCLIOffline(unittest.TestCase):
    def _run(self, argv):
        buf = io.StringIO()
        old = sys.stdout
        sys.stdout = buf
        try:
            code = main(argv)
        finally:
            sys.stdout = old
        return code, buf.getvalue()

    def test_feeds_list(self):
        code, out = self._run(["feeds", "list"])
        self.assertEqual(code, 0)
        self.assertIn("oscal-800-53-rev5-catalog", out)
        self.assertIn("attack-nist-mappings", out)

    def test_feeds_get_offline(self):
        code, out = self._run(["feeds", "get", "attack-nist-mappings", "--offline"])
        self.assertEqual(code, 0)
        self.assertIn("mapping_objects", out)

    def test_feeds_update_rejects_foreign_feed(self):
        code, _ = self._run(["feeds", "update", "cisa-kev"])
        self.assertEqual(code, 1)  # not a FRAMEWORKMAP feed

    def test_enrich_json_offline(self):
        code, out = self._run(["--format", "json", "enrich", "AC-2", "--offline"])
        self.assertEqual(code, 0)
        data = json.loads(out)
        self.assertEqual(data["control_id"], "AC-2")
        self.assertEqual(data["authoritative_title"], "Account Management")

    def test_enrich_csv_offline(self):
        import csv as _csv
        code, out = self._run(["--format", "csv", "enrich", "RA-5", "--offline"])
        self.assertEqual(code, 0)
        rows = list(_csv.reader(io.StringIO(out)))
        self.assertEqual(rows[0][0], "control_id")
        self.assertTrue(any(r[2].startswith("T") for r in rows[1:]))

    def test_threat_map_table_offline(self):
        code, out = self._run(["threat-map", "SOC2", "--offline"])
        self.assertEqual(code, 0)
        self.assertIn("AC-2", out)
        self.assertIn("ATT&CK:", out)
        self.assertIn("T1003", out)

    def test_threat_map_csv_offline(self):
        import csv as _csv
        code, out = self._run(["--format", "csv", "threat-map", "SOC2", "--offline"])
        self.assertEqual(code, 0)
        rows = list(_csv.reader(io.StringIO(out)))
        self.assertEqual(rows[0],
                         ["nist_id", "authoritative_title", "SOC2_ids",
                          "attack_techniques", "technique_count"])
        ac2 = next(r for r in rows[1:] if r[0] == "AC-2")
        self.assertIn("T1003", ac2[3])


class TestSnapshotRoundTrip(unittest.TestCase):
    """Air-gap sneakernet: export the cache, import into a fresh cache, re-serve."""

    def test_export_import(self):
        import tempfile
        snap = os.path.join(tempfile.mkdtemp(), "feeds.tar.gz")
        n = datafeeds.snapshot_export(snap)
        self.assertGreaterEqual(n, 2)
        fresh = tempfile.mkdtemp()
        old = os.environ["COGNIS_FEEDS_CACHE"]
        os.environ["COGNIS_FEEDS_CACHE"] = fresh
        try:
            datafeeds.snapshot_import(snap)
            doc = datafeeds.get("oscal-800-53-rev5-catalog", offline=True)
            self.assertIn("catalog", doc)
        finally:
            os.environ["COGNIS_FEEDS_CACHE"] = old


if __name__ == "__main__":
    unittest.main()
