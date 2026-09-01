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

Conservative first try (energy, not peak GHz):

- `CLOCK_PERIOD`: 20 ns (50 MHz)
- `FP_CORE_UTIL`: 35
- `PL_TARGET_DENSITY`: 0.50
- `SYNTH_STRATEGY`: `AREA 0`
- Shared RTL via `dir::../../rtl/...` so variants reuse `mac_unit`

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

## PDK reminder

OpenLane expects `PDK_ROOT` and `PDK=sky130A` on the host and mounted into Docker. Experiment 0 already proves that mount works on this machine. If a later run fails with a missing `sky130A` path, it is environment, not RTL.
