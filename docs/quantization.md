# Quantization policy

## Version 1 decision

Use **symmetric signed INT8 everywhere** for the first working hardware.

| Tensor | Range |
|---|---|
| Activation | −128 … +127 |
| Weight | −128 … +127 |
| Product | signed 16-bit |
| Accumulator | signed 32-bit |

Zero-point \(Z = 0\) for Version 1.

## Why not the manual’s mixed scheme yet

The manual mixes:

- signed INT8,
- asymmetric unsigned activation quantization (0–255),
- ReLU,
- zero-points,
- signed SystemVerilog datapaths.

Python describing 0–255 activations while RTL is `signed [7:0]` is a bit-exact verification trap. Asymmetric quantization can be a later experiment if it actually contributes to the research question.

## Mapping (symmetric)

\[
x_{\mathrm{int}} = \mathrm{clip}\left(\mathrm{round}\left(\frac{x_{\mathrm{float}}}{S}\right), -2^{n-1}, 2^{n-1}-1\right)
\]

\[
x_{\mathrm{float}} \approx S \cdot x_{\mathrm{int}}
\]

Scale \(S\) is a positive float chosen so the integer range covers the tensor’s observed magnitude. For INT8, \(q_{\max} = 127\).

After INT32 accumulation, requantize back to INT8 with an **offline** per-layer output scale computed in Python (`algorithm/`).

## INT4 (Phase 4 only)

Same symmetric rule with \(n = 4\) (\(q_{\max} = 7\)). Expect smaller multipliers and possible accuracy loss. **Measure** both; do not assume INT4 is better.

## Relation to a tiny MLP (later)

The manual’s software example is Input(8) → Dense(8×4) → ReLU → Dense(4×2) → Output(2). Hardware Version 1 implements the **first GEMV + ReLU** as a closed, verifiable accelerator. A second layer can wait until that datapath is bit-exact and physically closed.
