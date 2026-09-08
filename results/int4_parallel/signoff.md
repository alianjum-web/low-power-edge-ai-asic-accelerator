# INT4 parallel signoff

- OpenLane: v1.0.2, run tag `project_run_01`
- Top module: `accelerator_top_int4` (a pure port-pass-through wrapper around
  `accelerator_top #(.DATA_WIDTH(4))` -- **not** `accelerator_top` itself.
  See "Why this variant has a wrapper module" below.
- PDK/library: SKY130A / `sky130_fd_sc_hd`
- Clock: 20 ns (50 MHz target) -- unchanged from `int8_parallel`, per the
  fairness checklist (same `CLOCK_PERIOD`, intentionally not swept)
- Die area: 0.172923286025 mm^2 (172923.29 um^2)
- Total cells: 20,157 (synth_cell_count 5,553 pre-detailed-placement)
- Critical path: 7.47 ns (vs. int8_parallel's 7.98 ns) -- informational only;
  the *operating* frequency is still 50 MHz for both variants by control,
  not the higher frequency this slack would allow
- DRC: 0 Magic violations
- LVS: clean, 0 errors ("Circuits match uniquely")
- KLayout versus Magic XOR: 0 differences
- TritonRoute violations: 0
- Setup/hold violations: 0/0 at the typical corner
- Antenna: 14 pin and 11 net violations reported by ARC (int8_parallel had
  23/19 -- fewer, consistent with a smaller design, not separately
  investigated)
- Max fanout: violations reported in typical-corner STA checks (same
  caveat as int8_parallel)
- IR drop: run completed, but `VSRC_LOC_FILES` was not defined, so values
  may be inaccurate (same caveat as int8_parallel)

The raw OpenLane run remains under the local ignored `runs/` tree. This
directory contains only the curated summary and final GDS artifact.

## Why this variant has a wrapper module

`designs/accelerator_int4_parallel/config.json` was staged in Sprint 6 with
`"SYNTH_PARAMETERS": ["DATA_WIDTH=4"]`, relying on OpenLane's Yosys
`chparam` mechanism to override the width at synthesis time without
touching the shared RTL. Sprint 6's own `docs/optimization_plan.md`
flagged this as unverified against this repo's real OpenLane install.

Running it in Sprint 7 confirmed the risk: synthesis reported the
parameter override taking effect (`$paramod\accelerator_top\DATA_WIDTH=...4`
appeared in the Yosys log), but the final `check` pass found `y_out`
(all 16 bits), `busy`, and `done` completely undriven, and Yosys then
errored out (`Can't find module accelerator_top`). Reproduced directly in
standalone Yosys 0.33 (outside OpenLane) two ways:

- `hierarchy -top accelerator_top -chparam DATA_WIDTH 4` in one command
  crashes Yosys outright (`Assert 'modules_.count(module->name) == 0'
  failed in kernel/rtlil.cc:664`) -- an AST-frontend derived-module
  caching bug triggered by this module's memories (`act_mem`, `bias_mem`)
  combined with the chparam-forced reprocessing.
- `hierarchy -top accelerator_top; chparam -set DATA_WIDTH 4
  accelerator_top; hierarchy -top accelerator_top` (the usual workaround
  for the crash above) doesn't crash, but after `flatten` the submodule
  instances (`controller`, 4x `processing_element`, 4x `requantize`)
  stay as opaque, unflattened cells -- the parameter override never
  propagates down into them, and top-level `y_out`/`busy`/`done`/
  `mac_idx` come back undriven again.

A plain Verilog parameter override through instantiation --
`accelerator_top #(.DATA_WIDTH(4)) dut (.*)` inside a thin wrapper module,
no `chparam` involved -- hits neither bug and synthesizes cleanly (0
problems from `check`, real `$mul`/`$add` cells sized for 4-bit operands).
`designs/accelerator_int4_parallel/accelerator_top_int4.sv` is that
wrapper; `config.json` now points `DESIGN_NAME`/`VERILOG_FILES` at it
instead of using `SYNTH_PARAMETERS`.

Confirmed this actually produced an INT4 design, not an INT8 design under
an INT4 label (the exact failure mode `docs/optimization_plan.md` warned
about): the synthesized netlist's `y_out` port is `[15:0]` (`NUM_NEURONS *
DATA_WIDTH = 4*4`, not INT8's 32), and `y_out[15]` is driven by an actual
standard-cell output pin in `results/synthesis/accelerator_top_int4.v`,
not left floating. Die area and cell count also dropped substantially
from `int8_parallel` (see the main comparison), consistent with a
genuinely smaller multiplier array rather than an unchanged netlist.
