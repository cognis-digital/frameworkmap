# Demo 10 — Threat-informed crosswalk from authoritative data feeds (edge / air-gap)

**Persona.** A federal SSP author on a *disconnected* (air-gapped) GRC
workstation needs the NIST→SOC 2 crosswalk to carry (a) the **authoritative**
NIST SP 800-53 Rev 5 control titles and (b) the **ATT&CK techniques each NIST
control mitigates**, so the package shows it is threat-informed, not just
checkbox-mapped. No internet on the enclave.

## The feature

FRAMEWORKMAP bundles a stdlib ingestion layer (`frameworkmap.datafeeds`) wired
to two real, keyless feeds:

| feed id | source | gives us |
|---|---|---|
| `oscal-800-53-rev5-catalog` | NIST `usnistgov/oscal-content` | authoritative control titles |
| `attack-nist-mappings` | CTID `mappings-explorer` | ATT&CK techniques a control mitigates |

New commands:

```bash
frameworkmap feeds list                       # the feeds FRAMEWORKMAP consumes
frameworkmap feeds update                      # fetch + cache (online, once)
frameworkmap feeds get <id> --offline          # re-serve from cache
frameworkmap enrich AC-2 --offline             # title + ATT&CK techniques for one control
frameworkmap threat-map SOC2 --offline         # NIST->SOC2 crosswalk + ATT&CK coverage
```

## Air-gap workflow

```bash
# 1) On a connected staging box, fetch + cache the feeds:
frameworkmap feeds update

# 2) Snapshot the cache to a tarball for sneakernet:
python -m frameworkmap.datafeeds snapshot-export feeds.tar.gz

# 3) Carry feeds.tar.gz to the air-gapped enclave and import:
export COGNIS_FEEDS_CACHE=/secure/feeds
python -m frameworkmap.datafeeds snapshot-import feeds.tar.gz

# 4) Everything now runs --offline, never touching the network:
frameworkmap threat-map SOC2 --offline --format csv > ssp_threat_map.csv
```

## Run the demo (offline, against the committed fixtures)

```bash
python demos/10-threat-informed-feeds/run.py
```

`run.py` points `COGNIS_FEEDS_CACHE` at the trimmed test fixtures and prints the
enriched AC-2 control and the threat-informed NIST→SOC 2 crosswalk — entirely
offline.
