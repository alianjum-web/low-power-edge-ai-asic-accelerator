# Algorithm (Python golden model)

Phase 1, complete for Version 1. Files:

| File | Role |
|---|---|
| `reference_model.py` | 8x4 INT8 GEMV + bias + ReLU + requantize (`forward()`) |
| `quantization.py` | Symmetric signed quantize / dequantize / requantize |
| `generate_vectors.py` | Deterministic (seeded) weights, biases, inputs -> `verification/reference/vectors.{csv,hex}` |
| `tests/test_reference_model.py` | Hand-computed known-answer checks (zeros, negatives, bias-only, near-overflow, saturation) |
| `baseline_results.csv` | Op count, bit widths, latency target, expected hardware resources |

Version 1 policy: **symmetric signed INT8**, zero-point 0. See [docs/quantization.md](../docs/quantization.md).

Output requantize uses a power-of-two shift (`S = 2**shift`), documented per
call site: `shift=0` (pass-through + saturate) for the small hand-computed
test cases, `shift=8` for `generate_vectors.py`'s full-INT8-range random
vectors so they don't all trivially saturate to +-127. RTL must reproduce
this shift-and-round-half-up convention bit-exactly (Sprint 3) — see
`quantization.requantize_int8`.

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
python3 tests/test_reference_model.py # 8 known-answer checks
python3 generate_vectors.py           # regenerate verification/reference/vectors.{csv,hex}
```
