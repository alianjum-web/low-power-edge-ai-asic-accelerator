# Results

Curated artifacts only (metrics, comparison table, final GDS). Not full OpenLane run trees.

| Path | Contents |
|---|---|
| `baseline/` | Experiment 0 metrics + KLayout GDS |
| `int8_parallel/` | INT8 4-way baseline metrics, signoff summary, and `project_run_02` GDS |
| `int8_sequential/` | TBD |
| `int4_parallel/` | INT4 4-way optimized-variant metrics, signoff summary, and `project_run_01` GDS (Sprint 7) |
| `int4_sequential/` | TBD |
| `comparison.csv` | Four-point study table |

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

See [docs/research_methodology.md](../docs/research_methodology.md).
