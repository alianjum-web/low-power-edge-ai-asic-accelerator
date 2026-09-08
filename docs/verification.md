# Verification

The project uses three levels of validation. None is optional for a claimed “working” accelerator.

The active verification target is the Version 1 hierarchy rooted at `rtl/accelerator_top.sv`. The inherited SiliconNPU testbenches and MAC modules are reference-only and are not included in `scripts/run_sim.sh`; their results must not be used as evidence for the Version 1 accelerator.

## Level 1 — Mathematical (Python)

The golden model in `algorithm/` computes the same 8×4 INT8 GEMV + bias + ReLU + requantize as the RTL. Compare **final INT8 outputs**, not internal cycle timing, unless a cycle-accurate checker is added later.

Requirements:

- Fixed random seed / deterministic weights, biases, and stimuli.
- Vectors checked into `algorithm/` and/or `verification/reference/` (hex or CSV).
- Same scale factors used by software and by the RTL requantize path.

## Level 2 — RTL

Hierarchical tests (Phase 2):

| Test | What must pass |
|---|---|
| `verification/mac_core_tb.sv` | One MAC/dot-product core — audited 2026-09-07: now exercises signed-boundary (`INT8_MIN * INT8_MIN`) and cross-sign operands, not just the old unsigned all-ones case. 7/7 pass. |
| `verification/tb_processing_element.sv` | Eight sequential MACs with local weight column — written 2026-09-07, 4/4 pass, including "all eight weight registers hold independent values" |
| `verification/tb_accelerator.sv` | Four PEs, FSM IDLE→LOAD→COMPUTE→DONE_S — written 2026-09-07, loads 3 real golden vectors and checks both the INT32 accumulator and final INT8 output bit-exactly against `algorithm/reference_model.forward()`, 15/15 checks pass |
| Automated compare | Python expected == RTL observed — done for 3/5 vectors via the hand-written `tb_accelerator.sv` above; a scripted sweep over all 5 (and beyond) is still Sprint 3's job, not this sprint's |

See [baseline_reference.md](baseline_reference.md) for what the inherited `mac_core_tb.sv` / `silicon_npu_tb.sv` / `mac_core_pipelined_tb.sv` testbenches actually cover today.

Tools:

- Icarus Verilog (`iverilog -g2012`) for functional testbenches.
- Verilator `--lint-only -Wall` on RTL **before every OpenLane run**.
- GTKWave for FSM state and per-PE accumulators.

Neither tool needs to be preinstalled system-wide: if `apt-get install
iverilog verilator` isn't available (no root), both can be extracted
from their `.deb` packages into a user-writable prefix with no root
required — see [architecture_spec.md](architecture_spec.md) section 7,
"Reproducing this without root," for the exact commands. That's how
this project's own Sprint 2 verification was actually run.

## Level 3 — Physical

OpenLane must produce a netlist, placement, routing, STA, power, DRC, LVS, and GDSII. Experiment 0 already demonstrated this on the adder.

## Experiment 0 (already run)

`testbench/adder_8bit_tb.v` (mirrored under `verification/tb_adder_8bit.v`):

| A | B | Expected sum (8-bit wrap) |
|---|---|---|
| 10 | 20 | 30 |
| 100 | 50 | 150 |
| 255 | 1 | 0 (wrap) |
| 0 | 0 | 0 |

Combinational DUT. VCD was produced locally; binaries and VCDs stay out of Git (see `.gitignore`).

## Pass criteria for the first accelerator

- Python and RTL agree on every generated vector.
- Lint-clean enough to synthesize (no unmapped blackboxes).
- Only then: OpenLane.

Do not treat a one-shot “TEST PASSED” log from unverified manual RTL as Level 2 if the PE cannot store eight weights.
