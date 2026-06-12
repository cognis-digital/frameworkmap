"""Core crosswalk engine for FRAMEWORKMAP.

The engine is built around a catalog of *common control objectives* (themes).
Each framework's controls are tagged with one or more objective ids, so two
controls are considered equivalent (cross-mapped) when they share an objective.
This is exactly how GRC auto-mapping works: map every framework to a shared
spine, then derive N:N crosswalks from the spine.
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from typing import Dict, List, Optional

FRAMEWORKS = ["NIST", "ISO27001", "SOC2", "CMMC", "PCI"]

# Shared control objectives (the "spine"). id -> human label.
OBJECTIVES: Dict[str, str] = {
    "AC": "Access control & least privilege",
    "IA": "Identification & authentication",
    "AU": "Audit logging & monitoring",
    "CM": "Configuration & change management",
    "CP": "Backup, recovery & contingency",
    "IR": "Incident response",
    "RA": "Risk assessment",
    "SC": "Cryptography & transmission protection",
    "AT": "Security awareness & training",
    "MP": "Media & data protection",
    "PE": "Physical & environmental security",
    "VM": "Vulnerability management",
}

# Built-in catalog. Each control: framework, id, title, objectives[].
# Curated from publicly published control identifiers/titles.
_BUILTIN: List[dict] = [
    # NIST SP 800-53 rev5 families
    {"framework": "NIST", "id": "AC-2", "title": "Account Management", "objectives": ["AC", "IA"]},
    {"framework": "NIST", "id": "AC-6", "title": "Least Privilege", "objectives": ["AC"]},
    {"framework": "NIST", "id": "IA-2", "title": "Identification and Authentication", "objectives": ["IA"]},
    {"framework": "NIST", "id": "AU-2", "title": "Event Logging", "objectives": ["AU"]},
    {"framework": "NIST", "id": "AU-6", "title": "Audit Record Review", "objectives": ["AU"]},
    {"framework": "NIST", "id": "CM-2", "title": "Baseline Configuration", "objectives": ["CM"]},
    {"framework": "NIST", "id": "CP-9", "title": "System Backup", "objectives": ["CP"]},
    {"framework": "NIST", "id": "IR-4", "title": "Incident Handling", "objectives": ["IR"]},
    {"framework": "NIST", "id": "RA-3", "title": "Risk Assessment", "objectives": ["RA"]},
    {"framework": "NIST", "id": "RA-5", "title": "Vulnerability Monitoring and Scanning", "objectives": ["VM"]},
    {"framework": "NIST", "id": "SC-8", "title": "Transmission Confidentiality and Integrity", "objectives": ["SC"]},
    {"framework": "NIST", "id": "SC-28", "title": "Protection of Information at Rest", "objectives": ["SC", "MP"]},
    {"framework": "NIST", "id": "AT-2", "title": "Literacy Training and Awareness", "objectives": ["AT"]},
    {"framework": "NIST", "id": "MP-6", "title": "Media Sanitization", "objectives": ["MP"]},
    {"framework": "NIST", "id": "PE-3", "title": "Physical Access Control", "objectives": ["PE"]},
    # ISO/IEC 27001:2022 Annex A
    {"framework": "ISO27001", "id": "A.5.15", "title": "Access control", "objectives": ["AC"]},
    {"framework": "ISO27001", "id": "A.5.16", "title": "Identity management", "objectives": ["IA", "AC"]},
    {"framework": "ISO27001", "id": "A.5.18", "title": "Access rights", "objectives": ["AC"]},
    {"framework": "ISO27001", "id": "A.8.15", "title": "Logging", "objectives": ["AU"]},
    {"framework": "ISO27001", "id": "A.8.16", "title": "Monitoring activities", "objectives": ["AU"]},
    {"framework": "ISO27001", "id": "A.8.9", "title": "Configuration management", "objectives": ["CM"]},
    {"framework": "ISO27001", "id": "A.8.13", "title": "Information backup", "objectives": ["CP"]},
    {"framework": "ISO27001", "id": "A.5.26", "title": "Response to information security incidents", "objectives": ["IR"]},
    {"framework": "ISO27001", "id": "A.5.9", "title": "Inventory & risk of information assets", "objectives": ["RA"]},
    {"framework": "ISO27001", "id": "A.8.8", "title": "Management of technical vulnerabilities", "objectives": ["VM"]},
    {"framework": "ISO27001", "id": "A.8.24", "title": "Use of cryptography", "objectives": ["SC"]},
    {"framework": "ISO27001", "id": "A.6.3", "title": "Information security awareness, education and training", "objectives": ["AT"]},
    {"framework": "ISO27001", "id": "A.7.10", "title": "Storage media", "objectives": ["MP"]},
    {"framework": "ISO27001", "id": "A.7.1", "title": "Physical security perimeters", "objectives": ["PE"]},
    # SOC 2 Trust Services Criteria
    {"framework": "SOC2", "id": "CC6.1", "title": "Logical access security controls", "objectives": ["AC", "IA"]},
    {"framework": "SOC2", "id": "CC6.2", "title": "User registration & authorization", "objectives": ["AC"]},
    {"framework": "SOC2", "id": "CC6.6", "title": "Boundary protection / encryption in transit", "objectives": ["SC"]},
    {"framework": "SOC2", "id": "CC6.7", "title": "Data transmission & disposal", "objectives": ["SC", "MP"]},
    {"framework": "SOC2", "id": "CC7.1", "title": "Vulnerability detection", "objectives": ["VM"]},
    {"framework": "SOC2", "id": "CC7.2", "title": "Security event monitoring", "objectives": ["AU"]},
    {"framework": "SOC2", "id": "CC7.4", "title": "Incident response program", "objectives": ["IR"]},
    {"framework": "SOC2", "id": "CC8.1", "title": "Change management", "objectives": ["CM"]},
    {"framework": "SOC2", "id": "CC3.2", "title": "Risk identification & assessment", "objectives": ["RA"]},
    {"framework": "SOC2", "id": "A1.2", "title": "Backup & recovery (availability)", "objectives": ["CP"]},
    {"framework": "SOC2", "id": "CC2.2", "title": "Internal security awareness communication", "objectives": ["AT"]},
    # CMMC 2.0 practices
    {"framework": "CMMC", "id": "AC.L2-3.1.1", "title": "Limit system access to authorized users", "objectives": ["AC"]},
    {"framework": "CMMC", "id": "AC.L2-3.1.5", "title": "Least privilege", "objectives": ["AC"]},
    {"framework": "CMMC", "id": "IA.L2-3.5.3", "title": "Multifactor authentication", "objectives": ["IA"]},
    {"framework": "CMMC", "id": "AU.L2-3.3.1", "title": "Create and retain audit logs", "objectives": ["AU"]},
    {"framework": "CMMC", "id": "CM.L2-3.4.1", "title": "Establish configuration baselines", "objectives": ["CM"]},
    {"framework": "CMMC", "id": "IR.L2-3.6.1", "title": "Incident handling capability", "objectives": ["IR"]},
    {"framework": "CMMC", "id": "RA.L2-3.11.1", "title": "Periodic risk assessment", "objectives": ["RA"]},
    {"framework": "CMMC", "id": "RA.L2-3.11.2", "title": "Scan for vulnerabilities", "objectives": ["VM"]},
    {"framework": "CMMC", "id": "SC.L2-3.13.8", "title": "Cryptographic protection in transit", "objectives": ["SC"]},
    {"framework": "CMMC", "id": "AT.L2-3.2.1", "title": "Security awareness training", "objectives": ["AT"]},
    {"framework": "CMMC", "id": "MP.L2-3.8.3", "title": "Sanitize media before disposal", "objectives": ["MP"]},
    {"framework": "CMMC", "id": "PE.L2-3.10.1", "title": "Limit physical access", "objectives": ["PE"]},
    # PCI DSS v4.0 requirements
    {"framework": "PCI", "id": "7.2", "title": "Restrict access by business need to know", "objectives": ["AC"]},
    {"framework": "PCI", "id": "8.3", "title": "Strong authentication for users", "objectives": ["IA"]},
    {"framework": "PCI", "id": "10.2", "title": "Audit logs for all system components", "objectives": ["AU"]},
    {"framework": "PCI", "id": "10.4", "title": "Review audit logs", "objectives": ["AU"]},
    {"framework": "PCI", "id": "1.2", "title": "Network security controls configuration", "objectives": ["CM"]},
    {"framework": "PCI", "id": "6.3", "title": "Identify & rank vulnerabilities", "objectives": ["VM"]},
    {"framework": "PCI", "id": "11.3", "title": "Vulnerability scans & penetration testing", "objectives": ["VM"]},
    {"framework": "PCI", "id": "4.2", "title": "Strong cryptography over open networks", "objectives": ["SC"]},
    {"framework": "PCI", "id": "3.5", "title": "Protect stored account data", "objectives": ["SC", "MP"]},
    {"framework": "PCI", "id": "12.10", "title": "Incident response plan", "objectives": ["IR"]},
    {"framework": "PCI", "id": "12.6", "title": "Security awareness program", "objectives": ["AT"]},
    {"framework": "PCI", "id": "9.4", "title": "Physical media controls", "objectives": ["MP", "PE"]},
]


@dataclass
class Control:
    framework: str
    id: str
    title: str
    objectives: List[str] = field(default_factory=list)


@dataclass
class Crosswalk:
    """A single source control mapped to controls in other frameworks."""
    source: Dict[str, object]
    objectives: List[str]
    mappings: Dict[str, List[Dict[str, str]]]

    def to_dict(self) -> dict:
        return {"source": self.source, "objectives": self.objectives, "mappings": self.mappings}


def load_catalog(path: Optional[str] = None) -> List[Control]:
    """Load the control catalog. With no path, returns the built-in catalog.
    A path may point to a JSON file (list of control dicts) to extend/replace.
    """
    rows = list(_BUILTIN)
    if path:
        if not os.path.exists(path):
            raise FileNotFoundError(f"catalog not found: {path}")
        with open(path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
        if not isinstance(data, list):
            raise ValueError("catalog JSON must be a list of control objects")
        rows = data
    out: List[Control] = []
    for r in rows:
        fw = str(r["framework"]).upper()
        if fw not in FRAMEWORKS:
            raise ValueError(f"unknown framework {fw!r} (expected one of {FRAMEWORKS})")
        objs = [o.upper() for o in r.get("objectives", [])]
        for o in objs:
            if o not in OBJECTIVES:
                raise ValueError(f"unknown objective {o!r} on {r['id']}")
        out.append(Control(fw, str(r["id"]), str(r.get("title", "")), objs))
    return out


def _index_by_objective(catalog: List[Control]) -> Dict[str, List[Control]]:
    idx: Dict[str, List[Control]] = {}
    for c in catalog:
        for o in c.objectives:
            idx.setdefault(o, []).append(c)
    return idx


def _find(catalog: List[Control], control_id: str) -> Control:
    cid = control_id.strip().upper()
    for c in catalog:
        if c.id.upper() == cid:
            return c
    raise KeyError(f"control {control_id!r} not found in catalog")


def map_control(control_id: str, catalog: Optional[List[Control]] = None) -> Crosswalk:
    """Auto-map one control to equivalents in every other framework."""
    cat = catalog if catalog is not None else load_catalog()
    src = _find(cat, control_id)
    idx = _index_by_objective(cat)
    mappings: Dict[str, List[Dict[str, str]]] = {fw: [] for fw in FRAMEWORKS if fw != src.framework}
    seen = set()
    for obj in src.objectives:
        for c in idx.get(obj, []):
            if c.framework == src.framework:
                continue
            key = (c.framework, c.id)
            if key in seen:
                continue
            seen.add(key)
            mappings[c.framework].append({"id": c.id, "title": c.title, "via": obj})
    return Crosswalk(
        source={"framework": src.framework, "id": src.id, "title": src.title},
        objectives=src.objectives,
        mappings=mappings,
    )


def crosswalk_framework(source_fw: str, target_fw: str,
                        catalog: Optional[List[Control]] = None) -> List[dict]:
    """Full N:N crosswalk between two frameworks."""
    src_fw = source_fw.upper()
    tgt_fw = target_fw.upper()
    for fw in (src_fw, tgt_fw):
        if fw not in FRAMEWORKS:
            raise ValueError(f"unknown framework {fw!r}")
    cat = catalog if catalog is not None else load_catalog()
    idx = _index_by_objective(cat)
    rows: List[dict] = []
    for c in cat:
        if c.framework != src_fw:
            continue
        matches: List[Dict[str, str]] = []
        seen = set()
        for obj in c.objectives:
            for t in idx.get(obj, []):
                if t.framework != tgt_fw or t.id in seen:
                    continue
                seen.add(t.id)
                matches.append({"id": t.id, "title": t.title, "via": obj})
        rows.append({"source": {"id": c.id, "title": c.title}, "matches": matches})
    return rows


def coverage_report(source_fw: str, target_fw: str,
                    catalog: Optional[List[Control]] = None) -> dict:
    """How much of source framework maps onto the target framework."""
    rows = crosswalk_framework(source_fw, target_fw, catalog)
    total = len(rows)
    covered = sum(1 for r in rows if r["matches"])
    pct = round(100.0 * covered / total, 1) if total else 0.0
    return {
        "source": source_fw.upper(),
        "target": target_fw.upper(),
        "total_controls": total,
        "covered": covered,
        "uncovered": total - covered,
        "coverage_pct": pct,
    }


def find_gaps(source_fw: str, target_fw: str,
              catalog: Optional[List[Control]] = None) -> List[dict]:
    """Source controls with NO equivalent in the target framework."""
    rows = crosswalk_framework(source_fw, target_fw, catalog)
    return [{"id": r["source"]["id"], "title": r["source"]["title"]}
            for r in rows if not r["matches"]]
