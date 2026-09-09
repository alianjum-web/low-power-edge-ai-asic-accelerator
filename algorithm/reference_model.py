#!/usr/bin/env python3
"""Version 1 golden model: 8 inputs -> 4 output neurons -> ReLU -> 4 output
values, requantized to a signed `bits`-wide integer (default INT8):

    y_j = ReLU( sum_i x_i * w_ij + b_j )   requantized to INT`bits`

x: (8,) signed int      W: (8, 4) signed int      b: (4,) signed INT32, optional
x/W/y are INT8 by default (Version 1); pass bits=4 for the Sprint 6 INT4
bit-width-optimization variant (docs/optimization_plan.md) — same GEMV +
bias + ReLU, only the input/output quantization width changes, matching
docs/quantization.md's "INT4 (Phase 4 only)" policy.

The RTL built in later sprints must match these outputs bit-exactly on
the vectors in verification/reference/ (see docs/verification.md).
"""

import numpy as np

from quantization import requantize


def dense_int8(x, weights, bias=None):
    """Reference INT8 GEMV. Returns signed INT32 accumulated outputs.

    Each product x_i * w_ij fits in signed INT16 (max magnitude 128*128 =
    16384 < 32768); the 8-term sum per output fits comfortably in INT32
    (max magnitude 8*16384 = 131072). See docs/quantization.md.
    """
    x32 = np.asarray(x).astype(np.int32)
    w32 = np.asarray(weights).astype(np.int32)

    acc = x32 @ w32

    if bias is not None:
        acc = acc + np.asarray(bias).astype(np.int32)

    return acc


def relu(x):
    """ReLU activation."""
    return np.maximum(x, 0)


def forward(x, weights, bias=None, shift=0, bits=8):
    """Full Version 1 pipeline: GEMV -> bias -> ReLU -> requantize.

    Returns (acc_int32, y). `shift` is the per-layer output scale
    (S = 2**shift) documented in algorithm/README.md; shift=0 means the
    accumulator is saturated without scaling. `bits` selects the output
    (and, by convention, x/weight) quantization width -- 8 for Version 1
    INT8, 4 for the Sprint 6 INT4 optimization variant.
    """
    acc = dense_int8(x, weights, bias)
    activated = relu(acc)
    y = requantize(activated, shift, bits=bits)
    return acc, y


def main():
    # Deterministic smoke-test input (all outputs land at 0 post-ReLU —
    # a legitimate case, but see generate_vectors.py / tests for cases
    # that actually exercise a non-zero requantized output).
    x = np.array(
        [10, -20, 30, -40, 50, -60, 70, -80],
        dtype=np.int8
    )

    weights = np.array(
        [
            [1,  2,  3,  4],
            [2,  3,  4,  5],
            [3,  4,  5,  6],
            [4,  5,  6,  7],
            [5,  6,  7,  8],
            [6,  7,  8,  9],
            [7,  8,  9, 10],
            [8,  9, 10, 11],
        ],
        dtype=np.int8
    )

    bias = np.zeros(4, dtype=np.int32)

    acc, y = forward(x, weights, bias, shift=0)

    print("Input:")
    print(x)

    print("\nWeights:")
    print(weights)

    print("\nINT32 accumulation (post bias):")
    print(acc)

    print("\nFinal INT8 output (post ReLU + requantize, shift=0):")
    print(y)


if __name__ == "__main__":
    main()
