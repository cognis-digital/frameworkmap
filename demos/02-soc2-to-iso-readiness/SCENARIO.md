# Demo 02 — SOC 2 shop pursuing ISO 27001 (readiness check)

**Persona.** A B2B SaaS company already holds a SOC 2 Type II report. A large
European prospect requires ISO/IEC 27001:2022 certification. The compliance
lead wants to know, before paying for a gap assessment, *how much of the SOC 2
program already satisfies ISO 27001* — and which ISO controls have no SOC 2
analogue and therefore need net-new work.

## Where the data comes from

The built-in catalog already carries the SOC 2 Trust Services Criteria and the
ISO/IEC 27001:2022 Annex A controls, each tagged to the shared objective spine.
No custom catalog needed for this scenario.

## Run it

```bash
# What fraction of SOC 2 has an ISO 27001 equivalent?
python -m frameworkmap coverage SOC2 ISO27001

# The reverse direction is the one that matters for NEW work:
# which ISO 27001 controls are NOT covered by the existing SOC 2 program?
python -m frameworkmap gaps ISO27001 SOC2

# Full N:N mapping for the auditor's working paper:
python -m frameworkmap crosswalk SOC2 ISO27001 --format md
```

## What to expect

`coverage SOC2 ISO27001` reports **100%** — every SOC 2 criterion in the
catalog has at least one ISO 27001 control on the same objective. That is the
good news: the existing program is a strong base.

`gaps ISO27001 SOC2` surfaces the ISO controls with **no** SOC 2 analogue. In
the built-in catalog that is **A.7.1 Physical security perimeters** — the SOC 2
criteria in scope do not exercise the physical/environmental (`PE`) objective.
That short list is exactly what to scope into the ISO project plan.

## How to act

1. Treat the 100% SOC 2→ISO direction as evidence reuse — point the ISO auditor
   at existing SOC 2 evidence for those controls.
2. Open a remediation ticket for each control in the `gaps ISO27001 SOC2` list.
3. Re-run after each control is implemented and re-tagged to watch the gap close.
