# Results

Curated artifacts only (metrics, comparison table, final GDS). Not full OpenLane run trees.

| Path | Contents |
|---|---|
| `baseline/` | Experiment 0 metrics + KLayout GDS |
| `int8_parallel/` | INT8 4-way baseline metrics, signoff summary, and `project_run_02` GDS |
| `int8_sequential/` | Empty — out of scope, not run. Sprint 6 descoped the sequential-schedule axis to fit the project timeline; see `docs/optimization_plan.md`'s "one axis only." |
| `int4_parallel/` | INT4 4-way optimized-variant metrics, signoff summary, and `project_run_01` GDS (Sprint 7) |
| `int4_sequential/` | Empty — out of scope, not run (same decision as `int8_sequential/` above). |
| `comparison.csv` | Study table — populated rows are `adder_8bit` (Experiment 0), `int8_parallel` (baseline), `int4_parallel` (optimized); the two sequential rows are placeholders for the descoped axis, not pending measurements. |

See [`../screenshots/int8_parallel/`](../screenshots/int8_parallel/) and
[`../screenshots/int4_parallel/`](../screenshots/int4_parallel/) for the
floorplan/placement/routing figures rendered directly from each variant's
GDS (KLayout, `scripts/render_gds_screenshots.py`) — Sprint 5 for
`int8_parallel`, Sprint 7 for `int4_parallel`. The two won't look alike:
`int4_parallel` is a smaller, differently-placed-and-routed layout (see
`docs/ppa_comparison.md`), not a recolored copy of the INT8 image.
The rest of `../screenshots/` (`full_chip.png`, `cell_placement.png`,
`metal_routing.png`, `power_grid.png`, `signal_routing.png`) are renders of
the **inherited SiliconNPU baseline** (`results/silicon_npu/silicon_npu.gds`),
not this project's Experiment 0 adder or Version 1 accelerator — see
[docs/baseline_reference.md](../docs/baseline_reference.md).

Curated, captioned copies of the floorplan/placement/routing/final-GDSII views (plus architecture diagrams, the RTL waveform, and the PPA/accuracy/trade-off charts) are in [`../docs/figures/`](../docs/figures/) for the Sprint 8 report; this directory stays the raw/curated-metrics source of truth.

See [docs/research_methodology.md](../docs/research_methodology.md).
