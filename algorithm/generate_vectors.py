#!/usr/bin/env python3
"""Generate deterministic INT8 test vectors for RTL bit-exact comparison.

Writes verification/reference/vectors.csv (one row per vector: x, W
flattened row-major, b, INT32 acc, INT8 y) and vectors.hex (one line per
vector, space-separated two's-complement hex bytes, for $readmemh in a
future testbench). Same seed every run -> same vectors every run.
"""

import os

import numpy as np

from reference_model import forward

SEED = 1234
NUM_VECTORS = 5
SHIFT = 8  # 2**8 output scale; keeps full-range INT8 x/w products from
           # saturating to +-127 on every vector. See algorithm/README.md.

OUT_DIR = os.path.join(os.path.dirname(__file__), "..", "verification", "reference")


def to_hex_byte(v):
    return format(int(v) & 0xFF, "02x")


def generate(seed=SEED, num_vectors=NUM_VECTORS, shift=SHIFT):
    rng = np.random.default_rng(seed)
    vectors = []

    for _ in range(num_vectors):
        x = rng.integers(-128, 128, size=8, dtype=np.int32).astype(np.int8)
        w = rng.integers(-128, 128, size=(8, 4), dtype=np.int32).astype(np.int8)
        b = rng.integers(-1000, 1000, size=4, dtype=np.int32)

        acc, y = forward(x, w, b, shift=shift)
        vectors.append((x, w, b, acc, y))

    return vectors


def write_csv(vectors, path):
    header = (
        [f"x{i}" for i in range(8)]
        + [f"w{i}{j}" for i in range(8) for j in range(4)]
        + [f"b{j}" for j in range(4)]
        + [f"acc{j}" for j in range(4)]
        + [f"y{j}" for j in range(4)]
    )

    with open(path, "w") as f:
        f.write(",".join(header) + "\n")
        for x, w, b, acc, y in vectors:
            row = (
                [int(v) for v in x]
                + [int(v) for v in w.flatten()]
                + [int(v) for v in b]
                + [int(v) for v in acc]
                + [int(v) for v in y]
            )
            f.write(",".join(str(v) for v in row) + "\n")


def write_hex(vectors, path):
    with open(path, "w") as f:
        for x, w, b, acc, y in vectors:
            fields = [to_hex_byte(v) for v in x] + [to_hex_byte(v) for v in w.flatten()]
            f.write(" ".join(fields) + "\n")


def main():
    vectors = generate()
    os.makedirs(OUT_DIR, exist_ok=True)

    csv_path = os.path.join(OUT_DIR, "vectors.csv")
    hex_path = os.path.join(OUT_DIR, "vectors.hex")

    write_csv(vectors, csv_path)
    write_hex(vectors, hex_path)

    print(f"Wrote {len(vectors)} vectors (seed={SEED}, shift={SHIFT}) to:")
    print(f"  {csv_path}")
    print(f"  {hex_path}")


if __name__ == "__main__":
    main()
