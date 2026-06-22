# Demo 04 — Defense contractor: NIST 800-171 program → CMMC 2.0 Level 2

**Persona.** A small manufacturer in the Defense Industrial Base handles CUI and
must reach CMMC 2.0 Level 2. The IT lead already maintains a NIST-aligned
program and needs to show an assessor how each existing NIST control discharges
a CMMC practice, and confirm there are no blind spots before the C3PAO visit.

## Where the data comes from

Built-in catalog: NIST SP 800-53 families and CMMC 2.0 Level 2 practices, each
tagged to the shared objective spine.

## Run it

```bash
# Does every NIST control reach CMMC? (coverage of NIST onto CMMC)
python -m frameworkmap coverage NIST CMMC

# Walk the full mapping the assessor will want as evidence:
python -m frameworkmap crosswalk NIST CMMC

# Map a specific high-scrutiny CMMC practice back to its peers:
python -m frameworkmap map IA.L2-3.5.3      # multifactor authentication
```

## What to expect

`coverage NIST CMMC` reports a high percentage — the NIST families and CMMC
practices share most objectives. Any uncovered NIST control corresponds to an
objective CMMC Level 2 does not call out separately.

`map IA.L2-3.5.3` shows CMMC's MFA practice mapping to NIST IA-2, ISO 27001
A.5.16, SOC 2 CC6.1, and PCI 8.3 — all via the identification & authentication
(`IA`) objective. That is the cross-evidence trail for the assessor.

## How to act

1. Export the crosswalk as an SSP appendix (`--format md` or `--format csv`).
2. For any NIST control without a CMMC match, confirm it is genuinely out of
   CMMC Level 2 scope and note it in the assessment boundary.
