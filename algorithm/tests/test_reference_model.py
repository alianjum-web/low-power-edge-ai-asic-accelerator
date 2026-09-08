#!/usr/bin/env python3
"""Known-answer checks for the Version 1 golden model.

Assert-based, no pytest dependency (matches this repo's existing test
style — see docs/baseline_reference.md "Code conventions"). Every
expected value here is hand-computed, not just re-derived from the code
under test. Run: `python3 tests/test_reference_model.py` from `algorithm/`.
"""

import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from reference_model import dense_int8, forward, relu  # noqa: E402
from quantization import requantize_int8, requantize  # noqa: E402


def test_all_zero():
    """Zero input, zero weights, zero bias -> zero everywhere."""
    x = np.zeros(8, dtype=np.int8)
    w = np.zeros((8, 4), dtype=np.int8)
    b = np.zeros(4, dtype=np.int32)

    acc, y = forward(x, w, b, shift=0)

    assert list(acc) == [0, 0, 0, 0]
    assert list(y) == [0, 0, 0, 0]


def test_all_negative_accumulation_clips_to_zero_after_relu():
    """Hand-computed: x_i * w_ij products sum to a negative acc for every
    output column, so ReLU must zero every output regardless of shift.

    x = [10,-20,30,-40,50,-60,70,-80], W column j = [1+j, 2+j, ..., 8+j]
    acc_0 = 10*1 + -20*2 + 30*3 + -40*4 + 50*5 + -60*6 + 70*7 + -80*8
          = 10 - 40 + 90 - 160 + 250 - 360 + 490 - 640 = -360
    """
    x = np.array([10, -20, 30, -40, 50, -60, 70, -80], dtype=np.int8)
    w = np.array(
        [
            [1, 2, 3, 4],
            [2, 3, 4, 5],
            [3, 4, 5, 6],
            [4, 5, 6, 7],
            [5, 6, 7, 8],
            [6, 7, 8, 9],
            [7, 8, 9, 10],
            [8, 9, 10, 11],
        ],
        dtype=np.int8,
    )
    b = np.zeros(4, dtype=np.int32)

    acc, y = forward(x, w, b, shift=0)

    assert list(acc) == [-360, -400, -440, -480]
    assert list(y) == [0, 0, 0, 0]


def test_positive_sum_case():
    """x = 1..8, every weight column all-ones -> acc_j = sum(1..8) = 36."""
    x = np.array([1, 2, 3, 4, 5, 6, 7, 8], dtype=np.int8)
    w = np.ones((8, 4), dtype=np.int8)
    b = np.zeros(4, dtype=np.int32)

    acc, y = forward(x, w, b, shift=0)

    assert list(acc) == [36, 36, 36, 36]
    assert list(y) == [36, 36, 36, 36]


def test_bias_only_case():
    """Zero activations/weights isolates the bias-add + ReLU + requantize
    path: acc == bias, negative bias is zeroed by ReLU, positive bias
    already fits INT8 so requantize (shift=0) passes it through unchanged.
    """
    x = np.zeros(8, dtype=np.int8)
    w = np.zeros((8, 4), dtype=np.int8)
    b = np.array([100, -100, 0, 50], dtype=np.int32)

    acc, y = forward(x, w, b, shift=0)

    assert list(acc) == [100, -100, 0, 50]
    assert list(y) == [100, 0, 0, 50]


def test_int16_product_and_int32_accumulator_do_not_overflow():
    """docs/quantization.md commits to a signed INT16 product and signed
    INT32 accumulator. Verify the declared widths actually hold the
    worst-case INT8 x INT8 GEMV, i.e. this is not just an aspiration.
    """
    INT16_MAX = 32767
    INT32_MAX = 2147483647

    worst_case_product = (-128) * (-128)  # largest-magnitude INT8 product
    assert worst_case_product == 16384
    assert worst_case_product <= INT16_MAX

    worst_case_sum_of_8 = 8 * worst_case_product
    assert worst_case_sum_of_8 == 131072
    assert worst_case_sum_of_8 <= INT32_MAX

    # Same claim, exercised through the real dense_int8 path.
    x = np.full(8, -128, dtype=np.int8)
    w = np.full((8, 4), -128, dtype=np.int8)
    acc = dense_int8(x, w)
    assert list(acc) == [131072, 131072, 131072, 131072]


def test_requantize_saturates_at_int8_bounds():
    """requantize_int8 must clip, not wrap, once shifted values leave
    [-128, 127] — this is the near-overflow case the sprint asks for.
    """
    assert list(requantize_int8(np.array([200]), 0)) == [127]
    assert list(requantize_int8(np.array([-200]), 0)) == [-128]
    assert list(requantize_int8(np.array([127]), 0)) == [127]   # boundary, no clip
    assert list(requantize_int8(np.array([128]), 0)) == [127]   # just past boundary
    assert list(requantize_int8(np.array([-128]), 0)) == [-128]  # boundary, no clip


