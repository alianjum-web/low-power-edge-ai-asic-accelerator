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
rtl/            Synthesizable Verilog / SystemVerilog
verification/   Testbenches and reference vectors
designs/        OpenLane configs per design variant
results/        Curated metrics and final GDS artifacts
docs/           Architecture, verification, PD, research plan
scripts/        Simulation and OpenLane helpers
```

Do **not** commit the nested `OpenLane/` tree, virtualenvs, or raw run directories. GitHub is the lab notebook, not a dump of the ASIC toolchain.

## Current status

Phase 0 (baseline adder GDSII) is complete. Next: Python INT8 reference model, then a correct 8×4 accelerator (each PE holds eight weights), then OpenLane. Full roadmap: [docs/01_status_and_roadmap.md](docs/01_status_and_roadmap.md).

## Documentation

| Document | Contents |
|---|---|
| [docs/00_project_overview.md](docs/00_project_overview.md) | Scope, stack, validation levels |
| [docs/01_status_and_roadmap.md](docs/01_status_and_roadmap.md) | Checkpoint and next steps |
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
