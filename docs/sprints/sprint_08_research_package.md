# Sprint 8: Research validation + final research package

**Week 8** · **~20–25 hours** · **Phase 5** · Previous: [Sprint 7](sprint_07_optimization_experiment_and_ppa.md) · Next: applications / optional paper draft

---

## Goal

Turn the engineering project into a **master’s-level research portfolio project**: analysis, figures, table, technical report, and a clean GitHub layout.

This sprint does **not** require a formal university thesis. It **does** require a research-paper-style report of roughly **15–25 pages**.

**Project ≠ Thesis**, but **Project + rigorous research report = much stronger master’s portfolio.**

You can later convert the report into a research proposal, writing sample, GitHub documentation, or a conference-paper draft.

---

## 1. Analyze results

Explain:

- Why did area change?
- Why did power change?
- Why did timing change?
- What happened to accuracy?
- What is the hardware trade-off?
- Why does the optimization work physically/architecturally?

Tie answers to cells, wirelength, switching, extra cycles, quantization error — not slogans.

---

## 2. Produce figures

Minimum:

1. System architecture
2. MAC architecture
3. RTL simulation waveform
4. Baseline floorplan
5. Baseline placement
6. Baseline routing
7. Final GDSII
8. PPA comparison
9. Accuracy comparison
10. Optimization trade-off graph

Store under `docs/figures/` (and copy into the report). Experiment 0 adder plots are **toolchain evidence**, not a substitute for accelerator figures.

---

## 3. Create final table

Your main research result should look something like:

| Design   | Area | Power | Delay | Energy | Accuracy |
| -------- | ---: | ----: | -----: | -----: | -------: |
| Baseline |    X |     X |      X |      X |        X |
| Proposed |    X |     X |      X |      X |        X |

Mirror this in the root `README.md` (replace TBD rows). Until numbers exist, do not use CV language as a claim ([research_methodology.md](../research_methodology.md)).

---

## 4. Write the technical report

Recommended structure:

```text
1. Abstract
2. Introduction
3. Problem Statement
4. Related Work
5. Proposed Architecture
6. Hardware Design
7. RTL Implementation
8. Verification
9. ASIC Implementation
10. Optimization Method
11. Experimental Setup
12. Results
13. Discussion
14. Limitations
15. Conclusion
16. Future Work
17. References
```

Put the source in `docs/report/` (Markdown or LaTeX). Target 15–25 pages including figures.

Limitations must mention: tiny network, OpenLane/SKY130 academic flow, no silicon, possible STA/power-model uncertainty, dataset limits.

---

## 5. Prepare GitHub

Original plan’s example tree:

```text
Physics-Informed-Energy-Efficient-ASIC/
│
├── rtl/
├── testbench/
├── python/
├── openlane/
├── simulation/
├── synthesis/
├── reports/
├── gds/
├── figures/
├── results/
├── docs/
├── README.md
└── LICENSE
```

**This repository already uses a close equivalent.** Do not rename everything in Week 8. Map instead:

| Plan folder | This repo |
|---|---|
| `rtl/` | `rtl/` |
| `testbench/` | `verification/` (+ legacy `testbench/` for adder) |
| `python/` | `algorithm/` |
| `openlane/` | local OpenLane install + `designs/` configs (**do not vendor OpenLane source**) |
| `simulation/` | `scripts/run_sim.sh`, local VCDs gitignored |
| `synthesis/` | `synthesis/` |
| `reports/` | `docs/` + curated `results/` |
| `gds/` | `results/` (final GDS) |
| `figures/` | `docs/figures/` |
| `results/` | `results/` |
| `docs/` | `docs/` including this sprint plan |

README homepage: one sentence, Python→GDS chain, results table, then links. Reviewers skim the first ten seconds. See [github_and_lab_notebook.md](../github_and_lab_notebook.md).

Do **not** spend weeks decorating the README. Make it accurate.

Suggested milestone commits (historical list; catch up rather than rewriting history):

1. Baseline 8-bit adder RTL  
2. Adder functional verification  
3. Adder OpenLane config + curated metrics/GDS  
4. Documentation set  
5. Initial Python INT8 reference model  
6. Corrected accelerator RTL  
7. Bit-exact RTL verification  
8. Accelerator OpenLane implementation  
9. INT8 parallel results  
10. INT4 implementation (if in scope)  
11. Architecture comparison  
12. Final research results  

---

## The final package you should have

```text
1. Working Python reference model
2. Working Verilog/SystemVerilog RTL
3. Verified testbench
4. Simulation waveforms
5. Synthesized netlist
6. Baseline PPA
7. Optimized RTL
8. Optimized PPA
9. RTL-to-GDSII flow
10. Final GDSII
11. DRC/LVS/signoff evidence
12. Baseline vs optimized comparison
13. Technical report
14. GitHub repository
15. Architecture + results figures
```

**This is the minimum serious version for master’s applications.**

---

## Tasks a contributor can pick up

1. Figure pack (10 minimum).
2. Report sections 1–8 vs 9–17 (can split authorship).
3. README results table + license check.
4. `CONTRIBUTING.md` / sprint links stay current.
5. SOP/CV paragraph **only after** numbers are real.

---

## Acceptance criteria

- [ ] All 15 package items exist or are explicitly listed as N/A with reason
- [ ] 10 figures exist
- [ ] Report 15–25 pages with limitations and references
- [ ] README table matches `results/comparison.csv`
- [ ] Repo is cloneable without OpenLane source inside it
- [ ] New contributor can start at [02_eight_week_sprint_plan.md](../02_eight_week_sprint_plan.md)

---

## What not to do this week

- Do not learn every OpenLane variable.
- Do not add a RISC-V core “for the README.”
- Do not hide negative PPA.
- Do not claim fabrication or tapeout.

---

## After Week 8

Optional: conference-style paper draft, research proposal, or a second optimization — only if the package above is done.
