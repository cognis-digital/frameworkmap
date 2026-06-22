# Demo 08 — One-glance coverage matrix across all five frameworks

**Persona.** A vCISO advising several clients wants a single board-ready matrix
showing how completely each framework maps onto every other — so they can say
"if you build to PCI you are far from ISO-ready, but if you build to NIST you
are 100% ISO-ready." [`matrix.sh`](matrix.sh) drives the CLI over every pair and
emits a Markdown table.

## Run it

```bash
bash demos/08-multi-framework-matrix/matrix.sh
```

The script calls `frameworkmap --format json coverage <src> <tgt>` for each of
the 20 ordered framework pairs and reads `coverage_pct` from the JSON.

## What to expect (built-in catalog)

| src \ tgt | NIST | ISO27001 | SOC2 | CMMC | PCI |
|---|---|---|---|---|---|
| **NIST** | -- | 100.0% | 93.3% | 93.3% | 86.7% |
| **ISO27001** | 100.0% | -- | 92.9% | 92.9% | 85.7% |
| **SOC2** | 100.0% | 100.0% | -- | 90.9% | 81.8% |
| **CMMC** | 100.0% | 100.0% | 91.7% | -- | 91.7% |
| **PCI** | 100.0% | 100.0% | 100.0% | 100.0% | -- |

## How to read it

- **Rows are the source you build to; columns are the target you want credit
  for.** A high cell means "building to the row framework gets you most of the
  column framework for free."
- Everything maps cleanly **onto** NIST and ISO 27001 (100% columns) — they are
  the broadest spines.
- **PCI is the narrowest target** (lowest cells) — it omits backup/contingency
  and standalone risk-assessment objectives, so other frameworks do not map
  fully onto it.

## How to act

Pick the framework with the highest row average as your primary build target to
maximize reusable evidence, then close the per-target gaps with `gaps`.
