`timescale 1ns/1ps

module tb_edge_ai_accelerator;

    logic signed [7:0] x0, x1, x2, x3;
    logic signed [7:0] x4, x5, x6, x7;

    logic signed [31:0] y0, y1, y2, y3;

    edge_ai_accelerator dut (
        .x0(x0),
        .x1(x1),
        .x2(x2),
        .x3(x3),
        .x4(x4),
        .x5(x5),
        .x6(x6),
        .x7(x7),
        .y0(y0),
        .y1(y1),
        .y2(y2),
        .y3(y3)
    );

    initial begin

        x0 = 10;
        x1 = 20;
        x2 = 30;
        x3 = 40;
        x4 = 50;
        x5 = 60;
        x6 = 70;
        x7 = 80;

        #1;

        $display("Input: [%0d, %0d, %0d, %0d, %0d, %0d, %0d, %0d]",
                 x0, x1, x2, x3, x4, x5, x6, x7);

        $display("Output y0 = %0d", y0);
        $display("Output y1 = %0d", y1);
        $display("Output y2 = %0d", y2);
        $display("Output y3 = %0d", y3);

        if (y0 == 360 &&
            y1 == 0 &&
            y2 == 360 &&
            y3 == 0) begin

            $display("PASS: RTL matches Python reference.");

        end else begin

            $display("FAIL: RTL does not match Python reference.");

        end

        $finish;

    end

endmodule
