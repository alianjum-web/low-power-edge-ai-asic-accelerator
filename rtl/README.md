# RTL

## Present (Experiment 0)

| File | Notes |
|---|---|
| `adder_8bit.v` | Combinational 8-bit adder (OpenLane DUT) |
| `adder_8bit_baseline.v` | Frozen copy of the same module |

## Planned (Phase 2)

| File | Notes |
|---|---|
| `mac_unit.sv` | INT8×INT8 → INT16, INT32 accumulate |
| `processing_element.sv` | Eight-weight column + MAC |
| `accelerator_top.sv` | Four PEs + control FSM |

Do not synthesize accelerator RTL until it matches the Python golden model. A PE with a single `weight_reg` cannot implement an 8×4 weight-stationary layer as described in the manual. See [docs/architecture.md](../docs/architecture.md).
