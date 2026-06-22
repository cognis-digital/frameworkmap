# Demo 03 — PCI DSS v4.0 merchant cross-referencing NIST 800-53

**Persona.** A payments platform runs its security program against NIST
SP 800-53 and must also attest to PCI DSS v4.0 for its card-data environment.
The security engineer wants to know which NIST controls already discharge PCI
requirements (so QSA evidence can be reused) and which NIST controls have *no*
PCI counterpart (so they are not over-claimed in the PCI scope).

## Where the data comes from

Built-in catalog: NIST SP 800-53 rev5 families and PCI DSS v4.0 requirements,
both tagged to the shared objective spine.

## Run it

```bash
# Coverage of NIST onto PCI:
python -m frameworkmap coverage NIST PCI

# The NIST controls with NO PCI equivalent — do not claim these for PCI:
python -m frameworkmap gaps NIST PCI

# Map a single PCI requirement back to its NIST/ISO/SOC2/CMMC equivalents:
python -m frameworkmap map 11.3
```

## What to expect

`coverage NIST PCI` reports **86.7%** (13 of 15 NIST controls have a PCI match).

`gaps NIST PCI` returns exactly two controls:

- **CP-9 System Backup** — PCI DSS v4.0 has no dedicated backup/contingency
  requirement in the catalog spine (`CP` objective).
- **RA-3 Risk Assessment** — PCI's risk activities live inside other
  requirements, so there is no 1:1 `RA` match.

`map 11.3` shows PCI's "Vulnerability scans & penetration testing" mapping to
NIST RA-5, ISO 27001 A.8.8, SOC 2 CC7.1, and CMMC RA.L2-3.11.2 — all via the
vulnerability-management (`VM`) objective.

## How to act

1. Reuse NIST evidence for the 13 covered controls in the PCI assessment.
2. Do **not** list CP-9 / RA-3 as satisfying a PCI requirement — they answer to
   NIST scope only. Document them as out-of-PCI-scope.
