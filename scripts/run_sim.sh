#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BUILD_DIR="${ROOT_DIR}/verification/simulation"
mkdir -p "${BUILD_DIR}"

if ! command -v iverilog >/dev/null 2>&1; then
    echo "ERROR: iverilog is required for RTL regression." >&2
    echo "Install Icarus Verilog, then rerun scripts/run_sim.sh." >&2
    exit 127
fi

python3 "${ROOT_DIR}/scripts/check_reference_vectors.py"

run_tb() {
    local name="$1"
    shift
    local vvp_path="${BUILD_DIR}/${name}.vvp"
    local vcd_path="${BUILD_DIR}/${name}.vcd"
    echo "=== ${name} ==="
    iverilog -g2012 -o "${vvp_path}" -s "${name}" \
        -DDUMPFILE="\"${vcd_path}\"" "$@"
    vvp "${vvp_path}" +DUMPFILE="${vcd_path}"
}

run_tb adder_8bit_tb \
    "${ROOT_DIR}/verification/tb_adder_8bit.v" "${ROOT_DIR}/rtl/adder_8bit.v"

run_tb tb_processing_element \
    "${ROOT_DIR}/verification/tb_processing_element.sv" \
    "${ROOT_DIR}/rtl/processing_element.sv"

run_tb tb_accelerator \
    "${ROOT_DIR}/verification/tb_accelerator.sv" \
    "${ROOT_DIR}/rtl/accelerator_top.sv" "${ROOT_DIR}/rtl/controller.sv" \
    "${ROOT_DIR}/rtl/processing_element.sv" "${ROOT_DIR}/rtl/requantize.sv"

# Sprint 6 bit-width optimization variant: same RTL, DATA_WIDTH=4 instead
# of 8 (baked into tb_accelerator_int4.sv itself, not passed via -P, to
# keep this a plain iverilog invocation like the run above). See
# docs/optimization_plan.md.
run_tb tb_accelerator_int4 \
    "${ROOT_DIR}/verification/tb_accelerator_int4.sv" \
    "${ROOT_DIR}/rtl/accelerator_top.sv" "${ROOT_DIR}/rtl/controller.sv" \
    "${ROOT_DIR}/rtl/processing_element.sv" "${ROOT_DIR}/rtl/requantize.sv"

if command -v verilator >/dev/null 2>&1; then
    echo "=== Verilator lint (INT8, DATA_WIDTH=8 default) ==="
    verilator --lint-only -Wall --timing \
        --top-module accelerator_top \
        "${ROOT_DIR}/rtl/controller.sv" \
        "${ROOT_DIR}/rtl/processing_element.sv" \
        "${ROOT_DIR}/rtl/requantize.sv" \
        "${ROOT_DIR}/rtl/accelerator_top.sv"

    echo "=== Verilator lint (INT4 variant, DATA_WIDTH=4) ==="
    verilator --lint-only -Wall --timing \
        --top-module accelerator_top \
        -GDATA_WIDTH=4 -GNUM_INPUTS=8 -GNUM_NEURONS=4 -GACC_WIDTH=32 -GSHIFT_WIDTH=5 \
        "${ROOT_DIR}/rtl/controller.sv" \
        "${ROOT_DIR}/rtl/processing_element.sv" \
        "${ROOT_DIR}/rtl/requantize.sv" \
        "${ROOT_DIR}/rtl/accelerator_top.sv"
else
    echo "NOTICE: verilator not installed; lint step skipped."
fi

echo "RTL regression passed. Waveforms are in verification/simulation/."
