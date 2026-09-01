#!/usr/bin/env bash
# Run OpenLane on a design name that exists under designs/ AND in your OpenLane
# checkout. This repository does not vendor OpenLane.
#
# Usage:
#   OPENLANE_ROOT=/path/to/OpenLane ./scripts/run_openlane.sh adder_8bit
set -euo pipefail
DESIGN="${1:-adder_8bit}"
if [[ -z "${OPENLANE_ROOT:-}" ]]; then
  echo "Set OPENLANE_ROOT to your local OpenLane clone (gitignored in this repo)."
  exit 1
fi
if [[ -z "${PDK_ROOT:-}" || -z "${PDK:-}" ]]; then
  echo "Export PDK_ROOT and PDK (e.g. PDK=sky130A) before launching the flow."
  exit 1
fi
cd "$OPENLANE_ROOT"
./flow.tcl -design "$DESIGN"
