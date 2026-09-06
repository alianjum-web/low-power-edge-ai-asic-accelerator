# AGENTS.md — instructions for AI coding agents working on this repo

Read this before touching any file. It exists so an agent (or a new
human contributor) does not have to reconstruct project state from
chat history, and does not state things about this repo that are not
actually true. If anything below conflicts with the files it points
to, **the files win** — update this section, don't trust stale memory.

## What this project is

A SKY130 RTL-to-GDSII study of quantized MAC (multiply-accumulate)
architectures for a tiny Edge-AI accelerator, run as an 8-week
master's-portfolio project.

Chain: **Python golden model → quantization → SystemVerilog RTL →
functional verification → OpenLane synthesis/PD → GDSII → a controlled
INT8/INT4 × sequential/parallel comparison.**

Research question (frozen, do not reword without updating
`docs/research_question.md`):

> How do reduced numerical precision and MAC parallelism affect
> energy-efficiency, silicon area, timing, latency, and inference
> accuracy of a small Edge-AI accelerator in SKY130?

Version 1 workload (the only accelerator to build — do not invent a
bigger one): **8 inputs → 4 output neurons → ReLU → 4 INT8 outputs**,
32 MAC ops/inference, each PE holds eight weights (one output column).

## Ground truth hierarchy — read this order, do not skip

1. **`docs/01_status_and_roadmap.md`** — the single source of truth for
   "what is actually done vs. not done." Read it first, every session.
   It is written to be blunt about gaps (e.g. inherited RTL that is
   "not yet audited or complete"). Update it whenever you finish work —
   an agent five sessions from now will trust it over anything else.
2. **`CONTRIBUTING.md`** and **`docs/02_eight_week_sprint_plan.md`** +
   **`docs/sprints/sprint_NN_*.md`** — the plan is executed one sprint
   at a time. Do not jump ahead (e.g. do not touch OpenLane while
   accelerator RTL is unaudited) even if it looks easy.
3. **`docs/baseline_reference.md`** — this project inherited a working
   third-party RTL/OpenLane baseline (SiliconNPU, MIT-licensed:
   `rtl/mac_core*.sv`, `rtl/silicon_npu.sv`, `flow/`, `openmac/`,
   `tests/`, some of `scripts/`). Its own two original reports
   **contradict each other** on timing closure and test counts — this
   file flags that explicitly. Never cite a baseline PPA number as fact
   without checking it against this file's "unverified / not yet
   reproduced" caveats.
4. Everything else in `docs/` (`architecture.md`, `quantization.md`,
   `verification.md`, `physical_design.md`, `research_methodology.md`)
   is topic-specific detail consistent with the above — treat conflicts
   between a topic doc and the status doc as a sign the topic doc is
   stale, and fix it rather than picking whichever is convenient.

## Current state (as of 2026-09-06 — verify against the status doc before relying on this)

| Phase | Goal | Status |
|---|---|---|
| 0 | Adder through OpenLane to GDSII (toolchain proof) | Done. `results/baseline/`, run tag `RUN_2026.08.30_06.36.00`. |
| 1 | Python golden model, symmetric INT8, Version 1 | Done for Version 1: `algorithm/reference_model.py` + `quantization.py` (GEMV→bias→ReLU→requantize-to-INT8), 8/8 known-answer tests (`algorithm/tests/`), 5 deterministic vectors (`verification/reference/vectors.{csv,hex}`), `docs/research_question.md`, `algorithm/baseline_results.csv`. |
| 2 | Smallest correct accelerator RTL + simulation | **Not done.** Inherited baseline RTL (`rtl/mac_core.sv`, `rtl/silicon_npu.sv`) exists but is *not* the Version 1 accelerator: no signed arithmetic anywhere, no bias/ReLU/requantize, and `silicon_npu.sv` sums into **one scalar**, not 4 independent per-neuron outputs. Must be audited/rewritten, not assumed correct. |
| 3 | Verified accelerator through OpenLane → GDSII | Not started for Version 1. (Baseline's own `mac_core`/`silicon_npu` variants were *reportedly* taken through OpenLane by the original SiliconNPU authors, unreproduced here — see `docs/baseline_reference.md`.) |
| 4 | INT8/INT4 × sequential/parallel four-point study | Not started. |
| 5 | Package: figures, report, CV/SOP language | Structure ready; no numbers to report yet. |

## Hard rules

- **Never report a PPA number (area/power/timing/energy/accuracy) that
  isn't actually measured and sitting in `results/*.csv` or a cited run
  tag.** If it's not measured, say "not yet measured" — do not
  interpolate, estimate-and-present-as-fact, or reuse a baseline claim
  that `docs/baseline_reference.md` has flagged as contradicted/unverified.
- **Do not run OpenLane on accelerator RTL that hasn't passed a
  functional audit and Python↔RTL bit-exact comparison.** Experiment 0
  (the adder) is the only proven toolchain run; it does not certify
  any accelerator RTL.
- **Symmetric signed INT8, zero-point 0, everywhere for Version 1.**
  Do not introduce asymmetric unsigned 0–255 activations — it breaks
  bit-exact Python/RTL comparison (`docs/quantization.md`).
- **Exactly four hardware variants, no more:** INT8-sequential,
  INT8-4way-parallel, INT4-sequential, INT4-4way-parallel. Not five
  variants, not a broader design-space sweep, not INT4 before Phase 4.
- **No large neural network, custom PDK, fabrication, or CPU.** Out of
  scope, see `docs/research_question.md`.
- **Keep work inside the existing folders** — `algorithm/`, `rtl/`,
  `verification/`, `designs/`, `flow/`, `results/`, `docs/`, `scripts/`,
  `openmac/`, `tests/`. Don't create a parallel tree (e.g. a new
  `python_reference/`) when a sprint doc names an existing folder.
