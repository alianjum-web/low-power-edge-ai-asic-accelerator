// Version 1 accelerator top: NUM_NEURONS processing_elements (each holding
// its own NUM_INPUTS-deep weight column), a shared activation buffer
// broadcast to every PE, per-neuron bias registers, the controller FSM,
// and one requantize stage per neuron.
//
//   y_j = requantize( ReLU( sum_i x_i * w_ij + b_j ) ),  j = 0 .. NUM_NEURONS-1
//
// bit-exact with algorithm/reference_model.forward() given the same x, W
// (row-major, W[i][j] is input i's weight into neuron j), b, and shift.
// See docs/architecture_spec.md for the full port list, FSM/timing, and
// memory map -- this header only summarizes it.
//
// Buffers deliberately do NOT live in separate buffers.sv / accumulator.sv
// files: each PE's weight column is its own register array (see
// processing_element.sv), the activation buffer and bias registers live
// here in accelerator_top, and the accumulator is folded into each PE.
// This folding is intentional and documented, not an omission (see
// docs/architecture_spec.md "Module hierarchy").
module accelerator_top #(
    parameter int DATA_WIDTH  = 8,   // INT8 x / w / y
    parameter int NUM_INPUTS  = 8,   // dot-product length per neuron
    parameter int NUM_NEURONS = 4,   // number of PEs / outputs
    parameter int ACC_WIDTH   = 32,  // INT32 accumulator / bias
    parameter int SHIFT_WIDTH = 5    // requantize shift, 0..31
)(
    input  logic clk,
    input  logic rst_n,
    input  logic start,

    // Weight memory map: write one INT8 weight per cycle at (pe, idx).
    // weight[pe][idx] is neuron `pe`'s weight for input `idx`, i.e. w_{idx,pe}
    // in the y_j formula above. Writes take effect immediately (edge
    // triggered); the host must only write while busy == 0.
    input  logic                              weight_wr_en,
    input  logic [$clog2(NUM_NEURONS)-1:0]    weight_wr_pe,
    input  logic [$clog2(NUM_INPUTS)-1:0]     weight_wr_idx,
    input  logic signed [DATA_WIDTH-1:0]      weight_wr_data,

    // Activation memory map: write one INT8 activation per cycle at idx.
    // Shared by every PE (broadcast), not per-PE.
    input  logic                              act_wr_en,
    input  logic [$clog2(NUM_INPUTS)-1:0]     act_wr_idx,
    input  logic signed [DATA_WIDTH-1:0]      act_wr_data,

    // Bias memory map: one signed INT32 bias per neuron.
    input  logic                              bias_wr_en,
    input  logic [$clog2(NUM_NEURONS)-1:0]    bias_wr_pe,
    input  logic signed [ACC_WIDTH-1:0]       bias_wr_data,

    // Requantize output scale S = 2**shift_in, shared by all neurons.
    // Must be held stable through the cycle(s) y_out is read.
    input  logic [SHIFT_WIDTH-1:0]            shift_in,

    output logic                              busy,
    output logic                              done,

    // Four INT8 outputs read out in parallel (not streamed), packed
    // low-to-high: y_out[(j+1)*DATA_WIDTH-1 -: DATA_WIDTH] is neuron j's
    // signed INT8 output. Valid and held stable while done == 1.
    output logic [NUM_NEURONS*DATA_WIDTH-1:0] y_out
);

    localparam int IN_IDX_W = $clog2(NUM_INPUTS);
    localparam int PE_IDX_W = $clog2(NUM_NEURONS);

    // ---------------------------------------------------------------
    // Controller
    // ---------------------------------------------------------------
    logic [IN_IDX_W-1:0] mac_idx;
    logic acc_clear, mac_en;

    controller #(
        .NUM_MACS(NUM_INPUTS)
    ) u_controller (
        .clk      (clk),
        .rst_n    (rst_n),
        .start    (start),
        .mac_idx  (mac_idx),
        .acc_clear(acc_clear),
        .mac_en   (mac_en),
        .busy     (busy),
        .done     (done)
    );

    // ---------------------------------------------------------------
    // Activation buffer (shared, broadcast to every PE)
    // ---------------------------------------------------------------
    logic signed [DATA_WIDTH-1:0] act_mem [0:NUM_INPUTS-1];

    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            for (int i = 0; i < NUM_INPUTS; i++) act_mem[i] <= '0;
        end else if (act_wr_en) begin
            act_mem[act_wr_idx] <= act_wr_data;
        end
    end

    logic signed [DATA_WIDTH-1:0] x_broadcast;
    assign x_broadcast = act_mem[mac_idx];

    // ---------------------------------------------------------------
    // Bias registers (one per neuron)
    // ---------------------------------------------------------------
    logic signed [ACC_WIDTH-1:0] bias_mem [0:NUM_NEURONS-1];

    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            for (int p = 0; p < NUM_NEURONS; p++) bias_mem[p] <= '0;
        end else if (bias_wr_en) begin
            bias_mem[bias_wr_pe] <= bias_wr_data;
        end
    end

    // ---------------------------------------------------------------
    // Processing elements + per-neuron requantize
    // ---------------------------------------------------------------
    genvar p;
    generate
        for (p = 0; p < NUM_NEURONS; p++) begin : gen_pe
            logic pe_weight_wr_en;
            logic signed [ACC_WIDTH-1:0] pe_acc;

            assign pe_weight_wr_en = weight_wr_en && (weight_wr_pe == PE_IDX_W'(p));

            processing_element #(
                .DATA_WIDTH (DATA_WIDTH),
                .NUM_WEIGHTS(NUM_INPUTS),
                .ACC_WIDTH  (ACC_WIDTH)
            ) u_pe (
                .clk           (clk),
                .rst_n         (rst_n),
                .weight_wr_en  (pe_weight_wr_en),
                .weight_wr_idx (weight_wr_idx),
                .weight_wr_data(weight_wr_data),
                .acc_clear     (acc_clear),
                .mac_en        (mac_en),
                .mac_idx       (mac_idx),
                .x_in          (x_broadcast),
                .bias_in       (bias_mem[p]),
                .acc_out       (pe_acc)
            );

            requantize #(
                .ACC_WIDTH  (ACC_WIDTH),
                .OUT_WIDTH  (DATA_WIDTH),
                .SHIFT_WIDTH(SHIFT_WIDTH)
            ) u_requant (
                .acc_in  (pe_acc),
                .shift_in(shift_in),
                .y_out   (y_out[(p+1)*DATA_WIDTH-1 -: DATA_WIDTH])
            );
        end
    endgenerate

endmodule
