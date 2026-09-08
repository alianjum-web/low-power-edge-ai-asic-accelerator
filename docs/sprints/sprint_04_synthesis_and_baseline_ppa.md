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

- [x] OpenLane config exists and names the verified RTL
- [x] Synthesis completes; cell count and area recorded
- [x] Clock is real (CTS will matter in Sprint 5)
- [x] Baseline PPA table started (see `results/int8_parallel/metrics.csv`)
- [x] Run tag and config knobs written down (`project_run_02`)
- [x] No claim of “optimized” yet — this is baseline only

## Completed baseline evidence

The INT8 4-way baseline was run with OpenLane `v1.0.2` using run tag
`project_run_02`. The active configuration is
[`designs/accelerator_int8_parallel/config.json`](../../designs/accelerator_int8_parallel/config.json),
and it selects the verified `accelerator_top` RTL hierarchy with a real
`clk` port and a 20 ns clock.

Curated outputs are kept in
[`results/int8_parallel/`](../../results/int8_parallel/):

- [`metrics.csv`](../../results/int8_parallel/metrics.csv): area, cell count,
	timing, power, latency, throughput, and energy per inference.
- [`signoff.md`](../../results/int8_parallel/signoff.md): run settings and
	signoff summary.
- `accelerator_top_project_run_02.gds`: final GDS artifact.

Recorded baseline values:

| Metric | Value |
|---|---:|
| Die area | 0.246796414625 mm² |
| Total cells | 28,761 |
| Clock target | 20 ns / 50 MHz |
| Critical path | 7.98 ns |
| Typical internal power | 0.0257 µW |
| Typical switching power | 0.0313 µW |
| Typical leakage power | 0.000000053 µW |
| Latency | 10 cycles/inference |
| Energy per inference | 0.0114000106 nJ |

DRC, LVS, XOR, routing, setup, and hold checks are clean. ARC reported 23
pin-antenna and 19 net-antenna violations, and typical-corner STA reported
max-fanout warnings; these are recorded follow-up items, not silently treated
as clean signoff. IR-drop values may be inaccurate because `VSRC_LOC_FILES`
was not defined.

## How to verify Sprint 4

From the repository root:

```bash
python3 algorithm/tests/test_reference_model.py
python3 scripts/check_reference_vectors.py
python3 -m json.tool designs/accelerator_int8_parallel/config.json >/dev/null
test -s results/int8_parallel/metrics.csv
test -s results/int8_parallel/signoff.md
test -s results/int8_parallel/accelerator_top_project_run_02.gds
```

The first two commands verify the golden model and frozen vectors that gate
the synthesis run. The remaining commands verify that the Sprint 4 config and
curated physical-design evidence exist. To rerun the HDL regression and lint,
use `scripts/run_sim.sh`; it requires Icarus Verilog, and adds Verilator lint
when Verilator is installed. A fresh OpenLane rerun requires the local OpenLane
and SKY130 environment and should be compared with the curated run tag above.

Sprint 4 is complete for the INT8 parallel baseline when all commands above
pass and `signoff.md` still matches the reported run artifacts. Sprint 4 does
not claim the four-variant INT8/INT4 study, optimization, or final warning-free
manufacturing signoff.

---

## What not to do this week

- Do not change RTL “to make area pretty” without a new Sprint 3 regression.
- Do not start five OpenLane strategies at once.
- Do not commit the full `OpenLane/runs/` directory.
- Do not compare INT4 yet.

---

## Gate to Sprint 5

Baseline synthesis (and preferably a first PD attempt) exists. Sprint 5 is closing **accelerator** GDSII, DRC, LVS, STA — not re-learning the adder.
