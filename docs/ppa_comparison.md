# Sprint 7: PPA comparison (INT8 parallel baseline vs. INT4 parallel optimized)

Per [docs/optimization_plan.md](optimization_plan.md)'s "one axis only"
scope reduction, this compares `int8_parallel` (baseline, closed through
GDSII in Sprint 5) against `int4_parallel` (optimized, closed through
GDSII in this sprint). The sequential-schedule variants
(`int8_sequential`, `int4_sequential`) remain out of scope, per
[docs/research_methodology.md](research_methodology.md)'s four-point
matrix reduced to one axis for this project's timeline.

Both variants: OpenLane v1.0.2, SKY130A / `sky130_fd_sc_hd`,
`CLOCK_PERIOD=20` ns (50 MHz), `FP_CORE_UTIL=35`, `PL_TARGET_DENSITY=0.50`,
`SYNTH_STRATEGY=AREA 0` -- identical controls, only `DATA_WIDTH` differs
(8 vs. 4). Run tags: `int8_parallel/project_run_02`,
`int4_parallel/project_run_01`.

## Main comparison

| Metric | Baseline (INT8) | Optimized (INT4) | Improvement |
| --- | ---: | ---: | ---: |
| Die area (um^2) | 246,796.41 | 172,923.29 | **+29.93%** |
| Power, typical corner (mW) | 0.0000570001 | 0.0000212000 | **+62.81%** |
| Cycles / inference | 10 | 10 | 0% (unchanged, by control) |
| Operating frequency (MHz) | 50 | 50 | 0% (unchanged, by control) |
| Energy / inference (nJ) | 0.0000114000 | 0.0000042400 | **+62.81%** |
| Accuracy (synthetic, FP32 vs. quantized) | 90.78% | 81.37% | **-9.41 pts** (degraded) |

Sign convention (per the sprint spec): positive = optimized is smaller /
lower power / lower energy. Accuracy is a "higher is better" metric, so
its column is a plain percentage-point change, not run through the same
formula -- a positive number there would mean accuracy *improved*, and it
did not.

Area/power/energy improvements computed as
`(baseline - optimized) / baseline * 100` directly from
`results/comparison.csv` (not by hand-waving); see that file for the full
row-per-variant machine-readable numbers, including the two corrections
made while filling it in this sprint (below).

**Energy equals power improvement, exactly, and that is expected, not a
coincidence or an error:** cycle count and operating frequency are
unchanged by design (both controls), so `E = P * t` with `t` identical
between variants makes the two percentages algebraically the same. This
is the fairness checklist's "same or intentionally changed CLOCK_PERIOD"
working as intended, not a numerical fluke to be suspicious of.

**Critical path, informational only, not a controlled metric:** STA
reports 7.98 ns (INT8) vs. 7.47 ns (INT4) critical path at the same 20 ns
period -- INT4 has more timing slack, consistent with a smaller
multiplier, but this project did not re-target a faster clock for INT4
(same period was a deliberate control), so it is not reported as a
"frequency improvement." A follow-on experiment could re-close INT4 at a
tighter period and measure a real frequency/throughput gain; that was not
done here.

## What this means, plainly

- **Area and power/energy both improved by a similar, non-trivial margin**
  (~30% and ~63%) from halving the datapath width, with the schedule held
  identical -- consistent with Sprint 6's pre-registered hypothesis.
