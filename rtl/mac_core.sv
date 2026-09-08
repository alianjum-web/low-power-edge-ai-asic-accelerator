module mac_core #(
    parameter int WIDTH = 8,
    parameter int ARRAY_SIZE = 4
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

    // NOTE (audited 2026-09-07): operand_a/operand_b/a_slice/b_slice are
    // declared `signed` so each WIDTH-bit slice is interpreted as two's
    // complement (this project's quantization policy is symmetric signed
    // INT8, see docs/quantization.md). The caller packs signed values into
    // these flattened unsigned vectors; reinterpreting each slice as
    // `signed` here is what makes the multiply/accumulate below a true
    // signed dot product instead of an unsigned one. See
    // docs/architecture_spec.md "mac_core audit" for before/after vectors.
    localparam int ACC_WIDTH = WIDTH * 2 + $clog2(ARRAY_SIZE);

    typedef enum logic [1:0] { IDLE, ACCUM, DONE_S } state_t;

    state_t state, next_state;
    logic signed [ACC_WIDTH-1:0] accumulator, next_accumulator;
    int unsigned idx, next_idx;
    logic signed [WIDTH*2-1:0] product;
    logic signed [ACC_WIDTH-1:0] product_ext;

    logic signed [WIDTH-1:0] a_slice, b_slice;

    always_comb begin
        a_slice = operand_a[idx*WIDTH +: WIDTH];
        b_slice = operand_b[idx*WIDTH +: WIDTH];
    end

    // Explicit, deliberate sign-extension of the WIDTH*2-bit product up to
    // ACC_WIDTH bits (both sides are `signed`, so this is a true sign
    // extension, not a truncation/reinterpretation bug). The lint_off
    // pragma silences verilator's WIDTHEXPAND, which flags this as a width
    // change without knowing it is the intended sign-extend.
    /* verilator lint_off WIDTHEXPAND */
    assign product_ext = product;
    /* verilator lint_on WIDTHEXPAND */

    always_comb begin
        next_state = state;
        next_accumulator = accumulator;
        next_idx = idx;
        done = 1'b0;
        product = '0;

        case (state)
            IDLE: begin
                next_accumulator = '0;
                next_idx = 0;
                if (start) next_state = ACCUM;
            end

            ACCUM: begin
                product = a_slice * b_slice;
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
    // `overflow` is a legacy unsigned-style heuristic inherited from the
    // baseline (checks for a positive-looking top-2-bit pattern); it is not
    // a correct signed-overflow detector. It is retained as-is (not part
    // of this project's Version 1 datapath, which uses ACC_WIDTH sized
    // with enough headroom that a WIDTH=8/ARRAY_SIZE<=8 signed INT8 dot
    // product cannot overflow -- see docs/architecture_spec.md "Overflow
    // policy"). Do not rely on this flag for signed overflow detection.
    assign overflow = (accumulator != '0) && (accumulator[ACC_WIDTH-1:ACC_WIDTH-2] == 2'b01);
    assign zero     = (accumulator == '0);

endmodule
