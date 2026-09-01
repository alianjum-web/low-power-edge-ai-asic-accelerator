#!/usr/bin/env bash
# Simulate the Experiment 0 combinational 8-bit adder with Icarus Verilog.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT/verification"
iverilog -g2012 -o adder_8bit_tb.vvp tb_adder_8bit.v ../rtl/adder_8bit.v
vvp adder_8bit_tb.vvp
rm -f adder_8bit_tb.vvp
