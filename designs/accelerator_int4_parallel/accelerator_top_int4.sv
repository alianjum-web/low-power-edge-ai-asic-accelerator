// Synthesis wrapper for the INT4 variant (Sprint 7).
//
// OpenLane's `SYNTH_PARAMETERS` ("DATA_WIDTH=4", i.e. Yosys `hierarchy
// -chparam`) does not propagate correctly through accelerator_top's nested
// generate-based hierarchy (processing_element x4, requantize x4, all
// themselves parameterized) under this repo's Yosys 0.33 / OpenLane v1.0.2
// toolchain: `chparam`'s derived-module caching leaves top-level `y_out`,
// `busy`, and `done` undriven (confirmed with a standalone
// `hierarchy -chparam` run; also crashes yosys outright with `chparam -set`
// + a second `hierarchy` pass, a separate AST-frontend caching bug hit by
// this module's memories). A plain Verilog parameter override through
// instantiation (no chparam involved) does not hit either bug and
// synthesizes cleanly -- see docs/optimization_plan.md.
//
// This wrapper is pure port pass-through; no logic of its own. The
// DESIGN_NAME/top module for this run is `accelerator_top_int4`, not
// `accelerator_top`, purely because of this workaround.
module accelerator_top_int4 (
    input  logic clk,
    input  logic rst_n,
    input  logic start,

    input  logic                 weight_wr_en,
    input  logic [1:0]           weight_wr_pe,
    input  logic [2:0]           weight_wr_idx,
    input  logic signed [3:0]    weight_wr_data,

    input  logic                 act_wr_en,
    input  logic [2:0]           act_wr_idx,
    input  logic signed [3:0]    act_wr_data,

    input  logic                 bias_wr_en,
    input  logic [1:0]           bias_wr_pe,
    input  logic signed [31:0]   bias_wr_data,

    input  logic [4:0]           shift_in,

    output logic                 busy,
    output logic                 done,
    output logic [15:0]          y_out
);

    accelerator_top #(
        .DATA_WIDTH (4)
        // NUM_INPUTS, NUM_NEURONS, ACC_WIDTH, SHIFT_WIDTH stay at their
        // accelerator_top defaults (8, 4, 32, 5) -- identical to
        // accelerator_int8_parallel's controls.
    ) dut (.*);

endmodule
