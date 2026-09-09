# Status and roadmap

## Where the project actually stands

### Active implementation boundary

The active project implementation is the Version 1 Python model and four-PE accelerator rooted at `rtl/accelerator_top.sv`. The inherited SiliconNPU/MAC files remain only as attributed reference material and are excluded from the active simulation and lint flow. They are not part of the project's original implementation or its Version 1 evidence.

The intended research story is the full Python-to-GDS chain plus a four-point architecture study. The technical manual organizes that as nine modules. **Experiment 0 is already done**, so this project is not at Module 1.

Verified checkpoint:

```text
8-bit adder → OpenLane → physical implementation → GDSII
Run tag: RUN_2026.08.30_06.36.00
KLayout GDS: results/baseline/adder_8bit.klayout.gds
```

The adder exists to prove the toolchain before the accelerator. That proof is complete.

### Experiment 0 headline numbers

From `results/baseline/metrics.csv`:

| Metric | Value |
|---|---|
| Flow status | completed |
| Runtime | ~57 s |
| Die area | 0.002578 mm² |
| Synth cell count | 38 |
| Magic DRC | 0 |
| LVS errors | 0 |
| TritonRoute violations | 0 |
| Typical internal / switching / leakage (µW as dumped) | 1.22e-05 / 2e-05 / 3.35e-10 |
| Critical path | 1.67 ns |
| `CLOCK_PERIOD` in config | 10 ns |
| Strategy | `AREA 0`, `FP_CORE_UTIL` 30, `PL_TARGET_DENSITY` 0.55 |

**RTL actually implemented:** combinational `assign sum = a + b;` — not the clocked `cin`/`cout` listing in the manual. Document the silicon we built.

## Phases (preferred over following nine modules blindly)

| Phase | Goal | Status |
|---|---|---|
| 0 | Freeze and document the adder baseline | In progress (this docs set) |
| 1 | Correct Python reference model (symmetric INT8) | Complete for Version 1 (2026-09-06): `algorithm/` implements GEMV + bias + ReLU + requantize-to-INT8, 8/8 hand-computed known-answer tests pass (`algorithm/tests/test_reference_model.py`), 5 deterministic vectors generated to `verification/reference/vectors.{csv,hex}`. Bit-exact comparison against RTL is still Phase 2/3, not done. See [research_question.md](research_question.md). |
| 2 | Smallest correct accelerator: SV + simulation | **Complete for Version 1 (2026-09-07):** `rtl/accelerator_top.sv` + `rtl/processing_element.sv` + `rtl/controller.sv` + `rtl/requantize.sv` implement the 4-PE, signed INT8, bias+ReLU+requantize accelerator. The checked-in accelerator TB covers all 5 frozen vectors (20 accumulator/output checks), and `scripts/check_reference_vectors.py` confirms the CSV against `algorithm/reference_model.forward()`. Baseline RTL (`mac_core*.sv`, `silicon_npu.sv`) is audited and signed-fixed. HDL execution/lint still requires Icarus Verilog/Verilator on the host. See [architecture_spec.md](architecture_spec.md). |
| 3 | Verified accelerator through OpenLane → GDSII | **Complete for the INT8 parallel baseline (2026-09-08):** OpenLane `project_run_02` completed through GDS, LVS, DRC, ARC, and ERC for `accelerator_top`. Curated metrics, signoff notes, and the final GDS are in `results/int8_parallel/`. DRC, LVS, XOR, route, setup, and hold checks are clean; 23 pin and 19 net antenna violations plus max-fanout warnings remain documented for follow-up. |
| 4 | INT8/INT4 × sequential/parallel experiments | **Parallel axis complete (Sprint 7, 2026-09-08):** INT8 -> INT4 on the same 4-way-parallel schedule, one axis (see [optimization_plan.md](optimization_plan.md)). `int4_parallel` closed through OpenLane to GDSII (`project_run_01`) — DRC/LVS/XOR/route/setup-hold clean. Getting there required a wrapper module (`designs/accelerator_int4_parallel/accelerator_top_int4.sv`) after OpenLane's `SYNTH_PARAMETERS`/`chparam` mechanism turned out to leave `y_out`/`busy`/`done` undriven on this toolchain — see [ppa_comparison.md](ppa_comparison.md). `results/comparison.csv` now has measured area (-29.9%), power/energy (-62.8%), and synthetic accuracy (-9.4 points) for `int8_parallel` vs. `int4_parallel`; the sequential-schedule axis (`int8_sequential`, `int4_sequential`) remains deferred/out of scope. |
| 5 | Package: GitHub, figures, report, CV/SOP | Structure ready; no remote yet |

