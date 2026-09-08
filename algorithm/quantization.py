#!/usr/bin/env python3
"""Symmetric signed INT8/INT4 quantize / dequantize / requantize.

Policy (docs/quantization.md): symmetric signed quantization, zero-point
Z = 0, for activations, weights, and outputs. Do not mix this with
asymmetric unsigned (0-255) activations. INT8 is the Version 1 format;
INT4 (n=4, q_max=7) is the Sprint 6 bit-width optimization axis — same
symmetric rule, smaller n, per docs/quantization.md "INT4 (Phase 4 only)".
"""

import numpy as np

INT8_MIN = -128
INT8_MAX = 127

INT4_MIN = -8
INT4_MAX = 7

INT16_MIN = -32768
INT16_MAX = 32767

INT32_MIN = -2147483648
INT32_MAX = 2147483647


def qrange(bits):
    """Signed symmetric range for `bits`: (-2**(bits-1), 2**(bits-1) - 1)."""
    return -(2 ** (bits - 1)), 2 ** (bits - 1) - 1


def quantize_symmetric(x, scale, bits=8):
    """Quantize floating-point values to a signed `bits`-wide integer, scale S.

    q = clip(round(x / S), -2**(bits-1), 2**(bits-1) - 1)

    Default bits=8 keeps this bit-exact with the original INT8-only API.
    """
    qmin, qmax = qrange(bits)
    q = np.round(np.asarray(x, dtype=np.float64) / scale)
    q = np.clip(q, qmin, qmax)
    return q.astype(np.int8)


def dequantize(q, scale):
    """Convert signed integer values back to floating point: x ~= S * q."""
    return np.asarray(q).astype(np.float64) * scale


def requantize(acc, shift, bits=8):
    """Requantize an INT32 accumulator down to a signed `bits`-wide integer.

    Uses a power-of-two output scale (S = 2**shift), matching a
    hardware-friendly arithmetic right-shift with round-half-up — the
    convention the RTL requantize stage must reproduce bit-exactly
    (Sprint 3, and Sprint 6 for the INT4 variant of the same module).
    shift=0 is a pass-through with saturation only.
    """
    qmin, qmax = qrange(bits)
    acc = np.asarray(acc, dtype=np.int64)
    if shift > 0:
        rounding = 1 << (shift - 1)
        shifted = (acc + rounding) >> shift
    else:
        shifted = acc
    return np.clip(shifted, qmin, qmax).astype(np.int8)


def requantize_int8(acc, shift):
    """INT8 (bits=8) requantize — kept as its own name for existing callers."""
    return requantize(acc, shift, bits=8)
