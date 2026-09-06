# Research question (frozen — Sprint 1)

This file exists so a new contributor does not have to reconstruct the
question, hypothesis, and metrics from chat history. It consolidates
wording already committed to in
[00_project_overview.md](00_project_overview.md),
[research_methodology.md](research_methodology.md), and
[quantization.md](quantization.md) — it does not override them.

## Question

> How do reduced numerical precision and MAC parallelism affect
> energy-efficiency, silicon area, timing, latency, and inference
> accuracy of a small Edge-AI accelerator in SKY130?

## Hypothesis

- **INT8 vs INT4:** INT4 is expected to shrink multiplier area and
  switching power (smaller partial products), at the cost of larger
  accuracy loss. Do not assume this — measure both (see
  [quantization.md](quantization.md), "INT4 (Phase 4 only)").
- **Sequential vs 4-way parallel:** parallel MACs are expected to cut
  latency (cycles/inference) at the cost of more area and likely more
  instantaneous power. Sequential may look "low power" on a wattmeter
  and still lose on **energy/inference** if it takes many more cycles
  to finish (see [research_methodology.md](research_methodology.md)).
- **No winner declared in advance.** The four-point matrix (Phase 4)
  measures the intersection of precision x parallelism; a plausible
  a-priori guess is INT8-parallel for the best latency/accuracy
  balance and INT4-parallel as the aggressive low-area/low-power
  candidate with the largest accuracy risk — but this is a hypothesis
  to test, not a result to assume.

## Independent variables

- Numerical precision: INT8 vs INT4
- MAC datapath / parallelism: sequential (one MAC reused) vs 4-way
  parallel

## Dependent variables

- Die area (µm²)
- Max frequency / setup slack at the chosen `CLOCK_PERIOD`
- Total power (static + dynamic, mW)
- Latency (cycles/inference)
- Throughput (inferences/s)
- **Energy/inference** — headline metric (`docs/physical_design.md`:
  Power x cycles-per-inference x clock period)
- Inference accuracy (% vs FP32 reference)

## What "acceptable accuracy" means

Version 1's frozen vectors (`algorithm/generate_vectors.py`) are a
deterministic, seeded 8x4 layer — not a trained model on a real
dataset. For Phases 1-3, "accuracy" means **bit-exactness**: the Python
golden model and the RTL must produce the identical INT8 output on
every generated vector (see [verification.md](verification.md)). That
is measured now (`algorithm/tests/test_reference_model.py`, 8/8
passing) and will be re-measured against RTL in Sprint 3.

Classification/regression "accuracy vs FP32" (the metric the four-point
matrix in Phase 4 will report) only becomes meaningful once a tiny
dataset is adopted — training a toy NumPy MLP is explicitly optional
per this sprint. Until that decision is made, `algorithm/baseline_results.csv`
records this metric as `N/A`. If a dataset is adopted later, "acceptable"
will mean: quantized (INT8/INT4) accuracy does not degrade by more than
an agreed absolute-percentage-point tolerance versus the FP32 reference
on that dataset. The tolerance itself is deliberately left undefined
here — fixing a number before a dataset exists would be a fabricated
target, not a frozen one.

## Out of scope

- No general-purpose CPU.
- No custom PDK — `sky130A` / `sky130_fd_sc_hd` only.
- No fabrication / tape-out.
- No large neural network, CNN, or systolic array — Version 1 is fixed
  at 8 inputs -> 4 outputs (32 MACs/inference).
- No asymmetric / zero-point quantization for Version 1 — symmetric
  signed INT8 only (see [quantization.md](quantization.md)).
- Exactly four hardware variants (baseline INT8-sequential, INT8-4way,
  INT4-sequential, INT4-4way) — not five, not a broader sweep.
- No INT4 hardware and no frequency sweeps before Phase 4.

## Where these numbers actually get measured

- Four-point matrix and evaluation-table template:
  [research_methodology.md](research_methodology.md)
- Fill-in results: `results/comparison.csv`
- Version 1 software baseline (this sprint): `algorithm/baseline_results.csv`
