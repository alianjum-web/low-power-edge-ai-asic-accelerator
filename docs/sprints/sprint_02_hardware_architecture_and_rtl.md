# Sprint 2: Hardware architecture + RTL

**Week 2** · **~20–25 hours** · **Phase 2** · Previous: [Sprint 1](sprint_01_research_and_python_baseline.md) · Next: [Sprint 3](sprint_03_rtl_verification.md)

---

## Goal

Convert the mathematical model into synthesizable hardware: buffers, MAC, accumulator, activation, and a control FSM. Document interfaces and fixed-point behavior so Sprint 3 can test them.

Do **not** run OpenLane on this RTL until Sprint 3 passes.

---

## Why this sprint exists

Software integers become wires and registers. If the hierarchy or weight storage is wrong (classic bug: one `weight_reg` per PE instead of eight weights), later GDSII is an expensive picture of a wrong circuit.

---

## Checkpoint already in this repo

The earlier draft RTL (`rtl/mac_unit.sv`, `rtl/edge_ai_accelerator.sv`) — the combinational `edge_ai_accelerator` with hardcoded ±1 weights — was **not** the Version 1 architecture (no FSM, no loadable weights, not bit-exact to a general GEMV). It was superseded by the active Version 1 accelerator hierarchy. The inherited `rtl/mac_core.sv`, `rtl/mac_core_pipelined.sv`, and `rtl/silicon_npu.sv` are documented in [baseline_reference.md](../baseline_reference.md) for provenance only and are excluded from the active flow. The draft added nothing beyond what git history already preserves once superseded, so it was deleted 2026-09-07 rather than kept as a `legacy/` directory.

**This sprint is now done.** The inherited baseline had a real FSM and loadable weight/activation memory but did not match this project's Version 1 requirements. The active implementation is the separate module tree: `rtl/accelerator_top.sv`, `rtl/processing_element.sv`, `rtl/controller.sv`, `rtl/requantize.sv`. See [architecture_spec.md](../architecture_spec.md) for the full contract, FSM/timing, memory map, and verification evidence (bit-exact against the Python golden model on real vectors, not just reviewed).

`rtl/adder_8bit.v` is Experiment 0 only and was left alone.

---

## 1. Design modules

Create:

```text
accelerator_top
 ├── input_buffer
 ├── weight_buffer
 ├── mac_core
 ├── accumulator
 ├── activation
 └── controller/FSM
```

**This repository’s recommended Version 1 mapping:**

```text
accelerator_top.sv          (or keep a clear top name; document it)
 ├── processing_element.sv  (weight column + MAC + acc)
 ├── mac_core.sv (baseline, already exists)
 ├── activation / ReLU + requantize (module or section of top)
 └── controller.sv          (FSM)
```

Buffers may live inside the PE (weight column registers) and top (input broadcast). That is acceptable if `architecture_spec.md` says so. Do not hide eight weights in one register.

From [architecture.md](../architecture.md): four PEs, each with `w0j … w7j`, broadcast `x_i` for eight compute cycles, then bias, ReLU, requantize.

---

## 2. Define interfaces

For example:

```text
clk
rst
start
data_in
weight_in
valid
done
result
```

Write the **actual** port list in `docs/architecture_spec.md` (or a section of `docs/architecture.md`). Include:

- bit widths and signedness
- handshake (`start` / `valid` / `done`)
- how weights are loaded (serial vs parallel, how many cycles)
- how results are read (four INT8 outputs vs streaming)

A new contributor should be able to write a testbench from this spec alone.

---

## 3. Implement MAC

Conceptually:

```text
multiplication
      ↓
addition
      ↓
accumulator
```

Version 1 datapath:

```text
INT8 × INT8 → INT16 product → INT32 accumulate
```

Keep `mac_core` small and reusable when bit-width later changes (Sprint 6). Prefer parameters for widths.

---

## 4. Implement control FSM

Minimum states:

```text
IDLE
LOAD
COMPUTE
ACCUMULATE
DONE
```

You may split LOAD into weight-load vs input-load if the protocol needs it. You may merge ACCUMULATE into COMPUTE if accumulate happens every MAC cycle. **Document the mapping.** Waveforms in Sprint 3 will check:

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

---

## 5. Decide fixed-point representation

Document:

- signed/unsigned
- integer bits
- fractional bits
- overflow behavior
- saturation/truncation

Version 1 default (unless Sprint 1 froze something else):

| Signal | Format |
|---|---|
| `x`, `w` | signed INT8 (Q7.0 unless you document otherwise) |
| product | signed INT16 |
| accumulator | signed INT32 (wrap or saturate: **pick one and test it**) |
| ReLU | `max(0, acc)` before or after requantize (document order) |
| output | signed INT8 via documented scale / shift |

This must match the Python model. If Python saturates and RTL wraps, Sprint 3 will fail.

---

## Deliverables

```text
rtl/
 ├── accelerator_top.sv
 ├── mac_core.sv
 ├── accumulator.sv
 ├── controller.sv
 └── buffers.sv
```

If you fold accumulator into `mac_core` / PE, still list every module in the spec so reviewers can find it.

Also create:

```text
architecture_spec.md
```

Put it at **`docs/architecture_spec.md`** (and keep [architecture.md](../architecture.md) in sync, or make the spec the detailed contract and the architecture doc the narrative).

---

## Tasks a contributor can pick up

1. Draft `docs/architecture_spec.md` (ports, FSM, memory map of weights).
2. Audit and lint the inherited `rtl/mac_core.sv` (signed operands, overflow policy) rather than writing a new MAC from scratch.
3. Implement PE with **eight** weight registers and sequential MAC over `i = 0..7`.
4. Implement top with four PEs + FSM.
5. Implement ReLU + requantize identical to Python.
6. Run `verilator --lint-only -Wall` on new RTL (no OpenLane yet).

---

## Suggested commands

```bash
verilator --lint-only -Wall rtl/mac_core.sv
# add other modules as they appear
```

Icarus: `iverilog -g2012` belongs mainly in Sprint 3, but a smoke TB is allowed if it helps you code.

---

## Acceptance criteria

- [x] Module hierarchy matches the spec (or the spec was updated first). — `docs/architecture_spec.md` section 1; folding decisions (accumulator into PE, buffers into PE/top) documented there.
- [x] Each PE can hold eight weights. — `rtl/processing_element.sv`'s 8-deep `weight` register array; verified in `verification/tb_processing_element.sv` Test 1.
- [x] FSM states are named and documented. — `rtl/controller.sv` (IDLE/LOAD/COMPUTE/DONE_S); mapping to the sprint's 5-state list in `docs/architecture_spec.md` section 3.
- [x] Fixed-point and overflow policy are written down. — `docs/architecture_spec.md` section 5.
- [x] Lint is clean enough to simulate (no undriven resets, no width disasters). — `verilator --lint-only -Wall` clean on every file in `rtl/`, including the newly-clean audited baseline; see `docs/architecture_spec.md` section 7.
- [x] Adder Experiment 0 files are unchanged unless there is a documented bug. — `rtl/adder_8bit*.v` untouched; `verification/tb_adder_8bit.v` still passes (100+50=150, 255+1=0 wrap, 0+0=0).

---

## What not to do this week

- Do not start INT4 clones until INT8 Version 1 exists.
- Do not put a supplied `accelerator_top` through OpenLane until it exists **here** and passes Sprint 3.
- Do not optimize for power yet (Sprint 6).
- Do not add AXI, SRAM compilers, or a CPU.

---

## Gate to Sprint 3

RTL exists and is specified. Sprint 3 proves it against Python. If the spec and RTL disagree, fix one of them before writing more tests.
