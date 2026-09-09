#!/usr/bin/env python3
"""Synthetic FP32-vs-quantized accuracy measurement (Sprint 7).

No real dataset has been adopted for this project yet (see
algorithm/README.md's note on what "accuracy" means "before and after a
dataset is adopted", and docs/optimization_plan.md's "Deferred to Sprint
7 or later" list). This script measures what CAN be honestly measured
today: given the same random float32 activations/weights/bias, how much
does symmetric quantization to INT8 (or INT4) distort
dense_int8 -> ReLU -> requantize's output, relative to running the
identical dot-product + bias + ReLU math in float32 with no quantization
at all.

This is a quantization-noise measurement, not a task-accuracy number
(there is no labeled dataset or classification task here) -- reported as
such, not dressed up as more than it is.

Method:
  - x, W sampled uniform in [-1, 1); b sampled uniform in a smaller
    range (same ~1:131 bias:accumulator-headroom ratio idea as
    generate_vectors.py, scaled to this scheme's units).
  - Static per-tensor symmetric scale: scale = 1 / qmax for both x and
    W (maps the full float sampling range onto the full quantized
    range) -- not data-dependent per-sample, which would be an unusual
    (and easy to accidentally cheat) per-vector rescaling.
  - Quantize x, W with that scale; quantize b into the accumulator's
    units (scale_x * scale_w) directly, matching how bias enters the
    RTL's INT32 accumulator.
  - Run the existing golden dense_int8 -> relu -> requantize pipeline
    (bit-exact with the RTL) to get the quantized output y_q.
  - Dequantize: y_hat = y_q * scale_x * scale_w * 2**shift.
  - Compare y_hat against the float32 ground truth
    y_true = relu(x @ W + b) computed with no quantization anywhere.

Metric: NRMSE = RMSE(y_hat, y_true) / std(y_true); accuracy_pct =
100 * (1 - NRMSE), clipped to [0, 100]. Also reports MAE in the same
float units for a second, more interpretable number.

Uses the same SHIFT/SHIFT_INT4 as generate_vectors.py so the two bit
widths are compared under the same shift convention already frozen for
the RTL vectors, not a shift hand-picked to flatter one variant.
"""

import numpy as np

from generate_vectors import SHIFT, SHIFT_INT4, SEED
from quantization import quantize_symmetric, qrange
from reference_model import forward

NUM_SAMPLES = 2000
NUM_INPUTS = 8
NUM_NEURONS = 4
BIAS_FLOAT_RANGE = 1.0 / 131.0  # mirrors generate_vectors.py's ~1:131 bias:headroom ratio


def run(bits, shift, seed=SEED, num_samples=NUM_SAMPLES):
    rng = np.random.default_rng(seed)
    qmin, qmax = qrange(bits)
    scale_x = 1.0 / qmax
    scale_w = 1.0 / qmax
    scale_acc = scale_x * scale_w
    scale_out = scale_acc * (2 ** shift)

    y_true_all = np.empty((num_samples, NUM_NEURONS))
    y_hat_all = np.empty((num_samples, NUM_NEURONS))

    for n in range(num_samples):
        x_f = rng.uniform(-1.0, 1.0, size=NUM_INPUTS)
        w_f = rng.uniform(-1.0, 1.0, size=(NUM_INPUTS, NUM_NEURONS))
        b_f = rng.uniform(-BIAS_FLOAT_RANGE, BIAS_FLOAT_RANGE, size=NUM_NEURONS)

        y_true_all[n] = np.maximum(x_f @ w_f + b_f, 0.0)

        x_q = quantize_symmetric(x_f, scale_x, bits=bits)
        w_q = quantize_symmetric(w_f, scale_w, bits=bits)
        b_q = np.round(b_f / scale_acc).astype(np.int32)

        _, y_q = forward(x_q, w_q, b_q, shift=shift, bits=bits)
        y_hat_all[n] = y_q.astype(np.float64) * scale_out

    err = y_hat_all - y_true_all
    rmse = float(np.sqrt(np.mean(err ** 2)))
    mae = float(np.mean(np.abs(err)))
    std_true = float(np.std(y_true_all))
    nrmse = rmse / std_true if std_true > 0 else float("nan")
    accuracy_pct = max(0.0, 100.0 * (1.0 - nrmse))

    return {
        "bits": bits,
        "shift": shift,
        "num_samples": num_samples,
        "rmse": rmse,
        "mae": mae,
        "nrmse": nrmse,
        "accuracy_pct": accuracy_pct,
    }


def main():
    print(f"Synthetic FP32-vs-quantized accuracy (seed={SEED}, N={NUM_SAMPLES}, no real dataset)")
    print("Not a task-accuracy number -- see module docstring.\n")
    for bits, shift, label in [(8, SHIFT, "INT8"), (4, SHIFT_INT4, "INT4")]:
        r = run(bits, shift)
        print(f"{label} (bits={bits}, shift={shift}):")
        print(f"  RMSE          = {r['rmse']:.6f}")
        print(f"  MAE           = {r['mae']:.6f}")
        print(f"  NRMSE         = {r['nrmse']:.6f}")
        print(f"  accuracy_pct  = {r['accuracy_pct']:.4f}")
        print()


if __name__ == "__main__":
    main()
