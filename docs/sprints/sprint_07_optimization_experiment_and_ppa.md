# Sprint 7: Optimization experiment + PPA comparison

**Week 7** · **~20–25 hours** · **Phase 4 measure** · Previous: [Sprint 6](sprint_06_low_power_optimization.md) · Next: [Sprint 8](sprint_08_research_package.md)

---

## Goal

Repeat the ASIC flow for the optimized architecture and fill an honest comparison table.

Now repeat the ASIC flow for your optimized architecture.

You need:

```text
BASELINE
    ↓
RTL
    ↓
Synthesis
    ↓
GDSII
    ↓
PPA

OPTIMIZED
    ↓
RTL
    ↓
Synthesis
    ↓
GDSII
    ↓
PPA
```

If you have more than two variants (INT8/INT4 × sequential/parallel), each row is the same chain. Same OpenLane major version, same PDK, change one architectural variable at a time.

---

## Create the main comparison

| Metric    | Baseline | Optimized | Improvement |
| --------- | -------: | --------: | ----------: |
| Area      |        X |         X |           % |
| Power     |        X |         X |           % |
| Delay     |        X |         X |           % |
| Frequency |        X |         X |           % |
| Energy/op |        X |         X |           % |
| Accuracy  |        X |         X |           % |

This repo’s headline energy metric is **energy per inference**, which needs power **and** latency (cycles × period):

\[
E = P \times t
\]

Also fill `results/comparison.csv` with die area, slack, leakage, dynamic, cycles/inference, throughput, accuracy vs FP32.

Calculate:

\[
\mathrm{Area\ Improvement} =
\frac{A_{\mathrm{base}}-A_{\mathrm{opt}}}{A_{\mathrm{base}}}\times 100
\]

\[
\mathrm{Power\ Improvement} =
\frac{P_{\mathrm{base}}-P_{\mathrm{opt}}}{P_{\mathrm{base}}}\times 100
\]

Use the same formula family for energy and delay. **Sign convention:** positive improvement means the optimized design is smaller / lower power / lower energy. If delay got worse, the improvement is **negative**. Report that.

---

## Important

Do **not** manufacture impressive percentages.

If optimization makes performance worse but saves area, report that honestly.

That trade-off is itself a research result.

Sequential “low power” vs parallel “high watts” is a classic trap: **energy/inference** may reverse the ranking.

INT4 may shrink the multiplier and switching; it may also degrade accuracy. Measure both.

**We measure the intersection. We do not declare a winner in advance.**

---

## Fairness checklist

- [ ] Same PDK (`sky130A` / `sky130_fd_sc_hd`)
- [ ] Same OpenLane major version
- [ ] Same (or intentionally changed) `CLOCK_PERIOD` — document it
- [ ] Same vector set for accuracy
- [ ] Power from the same class of report (typical vs worst; internal/switching/leakage)
- [ ] Area from the same definition (die vs core vs cell area)
- [ ] Run tags recorded for every variant

---

## Tasks a contributor can pick up

1. OpenLane runs for each optimized variant.
2. Script extraction (`scripts/collect_results.py` if present) into CSV.
3. Accuracy rerun in Python for INT4 / approximate modes.
4. Compute improvement percentages **from CSV**, not by hand-waving.
5. Short notes: why a number moved (cell count, wirelength, extra cycles).

---

## Deliverables

- `results/comparison.csv` filled
- Per-variant curated `results/` (metrics, GDS if size allows)
- Signoff status for optimized GDS (DRC/LVS/STA)
- Draft discussion bullets for Sprint 8 (area, power, timing, accuracy)

---

## Acceptance criteria

- [x] Baseline and optimized both have PPA from the same methodology — same OpenLane v1.0.2 install, same PDK/library, same `CLOCK_PERIOD`; see [docs/ppa_comparison.md](../ppa_comparison.md)
- [x] Table includes area, power, delay/frequency, energy, accuracy — [docs/ppa_comparison.md](../ppa_comparison.md)'s main comparison table
- [x] Improvement formulas applied; negative results kept — accuracy is reported as a **-9.41 point** degradation, not dropped or reframed as a win
- [x] No variant claimed without a run tag — `int8_parallel/project_run_02`, `int4_parallel/project_run_01`, both recorded in `results/comparison.csv`

---

## What not to do this week

- Do not drop a slow design from the table.
- Do not mix adder Experiment 0 area with accelerator area as if they were the same experiment.
- Do not start the 15-page report until the table is real (outline is OK).
- Do not retune only the optimized design’s util/density to “win” unless you disclose it and retune baseline the same way.

---

## Gate to Sprint 8

The comparison table is populated from measurements. Sprint 8 explains **why** and packages the portfolio.
