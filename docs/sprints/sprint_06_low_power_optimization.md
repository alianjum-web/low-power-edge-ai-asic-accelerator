# Sprint 6: Low-power optimization

**Week 6** · **~20–25 hours** · **Phase 4 (design, not yet the full measure loop)** · Previous: [Sprint 5](sprint_05_rtl_to_gdsii.md) · Next: [Sprint 7](sprint_07_optimization_experiment_and_ppa.md)

---

## Goal

Choose **1–2** hardware optimizations, implement the optimized RTL (and Python if accuracy changes), and document the experiment **before** you chase percentages.

**This is the actual research contribution.**

Do not simply say:

> "I built an ASIC."

Thousands of people can reproduce a flow tutorial.

Instead:

> "I investigated a hardware optimization technique for reducing energy consumption in a resource-constrained Edge-AI accelerator."

---

## Why this sprint exists

Sprints 1–5 prove you can build and close a small accelerator. Master’s reviewers care that you **changed one thing**, measured PPA and accuracy, and explained the physics/architecture.

This week is **choose + implement + freeze the comparison protocol**. Sprint 7 repeats the ASIC flow and fills the table.

---

## Choose 1–2 optimization techniques

Do not attempt ten.

### Option A: Bit-width optimization

Compare:

```text
Baseline: 16/32-bit datapath
Optimized: 8-bit datapath
```

In **this** repo, the natural bit-width study is already framed as **INT8 vs INT4** (not a random 32-bit ALU). Measure:

- area
- power
- timing
- accuracy

Keep `mac_core` shared/parameterized when bit-width is the only change ([research_methodology.md](../research_methodology.md)).

### Option B: MAC architecture optimization

Compare:

```text
Baseline → conventional MAC
Optimized → resource-sharing / optimized datapath
```

In this repo that is **sequential vs 4-way parallel** (same precision). Sequential may look low-power in watts and still lose on **energy/inference** if it takes many more cycles. Measure energy/inference, not only watts.

### Option C: Clock gating

Reduce unnecessary switching during idle periods.

Use this only if you can show idle vs compute in the FSM and a fair power methodology (same vectors, same tool, same PDK).

### Option D: Approximate computation

More research-oriented, but riskier (accuracy story must be honest and reproducible).

---

## Recommendation for this timeline

**Quantization + datapath optimization**

because it connects naturally to Edge-AI.

That matches the four-point matrix **if time allows**:

| Design | Precision | MAC architecture |
|---|---|---|
| Baseline | INT8 | Sequential **or** the Version 1 parallel design you already closed — **freeze which one is “baseline”** |
| A | INT8 | 4-way parallel |
| B | INT4 | Sequential |
| C | INT4 | 4-way parallel |

If 8 weeks are tight after GDS pain, **one axis is enough**: e.g. INT8 sequential vs INT8 parallel, **or** INT8 vs INT4 on the same MAC schedule. Do not implement five techniques.

Write the choice in `docs/optimization_plan.md` (create this week) **before** looking at Sprint 7 percentages.

---

## Tasks a contributor can pick up

1. Write `docs/optimization_plan.md`: technique, hypothesis, what stays constant, what changes.
2. Parameterize `mac_core` / top for INT4 or sequential schedule (it already has `WIDTH`/`ARRAY_SIZE` parameters — reuse them; do not fork a second MAC file per precision).
3. Update Python golden model for INT4 (same vectors policy).
4. Re-run **Sprint 3-style** tests on optimized RTL (bit-exact to the new Python).
5. Do **not** declare PPA winners until Sprint 7 GDS/synth numbers exist.

---

## Deliverables

- `docs/optimization_plan.md`
- Optimized RTL under `rtl/` and/or `designs/accelerator_int4_*` / sequential configs
- Updated Python + vectors if precision changes
- Passing regression for the optimized design

Folders already reserved:

```text
designs/accelerator_int8_sequential/
designs/accelerator_int8_parallel/
designs/accelerator_int4_sequential/
designs/accelerator_int4_parallel/
```

---

## Acceptance criteria

- [ ] One or two techniques chosen and justified
- [ ] Baseline vs optimized **protocols** are comparable (same PDK, OpenLane major version, same golden-model method unless the experiment *is* quantization)
- [ ] Optimized RTL matches its Python model
- [ ] No fabricated percentage claims yet

---

## What not to do this week

- Do not implement five optimizations.
- Do not manufacture impressive percentages.
- Do not change PDK or clock period between variants unless that *is* the experiment (usually it is not).
- Do not skip verification on the optimized RTL.

---

## Gate to Sprint 7

Optimized design is specified, implemented, and verified. Sprint 7 is the **controlled ASIC rerun and table**.
