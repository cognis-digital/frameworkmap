#!/usr/bin/env python3
"""Offline demo of FRAMEWORKMAP's threat-informed data-feed enrichment.

Points COGNIS_FEEDS_CACHE at the committed trimmed fixtures and runs the
enrichment with offline=True, so it never touches the network.
"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
os.environ["COGNIS_FEEDS_CACHE"] = os.path.join(ROOT, "tests", "fixtures", "feeds_cache")

from frameworkmap import feeds  # noqa: E402
from frameworkmap.core import crosswalk_framework  # noqa: E402


def main() -> int:
    print("== enrich a single NIST control (offline) ==")
    d = feeds.enrich_nist_control("AC-2", offline=True)
    print(f"{d['control_id']}  {d['authoritative_title']}")
    print(f"  mitigates {d['technique_count']} ATT&CK technique(s):")
    for t in d["techniques_mitigated"]:
        print(f"    {t['technique']:<12} {t['name']}")

    print("\n== threat-informed NIST -> SOC 2 crosswalk (offline) ==")
    rows = crosswalk_framework("NIST", "SOC2")
    for r in feeds.threat_informed_crosswalk(rows, offline=True):
        src = r["source"]
        soc2 = ", ".join(m["id"] for m in r["matches"]) or "-- GAP --"
        techs = ", ".join(t["technique"] for t in r["techniques"]) or "(no ATT&CK)"
        title = r["authoritative_title"] or src["title"]
        print(f"  {src['id']:<8} {title}")
        print(f"           SOC2: {soc2}")
        print(f"           ATT&CK: {techs}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