## Do not do next

- Do not put a supplied `accelerator_top` through OpenLane until it exists here and passes a functional audit.
- Do not start INT4 or the four-variant matrix.
- Do not optimize power yet.
- Do not write the research paper yet.

## Eight-week execution plan

The preferred **calendar** for finishing the chain (algorithm → RTL → verification → OpenLane → GDSII → one or two optimizations → report) is:

**[02_eight_week_sprint_plan.md](02_eight_week_sprint_plan.md)** and **[sprints/](sprints/)**.

Phases in the table above still describe *what* is true of the repo. Sprints describe *when* a new person should do the work (~20–25 hours/week, eight weeks). Do not skip Sprint 3 (RTL vs Python) because Experiment 0 already produced adder GDSII.

## Immediate order of work

1. Preserve the successful adder project (done).
2. Put the project under Git and create a clean GitHub remote (curated files only).
3. Commit the verified adder baseline + these docs.
4. Audit any accelerator RTL before synthesis (weight-stationary / single `weight_reg` vs 32 weights). (done 2026-09-07, see [architecture_spec.md](architecture_spec.md) section 6)
5. Build the Python reference model. (done 2026-09-06)
6. Generate deterministic INT8 test vectors. (done 2026-09-06)
7. Design the correct 8×4 architecture (each PE holds eight weights). (done 2026-09-07: `rtl/accelerator_top.sv`)
8. Verify MAC → PE → top separately. (done 2026-09-07 at the smoke-TB level: `verification/tb_processing_element.sv`, `verification/tb_accelerator.sv` — full golden-vector sweep is Sprint 3)
9. Compare Python and RTL automatically. (the five frozen vectors are checked against Python by `scripts/check_reference_vectors.py`; the accelerator TB checks all five rows in RTL once Icarus is installed)
10. Only after functional correctness, run OpenLane. (done 2026-09-08 for INT8 parallel)
11. Extract area / power / timing. (done 2026-09-08 for INT8 parallel; see `results/int8_parallel/metrics.csv`)
12. Build sequential and INT4 variants.
13. Run the controlled research experiment.
14. Produce paper-quality results.

## Technical issues already identified (before silicon)

1. **PE weight storage — resolved 2026-09-07.** Four PEs with one `weight_reg` each cannot hold 32 weights as a weight-stationary array. A PE for output *j* needs `w0j … w7j`. `rtl/processing_element.sv` gives each PE its own 8-deep `weight` register array (one per input position), verified directly in `verification/tb_processing_element.sv` ("Test 1: Eight independent weight registers"). The inherited `rtl/silicon_npu.sv`'s single-scalar-accumulator limitation is intentionally *not* restructured in place — it stays a standalone OpenLane PPA baseline artifact; the 4-independent-neuron requirement is met by the separate `rtl/accelerator_top.sv` module tree instead. See [architecture_spec.md](architecture_spec.md) section 6.
2. **Quantization mix — resolved 2026-09-07 for the RTL side.** The manual mixes signed INT8 RTL with asymmetric unsigned 0–255 activations. Version 1 uses **symmetric signed INT8 everywhere**. See [quantization.md](quantization.md). The inherited baseline RTL (`mac_core.sv`, `mac_core_pipelined.sv`, `silicon_npu.sv`) was plain unsigned `logic` with no `signed` multiply anywhere — all three are now audited/signed-fixed and lint-clean, verified against updated testbenches with signed-boundary and cross-sign test cases (not just reviewed). `rtl/processing_element.sv` (the new accelerator's own MAC) was written signed from the start. See [architecture_spec.md](architecture_spec.md) section 6.

## Empty / unused directories (historical)

`python/` and `physical_design/` were created early and are empty. Canonical locations going forward: `algorithm/` and `docs/physical_design.md` plus `designs/` + `results/`.