- **Never commit** `OpenLane/` (local install, ~1.2 GB), PDK trees,
  `.venv/`, Docker caches, `*.vcd`, simulator binaries, or raw
  `runs/` directories. Curated summaries only in `results/`.
- **Update the status doc and this file when you finish real work.**
  A sprint isn't "done" until `docs/01_status_and_roadmap.md` and the
  relevant sprint doc's acceptance checklist reflect it.

## Known issues already on record (don't rediscover, don't ignore)

From `docs/01_status_and_roadmap.md` §"Technical issues already
identified":

1. `silicon_npu.sv` stores weights correctly (`weight_mem[DEPTH][ARRAY_SIZE]`,
   the right shape for weight-stationary) but **accumulates everything
   into one scalar `result`** instead of 4 independent per-neuron
   accumulators. Must be split before it matches Version 1.
2. Inherited RTL (`mac_core.sv`, `silicon_npu.sv`, `mac_core_pipelined.sv`)
   uses plain unsigned `logic` with **no signed multiply anywhere** —
   incompatible with the symmetric signed INT8 policy until audited/fixed.
3. `flow/openlane_config/*.tcl` hardcode an absolute Docker path
   (`/workspace/flow/src/...`); this repo runs OpenLane as a **local
   install**, so these configs will not run as-is.
4. `flow/openlane_config/npu_15ns.tcl` is misleadingly named — its
   actual `CLOCK_PERIOD` is `20.0`, not `15.0`. Check file contents,
   never filenames, before reusing a `.tcl` config.

## Conventions

- **RTL:** SystemVerilog-2012, `lowercase_snake_case`.
- **Python:** PEP 8, type hints where practical, dataclasses for config
  objects (see `openmac/`). No `pytest` dependency currently installed
  in this environment — tests are plain `assert`-based functions with
  descriptive names and a small `main()` runner (see
  `algorithm/tests/test_reference_model.py`, `tests/test_*.py`), not
  pytest fixtures/collection.
- **TCL:** OpenLane conventions, `::env()` for variables.
- Comments explain *why* (a non-obvious constraint, a known
  discrepancy), never *what* — identifiers and structure should already
  say what.

## Commands

```bash
# Python golden model (Phase 1)
cd algorithm
python3 reference_model.py              # smoke test on one hand-picked vector
python3 tests/test_reference_model.py   # 8 known-answer checks
python3 generate_vectors.py             # regenerate verification/reference/vectors.{csv,hex}

# Inherited baseline RTL simulation (Icarus Verilog, not confirmed installed everywhere)
cd verification && make sim                     # WIDTH=8 ARRAY_SIZE=4 default
cd verification && make sim WIDTH=16 ARRAY_SIZE=8

# Inherited Python ASIC-flow tooling unit tests (openmac/)
python3 run_tests.py

# Inherited OpenLane orchestration CLI (paths unchanged by the SiliconNPU merge)
python3 openmac.py sim --width 8 --array-size 4
python3 openmac.py flow --width 8 --array-size 4
python3 openmac.py parse
python3 openmac.py analyze
python3 openmac.py dash
```

## Repository map

```text
algorithm/      Python golden model, quantization, vector generation, tests (Phase 1 — done for V1)
rtl/            SystemVerilog: inherited baseline (mac_core*.sv, silicon_npu.sv) — unaudited for V1
verification/   Testbenches + verification/reference/ (frozen Python vectors)
designs/        OpenLane configs per variant (adder done; accelerator variants are placeholders)
flow/           Inherited SiliconNPU OpenLane orchestration (paths need fixing, see Known issues)
results/        Curated metrics + final GDS only, never full OpenLane run trees
docs/           Architecture/verification/PD/research plan — see Ground truth hierarchy above
legacy/         Retired pre-baseline RTL, kept for history, not extended
openmac/        Inherited Python ASIC-flow analysis/report-parsing library
scripts/        Simulation and OpenLane helper scripts (this project's + inherited)
tests/          Unit tests for openmac/ (not algorithm/ — that has its own tests/)
```

## Before you state anything is "done" or cite a number

1. Read the file, don't recall it — a memory of a function/number
   existing is a claim about the past, not the present.
2. If it's a PPA/accuracy number, confirm it's in a `results/*.csv` or
   named run tag, not prose from a doc (docs can and do go stale, and
   the inherited baseline docs are *known* to contradict each other).
3. If it's RTL functional status, check `docs/01_status_and_roadmap.md`
   §"Technical issues already identified" first — several inherited
   files look complete but are not audited for this project's signed
   INT8 requirements.
4. When in doubt, say what's unverified rather than presenting a guess
   as settled — this file and the status doc both exist specifically
   so agents don't have to guess.
