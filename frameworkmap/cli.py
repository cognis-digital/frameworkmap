"""Command-line interface for FRAMEWORKMAP."""
from __future__ import annotations

import argparse
import json
import sys
from typing import List, Optional

from . import TOOL_NAME, TOOL_VERSION
from .core import (
    FRAMEWORKS,
    OBJECTIVES,
    load_catalog,
    map_control,
    crosswalk_framework,
    coverage_report,
    find_gaps,
)


def _emit(obj, fmt: str, table_fn) -> None:
    if fmt == "json":
        print(json.dumps(obj, indent=2))
    else:
        table_fn(obj)


def _print_map(cw: dict) -> None:
    s = cw["source"]
    print(f"{s['framework']} {s['id']}  {s['title']}")
    print(f"objectives: {', '.join(cw['objectives'])}")
    for fw, items in cw["mappings"].items():
        if not items:
            print(f"  {fw:<9} (no mapping)")
            continue
        for it in items:
            print(f"  {fw:<9} {it['id']:<14} {it['title']}  [via {it['via']}]")


def _print_crosswalk(rows: list) -> None:
    for r in rows:
        src = r["source"]
        tgt = ", ".join(m["id"] for m in r["matches"]) or "-- GAP --"
        print(f"{src['id']:<14} -> {tgt}")


def _print_coverage(rep: dict) -> None:
    print(f"{rep['source']} -> {rep['target']}")
    print(f"  controls : {rep['total_controls']}")
    print(f"  covered  : {rep['covered']}")
    print(f"  gaps     : {rep['uncovered']}")
    print(f"  coverage : {rep['coverage_pct']}%")


def _print_gaps(gaps: list) -> None:
    if not gaps:
        print("(no gaps)")
    for g in gaps:
        print(f"{g['id']:<14} {g['title']}")


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog=TOOL_NAME, description="Crosswalk compliance controls across frameworks.")
    p.add_argument("--version", action="version", version=f"{TOOL_NAME} {TOOL_VERSION}")
    p.add_argument("--format", choices=["table", "json"], default="table")
    p.add_argument("--catalog", help="path to a JSON catalog to use instead of the built-in")
    sub = p.add_subparsers(dest="command", required=True)

    mp = sub.add_parser("map", help="auto-map one control to all other frameworks")
    mp.add_argument("control_id")

    cw = sub.add_parser("crosswalk", help="full crosswalk between two frameworks")
    cw.add_argument("source", choices=FRAMEWORKS)
    cw.add_argument("target", choices=FRAMEWORKS)

    co = sub.add_parser("coverage", help="coverage percentage of source onto target")
    co.add_argument("source", choices=FRAMEWORKS)
    co.add_argument("target", choices=FRAMEWORKS)

    gp = sub.add_parser("gaps", help="source controls with no target equivalent")
    gp.add_argument("source", choices=FRAMEWORKS)
    gp.add_argument("target", choices=FRAMEWORKS)

    sub.add_parser("frameworks", help="list supported frameworks")
    sub.add_parser("objectives", help="list shared control objectives")
    return p


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        catalog = load_catalog(args.catalog) if args.catalog else None
        if args.command == "map":
            cw = map_control(args.control_id, catalog)
            _emit(cw.to_dict(), args.format, _print_map)
        elif args.command == "crosswalk":
            rows = crosswalk_framework(args.source, args.target, catalog)
            _emit(rows, args.format, _print_crosswalk)
        elif args.command == "coverage":
            rep = coverage_report(args.source, args.target, catalog)
            _emit(rep, args.format, _print_coverage)
        elif args.command == "gaps":
            gaps = find_gaps(args.source, args.target, catalog)
            _emit(gaps, args.format, _print_gaps)
        elif args.command == "frameworks":
            _emit(FRAMEWORKS, args.format, lambda fw: print("\n".join(fw)))
        elif args.command == "objectives":
            _emit(OBJECTIVES, args.format,
                  lambda o: print("\n".join(f"{k}  {v}" for k, v in o.items())))
        else:  # pragma: no cover
            parser.error("unknown command")
            return 2
    except (KeyError, ValueError, FileNotFoundError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
