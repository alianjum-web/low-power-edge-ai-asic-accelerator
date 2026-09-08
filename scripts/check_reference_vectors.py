#!/usr/bin/env python3
"""Check every frozen CSV vector against the Python golden model."""

import csv
import os
import sys

import numpy as np

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(SCRIPT_DIR)
sys.path.insert(0, os.path.join(REPO_ROOT, "algorithm"))

from reference_model import forward


CSV_PATH = os.path.join(REPO_ROOT, "verification", "reference", "vectors.csv")
SHIFT = 8


def main():
    with open(CSV_PATH, newline="") as vector_file:
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

            actual_acc, actual_y = forward(x, weights, bias, shift=SHIFT)
            if not np.array_equal(actual_acc, expected_acc):
                raise AssertionError(f"vector {count}: accumulator mismatch")
            if not np.array_equal(actual_y, expected_y):
                raise AssertionError(f"vector {count}: output mismatch")

    print(f"Reference vectors: {count}/{count} passed (seed=1234, shift={SHIFT})")


if __name__ == "__main__":
    main()