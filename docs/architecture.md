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

## Manual PE issue (must audit)

The technical manual describes a weight-stationary PE with `acc += product` and a single `weight_reg`, plus four PEs, while the layer has 8 × 4 = 32 weights. One register cannot retain a column of eight weights. Do not run that RTL through OpenLane until the load/compute protocol is proven against the Python golden model.

## Planned RTL files (Phase 2)

| File | Role |
|---|---|
| `rtl/mac_unit.sv` | INT8×INT8 multiply + INT32 accumulate |
| `rtl/processing_element.sv` | Weight column + MAC + local acc |
| `rtl/accelerator_top.sv` | FSM: IDLE → LOAD → COMPUTE → STORE |

Keep `mac_unit` parameterized so INT4 and sequential variants reuse it.

## Research variants (Phase 4)

| Design | Precision | MAC architecture |
|---|---|---|
| Baseline | INT8 | Sequential (one MAC reused) |
| A | INT8 | 4-way parallel |
| B | INT4 | Sequential |
| C | INT4 | 4-way parallel |

Change one variable at a time. Do not enlarge the chip for its own sake.
