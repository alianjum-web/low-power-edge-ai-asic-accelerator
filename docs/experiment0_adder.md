# Experiment 0 — 8-bit adder RTL-to-GDSII

## Purpose

Prove PDK, Docker/OpenLane mount, and `flow.tcl` on a trivial design before the accelerator. This is **Experiment 0** in the research structure, not “Module 1 still pending.”

## RTL

Source of truth: `rtl/adder_8bit.v` (snapshot: `rtl/adder_8bit_baseline.v`).

Combinational 8-bit add, wraparound on overflow. Testbench: `testbench/adder_8bit_tb.v`. Local Yosys script: `synthesis/synth.ys`.

## OpenLane run

| Field | Value |
|---|---|
| Tag | `RUN_2026.08.30_06.36.00` |
| Design | `adder_8bit` |
| Flow | completed |
| Curated GDS | `results/baseline/adder_8bit.klayout.gds` |
| Curated metrics | `results/baseline/metrics.csv` |

Do not commit `OpenLane/designs/adder_8bit/runs/`.

## Signoff snapshot

From `results/baseline/metrics.csv`:

- Die area ≈ 0.002578 mm²
- Synth cells: 38
- Magic violations: 0
- LVS errors: 0
- TritonRoute violations: 0
- SPEF WNS: 0.0
- Typical power (CSV units, µW): internal 1.22e-05, switching 2e-05, leakage 3.35e-10
- Critical path: 1.67 ns
- Config period: 10 ns

## Preserved chain

```text
Adder RTL
  → simulation
  → synthesis
  → floorplan
  → placement
  → routing
  → DRC
  → LVS
  → GDSII
  → KLayout visualization
```

Any future accelerator failure should be treated as a **design** problem until proven otherwise.
