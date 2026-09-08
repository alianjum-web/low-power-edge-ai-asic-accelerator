#!/usr/bin/env python3
"""Generate deterministic INT8/INT4 test vectors for RTL bit-exact comparison.

Writes verification/reference/vectors.csv (one row per vector: x, W
flattened row-major, b, INT32 acc, INT8 y) and vectors.hex (one line per
vector, space-separated two's-complement hex bytes, for $readmemh in a
future testbench), plus the INT4 counterparts vectors_int4.{csv,hex} for
the Sprint 6 bit-width optimization variant (docs/optimization_plan.md).
Same seed every run -> same vectors every run, for both widths.
"""

import os

import numpy as np

from reference_model import forward

SEED = 1234
NUM_VECTORS = 5
SHIFT = 8  # 2**8 output scale; keeps full-range INT8 x/w products from
           # saturating to +-127 on every vector. See algorithm/README.md.

# INT4 variant: same seed/vector count, but its own shift and bias range.
# INT4's worst-case sum-of-8 magnitude is 8*(-8*-8)=512 (vs. INT8's
# 131072), so reusing INT8's +-1000 bias range would let the bias alone
# dominate every accumulator and never actually exercise the GEMV. The
# bias range below (+-4) keeps roughly the same bias:accumulator-headroom
# ratio as the INT8 vectors' 1000:131072 (~1:131). SHIFT_INT4=4 was then
# picked empirically (see docs/optimization_plan.md) so this seed's 5
# vectors span most of the INT4 output range [-8,7] without saturating on
# every vector, mirroring what SHIFT=8 does for the INT8 vectors above.
SHIFT_INT4 = 4
BIAS_RANGE_INT4 = 4  # bias sampled from [-4, 4)

OUT_DIR = os.path.join(os.path.dirname(__file__), "..", "verification", "reference")


def to_hex_byte(v):
    # Always a full two's-complement byte, even for INT4 values (-8..7
    # fits in a byte with room to spare) -- simplest common format, and
    # this file has no consumer yet ($readmemh use is still hypothetical,
    # per the module docstring).
    return format(int(v) & 0xFF, "02x")


def generate(seed=SEED, num_vectors=NUM_VECTORS, shift=SHIFT, bits=8, bias_range=1000):
    """Generate `num_vectors` deterministic (x, W, b, acc, y) tuples.

    `bits` selects the x/W/y quantization width (8 for Version 1 INT8, 4
    for the Sprint 6 INT4 variant); `bias_range` is sampled as
    `rng.integers(-bias_range, bias_range)`, independent of `bits` since
    the bias itself always stays INT32.
    """
    rng = np.random.default_rng(seed)
    qmin, qmax = -(2 ** (bits - 1)), 2 ** (bits - 1) - 1
    vectors = []

    for _ in range(num_vectors):
        x = rng.integers(qmin, qmax + 1, size=8, dtype=np.int32).astype(np.int8)
        w = rng.integers(qmin, qmax + 1, size=(8, 4), dtype=np.int32).astype(np.int8)
        b = rng.integers(-bias_range, bias_range, size=4, dtype=np.int32)

        acc, y = forward(x, w, b, shift=shift, bits=bits)
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
    os.makedirs(OUT_DIR, exist_ok=True)

    vectors = generate()
    csv_path = os.path.join(OUT_DIR, "vectors.csv")
    hex_path = os.path.join(OUT_DIR, "vectors.hex")
    write_csv(vectors, csv_path)
    write_hex(vectors, hex_path)
    print(f"Wrote {len(vectors)} INT8 vectors (seed={SEED}, shift={SHIFT}) to:")
    print(f"  {csv_path}")
    print(f"  {hex_path}")

    vectors_int4 = generate(shift=SHIFT_INT4, bits=4, bias_range=BIAS_RANGE_INT4)
    csv_int4_path = os.path.join(OUT_DIR, "vectors_int4.csv")
    hex_int4_path = os.path.join(OUT_DIR, "vectors_int4.hex")
    write_csv(vectors_int4, csv_int4_path)
    write_hex(vectors_int4, hex_int4_path)
    print(f"Wrote {len(vectors_int4)} INT4 vectors (seed={SEED}, shift={SHIFT_INT4}) to:")
    print(f"  {csv_int4_path}")
    print(f"  {hex_int4_path}")


if __name__ == "__main__":
    main()
