# Low-Power CMOS Accelerator for Edge-AI Signal Processing

A SKY130 RTL-to-GDSII study of low-power MAC architectures for quantized Edge-AI inference.

**Python → INT8/INT4 → SystemVerilog → OpenLane → GDSII**

## Key results

| Architecture | Precision | Area | Power | Frequency | Energy/inference | Accuracy |
|---|---|---:|---:|---:|---:|---:|
| Adder (Experiment 0) | n/a | 0.002578 mm² | see `results/baseline/` | CLOCK_PERIOD 10 ns | n/a | n/a |
| Sequential | INT8 | TBD | TBD | TBD | TBD | TBD |
| Parallel 4-MAC | INT8 | TBD | TBD | TBD | TBD | TBD |
| Sequential | INT4 | TBD | TBD | TBD | TBD | TBD |
| Parallel 4-MAC | INT4 | TBD | TBD | TBD | TBD | TBD |

Headline metric for the accelerator study: **energy per inference**. Experiment 0 is the toolchain proof (combinational 8-bit adder through OpenLane, run `RUN_2026.08.30_06.36.00`).

## Baseline

This project builds on the open-source **SiliconNPU** RTL-to-GDS baseline (MIT-licensed), merged into this repository on 2026-09-06. `rtl/silicon_npu.sv`, `rtl/mac_core.sv`, and `rtl/mac_core_pipelined.sv` are the baseline datapaths this project's INT8/INT4 sequential/parallel sprint work extends; `flow/` is the baseline's OpenLane orchestration. The original baseline's documentation (developer/user/install guides, its own final report) has been folded into [docs/baseline_reference.md](docs/baseline_reference.md) as a single source of truth — that file clearly marks which of the original authors' claims (toolchain versions, reported area/power/timing) have **not** been reproduced or verified in this repository. The previous from-scratch, unverified `edge_ai_accelerator.sv`/`mac_unit.sv` datapath has been retired to [legacy/](legacy/) now that `silicon_npu.sv`/`mac_core.sv` are the adopted baseline.

## Research question

How do reduced numerical precision and MAC parallelism affect energy-efficiency, silicon area, timing, latency, and inference accuracy of a small Edge-AI accelerator in SKY130?

## Hardware / flow

- SkyWater SKY130 (`sky130A`, `sky130_fd_sc_hd`)
- OpenLane (local checkout; not vendored in this repository)
- Yosys, OpenROAD, Magic, Netgen, KLayout
- Icarus Verilog / Verilator

## Verification

Python reference → RTL simulation → bit-exact comparison (three levels: math, RTL, physical). See [docs/verification.md](docs/verification.md).

## Physical design

RTL → synthesis → floorplan → placement → CTS → routing → DRC → LVS → GDSII. See [docs/physical_design.md](docs/physical_design.md).

## Repository layout

```text
algorithm/      Python golden model and test vectors (Phase 1)
rtl/            Synthesizable Verilog / SystemVerilog (baseline: silicon_npu.sv, mac_core*.sv)
verification/   Testbenches and reference vectors
designs/        OpenLane configs per design variant (Experiment 0 / this project's own runs)
flow/           SiliconNPU baseline's OpenLane orchestration (Makefile, config.tcl, openlane_config/)
results/        Curated metrics and final GDS artifacts
docs/           This project's architecture, verification, PD, research plan ("My Docs"),
                including baseline_reference.md (single source of truth for the former docs1/)
legacy/         Retired pre-baseline RTL (edge_ai_accelerator.sv, mac_unit.sv) and its testbenches
openmac/        Baseline's Python analysis/report-parsing library
scripts/        Simulation and OpenLane helpers (this project's + baseline's)
screenshots/    Baseline physical-design stage screenshots (placement, routing, power grid)
tests/          Unit tests for openmac/
```

Do **not** commit the nested `OpenLane/` tree, virtualenvs, or raw run directories. GitHub is the lab notebook, not a dump of the ASIC toolchain.

## Current status

Phase 0 (baseline adder GDSII) is complete. Next: Python INT8 reference model, then a correct 8×4 accelerator (each PE holds eight weights), then OpenLane.

**How to follow the work (new contributors):** complete the project as **8 weekly sprints** (~20–25 hours/week). Start at [docs/02_eight_week_sprint_plan.md](docs/02_eight_week_sprint_plan.md) and open only the current week under [docs/sprints/](docs/sprints/). Contribution rules: [CONTRIBUTING.md](CONTRIBUTING.md). Checkpoint list: [docs/01_status_and_roadmap.md](docs/01_status_and_roadmap.md).

## Documentation

| Document | Contents |
|---|---|
| [docs/00_project_overview.md](docs/00_project_overview.md) | Scope, stack, validation levels |
| [docs/01_status_and_roadmap.md](docs/01_status_and_roadmap.md) | Checkpoint and next steps |
| [docs/02_eight_week_sprint_plan.md](docs/02_eight_week_sprint_plan.md) | 8-week calendar, gates, stack, final package |
| [docs/sprints/](docs/sprints/) | Detailed Week 1–8 guides (tasks, files, acceptance) |
| [docs/architecture.md](docs/architecture.md) | Adder + planned PE array |
| [docs/quantization.md](docs/quantization.md) | Symmetric signed INT8 policy |
| [docs/verification.md](docs/verification.md) | Golden model and hierarchical tests |
| [docs/physical_design.md](docs/physical_design.md) | OpenLane knobs and metrics |
| [docs/experiment0_adder.md](docs/experiment0_adder.md) | Adder RTL-to-GDS evidence |
| [docs/research_methodology.md](docs/research_methodology.md) | Four-point experiment |
| [docs/github_and_lab_notebook.md](docs/github_and_lab_notebook.md) | What to commit |

## License

MIT. See [LICENSE](LICENSE).
# low-power-edge-ai-asic-accelerator
