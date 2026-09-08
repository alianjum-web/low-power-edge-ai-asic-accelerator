// Version 1 accelerator control FSM.
//
// States: IDLE -> LOAD -> COMPUTE -> DONE_S.
// ACCUMULATE from the sprint plan's minimum-states list is folded into
// COMPUTE (every COMPUTE cycle both multiplies and accumulates in the same
// cycle inside processing_element.sv), and DONE_S doubles as the "STORE"
// state named in docs/verification.md -- results are held stable on
// accelerator_top's y_out while done=1. See docs/architecture_spec.md
// "FSM" for the full state/mapping table.
module controller #(
    parameter int NUM_MACS = 8   // dot-product length == COMPUTE cycle count
)(
    input  logic clk,
    input  logic rst_n,
    input  logic start,          // pulse (or level) to begin one inference

    output logic [$clog2(NUM_MACS)-1:0] mac_idx,  // broadcast index i, valid while mac_en
    output logic acc_clear,      // 1 cycle in LOAD: PEs preload acc with bias
    output logic mac_en,         // asserted every COMPUTE cycle: PEs MAC-accumulate
    output logic busy,           // state != IDLE
    output logic done            // state == DONE_S; y_out is valid while high
);

    localparam int IDX_WIDTH = $clog2(NUM_MACS);
    localparam logic [IDX_WIDTH-1:0] LAST_IDX = IDX_WIDTH'(NUM_MACS - 1);

    typedef enum logic [1:0] { IDLE, LOAD, COMPUTE, DONE_S } state_t;

    state_t state, next_state;
    logic [IDX_WIDTH-1:0] idx, next_idx;

    always_comb begin
        next_state = state;
        next_idx   = idx;

        case (state)
            IDLE: begin
                next_idx = '0;
                if (start) next_state = LOAD;
            end

            LOAD: begin
                next_state = COMPUTE;
            end

            COMPUTE: begin
                if (idx == LAST_IDX) begin
                    next_state = DONE_S;
                end else begin
                    next_idx = idx + 1'b1;
                end
            end

            DONE_S: begin
                if (!start) next_state = IDLE;
            end

            default: next_state = IDLE;
        endcase
    end

    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            state <= IDLE;
            idx   <= '0;
        end else begin
            state <= next_state;
            idx   <= next_idx;
        end
    end

    assign mac_idx   = idx;
    assign acc_clear = (state == LOAD);
    assign mac_en    = (state == COMPUTE);
    assign busy      = (state != IDLE);
    assign done      = (state == DONE_S);

endmodule
