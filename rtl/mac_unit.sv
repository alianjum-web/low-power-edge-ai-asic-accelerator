module mac_unit (
    input  logic signed [7:0]  a,
    input  logic signed [7:0]  b,
    input  logic signed [31:0] acc_in,
    output logic signed [31:0] acc_out
);

    logic signed [15:0] product;

    assign product = a * b;
    assign acc_out = acc_in + product;

endmodule

