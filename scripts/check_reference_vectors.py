#!/usr/bin/env python3
"""Check every frozen CSV vector against the Python golden model.

Checks both the Version 1 INT8 vectors and the Sprint 6 INT4 optimization
variant (docs/optimization_plan.md) -- same GEMV/bias/ReLU pipeline, only
the quantization width (and therefore shift) differs.
"""

import csv
import os
import sys

import numpy as np

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(SCRIPT_DIR)
sys.path.insert(0, os.path.join(REPO_ROOT, "algorithm"))

from reference_model import forward


REFERENCE_DIR = os.path.join(REPO_ROOT, "verification", "reference")

VECTOR_SETS = [
    {"name": "INT8", "csv": "vectors.csv", "shift": 8, "bits": 8},
    {"name": "INT4", "csv": "vectors_int4.csv", "shift": 4, "bits": 4},
]


def check(csv_path, shift, bits):
    with open(csv_path, newline="") as vector_file:
        rows = csv.DictReader(vector_file)
        count = 0
        for count, row in enumerate(rows, start=1):
            x = np.array([int(row[f"x{i}"]) for i in range(8)], dtype=np.int8)
            weights = np.array(
                [[int(row[f"w{i}{j}"]) for j in range(4)] for i in range(8)],
                dtype=np.int8,
            )
            bias = np.array([int(row[f"b{j}"]) for j in range(4)], dtype=np.int32)
            expected_acc = np.array(
                [int(row[f"acc{j}"]) for j in range(4)], dtype=np.int32
            )
            expected_y = np.array([int(row[f"y{j}"]) for j in range(4)], dtype=np.int8)

            actual_acc, actual_y = forward(x, weights, bias, shift=shift, bits=bits)
            if not np.array_equal(actual_acc, expected_acc):
                raise AssertionError(f"vector {count}: accumulator mismatch")
            if not np.array_equal(actual_y, expected_y):
                raise AssertionError(f"vector {count}: output mismatch")
    return count


def main():
    for vector_set in VECTOR_SETS:
        csv_path = os.path.join(REFERENCE_DIR, vector_set["csv"])
        count = check(csv_path, vector_set["shift"], vector_set["bits"])
        print(
            f"Reference vectors ({vector_set['name']}): {count}/{count} passed "
            f"(seed=1234, shift={vector_set['shift']})"
        )


if __name__ == "__main__":
    main()