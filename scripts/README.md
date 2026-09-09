# Scripts

| Script | Role |
|---|---|
| `run_sim.sh` | Icarus sim for the Experiment 0 adder |
| `run_openlane.sh` | Wrapper notes for local OpenLane (does not vendor the flow) |
| `collect_results.py` | Copy metrics.csv from a run tag into `results/` |
| `render_gds_screenshots.py` | Render any curated `.gds` to PNG screenshots (full chip + placement/routing detail crops) via KLayout's `klayout.db` Python bindings. Used for `screenshots/int8_parallel/` (Sprint 5); not tied to any one design. |

OpenLane must already be installed and `PDK_ROOT` / `PDK` set.
