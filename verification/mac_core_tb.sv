// OpenMAC-PD testbench
//
// Parameters WIDTH and ARRAY_SIZE are read from iverilog command line:
//   iverilog ... -P mac_core_tb.WIDTH=16 -P mac_core_tb.ARRAY_SIZE=8
// or vvp runtime plusargs (consumed in the initial block below).
//
// Use +DUMPFILE=path to control waveform output.

`ifndef DUMPFILE
`define DUMPFILE "mac_core_tb.vcd"
`endif

module mac_core_tb #(
    parameter int WIDTH     = 8,
    parameter int ARRAY_SIZE = 4
);
    parameter int ACC_WIDTH = WIDTH * 2 + (ARRAY_SIZE > 1 ? $clog2(ARRAY_SIZE) : 0);

    logic                           clk;
    logic                           rst_n;
    logic                           start;
    logic [WIDTH*ARRAY_SIZE-1:0]    operand_a;
    logic [WIDTH*ARRAY_SIZE-1:0]    operand_b;
    logic [ACC_WIDTH-1:0]           result;
    logic                           done;
    logic                           overflow;
    logic                           zero;

    mac_core #(
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

    // 10 ns clock (5 ns half period)
    always #5 clk = ~clk;

    task set_operand(int idx, logic [WIDTH-1:0] a, logic [WIDTH-1:0] b);
        operand_a[idx*WIDTH +: WIDTH] = a;
        operand_b[idx*WIDTH +: WIDTH] = b;
    endtask

    longint expected;
    int pass_count;
    int fail_count;
    int i;

    initial begin
        $display("Starting MAC Core Testbench");
        $display("WIDTH=%0d, ARRAY_SIZE=%0d", WIDTH, ARRAY_SIZE);
        $display("----------------------------------------");

        clk = 0;
        rst_n = 0;
        start = 0;
        operand_a = 0;
        operand_b = 0;
        pass_count = 0;
        fail_count = 0;

        #20 rst_n = 1;
        #10;

        // ---- Test 1: basic accumulation ----------------------------
        $display("Test 1: Basic accumulation");
        for (i = 0; i < ARRAY_SIZE; i++) begin
            set_operand(i, i+2, i+1);
        end
        expected = 0;
        for (i = 0; i < ARRAY_SIZE; i++) expected += (i+2)*(i+1);
        start = 1;
        #10 start = 0;
        @(posedge done);
        #1;
        $display("  result = %0d (expected %0d)", result, expected);
        if (result !== expected) begin $display("  FAILED"); fail_count++; end
        else begin $display("  PASS"); pass_count++; end
        #20;

        // ---- Test 2: all zeros ------------------------------------
        $display("Test 2: All zeros");
        operand_a = 0;
        operand_b = 0;
        start = 1;
        #10 start = 0;
        @(posedge done);
        #1;
        $display("  result = %0d (expected 0)", result);
        if (result !== 0) begin $display("  FAILED"); fail_count++; end
        else begin $display("  PASS"); pass_count++; end
        $display("  zero flag = %b (expected 1)", zero);
        if (zero !== 1'b1) begin $display("  FAILED (zero flag)"); fail_count++; end
        else begin pass_count++; end
        #20;

        // ---- Test 3: most-negative values (signed) -----------------
        // Audited 2026-09-07: this project's operands are signed INT8
        // (docs/quantization.md), so the "extreme value" boundary case is
        // the most-negative representable value, not the unsigned
        // all-ones pattern. INT_MIN * INT_MIN is the largest-magnitude
        // product a signed dot product of this width can produce.
        $display("Test 3: Most-negative values (signed boundary)");
        begin
            logic [WIDTH-1:0] min_bits;
            longint min_signed;
            min_bits = {1'b1, {(WIDTH-1){1'b0}}};   // 1000...0 = -2^(WIDTH-1)
            min_signed = -(longint'(1) << (WIDTH-1));
            for (i = 0; i < ARRAY_SIZE; i++) set_operand(i, min_bits, min_bits);
            expected = 0;
            for (i = 0; i < ARRAY_SIZE; i++) expected += min_signed * min_signed;
            start = 1;
            #10 start = 0;
            @(posedge done);
            #1;
            $display("  result = %0d (expected %0d)", $signed(result), expected);
            if ($signed(result) !== expected) begin $display("  FAILED"); fail_count++; end
            else begin $display("  PASS"); pass_count++; end
            #20;
        end

        // ---- Test 4: single non-zero element ----------------------
        $display("Test 4: Single non-zero element");
        operand_a = 0;
        operand_b = 0;
        set_operand(0, 42, 3);
        start = 1;
        #10 start = 0;
        @(posedge done);
        #1;
        $display("  result = %0d (expected 126)", result);
        if (result !== 126) begin $display("  FAILED"); fail_count++; end
        else begin $display("  PASS"); pass_count++; end
        #20;

        // ---- Test 6: signed cross-sign product ----------------------
        // Direct evidence the audited signed fix is wired correctly:
        // a negative times a positive operand must produce a negative
        // result, which is impossible to get right by accident with
        // unsigned multiply.
        $display("Test 6: Signed cross-sign product (-5 * 3, summed)");
        operand_a = 0;
        operand_b = 0;
        begin
            logic [WIDTH-1:0] neg5, three;
            neg5  = WIDTH'(0) - WIDTH'(5);   // two's complement -5, any WIDTH
            three = WIDTH'(3);
            set_operand(0, neg5, three);
        end
        start = 1;
        #10 start = 0;
        @(posedge done);
        #1;
        $display("  result = %0d (expected -15)", $signed(result));
        if ($signed(result) !== -15) begin $display("  FAILED"); fail_count++; end
        else begin $display("  PASS"); pass_count++; end
        #20;

        // ---- Test 5: zero flag after reset ------------------------
        $display("Test 5: Zero flag after fresh accumulation");
        operand_a = 0;
        operand_b = 0;
        start = 1;
        #10 start = 0;
        @(posedge done);
        #1;
        $display("  zero flag = %b (expected 1)", zero);
        if (zero !== 1'b1) begin $display("  FAILED"); fail_count++; end
        else begin $display("  PASS"); pass_count++; end
        #20;

        // ---- Summary ----------------------------------------------
        $display("----------------------------------------");
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
        $dumpvars(0, mac_core_tb);
    end

endmodule
