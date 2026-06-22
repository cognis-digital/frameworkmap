"""Threat-informed, edge/air-gap data-feed enrichment for FRAMEWORKMAP.

FRAMEWORKMAP crosswalks compliance controls across NIST / ISO 27001 / SOC 2 /
CMMC / PCI using a curated objective "spine". This module wires it to two
*authoritative, keyless* upstream feeds so the crosswalk is no longer just
hand-curated titles — it resolves real control text and real adversary
behaviour:

  * ``oscal-800-53-rev5-catalog`` — NIST's own OSCAL publication of the
    SP 800-53 Rev 5 catalog. Used to resolve the **authoritative title** of any
    NIST control id (vs. the abbreviated title in the built-in spine).
    Source: github.com/usnistgov/oscal-content

  * ``attack-nist-mappings`` — the Center for Threat-Informed Defense
    "Mappings Explorer" crosswalk of MITRE ATT&CK techniques to the
    NIST 800-53 Rev 5 controls that mitigate them. Used to attach the real
    **ATT&CK techniques a control mitigates** to every crosswalk row, turning a
    compliance map into a threat-informed control map.
    Source: github.com/center-for-threat-informed-defense/mappings-explorer

Both feeds are fetched over HTTPS by the bundled :mod:`frameworkmap.datafeeds`
module, cached to disk, and re-served **offline** (``--offline`` /
``offline=True``) so FRAMEWORKMAP runs unchanged on disconnected / air-gapped
GRC workstations. See README "Edge / air-gap" for the snapshot workflow.

Defensive / authorized-use compliance tooling only.
"""
from __future__ import annotations

import re
from typing import Dict, List, Optional

from . import datafeeds

# Only these catalog feed ids are relevant to FRAMEWORKMAP. The bundled catalog
# (data_feeds_2026.json) carries many more; we deliberately restrict to these.
FEED_IDS = ["oscal-800-53-rev5-catalog", "attack-nist-mappings"]

_PAD_RE = re.compile(r"^([A-Za-z]{2})-0*(\d+)$")


def _norm(control_id: str) -> str:
    """Normalise a NIST control id to FAMILY-NUMBER, no zero padding, no
    enhancement suffix. ``AC-02`` -> ``AC-2``; ``ac-2(1)`` -> ``AC-2``."""
    cid = control_id.strip().upper()
    cid = cid.split("(")[0].strip()  # drop enhancement, e.g. AC-2(1)
    m = _PAD_RE.match(cid)
    if m:
        return f"{m.group(1)}-{int(m.group(2))}"
    return cid


# --------------------------------------------------------------------------- #
# OSCAL 800-53 rev5 — authoritative control titles
# --------------------------------------------------------------------------- #
def control_titles(*, offline: bool = False) -> Dict[str, str]:
    """Map normalised NIST control id -> authoritative OSCAL title.

    Walks the OSCAL ``catalog.groups[].controls[]`` tree (top-level controls
    only; enhancements collapse onto their base id).
    """
    doc = datafeeds.get("oscal-800-53-rev5-catalog", offline=offline)
    catalog = doc.get("catalog", doc)
    out: Dict[str, str] = {}

    def _walk(controls):
        for c in controls or []:
            cid = c.get("id")
            if cid:
                key = _norm(cid)
                # keep the first (base) title we see for a normalised id
                out.setdefault(key, c.get("title", ""))
            _walk(c.get("controls"))

    for g in catalog.get("groups", []):
        _walk(g.get("controls"))
    return out


def resolve_title(control_id: str, *, offline: bool = False) -> Optional[str]:
    """Authoritative OSCAL title for one NIST control id, or ``None``."""
    return control_titles(offline=offline).get(_norm(control_id))


# --------------------------------------------------------------------------- #
# ATT&CK <-> NIST mappings — techniques a control mitigates
# --------------------------------------------------------------------------- #
def technique_index(*, offline: bool = False) -> Dict[str, List[Dict[str, str]]]:
    """Map normalised NIST control id -> list of ATT&CK techniques it mitigates.

    Each entry: ``{"technique": "T1110", "name": "Brute Force",
    "mapping_type": "mitigates"}``. Only ``status == "complete"`` rows count.
    """
    doc = datafeeds.get("attack-nist-mappings", offline=offline)
    objs = doc.get("mapping_objects", [])
    idx: Dict[str, List[Dict[str, str]]] = {}
    seen: set = set()
    for o in objs:
        cap = o.get("capability_id")
        tech = o.get("attack_object_id")
        if not cap or not tech or o.get("status") not in (None, "complete"):
            if o.get("status") and o.get("status") != "complete":
                continue
        if not cap or not tech:
            continue
        key = _norm(cap)
        dedupe = (key, tech)
        if dedupe in seen:
            continue
        seen.add(dedupe)
        idx.setdefault(key, []).append({
            "technique": tech,
            "name": o.get("attack_object_name", ""),
            "mapping_type": o.get("mapping_type") or "mitigates",
        })
    for v in idx.values():
        v.sort(key=lambda t: t["technique"])
    return idx


def techniques_for(control_id: str, *, offline: bool = False) -> List[Dict[str, str]]:
    """ATT&CK techniques mitigated by one NIST control id (base + enhancements)."""
    return technique_index(offline=offline).get(_norm(control_id), [])


# --------------------------------------------------------------------------- #
# combined enrichment used by the CLI
# --------------------------------------------------------------------------- #
def enrich_nist_control(control_id: str, *, offline: bool = False) -> dict:
    """Authoritative title + mitigated ATT&CK techniques for a NIST control.

    This is the real enrichment: it joins the OSCAL catalog (title) and the
    CTID ATT&CK crosswalk (threat coverage) for a single control id.
    """
    titles = control_titles(offline=offline)
    techs = technique_index(offline=offline)
    key = _norm(control_id)
    return {
        "control_id": key,
        "authoritative_title": titles.get(key),
        "techniques_mitigated": techs.get(key, []),
        "technique_count": len(techs.get(key, [])),
    }


def threat_informed_crosswalk(rows: List[dict], *, offline: bool = False) -> List[dict]:
    """Attach ATT&CK technique coverage to NIST source rows of a crosswalk.

    ``rows`` is the output of :func:`frameworkmap.core.crosswalk_framework`
    where the *source* framework is NIST. Each row gets a ``techniques`` list
    and an ``authoritative_title`` resolved from the live/cached feeds.
    """
    titles = control_titles(offline=offline)
    techs = technique_index(offline=offline)
    out: List[dict] = []
    for r in rows:
        cid = r.get("source", {}).get("id", "")
        key = _norm(cid)
        enriched = dict(r)
        enriched["authoritative_title"] = titles.get(key)
        enriched["techniques"] = techs.get(key, [])
        out.append(enriched)
    return out
