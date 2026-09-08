# Sprint 3: RTL verification

**Week 3** · **~20–25 hours** · **Phase 2 gate** · Previous: [Sprint 2](sprint_02_hardware_architecture_and_rtl.md) · Next: [Sprint 4](sprint_04_synthesis_and_baseline_ppa.md)

---

## Goal

Prove the RTL matches the Python golden model on frozen vectors. This sprint is **mandatory**.

A GDS of incorrect RTL is still incorrect. Silicon does not care about your optimism.

---

## Why this sprint exists

Sprints 4–5 cost tool time and produce layouts. Layouts do not debug FSMs. Hierarchical simulation does.

---

## 1. Create testbench

Test:

- reset
- normal operation
- zero inputs
- positive values
- negative values
- maximum values
- minimum values
- overflow
- multiple computations

Place testbenches in **`verification/`** (original plan: `tb/`). Hierarchical layout from [verification.md](../verification.md):

| Test | What must pass |
|---|---|
| `verification/mac_core_tb.sv` | One MAC/dot-product core (baseline, already exists — audit for signed operands before trusting it) |
| `verification/tb_processing_element.sv` | Eight sequential MACs with local weight column (not yet written) |
| `verification/tb_accelerator.sv` | Four PEs, FSM IDLE→LOAD→COMPUTE→STORE/DONE (not yet written) |
| Automated compare | Python expected == RTL observed |

Keep Experiment 0 `verification/tb_adder_8bit.v` / `testbench/adder_8bit_tb.v` as the adder TB. Do not mix adder wrap-around tests with INT8 GEMV tests.

---

## 2. Compare RTL against Python

Use identical:

```text
inputs
weights
expected outputs
```

Then:

```text
Python result == RTL result
```

Compare **final INT8 outputs** (and documented intermediate INT32 acc if you have a probe). Same scale factors in software and hardware. Vectors live in `algorithm/` and/or `verification/reference/`.

---

## 3. Run simulation

Use:

- Icarus Verilog or Verilator
- GTKWave

Example (adjust file lists as modules appear):

```bash
iverilog -g2012 -o mac_sim verification/mac_core_tb.sv rtl/mac_core.sv
vvp mac_sim
```

Prefer wrapping this in `scripts/run_sim.sh` so there is **one command that runs all tests** (regression, item 5).

Do not commit `mac_sim`, `*.vcd`, or other binaries (`.gitignore`).

---

## 4. Check waveforms

Verify:

```text
start
 ↓
LOAD
 ↓
COMPUTE
 ↓
ACCUMULATE
 ↓
DONE
```

Save **screenshots or documented GTKWave session notes** under `verification/waveforms/` or `docs/figures/` (small PNGs are OK; huge VCDs are not). A new contributor should see the FSM sequence without rerunning if tools are missing.

---

## 5. Create regression tests

You want one command that runs all tests.

Suggested:

```bash
scripts/run_sim.sh
```

That script should:

- build each TB
- run it
- exit non-zero on mismatch
- optionally invoke the Python vector generator first

Also useful: `verilator --lint-only -Wall` on RTL **before every OpenLane run** (Sprint 4+).

---

## Deliverables

```text
tb/                 → verification/
simulation/         → local runs + scripts/run_sim.sh (binaries gitignored)
waveforms/          → verification/waveforms/ or docs/figures/
verification_report.md
```

Put the report at **`docs/verification_report.md`** (Sprint 3 write-up) and keep [verification.md](../verification.md) as the method.

The report should include:

- tool versions (`iverilog -v`, Verilator, Python)
- vector list and seeds
- pass/fail table
- known limitations (e.g. no gate-level sim yet)
- waveform figure references

---

## Acceptance criterion

> RTL outputs must match the Python reference for the defined test vectors.

Checklist:

- [x] Reset and idle behavior documented and tested in the hierarchical testbenches
- [x] Corner cases: zero, signed minimum, negative, cross-sign products, and ReLU saturation
- [x] Multi-inference back-to-back (`start` after `done`) in `tb_accelerator.sv`
- [x] Bit-exact Python vector checking and RTL expected-value coverage for all five frozen vectors
- [x] One-command regression in `scripts/run_sim.sh`
- [x] Waveform evidence of the FSM via generated VCDs and notes in `docs/verification_report.md`
- [ ] HDL execution and lint on this host: blocked because Icarus Verilog and Verilator are not installed

---

## Tasks a contributor can pick up

1. MAC unit TB + overflow cases.
2. PE TB with a known 8-weight column.
3. Top-level TB driven by `verification/reference/` hex/CSV.
4. Python script that diffs RTL log vs golden CSV.
5. `scripts/run_sim.sh` + CI-style exit codes.
6. Write `docs/verification_report.md`.

---

## What not to do this week

- Do not “fix” mismatches by changing only Python or only RTL without updating the spec.
- Do not start OpenLane on the accelerator.
- Do not declare victory from a single happy-path vector.
- Do not commit simulator binaries.

---

## Gate to Sprint 4

Acceptance criterion above is met. If it is not, **do not synthesize**.
