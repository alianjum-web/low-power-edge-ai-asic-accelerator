`ifndef DUMPFILE
`define DUMPFILE "mac_core_pipelined_tb.vcd"
`endif

module mac_core_pipelined_tb #(
    parameter int WIDTH     = 8,
    parameter int ARRAY_SIZE = 4
);
    parameter int ACC_WIDTH = WIDTH * 2 + $clog2(ARRAY_SIZE);

    logic                           clk;
    logic                           rst_n;
    logic                           start;
    logic [WIDTH*ARRAY_SIZE-1:0]    operand_a;
    logic [WIDTH*ARRAY_SIZE-1:0]    operand_b;
    logic signed [ACC_WIDTH-1:0]    result;
    logic                           done;
    logic                           overflow;
    logic                           zero;

    mac_core_pipelined #(
        .WIDTH(WIDTH),
        .ARRAY_SIZE(ARRAY_SIZE)
    ) dut (
        .clk(clk),
        .rst_n(rst_n),
        .start(start),
        .operand_a(operand_a),
        .operand_b(operand_b),
        .result(result),
        .done(done),
        .overflow(overflow),
        .zero(zero)
    );

    always #5 clk = ~clk;

    int pass_count = 0;
    int fail_count = 0;

    task set_operands(input logic [WIDTH-1:0] a, input logic [WIDTH-1:0] b);
        for (int i = 0; i < ARRAY_SIZE; i++) begin
            operand_a[i*WIDTH +: WIDTH] = a;
            operand_b[i*WIDTH +: WIDTH] = b;
        end
    endtask

    task run_and_check(longint expected);
        @(posedge clk);
        start = 1;
        @(posedge clk);
        start = 0;
        wait (done == 1'b1);
        @(posedge clk);
        #1;
        $display("  result = %0d (expected %0d)", result, expected);
        if (result !== expected) begin
            $display("  FAILED");
            fail_count++;
        end else begin
            $display("  PASS");
            pass_count++;
        end
        #20;
    endtask

    initial begin
        $display("Starting MAC Pipelined Testbench");
        $display("WIDTH=%0d, ARRAY_SIZE=%0d", WIDTH, ARRAY_SIZE);
        $display("-----------------------------------");

        clk = 0;
        rst_n = 0;
        start = 0;
        operand_a = 0;
        operand_b = 0;

        #20 rst_n = 1;
        #10;

        $display("Test 1: Basic accumulation (ones)");
        set_operands(1, 1);
        run_and_check(ARRAY_SIZE);

        $display("Test 2: All zeros");
        set_operands(0, 0);
        run_and_check(0);

        // Audited 2026-09-07: signed boundary case (INT_MIN * INT_MIN),
        // not the unsigned all-ones pattern -- see rtl/mac_core.sv header
        // comment and docs/architecture_spec.md.
        $display("Test 3: Most-negative values (signed boundary)");
        begin
            logic [WIDTH-1:0] min_bits;
            longint min_signed;
            min_bits = {1'b1, {(WIDTH-1){1'b0}}};
            min_signed = -(longint'(1) << (WIDTH-1));
            set_operands(min_bits, min_bits);
            run_and_check(ARRAY_SIZE * min_signed * min_signed);
        end

        $display("Test 4: Weighted sum (2 * 3)");
        set_operands(2, 3);
        run_and_check(ARRAY_SIZE * 2 * 3);

        $display("Test 5: Different operands");
        set_operands(5, 7);
        run_and_check(ARRAY_SIZE * 5 * 7);

        // Direct evidence of the signed fix: cross-sign product must be
        // negative (impossible to get right by accident with unsigned).
        $display("Test 6: Signed cross-sign product (-5 * 3)");
        begin
            logic [WIDTH-1:0] neg5, three;
            neg5  = WIDTH'(0) - WIDTH'(5);
            three = WIDTH'(3);
            set_operands(neg5, three);
            run_and_check(ARRAY_SIZE * (-15));
        end

        $display("-----------------------------------");
        $display("PASSED: %0d  FAILED: %0d", pass_count, fail_count);
        if (fail_count == 0)
            $display("ALL TESTS PASSED");
        else
            $display("SOME TESTS FAILED");
        $finish;
    end

    string dfile;
    initial begin
        dfile = `DUMPFILE;
        if ($value$plusargs("DUMPFILE=%s", dfile)) ;
        $dumpfile(dfile);
        $dumpvars(0, mac_core_pipelined_tb);
    end

endmodule
