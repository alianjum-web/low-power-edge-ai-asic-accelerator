#!/usr/bin/env python3
"""Symmetric signed INT8 quantize / dequantize / requantize.

Policy (docs/quantization.md): symmetric signed quantization, zero-point
Z = 0, for activations, weights, and outputs. Do not mix this with
asymmetric unsigned (0-255) activations.
"""

import numpy as np

INT8_MIN = -128
INT8_MAX = 127

INT16_MIN = -32768
INT16_MAX = 32767

INT32_MIN = -2147483648
INT32_MAX = 2147483647


def quantize_symmetric(x, scale):
    """Quantize floating-point values to signed INT8 with scale S.

    q = clip(round(x / S), -128, 127)
    """
    q = np.round(np.asarray(x, dtype=np.float64) / scale)
    q = np.clip(q, INT8_MIN, INT8_MAX)
    return q.astype(np.int8)


def dequantize(q, scale):
    """Convert signed integer values back to floating point: x ~= S * q."""
    return np.asarray(q).astype(np.float64) * scale


def requantize_int8(acc, shift):
    """Requantize an INT32 accumulator down to signed INT8.

    Uses a power-of-two output scale (S = 2**shift), matching a
    hardware-friendly arithmetic right-shift with round-half-up — the
    convention the RTL requantize stage must reproduce bit-exactly
    (Sprint 3). shift=0 is a pass-through with saturation only.
    """
    acc = np.asarray(acc, dtype=np.int64)
    if shift > 0:
        rounding = 1 << (shift - 1)
        shifted = (acc + rounding) >> shift
    else:
        shifted = acc
    return np.clip(shifted, INT8_MIN, INT8_MAX).astype(np.int8)
