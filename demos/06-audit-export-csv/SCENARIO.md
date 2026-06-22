# Demo 06 — Export a crosswalk to CSV / Markdown for the audit working paper

**Persona.** An auditor wants the NIST→ISO 27001 crosswalk as a spreadsheet to
drop into the engagement working papers, and a Markdown table to paste into the
report. The GRC analyst uses the `csv` and `md` output formats (new in this
release) so nothing has to be retyped.

## The feature

`--format` now accepts **`csv`** and **`md`** in addition to `table` and
`json`. Every command flattens to tidy rows:

- `map` / `crosswalk` → one row per source→target control pair (with the
  `via` objective that justifies the mapping)
- `coverage` → a single summary row
- `gaps` → one row per uncovered control

## Run it

```bash
# Spreadsheet for the working paper:
python -m frameworkmap --format csv crosswalk NIST ISO27001 > nist_iso_crosswalk.csv

# Markdown table to paste straight into the report:
python -m frameworkmap --format md crosswalk NIST ISO27001

# A single control's full cross-mapping as CSV:
python -m frameworkmap --format csv map AC-2

# Coverage summary as one CSV row (easy to append to a tracker):
python -m frameworkmap --format csv coverage NIST ISO27001
```

## What to expect

The CSV opens directly in Excel / Google Sheets with the header
`source_id,source_title,target_id,target_title,via`. The Markdown renders as a
GitHub-style table. Pipe characters in titles are escaped so the Markdown table
never breaks.

## How to act

1. Attach the CSV to the audit evidence folder.
2. Keep the one-row coverage CSV in a tracker that you append to each cycle to
   show coverage trending over time.
