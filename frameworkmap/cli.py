"""Command-line interface for FRAMEWORKMAP."""
from __future__ import annotations

import argparse
import csv
import io
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


def _emit(obj, fmt: str, table_fn, rows_fn=None) -> None:
    """Render *obj* in the requested format.

    table / json are always available. csv / md are tabular exports driven by
    *rows_fn*, which returns ``(header: list[str], rows: list[list[str]])`` —
    ideal for importing crosswalks into spreadsheets or audit deliverables.
    """
    if fmt == "json":
        print(json.dumps(obj, indent=2))
    elif fmt in ("csv", "md"):
        if rows_fn is None:
            raise ValueError(f"--format {fmt} is not supported for this command")
        header, rows = rows_fn(obj)
        if fmt == "csv":
            print(_to_csv(header, rows), end="")
        else:
            print(_to_md(header, rows))
    else:
        table_fn(obj)


def _to_csv(header: List[str], rows: List[List[str]]) -> str:
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\n")
    w.writerow(header)
    w.writerows(rows)
    return buf.getvalue()


def _to_md(header: List[str], rows: List[List[str]]) -> str:
    def esc(v: str) -> str:
        return str(v).replace("|", "\\|")
    out = ["| " + " | ".join(esc(h) for h in header) + " |",
           "| " + " | ".join("---" for _ in header) + " |"]
    for r in rows:
        out.append("| " + " | ".join(esc(c) for c in r) + " |")
    return "\n".join(out)


# ---- row extractors for tabular (csv/md) export ----------------------------

def _rows_map(cw: dict):
    s = cw["source"]
    header = ["source_framework", "source_id", "source_title",
              "target_framework", "target_id", "target_title", "via"]
    rows = []
    for fw, items in cw["mappings"].items():
        if not items:
            rows.append([s["framework"], s["id"], s["title"], fw, "", "(no mapping)", ""])
            continue
        for it in items:
            rows.append([s["framework"], s["id"], s["title"],
                         fw, it["id"], it["title"], it["via"]])
    return header, rows


def _rows_crosswalk(data):
    rows_in, src_fw, tgt_fw = data
    header = ["source_id", "source_title", "target_id", "target_title", "via"]
    rows = []
    for r in rows_in:
        src = r["source"]
        if not r["matches"]:
            rows.append([src["id"], src["title"], "", "-- GAP --", ""])
            continue
        for m in r["matches"]:
            rows.append([src["id"], src["title"], m["id"], m["title"], m["via"]])
    return header, rows


def _rows_coverage(rep: dict):
    header = ["source", "target", "total_controls", "covered", "uncovered", "coverage_pct"]
    rows = [[rep["source"], rep["target"], rep["total_controls"],
             rep["covered"], rep["uncovered"], rep["coverage_pct"]]]
    return header, rows


def _rows_gaps(data):
    gaps, src_fw, tgt_fw = data
    header = ["source_framework", "source_id", "source_title", "target_framework"]
    rows = [[src_fw, g["id"], g["title"], tgt_fw] for g in gaps]
    return header, rows


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
    p.add_argument("--format", choices=["table", "json", "csv", "md"], default="table",
                   help="table (default) · json · csv · md (Markdown table for audit reports)")
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
            _emit(cw.to_dict(), args.format, _print_map, _rows_map)
        elif args.command == "crosswalk":
            rows = crosswalk_framework(args.source, args.target, catalog)
            _emit(rows, args.format, _print_crosswalk,
                  lambda r: _rows_crosswalk((r, args.source.upper(), args.target.upper())))
        elif args.command == "coverage":
            rep = coverage_report(args.source, args.target, catalog)
            _emit(rep, args.format, _print_coverage, _rows_coverage)
        elif args.command == "gaps":
            gaps = find_gaps(args.source, args.target, catalog)
            _emit(gaps, args.format, _print_gaps,
                  lambda g: _rows_gaps((g, args.source.upper(), args.target.upper())))
        elif args.command == "frameworks":
            _emit(FRAMEWORKS, args.format, lambda fw: print("\n".join(fw)),
                  lambda fw: (["framework"], [[x] for x in fw]))
        elif args.command == "objectives":
            _emit(OBJECTIVES, args.format,
                  lambda o: print("\n".join(f"{k}  {v}" for k, v in o.items())),
                  lambda o: (["objective", "label"], [[k, v] for k, v in o.items()]))
        else:  # pragma: no cover
            parser.error("unknown command")
            return 2
    except (KeyError, ValueError, FileNotFoundError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
