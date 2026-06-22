# Demo 09 — Understand the objective spine (why two controls "match")

**Persona.** A new GRC analyst is skeptical of auto-mapping — "how does the tool
decide AC-2 equals CC6.1?" This demo shows the mechanism: a shared spine of
control **objectives**. Every mapping the tool produces names the objective it
went `via`, so nothing is a black box.

## The mechanism

Each framework's controls are tagged with one or more objective ids (the
"spine"). Two controls are equivalent exactly when they share an objective. List
the spine, then trace a mapping back to it.

## Run it

```bash
# The full shared spine (id -> human label):
python -m frameworkmap objectives

# As CSV, to drop into a data dictionary:
python -m frameworkmap --format csv objectives

# A single control's mapping — note the "[via XX]" objective on every row:
python -m frameworkmap map SC-8

# Same, machine-readable: each mapping carries its "via" objective:
python -m frameworkmap --format json map SC-8
```

## What to expect

`objectives` lists twelve objectives — `AC`, `IA`, `AU`, `CM`, `CP`, `IR`,
`RA`, `SC`, `AT`, `MP`, `PE`, `VM`.

`map SC-8` (NIST "Transmission Confidentiality and Integrity") maps to ISO 27001
A.8.24, SOC 2 CC6.6/CC6.7, CMMC SC.L2-3.13.8, and PCI 4.2/3.5 — **every row
tagged `[via SC]`**, the cryptography/transmission-protection objective. That
`via` is the audit-defensible justification for each mapping.

## How to act

1. When an auditor questions a mapping, show them the `via` objective and its
   label from `objectives` — that is the rationale.
2. To add your own controls (Demo 05), tag them with the right objective id and
   they immediately participate in every crosswalk.
