# Architecture

## Experiment 0 (implemented): 8-bit adder

```verilog
module adder_8bit (
    input  [7:0] a,
    input  [7:0] b,
    output [7:0] sum
);
    assign sum = a + b;
endmodule
```

- Combinational, no clock, no `cin`/`cout`.
- OpenLane `CLOCK_PORT` is empty.
- Copies: `rtl/adder_8bit.v`, `rtl/adder_8bit_baseline.v`, `designs/adder_8bit/adder_8bit.v`.

The manual’s clocked adder is **not** what went through OpenLane. Experiment 0 is a **toolchain proof**, not the research datapath.

## Inherited baseline (reference-only)

The inherited SiliconNPU MAC modules are retained for provenance and comparison only. They are not part of the active Version 1 accelerator hierarchy and are excluded from the standard simulation and lint flow. They must not be described as this project's original implementation.

The inherited `rtl/mac_core.sv`, `rtl/mac_core_pipelined.sv`, and `rtl/silicon_npu.sv` are documented in [baseline_reference.md](baseline_reference.md) for provenance only. The active Version 1 design does not depend on them; they are excluded from the current accelerator hierarchy.

**Audited and fixed 2026-09-07** (see [architecture_spec.md](architecture_spec.md) section 6 for the full before/after):
- `operand_a`/`operand_b` (and `silicon_npu.sv`'s `weight_mem`/`act_mem`) are now `signed`, so this project's quantization policy — symmetric signed INT8 ([docs/quantization.md](quantization.md)) — multiplies correctly instead of as unsigned magnitudes. Verified against updated testbenches with signed-boundary and cross-sign test cases, not just reviewed.
- `mac_core` still computes one dot product (one neuron); the 4-neuron, bias + ReLU + requantize accelerator is now implemented separately as `rtl/accelerator_top.sv` / `rtl/processing_element.sv` / `rtl/requantize.sv` / `rtl/controller.sv` (below), not by extending `mac_core` itself.
- The active Version 1 hierarchy is lint-clean with Verilator. The inherited reference modules are intentionally outside this lint target.

This replaces the retired `rtl/mac_unit.sv` / `rtl/edge_ai_accelerator.sv`, which was unsynthesized and unverified. The active implementation begins with the Version 1 accelerator below.

## Version 1 accelerator (to build)

Neural-network operation:

```text
8 inputs → 4 output neurons → ReLU → 4 INT8 outputs
```

\[
y_j = \mathrm{ReLU}\left(\sum_{i=0}^{7} x_i w_{ij} + b_j\right)
\]

32 MAC operations per inference.

### Recommended topology: four parallel accumulators

```text
              INPUT VECTOR
           x0 x1 x2 ... x7
                │
        ┌───────┴────────┐
        ▼                ▼
    PE / MAC 0       PE / MAC 1
    neuron 0         neuron 1
        ▼                ▼
    PE / MAC 2       PE / MAC 3
    neuron 2         neuron 3
```

Each PE has its **full weight column** (8 values), not a single register:

| PE | Weights |
|---|---|
| PE0 | w00 w10 w20 w30 w40 w50 w60 w70 |
| PE1 | w01 w11 w21 w31 w41 w51 w61 w71 |
| PE2 | w02 w12 w22 w32 w42 w52 w62 w72 |
| PE3 | w03 w13 w23 w33 w43 w53 w63 w73 |

Compute schedule (broadcast `x_i` to all PEs):

| Cycle | Operation |
|---|---|
| 0 | x0 × w0j |
| 1 | x1 × w1j |
| … | … |
| 7 | x7 × w7j |

After eight cycles: `accumulator[j] = Σ_i x_i w_ij`. Then add bias, ReLU, requantize to INT8.

Simple hardware is the right first milestone while learning physical design.

### Datapath widths (Version 1)

```text
INT8 × INT8 → INT16 product → INT32 accumulate → ReLU → requantize → INT8
```

## Manual PE issue (resolved 2026-09-07)

The technical manual describes a weight-stationary PE with `acc += product` and a single `weight_reg`, plus four PEs, while the layer has 8 × 4 = 32 weights. One register cannot retain a column of eight weights. `rtl/processing_element.sv` fixes this: each PE holds an 8-deep `weight` register array (one register per input position), verified directly in `verification/tb_processing_element.sv` ("Test 1: Eight independent weight registers" writes all eight and checks all eight survive together, not just the last write).

## RTL files (Phase 2, delivered)

| File | Role |
|---|---|
| `rtl/mac_core.sv` | Inherited baseline dot-product reference; excluded from the active Version 1 flow |
| `rtl/mac_core_pipelined.sv` | Inherited pipelined baseline reference; excluded from the active Version 1 flow |
| `rtl/silicon_npu.sv` | Inherited wrapper reference; excluded from the active Version 1 flow |
| `rtl/processing_element.sv` | Weight column (8 signed registers) + signed MAC + INT32 accumulator with bias preload |
| `rtl/controller.sv` | FSM: IDLE → LOAD → COMPUTE → DONE_S (ACCUMULATE folded into COMPUTE, DONE_S doubles as STORE — see architecture_spec.md section 3) |
| `rtl/requantize.sv` | ReLU + power-of-two shift/round/saturate to INT8, bit-exact with `algorithm/quantization.requantize_int8` composed with `algorithm/reference_model.relu` |
| `rtl/accelerator_top.sv` | Top: 4x `processing_element` + `controller` + 4x `requantize` + shared activation/bias memories |

See [architecture_spec.md](architecture_spec.md) for the full port lists, FSM/timing diagram, memory map, and verification evidence (bit-exact against `algorithm/reference_model.py` on real golden vectors, not just reviewed).

Keep `mac_core`'s `WIDTH`/`ARRAY_SIZE` parameters driving INT4 vs INT8 and sequential vs parallel variants, rather than reintroducing a separate `mac_unit`.

## Research variants (Phase 4)

| Design | Precision | MAC architecture |
|---|---|---|
| Baseline | INT8 | Sequential (one MAC reused) |
| A | INT8 | 4-way parallel |
| B | INT4 | Sequential |
| C | INT4 | 4-way parallel |

Change one variable at a time. Do not enlarge the chip for its own sake.
