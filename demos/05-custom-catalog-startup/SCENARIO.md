# Demo 05 — Bring your own catalog: honest coverage for a Series-A startup

**Persona.** A 20-person startup has only *actually implemented* a subset of
controls. The built-in catalog assumes a mature program, so it would overstate
readiness. The founder maintains a hand-curated `catalog.json` of the controls
the company can really evidence today and wants an honest coverage number for a
board update.

## The real input format

`--catalog FILE` **replaces** the built-in catalog with your own JSON — a list
of control objects, each `{"framework", "id", "title", "objectives": [...]}`.
`framework` must be one of NIST / ISO27001 / SOC2 / CMMC / PCI and each
objective must be a known spine id (`frameworkmap objectives`). See
[`catalog.json`](catalog.json): the startup tracks 6 SOC 2 criteria and 9 NIST
controls, but has **not** yet stood up vulnerability scanning, incident
response, or awareness training.

## Run it

```bash
C=demos/05-custom-catalog-startup/catalog.json

# Honest coverage of the NIST controls onto the SOC 2 program:
python -m frameworkmap --catalog "$C" coverage NIST SOC2

# Exactly which NIST controls have no SOC 2 evidence yet:
python -m frameworkmap --catalog "$C" gaps NIST SOC2

# A control the org has not implemented maps to nothing — by design:
python -m frameworkmap --catalog "$C" map RA-5
```

## What to expect

`coverage NIST SOC2` reports **66.7%** (6 of 9), not the inflated number the
built-in catalog would give. `gaps NIST SOC2` names the three real holes:

- **RA-5** Vulnerability Monitoring and Scanning (`VM`)
- **IR-4** Incident Handling (`IR`)
- **AT-2** Literacy Training and Awareness (`AT`)

`map RA-5` against this catalog returns "(no mapping)" for every framework —
because the org has no `VM` control on any other framework yet. That blank is
the signal, not a bug.

## How to act

1. Use 66.7% — not a vendor-default 100% — in the board deck.
2. Turn the three gaps into the next-quarter security roadmap.
3. As each control is implemented, add it to `catalog.json` and re-run to watch
   coverage rise.
