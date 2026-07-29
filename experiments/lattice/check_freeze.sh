#!/usr/bin/env bash
# Freeze check for the melodic scorer (G-006, 2026-07-25). Mirrors
# experiments/triads/check_freeze.sh check A: melodic.sha256 pins melodic.py;
# any edit fails until a human updates the pin. Run from experiments/lattice/.
set -euo pipefail
cd "$(dirname "$0")"
if shasum -a 256 -c melodic.sha256 >/dev/null 2>&1; then
  echo "freeze check A (hash pin): OK — melodic.py matches $(cut -d' ' -f1 melodic.sha256)"
else
  echo "freeze check A FAILED: melodic.py does not match melodic.sha256." >&2
  echo "melodic.py is FROZEN (v0.1.0, gate G-006). Changes need Marcus's approval + pin update." >&2
  exit 1
fi
