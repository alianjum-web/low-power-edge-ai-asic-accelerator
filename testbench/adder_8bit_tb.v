`timescale 1ns/1ps

module adder_8bit_tb;

    reg [7:0] a;
    reg [7:0] b;
    wire [7:0] sum;

    adder_8bit uut (
        .a(a),
        .b(b),
        .sum(sum)
    );

    initial begin

        $dumpfile("adder_8bit.vcd");
        $dumpvars(0, adder_8bit_tb);

        $monitor("Time=%0t | A=%d | B=%d | SUM=%d",
                 $time, a, b, sum);

        a = 8'd10;
        b = 8'd20;
        #10;

        a = 8'd100;
        b = 8'd50;
        #10;

        a = 8'd255;
        b = 8'd1;
        #10;

        a = 8'd0;
        b = 8'd0;
        #10;

        $finish;

    end

endmodule
