`timescale 1ns/1ps

module tb_mac_unit;

    logic signed [7:0]  a;
    logic signed [7:0]  b;
    logic signed [31:0] acc_in;
    logic signed [31:0] acc_out;

    mac_unit dut (
        .a(a),
        .b(b),
        .acc_in(acc_in),
        .acc_out(acc_out)
    );

    initial begin
        acc_in = 0;

        a = 10;  b = 1;   #1;
        $display("Test 1: %0d * %0d + %0d = %0d", a, b, acc_in, acc_out);

        a = -20; b = 3;   #1;
        $display("Test 2: %0d * %0d + %0d = %0d", a, b, acc_in, acc_out);

        a = -128; b = -128; #1;
        $display("Test 3: %0d * %0d + %0d = %0d", a, b, acc_in, acc_out);

        a = 127; b = 127; #1;
        $display("Test 4: %0d * %0d + %0d = %0d", a, b, acc_in, acc_out);

        $finish;
    end

endmodule

