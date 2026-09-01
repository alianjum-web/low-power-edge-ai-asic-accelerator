# OpenLane design configs

Each variant gets its own directory with `config.json` (and a small RTL copy if the flow requires it). Shared synthesizable source stays in `../../rtl/`.

| Directory | Role |
|---|---|
| `adder_8bit/` | Experiment 0 (present) |
| `accelerator_int8_parallel/` | Version 1 (Phase 3) |
| `accelerator_int8_sequential/` | Research baseline (Phase 4) |
| `accelerator_int4_parallel/` | Variant C |
| `accelerator_int4_sequential/` | Variant B |

Run OpenLane from the **local** OpenLane install; do not commit `runs/`. Point `VERILOG_FILES` at `dir::../../rtl/...` when the design is ready.

The nested `OpenLane/designs/adder_8bit/` copy was used for the successful 2026-08-30 run. Canonical project config: `designs/adder_8bit/config.json`.
