#!/usr/bin/env bash
# Build a full coverage matrix across every framework pair.
# Usage:  bash demos/08-multi-framework-matrix/matrix.sh
# Prints a Markdown table: rows = source framework, cols = target framework,
# cells = coverage_pct. Diagonal is "--".
set -euo pipefail

FW=(NIST ISO27001 SOC2 CMMC PCI)
PY="python -m frameworkmap"

# header
printf '| src \\ tgt |'
for t in "${FW[@]}"; do printf ' %s |' "$t"; done
printf '\n|%s|' '---'
for _ in "${FW[@]}"; do printf '%s|' '---'; done
printf '\n'

# rows
for s in "${FW[@]}"; do
  printf '| **%s** |' "$s"
  for t in "${FW[@]}"; do
    if [ "$s" = "$t" ]; then
      printf ' %s |' '--'
    else
      pct=$($PY --format json coverage "$s" "$t" | python -c 'import sys,json;print(json.load(sys.stdin)["coverage_pct"])')
      printf ' %s%% |' "$pct"
    fi
  done
  printf '\n'
done
