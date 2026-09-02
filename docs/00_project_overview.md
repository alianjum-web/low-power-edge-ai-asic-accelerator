# Design and Optimization of a Low-Power CMOS Accelerator
for Edge-AI Signal Processing

## One-sentence summary

A SKY130 RTL-to-GDSII study of quantized MAC architectures for Edge-AI inference, with a Python golden model, bit-exact RTL verification, and a controlled INT8/INT4 × sequential/parallel experiment.

## How to execute this (8 weeks)

Follow **[02_eight_week_sprint_plan.md](02_eight_week_sprint_plan.md)**. New contributors: [CONTRIBUTING.md](../CONTRIBUTING.md).

## Pipeline

Python/AI model → quantization → SystemVerilog RTL → functional verification → synthesis → floorplan → placement → CTS → routing → DRC/LVS → GDSII → architectural comparison.

## Stack

| Layer | Choice |
|---|---|
| Technology | SkyWater SKY130 (`sky130A`, `sky130_fd_sc_hd`) |
| Flow | OpenLane (local install; not stored as project source) |
| HDL | Verilog / SystemVerilog |
| Simulation | Icarus Verilog / Verilator |
| Physical | Yosys + OpenROAD + Magic + Netgen / KLayout |
| First hardware datatype | Symmetric signed INT8 |

## Research question

How do numerical precision (INT8 vs INT4) and MAC parallelism (sequential vs 4-way) affect area, power, timing, latency, energy/inference, and inference accuracy of a small Edge-AI accelerator in SKY130?

That is a research investigation, not merely “I built an AI accelerator.”

## Three validation levels (mandatory)

1. **Mathematical:** Python golden model produces the expected integer outputs.
2. **RTL:** SystemVerilog simulation matches Python bit-exactly on the same vectors.
3. **Physical:** OpenLane produces a synthesized netlist, placement, routing, STA, power, DRC, LVS, and GDSII.

Narrative:

```text
Algorithm → RTL → gate-level implementation → physical layout
```

## Scope (deliberately small)

Version 1 network: 8 inputs → 4 output neurons → ReLU → 4 INT8 outputs.

\[
y_j = \mathrm{ReLU}\left(\sum_{i=0}^{7} x_i w_{ij} + b_j\right)
\]

That is 8 × 4 = 32 MAC operations per inference. Small enough to debug by hand; large enough to demonstrate a real accelerator datapath.

The project does **not** need a giant CNN, custom SRAM, or a 64×64 systolic array.

## Scholarship story

The chain is: physics → mathematical modeling → numerical representation → AI inference → digital architecture → RTL → verification → ASIC implementation → physical measurements → optimization.

Evidence to keep in the repository: Python model, quantization, RTL, automated verification, OpenLane reports, GDSII, area/power/timing, INT8 vs INT4, sequential vs parallel, energy/accuracy trade-off.

## What this repository is not

It is not a dump of OpenLane source, Docker caches, PDK files, or every failed run. GitHub is the laboratory notebook. See [github_and_lab_notebook.md](github_and_lab_notebook.md).
