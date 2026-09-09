# Sprint 5: Complete RTL → GDSII

**Week 5** · **~20–25 hours** · **Phase 3 complete** · Previous: [Sprint 4](sprint_04_synthesis_and_baseline_ppa.md) · Next: [Sprint 6](sprint_06_low_power_optimization.md)

---

## Goal

Finish the physical-design chain for the **verified accelerator** through GDSII and signoff evidence.

This is where existing Experiment 0 experience is valuable. You already took an 8-bit adder through OpenLane and obtained GDSII. This sprint is **not** learning the flow from zero. It is applying that workflow to the real accelerator.

---

## Physical-design chain

```text
RTL
 ↓
Synthesis
 ↓
Floorplan
 ↓
Power Distribution Network
 ↓
Placement
 ↓
Clock Tree Synthesis
 ↓
Routing
 ↓
Parasitic extraction
 ↓
STA
 ↓
DRC
 ↓
LVS
 ↓
Antenna checks
 ↓
GDSII
```

These are standard stages in the OpenLane/OpenROAD ecosystem.

CTS **was not meaningful** for the combinational adder (`CLOCK_PORT` empty). The accelerator **must** have a clock and a real CTS report.

---

## Check (stage by stage)

### Floorplan

- core area
- utilization
- IO placement
- PDN

### Placement

- congestion
- cell density
- timing

### CTS

- clock insertion delay
- skew
- timing

### Routing

- routing completion
- congestion
- antenna violations

### Signoff

- DRC
- LVS
- STA
- antenna

If a stage fails, use [physical_design.md](../physical_design.md) (typical beginner failures). Lower utilization/density before widening the design.

---

## Final physical outputs

You need:

```text
accelerator.gds
accelerator.def
accelerator.lef
netlist.v
timing reports
power reports
area reports
DRC report
LVS report
```

Curate into `results/` (final GDS per variant is a reasonable git artifact if small enough; adder GDS was ~192 KB). Intermediate `runs/` stay local.

Name files so a new person can find **which variant and which run tag** they came from.

---

## Tasks a contributor can pick up

1. Drive OpenLane to completion; record the run tag.
2. Fill a signoff checklist (DRC 0? LVS 0? route violations?).
3. Copy GDS/DEF/LEF/netlist summaries to `results/`.
4. Screenshot floorplan, placement, routing, GDS for Sprint 8 figures (baseline set).
5. Update `docs/experiment` notes for the **accelerator** (do not overwrite Experiment 0 adder evidence).

---

## Acceptance criteria

- [x] Full chain completed for Version 1 INT8 baseline
- [x] GDSII exists and is viewable (KLayout)
- [x] DRC, LVS, STA, antenna status recorded (zeros or documented waivers)
- [x] Timing includes clock tree (not just combo adder path)
- [x] Power and area numbers refresh the Sprint 4 table
- [x] GitHub still does not contain the OpenLane source tree

## Completed evidence (INT8 4-way baseline)

The chain in the diagram above ran to completion for `accelerator_top` with
OpenLane `v1.0.2`, run tag `project_run_02` (config:
[`designs/accelerator_int8_parallel/config.json`](../../designs/accelerator_int8_parallel/config.json),
`CLOCK_PORT=clk`, `CLOCK_PERIOD=20` ns). This is the same run Sprint 4
recorded a starting PPA table from; Sprint 5's job was closing placement →
CTS → routing → signoff → GDSII for it, which is what is verified below.

| Stage check | Result |
|---|---|
| Floorplan | Die 491.455 x 502.175 µm (0.246796414625 mm²), `FP_CORE_UTIL` 35, `PL_TARGET_DENSITY` 0.50 |
| Placement | Completed, final utilization 35.99% |
| CTS | Real (clocked design, `clk` port); worst setup slack **3.74 ns**, worst hold slack **0.16 ns**, WNS/TNS 0.00 at the typical corner (`reports/cts/13-cts_sta.summary.rpt` in the local run) |
| Routing | TritonRoute violations: 0 |
| DRC | Magic: 0 violations (`reports/signoff/drc.rpt`) |
| LVS | Netgen: 0 errors (`reports/signoff/39-accelerator_top.lvs.rpt`: "Total errors = 0") |
| KLayout vs. Magic XOR | 0 differences |
| Antenna | ARC-reported: **23 unique pins / 19 unique nets** violating (verified by counting `reports/signoff/41-antenna_violators.rpt` directly, not just trusting the summary) — documented follow-up, not waived silently |
| Max fanout | Warnings present in typical-corner STA; documented, not cleaned this sprint (would require RTL/config changes out of Sprint 5 scope) |
| IR drop | Run completed but `VSRC_LOC_FILES` was not set, so values may be inaccurate — flagged in `signoff.md`, not presented as signed-off |