- **Accuracy measurably degraded** (~9.4 points on this synthetic metric),
  also consistent with the pre-registered hypothesis ("INT4 has a 16x
  coarser quantization step over the same represented range").
- **We do not declare a winner.** Whether a ~30 point accuracy drop is an
  acceptable trade for ~30-63% area/energy savings is a task-dependent
  judgment call this project cannot make without a real workload/dataset
  (see "Accuracy caveat" below) -- that is Sprint 8's discussion, not a
  conclusion to pre-empt here.

## Two corrections made while filling this table (documented, not hidden)

1. **`int8_parallel`'s `energy_per_inference_nj` had a 1000x unit bug.**
   It was previously `0.0114000106`, computed as `P[mW] * t[ns]` --
   dimensionally that product is picojoules, not nanojoules
   (`mW * ns = 1e-3 W * 1e-9 s = 1e-12 J = 1 pJ`). The corrected value,
   `P[W] * t[s]` converted to nJ, is `0.0000114000106` nJ. Fixed in
   `results/comparison.csv`; `int4_parallel`'s value was computed
   correctly from the start using the fixed formula.
2. **`int4_parallel`'s staged config did not actually synthesize as
   INT4 on the first attempt.** See "Synthesis finding" below --
   this section exists because it very nearly went unnoticed (the
   config *looked* correct and OpenLane's own log showed the parameter
   override "taking effect" before failing later in the same run).

## Synthesis finding: `SYNTH_PARAMETERS`/`chparam` is broken for this design on this toolchain

`docs/optimization_plan.md` (Sprint 6) staged `int4_parallel/config.json`
with `"SYNTH_PARAMETERS": ["DATA_WIDTH=4"]` and explicitly flagged it as
**not yet verified** against this repo's real OpenLane install, warning
that "if it silently does nothing, the run would synthesize an INT8
design under an INT4 label."

Running it in this sprint surfaced a worse failure mode than "silently
does nothing": Yosys's `hierarchy -chparam` mechanism does not correctly
propagate `DATA_WIDTH=4` through `accelerator_top`'s nested
generate-based hierarchy (4x parameterized `processing_element`, 4x
parameterized `requantize`) under this repo's Yosys 0.33 / OpenLane
v1.0.2. The parameter override visibly "took" (the derived module was
named `$paramod\accelerator_top\DATA_WIDTH=32'...4` in the log), but the
final `check` pass found the top-level `y_out` (all 16 bits), `busy`, and
`done` completely undriven, and the flow errored out. Confirmed
independently in standalone Yosys outside OpenLane (two different failure
modes depending on how `chparam` is invoked -- see
`results/int4_parallel/signoff.md` for the exact commands and errors).

**Fix:** `designs/accelerator_int4_parallel/accelerator_top_int4.sv`, a
thin wrapper module that instantiates
`accelerator_top #(.DATA_WIDTH(4))` through an ordinary Verilog parameter
override (no `chparam` involved). `config.json` now points
`DESIGN_NAME`/`VERILOG_FILES` at the wrapper. Verified clean in isolated
Yosys (0 problems from `check`) before re-running the full OpenLane flow,
which then completed with DRC/LVS/XOR/route/setup/hold all clean.

**Confirmed this produced a genuine INT4 design**, not INT8 silently
mislabeled: the synthesized netlist's `y_out` port is `[15:0]` (`4
neurons * 4 bits`, not INT8's 32), driven by real standard-cell output
pins, and both die area (-29.9%) and total cell count (28,761 -> 20,157)
dropped substantially and independently of any accuracy/timing
side-effects -- not the signature of an unchanged netlist.

## Accuracy caveat

`accuracy_pct` in `results/comparison.csv` for both rows comes from
`algorithm/measure_accuracy.py`, added this sprint. This project has not
adopted a real dataset or task (see `algorithm/README.md`), so this is a
**synthetic quantization-noise measurement**, not a task-accuracy number:
paired random float32 activations/weights/bias (same draw for both bit
widths, seed 1234, N=2000), symmetric per-tensor quantization at a fixed
static scale, run through the existing bit-exact golden pipeline, compared
against the unquantized float32 forward pass via NRMSE
(`accuracy_pct = 100 * (1 - NRMSE)`, clipped to `[0, 100]`). Treat the
90.78% / 81.37% figures as "how much quantization noise this scheme
introduces on random data," not as "this accelerator is 81-91% accurate
at some task."

## Fairness checklist

- [x] Same PDK (`sky130A` / `sky130_fd_sc_hd`)
- [x] Same OpenLane major version (v1.0.2, both runs)
- [x] Same `CLOCK_PERIOD` (20 ns / 50 MHz), unchanged intentionally
- [x] Same golden-model method for the accuracy figure (same seed, same
      paired random draw, only `bits`/`shift` differ)
- [x] Power from the same class of report (typical corner,
      internal+switching+leakage, both runs)
- [x] Area from the same definition (`DIEAREA_mm^2` from OpenLane's own
      metrics report, both runs)
- [x] Run tags recorded for every variant (`project_run_02` / `project_run_01`)

## Draft discussion bullets for Sprint 8

- Halving datapath width bought ~30% area and ~63% power/energy at this
  clock target, for a measured ~9.4-point synthetic-accuracy cost --
  report the trade-off, not a winner.
- The `chparam` failure is itself a finding worth a paragraph: a
  parameter-sweep technique that "looks fine" in a tool's log can still
  produce a broken netlist; the RTL-model-to-gate-level comparison
  (checking driven-ness, not just "did the parameter apply") is what
  caught it here, not visual inspection of the log.
- INT4's larger timing slack (7.47 ns vs. 7.98 ns critical path at the
  same 20 ns period) was not converted into a frequency/throughput
  number in this sprint -- an open follow-on: re-close INT4 at a tighter
  `CLOCK_PERIOD` and see whether a real frequency win survives routing.
  Doing that for INT8 as well (not just INT4) would keep it a fair
  comparison.
- The accuracy figure is synthetic (no dataset). Before writing an
  accuracy claim into the Sprint 8 report or the SOP paragraph in
  `docs/research_methodology.md`, decide whether a small adopted dataset
  is in scope, or keep describing this explicitly as quantization noise
  on synthetic data.
- Sequential-schedule variants (`int8_sequential`, `int4_sequential`)
  are still empty; Sprint 8 should decide whether the four-point matrix
  gets completed or the write-up explicitly scopes to the one axis
  actually measured.
