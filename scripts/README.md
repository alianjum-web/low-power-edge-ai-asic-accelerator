# Scripts

| Script | Role |
|---|---|
| `run_sim.sh` | Icarus sim for the Experiment 0 adder |
| `run_openlane.sh` | Wrapper notes for local OpenLane (does not vendor the flow) |
| `collect_results.py` | Copy metrics.csv from a run tag into `results/` |
| `render_gds_screenshots.py` | Render any curated `.gds` to PNG screenshots (full chip + placement/routing detail crops) via KLayout's `klayout.db` Python bindings. Used for `screenshots/int8_parallel/` (Sprint 5); not tied to any one design. |
| `render_gds_stage_views.py` | Render a curated `.gds` through per-stage GDS-layer filters (floorplan = die + power straps, placement = diff/poly/nwell zoomed to a cell-row window, routing = met1-3 + vias, final = every layer). Sprint 8, used for `docs/figures/fig04-07`. Needs the `klayout` pip package, not OpenLane. |
| `plot_rtl_waveform.py` | Parse `verification/simulation/tb_accelerator.vcd` and render a digital timing diagram (clk/rst_n/start/acc_clear/busy/mac_idx/done/y_out) for the first inference. Sprint 8, used for `docs/figures/fig03`. Needs `matplotlib`; regenerate the VCD with `run_sim.sh` first if missing. |
| `plot_ppa_charts.py` | Render the PPA, accuracy, and optimization-trade-off comparison charts directly from `results/comparison.csv` (no hand-copied numbers). Sprint 8, used for `docs/figures/fig08-10`. Needs `matplotlib`. |

OpenLane must already be installed and `PDK_ROOT` / `PDK` set for the OpenLane-dependent scripts above. `render_gds_stage_views.py`, `plot_rtl_waveform.py`, and `plot_ppa_charts.py` need only `klayout`/`matplotlib` (`pip install klayout matplotlib` in a venv) and read already-curated repo artifacts, not a live OpenLane install.
