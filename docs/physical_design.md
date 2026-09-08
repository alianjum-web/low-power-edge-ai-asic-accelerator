# Physical design (SKY130 / OpenLane)

## Role of Experiment 0

Never debug a complex accelerator and a broken toolchain at the same time. The adder run `RUN_2026.08.30_06.36.00` closed:

synthesis → floorplan → placement → routing → Magic DRC → LVS → GDSII.

CTS is not meaningful for the combinational adder (`CLOCK_PORT` empty). The accelerator **will** need a real clock and CTS.

OpenLane lives as a **local install** (`OpenLane/` on disk, ~1.2 GB). It is gitignored. Do not vendor it.

## Experiment 0 config (what actually ran)

`designs/adder_8bit/config.json`:

| Key | Value |
|---|---|
| `DESIGN_NAME` | `adder_8bit` |
| `VERILOG_FILES` | `dir::adder_8bit.v` |
| `CLOCK_PORT` | `""` |
| `CLOCK_PERIOD` | 10 |
| `FP_CORE_UTIL` | 30 |
| `PL_TARGET_DENSITY` | 0.55 |

Metrics also record `SYNTH_STRATEGY` `AREA 0` and `sky130_fd_sc_hd`.

There is `OpenLane/designs/adder_8bit/config_lowpower.json` (util 45, density 0.6). That is **not** the tagged successful run.

## Flow stages (what breaks)

| Stage | Tool | Typical beginner failure |
|---|---|---|
| Synthesis | Yosys + ABC | Unmapped gates: SV constructs, missing files |
| Floorplan | OpenROAD | `FP_CORE_UTIL` too high |
| Placement | RePlAce / OpenDP | `PL_TARGET_DENSITY` too close to 1.0 |
| CTS | TritonCTS | Wrong `CLOCK_PORT` / too tight `CLOCK_PERIOD` |
| Routing | FastRoute + TritonRoute | Congestion from high util/density or wide buses |
| DRC / LVS | Magic + Netgen | Congestion DRC; dangling ports → LVS |
| GDS | Magic / KLayout | — |

## Accelerator starting knobs (tune after RTL exists)

The active baseline config for Sprint 4 is in [../designs/accelerator_int8_parallel/config.json](../designs/accelerator_int8_parallel/config.json):

- `CLOCK_PORT`: `clk`
- `CLOCK_PERIOD`: 20 ns (50 MHz)
- `FP_CORE_UTIL`: 35
- `PL_TARGET_DENSITY`: 0.50
- `SYNTH_STRATEGY`: `AREA 0`
- Shared RTL via the active Version 1 accelerator hierarchy; inherited baseline modules are reference-only and are not selected for current accelerator runs.

The INT8 parallel baseline has now been measured with OpenLane run `project_run_02`. Curated values are in [../results/int8_parallel/metrics.csv](../results/int8_parallel/metrics.csv), with signoff details in [../results/int8_parallel/signoff.md](../results/int8_parallel/signoff.md). The run completed through GDS/LVS/DRC, but antenna and max-fanout warnings remain documented rather than silently discarded.

Wide 32-bit accumulator buses route poorly at high density. If placement or routing fails, lower density first; do not raise `OUT_DIM`.

## Metrics to extract for every architecture

**Hardware:** area, cell count, utilization, maximum frequency, setup slack, hold slack, dynamic power, leakage power, total power.

**Architecture:** cycles/inference, throughput, MACs/cycle, **energy/inference**.

**AI:** FP32 accuracy, INT8 accuracy, INT4 accuracy, accuracy degradation.

Energy per inference ≈ Power × (cycles per inference × clock period). This is the headline “low-power edge” number.

## Report locations (OpenLane)

After a run, copy **summaries** into `results/<variant>/`, not the whole `runs/` tree:

- Die area: synthesis / floorplan reports
- Slack: signoff STA
- Power: signoff power (internal, switching, leakage)
- Manufacturability: Magic DRC, LVS, KLayout if enabled

## Baseline OpenLane configs (inherited)

`flow/openlane_config/*.tcl` and `flow/config.tcl` are the SiliconNPU baseline's own OpenLane configs for `mac_core`, `mac_core_pipelined`, and `silicon_npu` — real starting points, not fabricated. Two things were found by reading every `.tcl` file directly (not just the prose in `docs1/final_report.md`):

- **Fixed 2026-09-07:** all four files originally hardcoded `VERILOG_FILES` as an absolute Docker path (`/workspace/flow/src/...`), which assumed the baseline's own WSL2 + Docker install (see [baseline_reference.md](baseline_reference.md)). This repo runs OpenLane as a **local install** (see above) — all four now use a relative `dir::` reference pointing at `rtl/*.sv` directly, and the `flow/src/*.sv` duplicate copies those paths used to require have been deleted.
- `flow/openlane_config/npu_15ns.tcl` is still misleadingly named: its `CLOCK_PERIOD` is actually `20.0`, not `15.0` — check the file, not the filename, before reusing it. (Not fixed — the mismatch is between the filename and its own content, not something blocking the config from running; renaming is Phase 4 sweep housekeeping.)

See [baseline_reference.md](baseline_reference.md) for the full inherited toolchain/PPA claims and what has and hasn't been reproduced here.

## PDK reminder

OpenLane expects `PDK_ROOT` and `PDK=sky130A` on the host and mounted into Docker. Experiment 0 already proves that mount works on this machine. If a later run fails with a missing `sky130A` path, it is environment, not RTL.