def test_requantize_shift_rounding():
    """shift>0 divides by 2**shift with round-half-up before clipping.

    acc=200, shift=8: (200 + 128) >> 8 = 328 >> 8 = 1
    acc=1016, shift=8: (1016 + 128) >> 8 = 1144 >> 8 = 4
    """
    assert list(requantize_int8(np.array([200]), 8)) == [1]
    assert list(requantize_int8(np.array([127 * 8]), 8)) == [4]


def test_relu_zeroes_negative_and_passes_positive():
    x = np.array([-5, 0, 5], dtype=np.int32)
    assert list(relu(x)) == [0, 0, 5]


# ---- Sprint 6: INT4 bit-width optimization variant (docs/optimization_plan.md) ----
# Same GEMV/bias/ReLU/requantize pipeline as above, bits=4 instead of the
# default 8. requantize_int8 is unchanged (still bits=8, verified above);
# these exercise the new generic `requantize(..., bits=4)` path instead.


def test_int4_requantize_saturates_at_int4_bounds():
    """bits=4 must clip to [-8, 7], not [-128, 127]."""
    assert list(requantize(np.array([200]), 0, bits=4)) == [7]
    assert list(requantize(np.array([-200]), 0, bits=4)) == [-8]
    assert list(requantize(np.array([7]), 0, bits=4)) == [7]     # boundary, no clip
    assert list(requantize(np.array([8]), 0, bits=4)) == [7]     # just past boundary
    assert list(requantize(np.array([-8]), 0, bits=4)) == [-8]   # boundary, no clip


def test_int4_requantize_shift_rounding():
    """Same round-half-up convention as INT8, just a narrower output clip.

    acc=20, shift=2: (20 + 2) >> 2 = 22 >> 2 = 5
    acc=100, shift=2: (100 + 2) >> 2 = 25 -> clipped to 7
    """
    assert list(requantize(np.array([20]), 2, bits=4)) == [5]
    assert list(requantize(np.array([100]), 2, bits=4)) == [7]


def test_int4_product_and_accumulator_do_not_overflow():
    """Largest-magnitude INT4 x INT4 product and its 8-term sum, same
    headroom argument as the INT8 test above but for n=4 (q_max=7).
    """
    worst_case_product = (-8) * (-8)  # largest-magnitude INT4 product
    assert worst_case_product == 64

    worst_case_sum_of_8 = 8 * worst_case_product
    assert worst_case_sum_of_8 == 512

    x = np.full(8, -8, dtype=np.int8)
    w = np.full((8, 4), -8, dtype=np.int8)
    acc = dense_int8(x, w)
    assert list(acc) == [512, 512, 512, 512]


def test_int4_forward_matches_int8_pipeline_shape():
    """forward(..., bits=4) walks the identical GEMV -> bias -> ReLU path
    as the INT8 default; only the requantize clip range should differ.
    """
    x = np.array([1, 2, 3, 4, 5, 6, 7, -8], dtype=np.int8)
    w = np.ones((8, 4), dtype=np.int8)
    b = np.zeros(4, dtype=np.int32)

    acc, y = forward(x, w, b, shift=0, bits=4)

    assert list(acc) == [20, 20, 20, 20]     # sum(1..7) - 8 = 20, same for every column
    assert list(y) == [7, 7, 7, 7]           # 20 saturates to INT4_MAX


ALL_TESTS = [
    test_all_zero,
    test_all_negative_accumulation_clips_to_zero_after_relu,
    test_positive_sum_case,
    test_bias_only_case,
    test_int16_product_and_int32_accumulator_do_not_overflow,
    test_requantize_saturates_at_int8_bounds,
    test_requantize_shift_rounding,
    test_relu_zeroes_negative_and_passes_positive,
    test_int4_requantize_saturates_at_int4_bounds,
    test_int4_requantize_shift_rounding,
    test_int4_product_and_accumulator_do_not_overflow,
    test_int4_forward_matches_int8_pipeline_shape,
]


def main():
    failures = []
    for test in ALL_TESTS:
        try:
            test()
            print(f"PASS  {test.__name__}")
        except AssertionError as exc:
            failures.append(test.__name__)
            print(f"FAIL  {test.__name__}: {exc}")

    print(f"\n{len(ALL_TESTS) - len(failures)}/{len(ALL_TESTS)} passed")
    if failures:
        sys.exit(1)


if __name__ == "__main__":
    main()
