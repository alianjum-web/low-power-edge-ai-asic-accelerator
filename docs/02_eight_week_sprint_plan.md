# Eight-week sprint plan (master overview)

This is the calendar. Each week has its own detailed guide under
[sprints/](sprints/) — read this file for the shape of the whole
project, then open only the current week.

Do not skip a week because a later one looks easier (e.g. do not touch
OpenLane during Week 2 just because Experiment 0 already proved the
toolchain). Do not start a week whose gate has not been passed.

## Calendar

| Week | Phase | Sprint guide | Goal |
|---|---|---|---|
| 1 | 1 | [sprint_01_research_and_python_baseline.md](sprints/sprint_01_research_and_python_baseline.md) | Freeze the research question and workload; build a correct Python golden model (GEMV + bias + ReLU + requantize). |
| 2 | 2 | [sprint_02_hardware_architecture_and_rtl.md](sprints/sprint_02_hardware_architecture_and_rtl.md) | Convert the golden model into synthesizable SystemVerilog: MAC, accumulator, activation, control FSM. |
| 3 | 2 (gate) | [sprint_03_rtl_verification.md](sprints/sprint_03_rtl_verification.md) | Prove RTL matches Python bit-exactly on the frozen vectors. Mandatory — do not proceed on a guess. |
| 4 | 3 (start) | [sprint_04_synthesis_and_baseline_ppa.md](sprints/sprint_04_synthesis_and_baseline_ppa.md) | Yosys synthesis + a baseline OpenLane run; first real PPA numbers. |
| 5 | 3 (complete) | [sprint_05_rtl_to_gdsii.md](sprints/sprint_05_rtl_to_gdsii.md) | Finish the verified accelerator through placement, routing, DRC/LVS, and GDSII. |
| 6 | 4 (design) | [sprint_06_low_power_optimization.md](sprints/sprint_06_low_power_optimization.md) | Choose 1–2 optimizations (e.g. INT4, parallel MACs) and implement them — design only, not yet the measurement loop. |
| 7 | 4 (measure) | [sprint_07_optimization_experiment_and_ppa.md](sprints/sprint_07_optimization_experiment_and_ppa.md) | Run the optimized variant(s) through the same flow and fill the comparison table honestly. |
| 8 | 5 | [sprint_08_research_package.md](sprints/sprint_08_research_package.md) | Package the project: figures, PPA/accuracy tables, technical report, CV/SOP language. |

~20–25 hours/week. This maps onto the Phase table in
[01_status_and_roadmap.md](01_status_and_roadmap.md); that file tracks
*what is actually done*, this file tracks *when a new contributor
should do it*.

## Gates (do not cross without passing)

- **End of Week 3:** Python and RTL must agree bit-exactly on every
  frozen vector. If they don't, stay in Sprint 3 — do not start
  synthesis on unverified RTL (see the "Hard rules" in
  [../AGENTS.md](../AGENTS.md)).
- **End of Week 5:** the accelerator must be DRC/LVS-clean GDSII before
  any optimization work starts.
- **End of Week 7:** exactly the four variants in
  [research_methodology.md](research_methodology.md) — INT8/INT4 ×
  sequential/parallel — no fifth variant, no broader design-space sweep.

## Minimum skills

- Python (NumPy) well enough to write a small quantized GEMV.
- SystemVerilog-2012: modules, FSMs, parameterization (`WIDTH`,
  `ARRAY_SIZE`), signed arithmetic.
- Icarus Verilog / Verilator for simulation; GTKWave for waveform debug.
- Enough Yosys/OpenROAD/Magic/Netgen/OpenLane familiarity to run a
  local-install flow and read STA/power/DRC/LVS reports (see
  [physical_design.md](physical_design.md)).
- Git/GitHub hygiene for curated commits (see
  [github_and_lab_notebook.md](github_and_lab_notebook.md)).

## What not to learn / build (out of scope)

- No general-purpose CPU, no instruction set, no compiler.
- No large neural network, CNN, or systolic array — Version 1 is fixed
  at 8 inputs → 4 outputs, 32 MACs/inference.
- No custom PDK, no fabrication/tape-out — `sky130A` /
  `sky130_fd_sc_hd` only.
- No asymmetric/zero-point quantization for Version 1 — symmetric
  signed INT8 only.
- No fifth hardware variant beyond the four-point INT8/INT4 ×
  sequential/parallel matrix.
- No frequency sweeps or paper writing before Version 1 INT8-parallel
  is bit-exact and physically closed.

See [research_question.md](research_question.md) "Out of scope" for
the frozen version of this list.

## Final package (Week 8 deliverables)

- Curated `results/` per variant: PPA (area, power, slack, frequency),
  energy/inference, accuracy — `results/comparison.csv`.
- Final GDSII per variant.
- Figures: architecture diagram, PPA/accuracy comparison charts.
- Technical report / write-up following
  [research_methodology.md](research_methodology.md)'s evaluation
  table.
- CV/SOP paragraph, filled in only once the numbers above are real
  (see research_methodology.md's "SOP / CV language").
- A clean, curated GitHub repository — no `OpenLane/` tree, no raw
  `runs/` directories, no simulator binaries (see
  [github_and_lab_notebook.md](github_and_lab_notebook.md)).
