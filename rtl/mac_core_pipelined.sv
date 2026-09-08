module mac_core_pipelined #(
    parameter int WIDTH = 8,
    parameter int ARRAY_SIZE = 4,
    parameter int PIPELINE_DEPTH = 2
)(
    input  logic                                    clk,
    input  logic                                    rst_n,
    input  logic                                    start,
    input  logic [WIDTH*ARRAY_SIZE-1:0]             operand_a,
    input  logic [WIDTH*ARRAY_SIZE-1:0]             operand_b,
    output logic signed [WIDTH*2+$clog2(ARRAY_SIZE)-1:0] result,
    output logic                                    done,
    output logic                                    overflow,
    output logic                                    zero
);

    // NOTE (audited 2026-09-07): signed fix mirrors rtl/mac_core.sv --
    // see that file's header comment and docs/architecture_spec.md.
    localparam int ACC_WIDTH = WIDTH * 2 + $clog2(ARRAY_SIZE);

    typedef enum logic [1:0] { IDLE, ACCUM, DONE_S } state_t;

    state_t state, next_state;
    logic signed [ACC_WIDTH-1:0] accumulator, next_accumulator;
    int unsigned idx, next_idx;

    logic signed [WIDTH-1:0] a_slice, b_slice;
    logic signed [WIDTH*2-1:0] product;
    logic signed [ACC_WIDTH-1:0] product_ext;

    always_comb begin
        a_slice = operand_a[idx*WIDTH +: WIDTH];
        b_slice = operand_b[idx*WIDTH +: WIDTH];
    end

    generate
        if (PIPELINE_DEPTH >= 1) begin : gen_pipe
            logic signed [WIDTH*2-1:0] pipe [PIPELINE_DEPTH-1:0];
            always_ff @(posedge clk or negedge rst_n) begin
                if (!rst_n) begin
                    for (int p = 0; p < PIPELINE_DEPTH; p++) pipe[p] <= '0;
                end else begin
                    pipe[0] <= a_slice * b_slice;
                    for (int p = 1; p < PIPELINE_DEPTH; p++) pipe[p] <= pipe[p-1];
                end
            end
            assign product = pipe[PIPELINE_DEPTH-1];
        end else begin : gen_nopipe
            assign product = a_slice * b_slice;
        end
    endgenerate

    // Explicit, deliberate sign-extension -- see rtl/mac_core.sv for the
    // identical pattern and rationale.
    /* verilator lint_off WIDTHEXPAND */
    assign product_ext = product;
    /* verilator lint_on WIDTHEXPAND */

    always_comb begin
        next_state = state;
        next_accumulator = accumulator;
        next_idx = idx;
        done = 1'b0;

        case (state)
            IDLE: begin
                next_accumulator = '0;
                next_idx = 0;
                if (start) next_state = ACCUM;
            end

            ACCUM: begin
                next_accumulator = accumulator + product_ext;
                if (idx == ARRAY_SIZE - 1) begin
                    next_state = DONE_S;
                end else begin
                    next_idx = idx + 1;
                end
            end

            DONE_S: begin
                done = 1'b1;
                if (!start) next_state = IDLE;
            end

            default: next_state = IDLE;
        endcase
    end

    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            state <= IDLE;
            accumulator <= '0;
            idx <= 0;
        end else begin
            state <= next_state;
            accumulator <= next_accumulator;
            idx <= next_idx;
        end
    end

    assign result = accumulator;
    // See rtl/mac_core.sv -- same legacy overflow heuristic, same caveat.
    assign overflow = (accumulator != '0) && (accumulator[ACC_WIDTH-1:ACC_WIDTH-2] == 2'b01);
    assign zero     = (accumulator == '0);

endmodule
