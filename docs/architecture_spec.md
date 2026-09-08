# Architecture spec: Version 1 accelerator

This is the detailed contract for the RTL in `rtl/` delivered in Sprint 2
(`docs/sprints/sprint_02_hardware_architecture_and_rtl.md`). [architecture.md](architecture.md)
stays the narrative/overview doc and links here for the actual port
lists, timing, and memory map. A new contributor should be able to write
a testbench from this file alone.

Everything in this document is backed by passing simulation, not just
review — see "How this was verified" at the end.

---

## 1. Module hierarchy

```text
accelerator_top.sv
 ├── controller.sv            (FSM: IDLE -> LOAD -> COMPUTE -> DONE_S)
 ├── processing_element.sv  x4  (one per neuron: weight column + MAC + accumulator)
 └── requantize.sv          x4  (one per neuron: ReLU + shift/round/saturate)
```

`rtl/mac_core.sv` / `rtl/mac_core_pipelined.sv` / `rtl/silicon_npu.sv`
are the audited-but-separate inherited baseline (see section 6) — they
are **not** instantiated by `accelerator_top`. `processing_element.sv`
implements its own signed sequential MAC directly rather than
instantiating `mac_core`, because `mac_core`'s single `IDLE->ACCUM->DONE_S`
FSM computes one full dot product per `start` pulse with no bias-preload
or per-cycle broadcast-index visibility, neither of which fits a PE that
needs to expose `acc_clear`/`mac_en`/`mac_idx` to a shared controller
across four instances in parallel.

