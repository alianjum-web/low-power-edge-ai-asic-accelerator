# Status and roadmap

## Where the project actually stands

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
| 1 | Correct Python reference model (symmetric INT8) | Not started (`algorithm/` stub) |
| 2 | Smallest correct accelerator: SV + simulation | Not started (no PE/MAC RTL yet) |
| 3 | Verified accelerator through OpenLane → GDSII | Not started |
| 4 | INT8/INT4 × sequential/parallel experiments | Not started |
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
4. Audit any accelerator RTL before synthesis (weight-stationary / single `weight_reg` vs 32 weights).
5. Build the Python reference model.
6. Generate deterministic INT8 test vectors.
7. Design the correct 8×4 architecture (each PE holds eight weights).
8. Verify MAC → PE → top separately.
9. Compare Python and RTL automatically.
10. Only after functional correctness, run OpenLane.
11. Extract area / power / timing.
12. Build sequential and INT4 variants.
13. Run the controlled research experiment.
14. Produce paper-quality results.

## Technical issues already identified (before silicon)

1. **PE weight storage.** Four PEs with one `weight_reg` each cannot hold 32 weights as a weight-stationary array. A PE for output *j* needs `w0j … w7j`. Audit `weight_load_en` before trusting any claimed sim pass.
2. **Quantization mix.** The manual mixes signed INT8 RTL with asymmetric unsigned 0–255 activations. Version 1 uses **symmetric signed INT8 everywhere**. See [quantization.md](quantization.md).

## Empty / unused directories (historical)

`python/` and `physical_design/` were created early and are empty. Canonical locations going forward: `algorithm/` and `docs/physical_design.md` plus `designs/` + `results/`.
