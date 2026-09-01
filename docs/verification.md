# Verification

The project uses three levels of validation. None is optional for a claimed “working” accelerator.

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
| `verification/tb_mac_unit.sv` | One MAC, documented overflow/saturate policy |
| `verification/tb_processing_element.sv` | Eight sequential MACs with local weight column |
| `verification/tb_accelerator.sv` | Four PEs, FSM IDLE→LOAD→COMPUTE→STORE |
| Automated compare | Python expected == RTL observed |

Tools:

- Icarus Verilog (`iverilog -g2012`) for functional testbenches.
- Verilator `--lint-only -Wall` on RTL **before every OpenLane run**.
- GTKWave for FSM state and per-PE accumulators.

## Level 3 — Physical

OpenLane must produce a netlist, placement, routing, STA, power, DRC, LVS, and GDSII. Experiment 0 already demonstrated this on the adder.

## Experiment 0 (already run)

`testbench/adder_8bit_tb.v` (to be mirrored under `verification/`):

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
