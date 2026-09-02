# Sprint 1: Research definition + software baseline

**Week 1** · **~20–25 hours** · **Phase 1** · Previous: none · Next: [Sprint 2](sprint_02_hardware_architecture_and_rtl.md)

---

## Goal

Freeze the accelerator workload, write the research question, and implement a **Python reference model that produces correct outputs**. Hardware work in later sprints is worthless if this model is wrong.

**Do not proceed until your Python model produces correct outputs.**

---

## Why this sprint exists

The complete chain starts with the algorithm, not with OpenLane. Software is the golden model. RTL, GDSII, and PPA all hang off the integers this sprint defines.

---

## Checkpoint already in this repo (do not redo)

- Experiment 0: combinational 8-bit adder through OpenLane to GDSII (`docs/experiment0_adder.md`).
- Draft research question and INT8 policy exist in `docs/00_project_overview.md` and `docs/quantization.md`.
- There is a **draft** `algorithm/reference_model.py`. Treat it as a starting point: audit it, complete tests, and freeze vectors. Do not assume it is finished.

---

## 1. Choose the accelerator

Do **not** attempt a large neural network.

Use a small workload such as:

**Quantized fully connected / MAC accelerator**

Architecture:

```text
Input
  ↓
Input Buffer
  ↓
MAC Units
  ↓
Accumulator
  ↓
Activation
  ↓
Output
```

A MAC performs:

\[
y = \sum_{i=0}^{N-1} x_i w_i
\]

Start with:

- 8-bit signed inputs
- 8-bit signed weights
- 16/32-bit accumulator (this project: **INT16 product, INT32 accumulate**)
- small number of MAC units

**This repository’s Version 1 (use this, do not invent a bigger net):**

```text
8 inputs → 4 output neurons → ReLU → 4 INT8 outputs
```

\[
y_j = \mathrm{ReLU}\left(\sum_{i=0}^{7} x_i w_{ij} + b_j\right)
\]

32 MAC operations per inference. Each PE holds **eight weights** (one output column), not a single weight register. See [architecture.md](../architecture.md).

---

## 2. Define the research question

Example from the original plan:

> Can a lightweight quantized and hardware-optimized Edge-AI accelerator reduce energy and silicon area while maintaining acceptable inference accuracy?

Repository wording (preferred for README and report):

> How do reduced numerical precision and MAC parallelism affect energy-efficiency, silicon area, timing, latency, and inference accuracy of a small Edge-AI accelerator in SKY130?

Write the frozen question in `docs/research_question.md` (deliverable below) so a new contributor does not have to hunt through chat history.

Also write, in the same file:

- **Hypothesis** (what you expect INT8 vs INT4 and sequential vs parallel to do)
- **Independent variables** (precision, MAC parallelism / datapath)
- **Dependent variables** (area, power, delay, frequency, energy/op or energy/inference, accuracy)
- **What “acceptable accuracy” means** (e.g. drop vs FP32 on a tiny synthetic or a named tiny dataset)
- **What is out of scope** (no CPU, no custom PDK, no fabrication)

You do **not** run the four-point hardware matrix this week. You only freeze the question so Sprints 6–7 are not a fishing expedition.

---

## 3. Build Python reference model

Use:

- Python
- NumPy
- optionally PyTorch (not required for Version 1)

Implement:

```text
input
→ multiplication
→ accumulation
→ activation
→ output
```

Concrete Version 1 pipeline:

```text
x (INT8, length 8)
W (INT8, 8×4)
b (INT32, length 4, optional)
→ acc_j = Σ_i x_i w_ij + b_j   (INT32)
→ ReLU
→ requantize to INT8 (document scale)
→ y (INT8, length 4)
```

Place code in **`algorithm/`**, not a new `python_reference/` tree.

Suggested files (align with `algorithm/README.md`):

| File | Role |
|---|---|
| `algorithm/reference_model.py` or `model.py` | GEMV + ReLU + requantize |
| `algorithm/quantization.py` | symmetric signed quantize / dequantize |
| `algorithm/generate_vectors.py` | seeded weights, biases, inputs → CSV/hex |
| `algorithm/tests/` or a small `pytest` / script | known-answer checks |

Policy: **symmetric signed INT8**, zero-point 0. Do not mix unsigned 0–255 activations with signed hardware. See [quantization.md](../quantization.md).

Training a toy NumPy MLP is **optional**. A fixed, seeded 8×4 layer is enough to verify MAC → PE → top.

---

## 4. Establish baseline measurements

Record:

- inference accuracy (even if the “dataset” is synthetic; document how you compute it)
- number of operations (32 MACs per inference for Version 1)
- bit width (INT8 in / INT16 product / INT32 acc / INT8 out)
- latency target (cycles: at least 8 compute cycles for the parallel-4 PE schedule, plus load/store; sequential variant will differ later)
- expected hardware resources (4 MAC/PE units, 32 weights, 4 accumulators, FSM)

Write numbers into `algorithm/baseline_results.csv` (and keep a human summary in `docs/research_question.md` or `algorithm/README.md`).

---

## Deliverables

Original plan names → **this repo**:

```text
docs/research_question.md
algorithm/                  (was python_reference/)
algorithm/baseline_results.csv
docs/figures/architecture.png   (or docs/architecture.md diagrams until a PNG exists)
```

Also expected by the original plan:

```text
research_question.md
python_reference/
baseline_results.csv
architecture.png
```

Create `docs/research_question.md` and `algorithm/baseline_results.csv` this week. A first architecture diagram can be a PNG under `docs/figures/` **or** a clearly labeled ASCII/markdown figure in `docs/architecture.md` if you do not have drawing tools yet. Sprint 8 still requires publication-quality figures.

---

## Tasks a contributor can pick up

1. Write `docs/research_question.md` from the frozen Version 1 scope.
2. Finish and test the NumPy golden model (multiply, accumulate, ReLU, requantize).
3. Generate **checked-in** test vectors (`verification/reference/` and/or `algorithm/`).
4. Hand-compute 2–3 tiny examples (including zeros, negatives, and a near-overflow product) and show the model matches.
5. Fill `algorithm/baseline_results.csv`.
6. Sketch `architecture.png` from the block diagram in this sprint.

---

## Suggested commands

```bash
cd algorithm
python3 -m pytest -q          # if tests exist
python3 reference_model.py    # if the file is runnable
python3 generate_vectors.py   # once this script exists
```

Use a project venv if you add dependencies; do not commit `.venv/`.

---

## Acceptance criteria

- [ ] Research question, hypothesis, and metrics are written down.
- [ ] Python GEMV + ReLU (+ requantize if Version 1 needs INT8 outputs) matches hand-computed cases.
- [ ] Same integers will be reused in Sprint 3 (`Python result == RTL result`).
- [ ] CSV baseline exists (even if accuracy is “N/A pending dataset”; then say so).
- [ ] Architecture diagram or equivalent markdown figure exists.
- [ ] No OpenLane run on unfinished accelerator RTL.

---

## What not to do this week

- Do not synthesize or place the accelerator.
- Do not start INT4 hardware.
- Do not write the 15-page report yet.
- Do not implement five MAC variants.
- Do not “fix” Experiment 0 adder RTL unless it is broken; it is the toolchain proof.

---

## Gate to Sprint 2

Python model produces **correct** outputs for the frozen vectors. If it does not, stay here.
