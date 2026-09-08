// ReLU + power-of-two requantize, bit-exact with
// algorithm/quantization.requantize_int8() composed after algorithm/
// reference_model.relu(): forward() does acc -> relu(acc) -> requantize.
//
//   relu_val = max(0, acc_in)
//   shifted  = shift_in == 0 ? relu_val
//                            : (relu_val + (1 <<< (shift_in-1))) >>> shift_in
//   y_out    = clip(shifted, OUT_MIN, OUT_MAX)
//
// Purely combinational: acc_in must already be the PE's final
// post-bias accumulator (valid the same cycle controller.sv asserts
// done), and shift_in must be held stable while it is read.
module requantize #(
    parameter int ACC_WIDTH   = 32,
    parameter int OUT_WIDTH   = 8,
    parameter int SHIFT_WIDTH = 5    // supports shift_in = 0 .. 31
)(
    input  logic signed [ACC_WIDTH-1:0] acc_in,
    input  logic [SHIFT_WIDTH-1:0]      shift_in,
    output logic signed [OUT_WIDTH-1:0] y_out
);

    localparam signed [OUT_WIDTH-1:0] OUT_MAX = {1'b0, {(OUT_WIDTH-1){1'b1}}}; //  127
    localparam signed [OUT_WIDTH-1:0] OUT_MIN = {1'b1, {(OUT_WIDTH-1){1'b0}}}; // -128

    logic signed [ACC_WIDTH-1:0] relu_val;
    logic signed [ACC_WIDTH-1:0] rounding;
    logic signed [ACC_WIDTH-1:0] shifted;

    // ReLU before requantize (order documented in docs/architecture_spec.md).
    assign relu_val = acc_in[ACC_WIDTH-1] ? '0 : acc_in;

    // Round-half-up arithmetic right shift; shift_in == 0 is pass-through
    // with no rounding term added, matching quantization.requantize_int8.
    assign rounding = (shift_in == '0) ? '0 : (ACC_WIDTH'(1) <<< (shift_in - 1));
    assign shifted  = (shift_in == '0) ? relu_val
                                        : ((relu_val + rounding) >>> shift_in);

    // NOTE: because ReLU runs first (relu_val >= 0 always), `shifted` can
    // never be negative here, so the OUT_MIN branch below is unreachable
    // in this project's Version 1 pipeline -- kept for correctness if
    // this module is ever reused without a preceding ReLU (e.g. a future
    // variant), not because it fires today. Verified in
    // verification/tb_accelerator.sv and the requantize.sv smoke checks
    // referenced in docs/architecture_spec.md.
    always_comb begin
        if (shifted > ACC_WIDTH'(OUT_MAX))
            y_out = OUT_MAX;
        else if (shifted < ACC_WIDTH'(OUT_MIN))
            y_out = OUT_MIN;
        else
            y_out = OUT_WIDTH'(shifted);
    end

endmodule
