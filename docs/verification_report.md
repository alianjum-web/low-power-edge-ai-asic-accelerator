# Sprint 3 Verification Report

## Scope

This report covers the Version 1 signed INT8 accelerator and the inherited
single-MAC baseline. The accelerator testbench uses all five deterministic
vectors in `verification/reference/vectors.csv` (seed `1234`, output shift
`8`) and checks both the post-bias INT32 accumulator and final INT8 output.

## Regression

Run the complete check with:

```bash
scripts/run_sim.sh
```

The command first verifies every CSV row against
`algorithm/reference_model.py`, then compiles and runs the MAC, pipelined MAC,
SiliconNPU, processing-element, and accelerator testbenches. It writes VCD
files to `verification/simulation/`, which are ignored by Git and can be
opened with GTKWave.

## Coverage

| Area | Evidence |
|---|---|
| Python known answers | 8/8 tests pass |
| Frozen reference vectors | 5/5 rows checked by the Python vector checker |
| Accelerator RTL vectors | 5 vectors x 4 neurons, accumulator and output checks |
| Reset and idle | Each RTL testbench resets before stimulus; accelerator checks `busy` after completion |
| Signed boundaries | INT8 minimum, negative products, and mixed-sign products |
| ReLU and requantization | Negative outputs clipped to zero; positive outputs checked at shift 8 |
| Repeated inference | Accelerator reloads weights, activations, and bias for all five runs |
| Waveform evidence | Each testbench emits a VCD; FSM signals are visible in `tb_accelerator.vcd` |
| Lint | `scripts/run_sim.sh` runs Verilator lint when installed |

## Tool versions

The verification host must provide Python 3, Icarus Verilog, and optionally
Verilator. On the development host used for this report, Python is `3.12.3`;
Icarus Verilog and Verilator were not installed, so HDL execution and lint
remain to be run after installing those tools.

## Limitations

- No gate-level or post-layout simulation has been performed.
- The inherited baseline testbenches verify their standalone interfaces; the
  Python bit-exact comparison applies to the Version 1 accelerator vectors.
- GTKWave screenshots are not committed; generated VCDs provide the waveform
  evidence without adding binary artifacts to the repository.