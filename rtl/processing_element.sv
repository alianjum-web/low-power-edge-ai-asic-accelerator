// One accelerator neuron: a full weight COLUMN (NUM_WEIGHTS independent
// signed registers -- never a single shared register, see
// docs/sprints/sprint_02_hardware_architecture_and_rtl.md "classic bug"),
// a signed INT8 x INT8 multiply, and a signed accumulator that is
// preloaded with this neuron's bias and then summed over one broadcast
// activation per cycle for NUM_WEIGHTS cycles:
//
//   acc = bias_in; repeat (i = 0..NUM_WEIGHTS-1): acc += x_in[i] * weight[i]
//
// which is bit-exact with algorithm/reference_model.py's
// `dense_int8()` (x @ W + b) for this neuron's column, given the same
// operands in the same order. Controlled by rtl/controller.sv, which
// drives acc_clear/mac_en/mac_idx identically to every PE in parallel.
module processing_element #(
    parameter int DATA_WIDTH  = 8,   // x / w bit width (signed)
    parameter int NUM_WEIGHTS = 8,   // dot-product length (weight column size)
    parameter int ACC_WIDTH   = 32   // accumulator / bias width (signed)
)(
    input  logic clk,
    input  logic rst_n,

    // Weight column write port -- one weight register written per cycle,
    // NOT one register for all eight (see module header).
    input  logic                             weight_wr_en,
    input  logic [$clog2(NUM_WEIGHTS)-1:0]   weight_wr_idx,
    input  logic signed [DATA_WIDTH-1:0]     weight_wr_data,

    // Control, shared/broadcast from controller.sv to every PE.
    input  logic                             acc_clear,   // acc <= bias_in
    input  logic                             mac_en,      // acc += x_in * weight[mac_idx]
    input  logic [$clog2(NUM_WEIGHTS)-1:0]   mac_idx,

    // Datapath.
    input  logic signed [DATA_WIDTH-1:0]     x_in,        // broadcast activation x_i
    input  logic signed [ACC_WIDTH-1:0]      bias_in,

    output logic signed [ACC_WIDTH-1:0]      acc_out
);

    logic signed [DATA_WIDTH-1:0] weight [0:NUM_WEIGHTS-1];
    logic signed [ACC_WIDTH-1:0]  acc;

    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            for (int i = 0; i < NUM_WEIGHTS; i++) weight[i] <= '0;
        end else if (weight_wr_en) begin
            weight[weight_wr_idx] <= weight_wr_data;
        end
    end

    logic signed [2*DATA_WIDTH-1:0] product;
    logic signed [ACC_WIDTH-1:0]    product_ext;

    assign product = x_in * weight[mac_idx];

    // Deliberate sign-extension of the DATA_WIDTH*2-bit product up to
    // ACC_WIDTH bits (both signed) -- see rtl/mac_core.sv for the same
    // pattern and rationale.
    /* verilator lint_off WIDTHEXPAND */
    assign product_ext = product;
    /* verilator lint_on WIDTHEXPAND */

    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            acc <= '0;
        end else if (acc_clear) begin
            acc <= bias_in;
        end else if (mac_en) begin
            acc <= acc + product_ext;
        end
    end

    assign acc_out = acc;

endmodule
