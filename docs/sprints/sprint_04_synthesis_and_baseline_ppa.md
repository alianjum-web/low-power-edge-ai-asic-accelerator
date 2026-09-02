# Sprint 4: Synthesis + baseline PPA

**Week 4** · **~20–25 hours** · **Phase 3 start** · Previous: [Sprint 3](sprint_03_rtl_verification.md) · Next: [Sprint 5](sprint_05_rtl_to_gdsii.md)

---

## Goal

Turn the verified accelerator into an ASIC project: Yosys synthesis, OpenLane configuration, a **baseline** physical run, and a first PPA table.

Now your project becomes an ASIC project.

Use:

- Yosys
- OpenLane
- SKY130

OpenLane/Yosys perform synthesis and technology mapping, followed by timing analysis and physical-design stages.

---

## Why this sprint exists

You already closed Experiment 0 (adder). This week you **reuse that workflow** on the real DUT, with a clock, CTS, and honest baseline numbers. You are not learning OpenLane from zero.

Do **not** start INT4 or a second architecture until this baseline exists (see [research_methodology.md](../research_methodology.md)).

---

## 1. Prepare OpenLane configuration

Define:

- design name
- Verilog files
- clock
- clock period
- PDK
- standard-cell library
- utilization
- die/core parameters

**This repo:** add a design under `designs/`, for example `designs/accelerator_int8_parallel/` (folder already reserved). Point `VERILOG_FILES` at `rtl/` (shared), not a second copy, unless you have a reason.

Experiment 0 reference: `designs/adder_8bit/config.json`.

Accelerator **starting knobs** from [physical_design.md](../physical_design.md) (tune after RTL exists):

| Knob | Conservative first try |
|---|---|
| PDK / lib | `sky130A` / `sky130_fd_sc_hd` |
| `CLOCK_PORT` | real clock name from the spec (not empty; adder was combinational) |
| `CLOCK_PERIOD` | 20 ns (50 MHz) for a first energy-oriented run |
| `FP_CORE_UTIL` | 35 |
| `PL_TARGET_DENSITY` | 0.50 |
| `SYNTH_STRATEGY` | `AREA 0` |

Wide 32-bit accumulator buses route poorly at high density. If placement or routing fails, **lower density first**; do not raise `OUT_DIM`.

OpenLane is a **local install**, gitignored. Do not vendor it. Helpers: `scripts/run_openlane.sh`.

---

## 2. Run synthesis

Generate:

```text
RTL
 ↓
gate-level netlist
```

You may run Yosys standalone (`synthesis/synth.ys` exists for the adder) **and/or** let OpenLane invoke Yosys. For the accelerator, OpenLane is the source of truth for PPA. Keep curated netlists small if you commit them (`results/` or `synthesis/` with a clear name).

---

## 3. Examine synthesis reports

Record:

- cell count
- area
- timing
- sequential elements
- combinational logic

Copy **summaries** into `results/baseline/` (CSV + short notes). Do not git-add entire `runs/` trees.

---

## 4. Run baseline physical design

Run:

```text
Floorplan
↓
Placement
↓
CTS
↓
Routing
↓
Signoff
```

If the full GDSII chain does not finish in Week 4, still record synthesis + as far as you got, and finish the chain in Sprint 5. Prefer finishing a conservative config over a heroic frequency that fails routing.

---

## 5. Record baseline PPA

Create:

| Metric    | Baseline |
| --------- | -------: |
| Area      |        X |
| Power     |        X |
| Delay     |        X |
| Frequency |        X |
| Energy    |        X |

Also record what this repo cares about for later papers:

- latency (cycles/inference)
- energy/inference (headline)
- cell count, slack, leakage vs dynamic

Use `results/baseline/metrics.csv` style (adder already has an example) and `results/comparison.csv` as the long-term table.

---

## Deliverable

```text
baseline_ppa.csv
baseline_reports/
baseline_netlist/
```

Map to:

```text
results/baseline/          (metrics, curated reports, GDS when ready)
designs/<variant>/config.json
synthesis/                 (optional Yosys artifacts for the accelerator)
docs/physical_design.md    (update knobs that actually ran)
```

---

## Tasks a contributor can pick up

1. Write `designs/<accelerator>/config.json` with correct `CLOCK_PORT` and file list.
2. Dry-run synthesis; fix SV constructs Yosys rejects.
3. First OpenLane run; triage util/density vs congestion.
4. Extract area / power / timing into CSV.
5. Document the **run tag** (like `RUN_2026.08.30_06.36.00` for the adder).

---

## Acceptance criteria

- [ ] OpenLane config exists and names the verified RTL
- [ ] Synthesis completes; cell count and area recorded
- [ ] Clock is real (CTS will matter in Sprint 5)
- [ ] Baseline PPA table started (even if GDS is Sprint 5)
- [ ] Run tag and config knobs written down
- [ ] No claim of “optimized” yet — this is baseline only

---

## What not to do this week

- Do not change RTL “to make area pretty” without a new Sprint 3 regression.
- Do not start five OpenLane strategies at once.
- Do not commit the full `OpenLane/runs/` directory.
- Do not compare INT4 yet.

---

## Gate to Sprint 5

Baseline synthesis (and preferably a first PD attempt) exists. Sprint 5 is closing **accelerator** GDSII, DRC, LVS, STA — not re-learning the adder.
