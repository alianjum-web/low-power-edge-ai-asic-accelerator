module edge_ai_accelerator (
    input  logic signed [7:0] x0,
    input  logic signed [7:0] x1,
    input  logic signed [7:0] x2,
    input  logic signed [7:0] x3,
    input  logic signed [7:0] x4,
    input  logic signed [7:0] x5,
    input  logic signed [7:0] x6,
    input  logic signed [7:0] x7,

    output logic signed [31:0] y0,
    output logic signed [31:0] y1,
    output logic signed [31:0] y2,
    output logic signed [31:0] y3
);

    logic signed [31:0] acc0;
    logic signed [31:0] acc1;
    logic signed [31:0] acc2;
    logic signed [31:0] acc3;

    always_comb begin

        acc0 = (x0 * 8'sd1) + (x1 * 8'sd1) +
               (x2 * 8'sd1) + (x3 * 8'sd1) +
               (x4 * 8'sd1) + (x5 * 8'sd1) +
               (x6 * 8'sd1) + (x7 * 8'sd1);

        acc1 = (x0 * -8'sd1) + (x1 * -8'sd1) +
               (x2 * -8'sd1) + (x3 * -8'sd1) +
               (x4 * -8'sd1) + (x5 * -8'sd1) +
               (x6 * -8'sd1) + (x7 * -8'sd1);

        acc2 = (x0 * 8'sd1) + (x1 * 8'sd1) +
               (x2 * 8'sd1) + (x3 * 8'sd1) +
               (x4 * 8'sd1) + (x5 * 8'sd1) +
               (x6 * 8'sd1) + (x7 * 8'sd1);

        acc3 = (x0 * -8'sd1) + (x1 * -8'sd1) +
               (x2 * -8'sd1) + (x3 * -8'sd1) +
               (x4 * -8'sd1) + (x5 * -8'sd1) +
               (x6 * -8'sd1) + (x7 * -8'sd1);

        y0 = (acc0 > 0) ? acc0 : 32'sd0;
        y1 = (acc1 > 0) ? acc1 : 32'sd0;
        y2 = (acc2 > 0) ? acc2 : 32'sd0;
        y3 = (acc3 > 0) ? acc3 : 32'sd0;

    end

endmodule

