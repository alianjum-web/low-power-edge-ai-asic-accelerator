# Figures (Sprint 8)

Ten required figures plus three supplemental INT4 layout renders, all generated from artifacts already in this repo (no fabricated data) by the scripts in [`../../scripts/`](../../scripts/README.md) — `render_gds_stage_views.py`, `plot_rtl_waveform.py`, `plot_ppa_charts.py`. Each figure's caption below says exactly what it was built from; regenerate any of them with those scripts (they need only `klayout`/`matplotlib` in a venv, not a live OpenLane install — see `scripts/README.md`). fig01/fig02 (the two architecture diagrams) are hand-authored SVGs, checked in alongside their rasterized PNGs.

| File | Contents | Built from |
|---|---|---|
| `fig01_system_architecture.png` (+ `.svg`) | `accelerator_top` block diagram: host write ports, `act_mem`/`bias_mem`, `controller` FSM, 4x `processing_element`, 4x `requantize`, packed `y_out` | `docs/architecture_spec.md` port list and section 3 timing, hand-drawn |
| `fig02_mac_pe_architecture.png` (+ `.svg`) | Single `processing_element` internals: weight register file, signed multiplier, bias-preload mux, INT32 accumulator, control signals | `rtl/processing_element.sv`, `docs/architecture_spec.md` section 5 |
| `fig03_rtl_simulation_waveform.png` | Digital timing diagram (`clk`, `rst_n`, `start`, `acc_clear`, `busy`, `mac_idx`, `done`, `y_out`) for the first inference in the accelerator testbench | `scripts/plot_rtl_waveform.py` on `verification/simulation/tb_accelerator.vcd` (vector 0, IDLE→LOAD→COMPUTE×8→DONE_S) |
| `fig04_baseline_floorplan.png` | INT8 baseline die outline + top-level power straps/rings (met4/met5) | `scripts/render_gds_stage_views.py results/int8_parallel/accelerator_top_project_run_02.gds <out_dir> int8_parallel` (writes all four stages per run; this is the `_floorplan.png` output) |
| `fig05_baseline_placement.png` | INT8 baseline standard-cell rows (diff/poly/nwell), zoomed to a ~17 um window so individual placed cells are visible | Same command, `_placement.png` output (diff/poly/nwell layers only, cropped) |
| `fig06_baseline_routing.png` | INT8 baseline signal routing (met1-met3 + vias) | Same command, `_routing.png` output |
| `fig07_final_gdsii_comparison.png` | Full signed-off layout, INT8 baseline vs INT4 optimized, side by side | `render_gds_stage_views.py`'s `final` output for both GDS files, composited with ImageMagick `montage` |
| `fig08_ppa_comparison.png` | Die area / power / energy-per-inference bar charts, INT8 vs INT4 | `scripts/plot_ppa_charts.py` on `results/comparison.csv` |
| `fig09_accuracy_comparison.png` | Synthetic accuracy bar chart, INT8 vs INT4 | `scripts/plot_ppa_charts.py` on `results/comparison.csv` (from `algorithm/measure_accuracy.py`) |
| `fig10_optimization_tradeoff.png` | Area/energy saving (%) vs accuracy cost (points), one measured point, not an interpolated curve | `scripts/plot_ppa_charts.py` on `results/comparison.csv` |
| `supplemental_int4_floorplan.png`, `supplemental_int4_placement.png`, `supplemental_int4_routing.png` | Same layer-filtered views as fig04-06, for the INT4 variant | `scripts/render_gds_stage_views.py` on `results/int4_parallel/accelerator_top_int4_project_run_01.gds` |

**Honesty note on fig04-07:** this project only ever captured the final, signed-off (DRC/LVS/route-clean) GDSII per variant — no separate intermediate floorplan-only or placement-only OpenROAD snapshot exists in `results/`. fig04-06 are the *same* final GDS viewed through different GDS-layer filters (power straps only / front-end-of-line cell layers only / routing metals only) to illustrate what each stage's output looks like, not literal snapshots taken mid-flow. Do not cite them as evidence of an intermediate floorplan or placement run distinct from the one in `results/int8_parallel/`.

See [../report/report.md](../report/report.md) for the sprint's technical report, which embeds all ten numbered figures.
