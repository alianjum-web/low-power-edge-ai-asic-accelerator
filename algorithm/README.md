# Algorithm (Python golden model)

Phase 1, complete for Version 1. `forward()`/`requantize()` also support
the Sprint 6 INT4 bit-width-optimization variant (`bits=4`) — see
[docs/optimization_plan.md](../docs/optimization_plan.md). Files:

| File | Role |
|---|---|
| `reference_model.py` | 8x4 GEMV + bias + ReLU + requantize (`forward(..., bits=8)`); INT8 by default, `bits=4` for the Sprint 6 variant |
| `quantization.py` | Symmetric signed quantize / dequantize / requantize, generic over bit width (`requantize(acc, shift, bits=8)`); `requantize_int8` kept as the `bits=8` alias for existing callers |
| `generate_vectors.py` | Deterministic (seeded) weights, biases, inputs -> `verification/reference/vectors.{csv,hex}` (INT8) and `vectors_int4.{csv,hex}` (INT4) |
| `tests/test_reference_model.py` | Hand-computed known-answer checks: zeros, negatives, bias-only, near-overflow, saturation (INT8 + INT4) |
| `baseline_results.csv` | Op count, bit widths, latency target, expected hardware resources |

Version 1 policy: **symmetric signed INT8**, zero-point 0, with INT4 as
the Sprint 6 optimization axis (same symmetric rule, n=4). See
[docs/quantization.md](../docs/quantization.md).

Output requantize uses a power-of-two shift (`S = 2**shift`), documented per
call site: `shift=0` (pass-through + saturate) for the small hand-computed
test cases, `shift=8` for `generate_vectors.py`'s full-INT8-range random
vectors so they don't all trivially saturate to +-127 (`SHIFT_INT4=4` for
the INT4 vectors, picked the same way at INT4's smaller dynamic range —
see `generate_vectors.py`'s `SHIFT_INT4` comment). RTL must reproduce
this shift-and-round-half-up convention bit-exactly (Sprint 3 for INT8,
Sprint 6 for INT4) — see `quantization.requantize`.

Export the same integers the RTL will consume. Do not mix unsigned 0-255
activations with signed hardware.

Training a toy NumPy MLP is optional and not done here — the fixed, seeded
8x4 layer is enough to verify MAC -> PE -> top. See
[docs/research_question.md](../docs/research_question.md) for what
"accuracy" means before and after a dataset is adopted.

## Run

```bash
cd algorithm
python3 reference_model.py            # smoke test on one hand-picked vector
python3 tests/test_reference_model.py # 12 known-answer checks (8 INT8 + 4 INT4)
python3 generate_vectors.py           # regenerate vectors.{csv,hex} and vectors_int4.{csv,hex}
```