Final physical outputs (curated in
[`results/int8_parallel/`](../../results/int8_parallel/), full run tree stays
local and gitignored under `designs/accelerator_int8_parallel/runs/`):

- `accelerator_top_project_run_02.gds` — confirmed to load in KLayout with
  top cell `accelerator_top`, 183 cells in the hierarchy, bbox matching the
  die area above.
- `metrics.csv`, `signoff.md` — curated PPA and signoff summary (see Sprint 4
  doc for the full table; Sprint 5 adds CTS/route/signoff closure on top of
  it, not a second set of numbers).
- Floorplan/placement/routing screenshots rendered directly from that GDS via
  `scripts/render_gds_screenshots.py` (KLayout Python bindings) are in
  [`../../screenshots/int8_parallel/`](../../screenshots/int8_parallel/):
  `accelerator_top_full_chip.png`, `accelerator_top_placement_detail.png`,
  `accelerator_top_routing_detail.png`.
- `docs/physical_design.md` and `README.md` reflect the measured baseline,
  not a pending one.
- GitHub: `git ls-files | grep runs/` returns nothing — no OpenLane run tree
  is tracked; `OpenLane/`, `runs/`, `*.rpt`, `reports/` etc. are gitignored
  (see `.gitignore`).

This baseline still has open, documented items (antenna and max-fanout
warnings, unverified IR drop) — it is **DRC/LVS-clean GDSII**, which is the
Week 5 gate in
[`02_eight_week_sprint_plan.md`](../02_eight_week_sprint_plan.md), not a
zero-warning manufacturing signoff. Do not upgrade "documented follow-up" to
"clean" for those two items without actually re-running signoff and checking
the reports again.

## How to verify Sprint 5

From the repository root:

```bash
# GDS is well-formed and viewable (requires the `klayout` Python package;
# `pip install klayout` in a venv, or run inside the OpenLane container)
python3 -c "
import klayout.db as db
l = db.Layout(); l.read('results/int8_parallel/accelerator_top_project_run_02.gds')
c = l.top_cell()
print(c.name, c.bbox().width()*l.dbu, 'x', c.bbox().height()*l.dbu, 'um')
"

# Curated evidence exists and is non-empty
test -s results/int8_parallel/metrics.csv
test -s results/int8_parallel/signoff.md
test -s results/int8_parallel/accelerator_top_project_run_02.gds
test -s screenshots/int8_parallel/accelerator_top_full_chip.png

# DRC/LVS/antenna claims match the raw local run (requires the local,
# gitignored designs/accelerator_int8_parallel/runs/project_run_02/ tree —
# rerun OpenLane with run tag project_run_02 if it isn't present locally)
grep "Total errors" designs/accelerator_int8_parallel/runs/project_run_02/reports/signoff/39-accelerator_top.lvs.rpt
grep -c "COUNT: 0" designs/accelerator_int8_parallel/runs/project_run_02/reports/signoff/drc.rpt
grep -oP 'Net: \K[^,]+' designs/accelerator_int8_parallel/runs/project_run_02/reports/signoff/41-antenna_violators.rpt | sort -u | wc -l   # expect 19
grep -oP 'Pin: \K[^,]+' designs/accelerator_int8_parallel/runs/project_run_02/reports/signoff/41-antenna_violators.rpt | sort -u | wc -l   # expect 23

# GitHub does not contain the OpenLane source tree or raw run trees
git ls-files | grep -c '^OpenLane/'   # expect 0
git ls-files | grep -c 'runs/'        # expect 0
```

Sprint 5 is complete for the INT8 parallel baseline when all commands above
pass and `signoff.md` still matches the reported run artifacts. It does not
claim a warning-free manufacturing signoff (antenna/max-fanout remain open)
or the INT4/sequential variants — those are Sprint 6/7.

---

## What not to do this week

- Do not start the optimized RTL until baseline GDS is captured.
- Do not “clean” DRC by changing functionality without Sprint 3.
- Do not fabricate silicon.
- Do not design a custom PDK.

---

## Gate to Sprint 6

Baseline accelerator GDSII + signoff evidence exist. Sprint 6 chooses **one or two** optimizations; it does not reopen “does OpenLane work?”
