#!/usr/bin/env python3

import numpy as np


INT8_MIN = -128
INT8_MAX = 127


def quantize_symmetric(x, scale):
    """Quantize floating-point values to signed INT8."""
    q = np.round(x / scale)
    q = np.clip(q, INT8_MIN, INT8_MAX)
    return q.astype(np.int8)


def dequantize(q, scale):
    """Convert signed integer values back to floating point."""
    return q.astype(np.float32) * scale


def dense_int8(x, weights, bias=None):
    """
    Reference INT8 GEMV.

    x:       shape (8,), signed INT8
    weights: shape (8, 4), signed INT8
    bias:    optional shape (4,), INT32

    Returns:
        signed INT32 accumulated outputs
    """
    x32 = x.astype(np.int32)
    w32 = weights.astype(np.int32)

    acc = x32 @ w32

    if bias is not None:
        acc = acc + bias.astype(np.int32)

    return acc


def relu(x):
    """ReLU activation."""
    return np.maximum(x, 0)


def main():
    # Deterministic test input
    x = np.array(
        [10, -20, 30, -40, 50, -60, 70, -80],
        dtype=np.int8
    )

    # 8 inputs x 4 output neurons
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

    acc = dense_int8(x, weights, bias)
    activated = relu(acc)

    print("Input:")
    print(x)

    print("\nWeights:")
    print(weights)

    print("\nINT32 accumulation:")
    print(acc)

    print("\nAfter ReLU:")
    print(activated)


if __name__ == "__main__":
    main()

