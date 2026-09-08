# Research methodology

## Question

How does reduced numerical precision and MAC parallelism affect the energy-efficiency, silicon area, timing, latency, and inference accuracy of a small Edge-AI accelerator in SKY130?

## Four-point matrix (Phase 4 only)

| Design | Precision | MAC architecture | Expected *hypothesis* (not a result) |
|---|---|---|---|
| Baseline | INT8 | Sequential | Smallest area, highest latency |
| A | INT8 | 4-way parallel | Higher throughput, more area/power |
| B | INT4 | Sequential | Smaller multiplier; accuracy risk |
| C | INT4 | 4-way parallel | Best throughput-per-area-per-watt *candidate*; largest accuracy risk |

INT4 may shrink the multiplier and switching; it may also degrade accuracy.

Parallel MACs may cut latency; they add hardware and possibly power.

Sequential may look “low power” on a wattmeter and still lose on **energy/inference** if it takes many more cycles.

**We measure the intersection. We do not declare a winner in advance.**

## Controls

- Same PDK (`sky130A` / `sky130_fd_sc_hd`)
- Same OpenLane major version
- Same golden-model method (symmetric quantization unless the experiment *is* asymmetric)
- Change one architectural variable at a time
- Keep the active Version 1 accelerator hierarchy shared when bit-width is the only change; inherited `mac_core` modules are reference-only.

## Evaluation table (fill with measured numbers)

Record for every variant:

- Die area (µm²)
- Max frequency / slack at the chosen `CLOCK_PERIOD`
- Total power (static + dynamic)
- Latency (cycles/inference)
- Throughput (inferences/s)
- Energy/inference (headline)
- Accuracy % (FP32 vs quantized)

Template: `results/comparison.csv`.

## What we do not measure yet

Do not start frequency sweeps, INT4, or paper writing before Version 1 INT8 parallel is bit-exact and physically closed.

## SOP / CV language (fill numbers later)

Template only — replace brackets after Phase 4:

> I designed, implemented, and physically verified a quantized INT8 MAC neural-network accelerator through the open-source ASIC flow (Yosys, OpenROAD, Magic, SkyWater SKY130), from RTL through DRC/LVS-clean GDSII. I ran a controlled four-point study (INT8/INT4 × sequential/parallel), quantifying area, power, latency, energy/inference, and accuracy.

Until those numbers exist, do not use this paragraph as a claim.
