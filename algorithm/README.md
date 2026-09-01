# Algorithm (Python golden model)

Phase 1 lives here. Files to add (not yet implemented):

| File | Role |
|---|---|
| `model.py` | 8×4 INT8 GEMV + ReLU (+ optional second layer later) |
| `quantization.py` | Symmetric signed quantize / dequantize / requantize |
| `generate_vectors.py` | Deterministic weights, biases, inputs → hex/CSV |

Version 1 policy: **symmetric signed INT8**, zero-point 0. See [docs/quantization.md](../docs/quantization.md).

Export the same integers the RTL will consume. Do not mix unsigned 0–255 activations with signed hardware.

Training a toy NumPy MLP is optional for the first bit-exact datapath. A fixed, seeded 8×4 layer is enough to verify MAC → PE → top.
