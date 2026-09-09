# Optimization plan (Sprint 6)

Written **before** looking at any Sprint 7 percentages, per
[sprint_06_low_power_optimization.md](sprints/sprint_06_low_power_optimization.md)'s
instruction. This is the pre-registration of the experiment, not its result.

---

## Technique chosen

**Bit-width optimization: INT8 -> INT4 datapath**
([sprint_06](sprints/sprint_06_low_power_optimization.md) Option A), on the
**same MAC architecture and schedule already closed through GDSII**
(`accelerator_top`'s 4-way parallel PEs — one PE per neuron, 8 sequential
MAC cycles per PE per inference; see
[architecture_spec.md](architecture_spec.md)).

**One axis only.** This project's own [research_methodology.md](research_methodology.md)
four-point matrix has a precision axis (INT8/INT4) and a MAC-architecture
axis (sequential/4-way parallel). Sprint 6 explicitly permits reducing
scope to one axis "if 8 weeks are tight after GDS pain" and explicitly
forbids implementing five techniques at once. The sequential-schedule
variants (`accelerator_int8_sequential`, `accelerator_int4_sequential`)
are **not** attempted this sprint; they stay reserved (empty) folders for
a later sprint if time allows.

## Hypothesis (not a result)

Halving the activation/weight width from 8 to 4 bits should:

- shrink the per-PE multiplier (`DATA_WIDTH x DATA_WIDTH` -> smaller
  partial-product tree) and its switching activity, likely reducing area
  and dynamic power;
- **not** change latency (still `NUM_INPUTS` = 8 COMPUTE cycles/inference
  — the schedule is unchanged, only operand width is);
- **degrade accuracy** relative to the INT8 vectors, because INT4 has a
  16x coarser quantization step over the same represented range.

We measure all of the above in Sprint 7. **We do not declare a winner
here.**

## What stays constant (the controls)

Per [research_methodology.md](research_methodology.md)'s "change one
architectural variable at a time":

| Control | Value | Same as baseline? |
|---|---|---|
| MAC architecture / schedule | 4-way parallel, 8 sequential MAC cycles/PE | Yes — identical `controller.sv` FSM, identical cycle count |
| RTL module set | `accelerator_top.sv`, `controller.sv`, `processing_element.sv`, `requantize.sv` | Yes — **the same files**, no fork. Only the `DATA_WIDTH` parameter differs at instantiation/synthesis time. |
| `ACC_WIDTH` | 32 | Yes — deliberately *not* shrunk, so this remains a single-variable (precision-only) change. INT4's worst-case accumulator magnitude (512, see below) has even more headroom in 32 bits than INT8's did, so this costs nothing in correctness and keeps the comparison honest. |
| `NUM_INPUTS`, `NUM_NEURONS` | 8, 4 | Yes |
| PDK / std cell library | `sky130A` / `sky130_fd_sc_hd` | Will be, in Sprint 7 |
| OpenLane major version | same install used for `int8_parallel`'s `project_run_02` | Will be, in Sprint 7 |
| `CLOCK_PERIOD` | 20 ns | Will be, in Sprint 7 — `designs/accelerator_int4_parallel/config.json` copies `int8_parallel`'s config verbatim except for the width override below |
| Golden-model method | symmetric signed quantization, zero-point 0 | Yes — same policy, per [quantization.md](quantization.md)'s "INT4 (Phase 4 only)" section, n=4 instead of n=8 |
| Vector generation seed/policy | seed=1234, same `rng` call shape | Yes — `algorithm/generate_vectors.py`'s INT4 path reuses the same seed and vector count |

## What changes (the one variable)

| Item | Baseline (INT8) | Optimized (INT4) |
|---|---|---|
| `DATA_WIDTH` (accelerator_top / processing_element / requantize parameter) | 8 | 4 |
| Activation / weight range | [-128, 127] | [-8, 7] |
| Output (`y_out` per-lane) range | [-128, 127] | [-8, 7] |
| Requantize shift used for the frozen test vectors | 8 | 4 (see note below) |
| Bias sample range in `generate_vectors.py` | [-1000, 1000) | [-4, 4) |

