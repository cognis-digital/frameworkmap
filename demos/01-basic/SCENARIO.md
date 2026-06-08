# Demo 01 - Auto-mapping a NIST control across the GRC stack

**Persona.** A compliance lead at a SaaS company already runs a SOC 2 program
and is now pursuing ISO 27001, while a federal customer wants CMMC alignment.
Manually re-mapping every control across five frameworks is the painful,
error-prone part of GRC. FRAMEWORKMAP collapses that to one command.

## The killer feature: auto-mapping

Every framework's controls are tagged to a shared spine of control objectives
(access control, logging, cryptography, incident response, ...). Two controls
are equivalent when they share an objective, so a single mapping to the spine
yields all N:N crosswalks for free.

## Run it

```
python -m frameworkmap map AC-2
python -m frameworkmap map AC-2 --format json
```

`AC-2` (NIST Account Management) auto-maps to SOC 2 CC6.1, ISO 27001 A.5.15 /
A.5.16, CMMC AC.L2-3.1.1, and PCI 7.2 / 8.3 -- because they all touch the
`AC` (access control) and `IA` (identification & authentication) objectives.

## Coverage and gap analysis

```
python -m frameworkmap coverage SOC2 ISO27001
python -m frameworkmap gaps PCI ISO27001 --format json
```

`coverage` reports what fraction of a source framework has an equivalent in a
target framework; `gaps` lists the source controls that have no equivalent --
the exact list an auditor needs before a new certification.

## Use your own catalog

Pass `--catalog demos/01-basic/catalog_extra.json` to extend or replace the
built-in control set with your own organization's controls (same schema).
