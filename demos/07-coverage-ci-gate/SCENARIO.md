# Demo 07 — CI gate: fail the build when audit-readiness drops

**Persona.** A platform team treats compliance as code. They want CI to fail if
the SOC 2 → ISO 27001 coverage ever falls below their committed threshold (a
proxy for "someone deleted a control and broke the crosswalk"). They wire
`frameworkmap` JSON output into a `jq` assertion.

## Run it

```bash
# Manual check — coverage as machine-readable JSON:
python -m frameworkmap --format json coverage SOC2 ISO27001

# CI gate: require >= 90% coverage, else non-zero exit.
python -m frameworkmap --format json coverage SOC2 ISO27001 \
  | jq -e '.coverage_pct >= 90'
echo "exit=$?"   # 0 = pass, non-zero = fail the build
```

The JSON shape is:

```json
{
  "source": "SOC2",
  "target": "ISO27001",
  "total_controls": 11,
  "covered": 11,
  "uncovered": 0,
  "coverage_pct": 100.0
}
```

## Drop-in GitHub Actions step

```yaml
- name: Compliance crosswalk gate
  run: |
    pip install -e .
    python -m frameworkmap --format json coverage SOC2 ISO27001 \
      | jq -e '.coverage_pct >= 90'
```

## What to expect

With the built-in catalog, SOC 2 → ISO 27001 coverage is **100%**, so the gate
passes (`exit=0`). Point `--catalog` at your own catalog and the gate fails the
moment your real coverage dips below 90.

## How to act

1. Set the threshold to your committed audit-readiness floor.
2. When the gate fails, run the same pair without `jq` to see the number, then
   `gaps SOC2 ISO27001` to find what regressed.