**Why the bias range also changes, even though bias stays INT32:**
INT8's worst-case sum-of-8-products magnitude is 131,072, so a bias
sampled from +-1000 is a small perturbation (~1:131 ratio) that still lets
the GEMV term dominate the test. INT4's worst-case sum-of-8 magnitude is
only 512 (`8 * (-8*-8)`); reusing +-1000 would let the bias swamp the
dot-product term on almost every vector, which would not actually
exercise the MAC datapath. +-4 keeps roughly the same
bias:accumulator-headroom ratio. This is a test-vector generation
decision, not a hardware change — the bias port is still signed INT32 in
both variants, unmodified.

**Why the shift changes:** `shift` is Python-side test tooling (picking
the output scale so the frozen vectors exercise a spread of outputs
without saturating on every single one), not an RTL parameter — see
[quantization.md](quantization.md)'s definition of `S = 2**shift` as an
"offline per-layer output scale computed in Python". `SHIFT=8` was
chosen for INT8 specifically because it "keeps full-range INT8 x/w
products from saturating... on every vector" (`algorithm/README.md`).
The same reasoning at INT4's much smaller dynamic range picks
`SHIFT_INT4=4` empirically (checked against this seed's 5 vectors: 0/20
outputs saturate, values span 0..6 of the available 0..7 positive
range — see `algorithm/generate_vectors.py`'s `SHIFT_INT4` comment).

## Overflow / headroom re-check for INT4

Same method as [architecture_spec.md](architecture_spec.md) section 5,
substituting n=4:

- Largest-magnitude INT4 product: `(-8) * (-8) = 64`
- Largest-magnitude 8-term accumulator (pre-bias): `8 * 64 = 512`
- `ACC_WIDTH = 32` (unchanged) holds this with enormous headroom to
  spare — same conclusion as INT8, no saturation/wrap logic needed in
  the accumulator itself.
- Output saturation (`requantize.sv`'s clip to `[-8, 7]`) is exercised
  the same way as INT8's clip to `[-128, 127]` — see
  `algorithm/tests/test_reference_model.py`'s
  `test_int4_requantize_saturates_at_int4_bounds`.

## Implementation (what actually changed, Sprint 6)

No new MAC/PE/controller/requantize RTL file was written — the whole
point of the parameter reuse is that none was needed:

- `rtl/accelerator_top.sv`, `processing_element.sv`, `requantize.sv` were
  already generically parameterized on `DATA_WIDTH` (verified by reading
  each file — see [architecture_spec.md](architecture_spec.md)). Sprint 6
  instantiates the same files with `DATA_WIDTH=4` instead of forking a
  second copy.
- `algorithm/quantization.py`: added a generic `qrange(bits)` /
  `requantize(acc, shift, bits=8)`; `requantize_int8` is now a thin
  `bits=8` wrapper over it, kept for existing callers.
- `algorithm/reference_model.py`: `forward(..., bits=8)` threads the new
  parameter through to `requantize`; `dense_int8`/`relu` are unchanged
  (already width-agnostic).
- `algorithm/generate_vectors.py`: `generate()` takes `bits`/`bias_range`;
  `main()` now also writes `verification/reference/vectors_int4.{csv,hex}`
  alongside the untouched, bit-exact-frozen `vectors.{csv,hex}`.
- `algorithm/tests/test_reference_model.py`: 4 new INT4 known-answer
  tests (saturation, rounding, headroom, end-to-end shape) — 12/12 pass.
- `scripts/check_reference_vectors.py`: now checks both vector sets
  against the golden model — 5/5 INT8 + 5/5 INT4 pass.
- `verification/tb_accelerator_int4.sv`: new testbench, structurally
  identical to `tb_accelerator.sv`, instantiating `accelerator_top` with
  `DATA_WIDTH=4` and loading all 5 INT4 golden vectors — 25/25 checks
  (5 vectors x (4 neurons + 1 busy-drop check)) pass bit-exact against
  `algorithm/reference_model.forward(..., bits=4)`.
- `scripts/run_sim.sh`: now runs the INT4 testbench and a second
  Verilator lint pass with `-GDATA_WIDTH=4`, both clean.
- `designs/accelerator_int4_parallel/config.json`: staged (not run) —
  identical to `accelerator_int8_parallel/config.json`'s
  `CLOCK_PERIOD`/`FP_CORE_UTIL`/`PL_TARGET_DENSITY`/`SYNTH_STRATEGY`,
  plus `"SYNTH_PARAMETERS": ["DATA_WIDTH=4"]` to override the Verilog
  parameter at synthesis time (OpenLane's Yosys `chparam` mechanism).
  **Not yet verified against this repo's actual OpenLane v1.0.2 install**
  (`results/int8_parallel/signoff.md`) — the legacy `openmac/tclgen.py`
  flow used for `mac_core` passes `-chparam` directly in a hand-written
  Yosys script rather than through OpenLane's own `config.json`, so this
  key has not been exercised in this repo before. Confirm it takes effect
  (e.g. check the synthesized netlist's multiplier width, or `grep
  chparam` in OpenLane's own generated synthesis log) before trusting any
  `int4_parallel` PPA numbers in Sprint 7 — if it silently does nothing,
  the run would synthesize an INT8 design under an INT4 label.
  Actually running this through OpenLane/GDSII is **Sprint 7's job**, not
  this sprint's — per "do not declare PPA winners until Sprint 7 GDS/synth
  numbers exist."
- `results/comparison.csv`: `int4_parallel` row's `notes` column updated
  to record that RTL/verification is done and PPA is pending; **no
  numeric PPA columns were filled in** (still blank, honestly).

## Deferred to Sprint 7 (or later, if time allows)

- Running `designs/accelerator_int4_parallel/config.json` through
  OpenLane to GDSII and filling `results/comparison.csv`'s numeric
  columns for `int4_parallel`.
- The sequential-schedule axis (`accelerator_int8_sequential`,
  `accelerator_int4_sequential`) — out of scope for the one axis chosen
  this sprint.
- Any accuracy-on-real-data comparison beyond the synthetic golden
  vectors (per [research_question.md](research_question.md), a dataset
  hasn't been adopted yet).

## Sprint 7 update (added after the fact — does not alter the pre-registration above)

Both deferred items are done: `int4_parallel` is now through OpenLane to
GDSII (DRC/LVS/XOR/route/setup-hold clean) and `results/comparison.csv`'s
numeric columns are filled for both `int8_parallel` and `int4_parallel`.
See [docs/ppa_comparison.md](ppa_comparison.md) for the numbers,
including a synthesis bug this staged config actually hit
(`SYNTH_PARAMETERS`/`chparam` did not propagate `DATA_WIDTH=4` correctly
under this repo's Yosys/OpenLane versions — worked around with a wrapper
module, not by editing the shared RTL). The sequential-schedule axis
remains out of scope, unchanged from this sprint's decision.

## Acceptance criteria (self-check against sprint_06)

- [x] One technique chosen and justified (INT8 -> INT4, 4-way-parallel
      schedule held constant)
- [x] Baseline vs optimized protocols are comparable: same PDK
      (staged), same OpenLane major version (staged), same golden-model
      *method* (symmetric quantization) — width is exactly what the
      experiment varies
- [x] Optimized RTL matches its Python model: 25/25 bit-exact
      (`verification/tb_accelerator_int4.sv`)
- [x] No fabricated percentage claims — `results/comparison.csv`'s
      numeric PPA columns for `int4_parallel` remain blank
