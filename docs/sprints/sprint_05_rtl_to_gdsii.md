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

- [ ] Full chain completed for Version 1 INT8 baseline
- [ ] GDSII exists and is viewable (KLayout)
- [ ] DRC, LVS, STA, antenna status recorded (zeros or documented waivers)
- [ ] Timing includes clock tree (not just combo adder path)
- [ ] Power and area numbers refresh the Sprint 4 table
- [ ] GitHub still does not contain the OpenLane source tree

---

## What not to do this week

- Do not start the optimized RTL until baseline GDS is captured.
- Do not “clean” DRC by changing functionality without Sprint 3.
- Do not fabricate silicon.
- Do not design a custom PDK.

---

## Gate to Sprint 6

Baseline accelerator GDSII + signoff evidence exist. Sprint 6 chooses **one or two** optimizations; it does not reopen “does OpenLane work?”