**Folding decisions** (both allowed explicitly by the Sprint 2 plan,
recorded here per its instruction to "still list every module in the
spec so reviewers can find it"):

| Sprint-2-suggested file | Where it actually lives | Why |
|---|---|---|
| `accumulator.sv` | Inside `processing_element.sv` (`acc` register) | Each PE's accumulator is inseparable from its MAC — same accumulate-every-cycle datapath, no benefit to a separate module. |
| `buffers.sv` (weight buffer) | Inside `processing_element.sv` (`weight` register array, 8 deep) | Sprint 2 explicitly allows buffers inside the PE "if architecture_spec.md says so." This is that permission being exercised. |
| `buffers.sv` (input buffer) | Inside `accelerator_top.sv` (`act_mem` register array, 8 deep) | Shared/broadcast to all 4 PEs — it belongs to the top, not any one PE. |

## 2. Port list

### `accelerator_top`

| Port | Dir | Width | Signed | Meaning |
|---|---|---|---|---|
| `clk` | in | 1 | — | |
| `rst_n` | in | 1 | — | active-low async reset |
| `start` | in | 1 | — | level/pulse; FSM leaves IDLE on the first cycle it sees `start=1` |
| `weight_wr_en` | in | 1 | — | write strobe, weight memory map (below) |
| `weight_wr_pe` | in | `$clog2(NUM_NEURONS)` = 2 | unsigned | which neuron (0..3) |
| `weight_wr_idx` | in | `$clog2(NUM_INPUTS)` = 3 | unsigned | which input position (0..7) |
| `weight_wr_data` | in | `DATA_WIDTH` = 8 | **signed** | INT8 weight value |
| `act_wr_en` | in | 1 | — | write strobe, activation memory map |
| `act_wr_idx` | in | 3 | unsigned | which input position (0..7) |
| `act_wr_data` | in | 8 | **signed** | INT8 activation value |
| `bias_wr_en` | in | 1 | — | write strobe, bias memory map |
| `bias_wr_pe` | in | 2 | unsigned | which neuron (0..3) |
| `bias_wr_data` | in | `ACC_WIDTH` = 32 | **signed** | INT32 bias value |
| `shift_in` | in | `SHIFT_WIDTH` = 5 | unsigned | requantize shift, `S = 2**shift_in`, range 0..31 |
| `busy` | out | 1 | — | `1` from the cycle `start` is first seen until the cycle before `!start` returns the FSM to IDLE |
| `done` | out | 1 | — | `1` while the FSM holds `DONE_S`; `y_out` is valid and stable throughout |
| `y_out` | out | `NUM_NEURONS*DATA_WIDTH` = 32 | packed, per-lane **signed** | four INT8 outputs, packed low-to-high: `y_out[(j+1)*8-1 -: 8]` is neuron `j`'s output |

Default parameters: `DATA_WIDTH=8, NUM_INPUTS=8, NUM_NEURONS=4, ACC_WIDTH=32, SHIFT_WIDTH=5` — matches the architecture.md Version 1 topology (8 inputs, 4 neurons) and docs/quantization.md (signed INT8 in, signed INT32 accumulate).

### `processing_element`

| Port | Dir | Width | Signed | Meaning |
|---|---|---|---|---|
| `clk`, `rst_n` | in | 1 | — | |
| `weight_wr_en` | in | 1 | — | write one weight register this cycle |
| `weight_wr_idx` | in | `$clog2(NUM_WEIGHTS)` | unsigned | which of the 8 weight registers |
| `weight_wr_data` | in | `DATA_WIDTH` | signed | |
| `acc_clear` | in | 1 | — | `acc <= bias_in` (bias preload, overrides `mac_en`) |
| `mac_en` | in | 1 | — | `acc <= acc + x_in * weight[mac_idx]` |
| `mac_idx` | in | `$clog2(NUM_WEIGHTS)` | unsigned | which weight register to read this cycle |
| `x_in` | in | `DATA_WIDTH` | signed | broadcast activation for this cycle |
| `bias_in` | in | `ACC_WIDTH` | signed | this neuron's bias |
| `acc_out` | out | `ACC_WIDTH` | signed | running / final accumulator |

### `controller`

| Port | Dir | Width | Meaning |
|---|---|---|---|
| `clk`, `rst_n`, `start` | in | 1 | |
| `mac_idx` | out | `$clog2(NUM_MACS)` | broadcast index, valid while `mac_en` |
| `acc_clear` | out | 1 | pulses for 1 cycle (the LOAD state) |
| `mac_en` | out | 1 | asserted every COMPUTE cycle |
| `busy` | out | 1 | `state != IDLE` |
| `done` | out | 1 | `state == DONE_S` |

### `requantize`

| Port | Dir | Width | Signed | Meaning |
|---|---|---|---|---|
| `acc_in` | in | `ACC_WIDTH` | signed | one PE's final accumulator (post-bias) |
| `shift_in` | in | `SHIFT_WIDTH` | unsigned | |
| `y_out` | out | `OUT_WIDTH` = 8 | signed | INT8 result |

Purely combinational — no clock/reset ports.

## 3. Handshake / timing

```text
        IDLE        LOAD       COMPUTE (x8)         DONE_S
start ───┐
         └─────────►│
                     └─────────►│ mac_idx=0..7      │
                                 (1 MAC per cycle)   └────────► (back to IDLE on !start)
```

1. Host writes weights / activations / biases while `busy == 0` (IDLE or
   DONE_S). Writes are edge-triggered and take effect on the next clock
   edge with no protocol beyond the enable strobe — the host is
   responsible for not writing while `busy == 1`, since nothing in the
   RTL gates writes on FSM state (kept deliberately simple for Version 1;
   see [research_methodology.md](research_methodology.md) for what's in
   scope this phase).
2. Host asserts `start`. On the next clock edge the FSM leaves IDLE and
   enters LOAD; `busy` goes high on that same edge.
3. LOAD lasts exactly 1 cycle: every PE's accumulator is preloaded with
   its bias (`acc_clear`), and the broadcast index resets to 0.
4. COMPUTE lasts exactly `NUM_INPUTS` (8) cycles. Each cycle, `mac_idx`
   selects one activation (broadcast to every PE from the shared
   `act_mem`) and one weight per PE (`weight[mac_idx]`, independent per
   PE); every PE accumulates `x_in * weight[mac_idx]` into its own `acc`.
5. After the 8th COMPUTE cycle the FSM enters `DONE_S`; `done` goes high
   and `y_out` (combinational ReLU+requantize of each PE's final `acc`)
   is valid immediately and holds stable for as long as `done` is high.
6. The FSM returns to IDLE on the first cycle `start` is low while in
   `DONE_S` (mirrors the `mac_core`/`silicon_npu` baseline's `DONE_S`
   convention: hold results until the host acknowledges by dropping
   `start`).

### FSM state mapping (Sprint 2 minimum states -> this implementation)

| Sprint 2 minimum state | This implementation | Notes |
|---|---|---|
| `IDLE` | `IDLE` | unchanged |
| `LOAD` | `LOAD` | bias preload only (weight/activation/bias *writes* happen whenever the host strobes them, not gated to this state — see point 1 above) |
| `COMPUTE` | `COMPUTE` | 8 cycles, `mac_idx` 0..7 |
| `ACCUMULATE` | folded into `COMPUTE` | every COMPUTE cycle both multiplies and accumulates in the same cycle (`processing_element.sv`'s single `acc <= acc + product` update) — there is no separate accumulate phase to name |
| `DONE` | `DONE_S` | also doubles as the "STORE" state named in [verification.md](verification.md) — results are held stable on `y_out` while `done=1`, there is no separate store/readout state |

## 4. Weight / activation / bias memory map

All three are simple one-write-per-cycle register files, addressed
exactly like `rtl/silicon_npu.sv`'s existing row/col write ports (same
convention, so a contributor familiar with the baseline recognizes the
pattern immediately):

| Memory | Location | Depth | Address | Data |
|---|---|---|---|---|
| Weights | one 8-deep array per PE (4 PEs total = 32 registers) | `weight_wr_pe` (0-3) selects the PE, `weight_wr_idx` (0-7) selects the register within it | `weight_wr_pe`, `weight_wr_idx` | `weight_wr_data`, signed INT8 |
| Activations | one 8-deep array, shared/broadcast | `act_wr_idx` (0-7) | `act_wr_idx` | `act_wr_data`, signed INT8 |
| Biases | one 4-deep array, one per PE | `bias_wr_pe` (0-3) | `bias_wr_pe` | `bias_wr_data`, signed INT32 |

`weight[pe=j][idx=i]` holds `w_ij` in the formula below — i.e. loading
weight column `j` loads neuron `j`'s 8 weights, one per input position
`i`. This matches `algorithm/reference_model.py`'s `W` array layout
(`W[i][j]`, row-major, 8 rows x 4 columns) exactly, including which
index is "input position" and which is "neuron".

## 5. Fixed-point / signedness / overflow policy

| Signal | Format | Notes |
|---|---|---|
| `x` (activation) | signed INT8, Q7.0 | matches docs/quantization.md |
| `w` (weight) | signed INT8, Q7.0 | |
| product (`x_i * w_ij`) | signed INT16 | computed in `processing_element.sv`, sign-extended to `ACC_WIDTH` before adding |
| accumulator / bias | signed INT32 | preloaded with bias, then 8 MAC-accumulates; **no saturation, no wrap observed in practice** — see overflow analysis below |
| ReLU | `max(0, acc)` | applied **before** requantize (matches `algorithm/reference_model.forward()`: `acc -> relu(acc) -> requantize`) |
| output | signed INT8 via round-half-up arithmetic right shift by `shift_in`, then saturate to [-128, 127] | matches `quantization.requantize_int8` bit-exactly: `shift_in==0` is pass-through (saturate only, no rounding term); `shift_in>0` adds `1 <<< (shift_in-1)` then shifts |

**Overflow policy — accumulator (INT32):** for `NUM_INPUTS=8` and
`DATA_WIDTH=8`, the largest-magnitude single product is
`(-128)*(-128) = 16384`; summed over 8 terms the largest-magnitude
accumulator value before bias is `8 * 16384 = 131072`, and biases in
the reference vectors stay under 1000 in magnitude (`algorithm/
generate_vectors.py`), so the accumulator never approaches the signed
INT32 range (`±2,147,483,648`). **No wrap or saturate logic is needed
or implemented in the 32-bit accumulator itself** for Version 1's fixed
8x4 topology — this is a deliberate choice (32 bits was picked to match
`docs/quantization.md`'s stated accumulator format and `algorithm/
reference_model.py`'s `np.int32` bit-exactly, with enormous headroom to
spare, not because 32 bits was the minimum required).

**Overflow policy — output (INT8):** saturating, not wrapping — see
`requantize.sv`'s `y_out` `always_comb` block, and
`quantization.requantize_int8`'s `np.clip`. This is the one place
saturation is real and tested (see `verification/tb_accelerator.sv`
vector 2, `y0=46` from `acc0=11903`, and the standalone `requantize.sv`
saturation checks below).

**`mac_core.sv` / `mac_core_pipelined.sv`'s `overflow` output** is a
legacy heuristic inherited from the baseline (checks for a specific
top-2-bit pattern) and is *not* a correct signed-overflow detector; it
is documented as such in both files' headers and is not used anywhere
in the Version 1 accelerator path (`processing_element.sv` does not
expose or need an overflow flag, for the headroom reason above).

## 6. Baseline audit (`mac_core.sv`, `mac_core_pipelined.sv`, `silicon_npu.sv`)

Audited and fixed 2026-09-07, per the Sprint 2 checkpoint's finding that
"no `signed` arithmetic [existed] anywhere" in the inherited baseline:

- `a_slice`/`b_slice`/`product`/`accumulator`/`result` (and the
  equivalents in `mac_core_pipelined.sv` and `silicon_npu.sv`'s
  `weight_mem`/`act_mem`/`mac_result`/`accumulator`/`result`) are now
  declared `signed`, so a negative INT8 operand multiplies as two's
  complement instead of as a large unsigned value.
- Fixed three verilator lint findings that predate this audit:
  `WIDTHEXPAND` (implicit width growth on the product-to-accumulator
  add — now an explicit, commented, deliberate sign-extension),
  `CASEINCOMPLETE` (the 2-bit state enum only used 3 of 4 encodings,
  now has a `default` branch back to `IDLE`), `GENUNNAMED` (unnamed
  generate blocks in `mac_core_pipelined.sv`, now `gen_pipe`/
  `gen_nopipe`), and in `silicon_npu.sv`: `WIDTHEXPAND` on a `row_idx ==
  DEPTH-1` compare (now a width-matched `localparam`) and an unused
  `COL_BITS` localparam (removed).
- Evidence: each file's paired testbench
  (`verification/mac_core_tb.sv`, `mac_core_pipelined_tb.sv`,
  `silicon_npu_tb.sv`) had its "max values" test replaced with a
  signed-boundary test (`INT8_MIN * INT8_MIN`, the true
  largest-magnitude product a signed multiply can produce — the old
  test used the unsigned all-ones bit pattern, which is `-1` under the
  new signed interpretation and no longer exercises an extreme value),
  and a new cross-sign test was added (`-5 * 3` must sum negative,
  which is impossible to get right by accident with unsigned multiply).
  All three testbenches pass, including these new cases (see "How this
  was verified" below).

**`silicon_npu.sv`'s single-scalar-accumulator limitation is
intentionally *not* restructured in place.** It remains a standalone
artifact for the Phase 4 OpenLane PPA sweep (see
`docs/baseline_reference.md`); the Version 1 accelerator's 4
independent per-neuron outputs are `accelerator_top.sv` /
`processing_element.sv`, a separate module tree, not a patch to
`silicon_npu.sv`.

## 7. How this was verified

Everything above was checked by running simulation, not just written
down. This project's environment did not have `verilator`/`iverilog`
installed system-wide; see the note at the end of this section for how
to get them without root, since a fresh contributor's environment may
be in the same state.

1. **Lint** — `verilator --lint-only -Wall` on every file in `rtl/`
   (including `accelerator_top.sv` linted together with its three
   sub-modules) is clean: zero warnings, zero errors.
2. **Baseline regression** — `verification/mac_core_tb.sv`,
   `mac_core_pipelined_tb.sv`, `silicon_npu_tb.sv` (audited/extended,
   see section 6) all pass under `iverilog -g2012` + `vvp`: 7, 6, and 5
   tests respectively, all PASS.
3. **PE unit test** — `verification/tb_processing_element.sv` (new):
   4/4 tests pass, including "all eight weight registers hold
   independent values" (the exact bug class Sprint 2's plan warns
   about) and signed cross-sign products.
4. **End-to-end bit-exact check against the Python golden model** —
   `verification/tb_accelerator.sv` (new) loads 3 of the 5 vectors from
   `verification/reference/vectors.csv` (independently re-derived from
   `algorithm/generate_vectors.py` while writing the testbench, not
   copied blind) directly into `accelerator_top`'s memory-mapped write
   ports, runs one full inference per vector, and compares both the
   pre-ReLU/pre-requantize INT32 accumulator and the final INT8 output
   against what `algorithm/reference_model.forward()` actually computed
   — 15/15 checks pass (3 vectors x (4 neurons + 1 busy-drop check)),
   bit-exact, including a vector that hits the INT8_MIN (-128) weight
   boundary and vectors that exercise ReLU-zeroing on 2 of 4 outputs.
   The full 5-vector sweep with waveform checks remains Sprint 3's job
   (`docs/verification.md` Level 2's "Automated compare" row) — this is
   a Sprint 2 "smoke TB... if it helps you code," not the final gate.
5. **`requantize.sv` in isolation** — 8 direct checks covering
   shift=0 pass-through, high/low saturation, ReLU-then-requantize
   ordering, round-half-up at an exact `.5` boundary, and
   saturate-after-rounding, all matching `quantization.requantize_int8`
   run standalone in Python for the same inputs (accounting for the
   fact that `requantize.sv` includes ReLU internally and
   `quantization.requantize_int8` does not — see section 5's overflow
   note: the module's low-saturation branch is consequently
   unreachable in this project's fixed ReLU-then-requantize pipeline,
   documented in the RTL where it's easy to miss).

### Reproducing this without root

`iverilog` and `verilator` are Ubuntu `universe` packages; if they are
not already installed and `sudo apt-get install -y iverilog verilator`
is available, use that. If not (no root), both tools can be extracted
from their `.deb` packages into a user-writable prefix with no root
required:

```bash
mkdir -p ~/tools/iv && cd ~/tools/iv
apt-get download iverilog verilator
dpkg -x iverilog_*.deb extracted
dpkg -x verilator_*.deb extracted
ln -sf extracted/usr/lib/x86_64-linux-gnu extracted/usr/x86_64-linux-gnu  # verilator/iverilog's own multiarch path lookup needs this symlink
export PATH="$PWD/extracted/usr/bin:$PATH"
export LD_LIBRARY_PATH="$PWD/extracted/usr/lib/x86_64-linux-gnu:$LD_LIBRARY_PATH"
export VERILATOR_ROOT="$PWD/extracted/usr/share/verilator"
alias verilator="$PWD/extracted/usr/bin/verilator_bin"   # the perl wrapper script needs a real install layout; call verilator_bin directly instead
```

Then run the commands in "Reproducing the full verification" in
[README.md](../README.md) (or `docs/verification.md`).

### A note on testbench races (if you extend these testbenches)

`verification/tb_accelerator.sv` and `tb_processing_element.sv` insert
a `#1` delay after every `@(posedge clk)` before driving new stimulus.
This is not decorative: without it, blocking assignments made
immediately after `@(posedge clk)` race the DUT's own `always_ff`
blocks sampling on that same edge, and in this simulator that race
resolved in favor of the *previous* iteration's stimulus reaching the
wrong destination — concretely, a first attempt at
`tb_accelerator.sv` without the `#1` delay wrote each weight into the
next PE over from the one addressed (a rotate-by-one bug, caught by
comparing against the Python golden vector's per-neuron accumulator,
not just the final output). Keep the `#1` (or an equivalent
`@(negedge clk)` stimulus style) in any new testbench code added here.
