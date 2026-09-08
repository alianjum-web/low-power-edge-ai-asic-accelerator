// Unit testbench for rtl/processing_element.sv: eight independent weight
// registers (not one shared register), signed sequential MAC over
// i = 0..NUM_WEIGHTS-1, bias preload via acc_clear. See
// docs/verification.md Level 2 and docs/architecture_spec.md.
`ifndef DUMPFILE
`define DUMPFILE "tb_processing_element.vcd"
`endif

module tb_processing_element;

    localparam int DATA_WIDTH  = 8;
    localparam int NUM_WEIGHTS = 8;
    localparam int ACC_WIDTH   = 32;
    localparam int IDX_W       = $clog2(NUM_WEIGHTS);

    logic clk, rst_n;
    logic weight_wr_en;
    logic [IDX_W-1:0] weight_wr_idx;
    logic signed [DATA_WIDTH-1:0] weight_wr_data;
    logic acc_clear, mac_en;
    logic [IDX_W-1:0] mac_idx;
    logic signed [DATA_WIDTH-1:0] x_in;
    logic signed [ACC_WIDTH-1:0] bias_in;
    logic signed [ACC_WIDTH-1:0] acc_out;

    processing_element #(
        .DATA_WIDTH (DATA_WIDTH),
        .NUM_WEIGHTS(NUM_WEIGHTS),
        .ACC_WIDTH  (ACC_WIDTH)
    ) dut (
        .clk           (clk),
        .rst_n         (rst_n),
        .weight_wr_en  (weight_wr_en),
        .weight_wr_idx (weight_wr_idx),
        .weight_wr_data(weight_wr_data),
        .acc_clear     (acc_clear),
        .mac_en        (mac_en),
        .mac_idx       (mac_idx),
        .x_in          (x_in),
        .bias_in       (bias_in),
        .acc_out       (acc_out)
    );

    always #5 clk = ~clk;

    int pass_count = 0;
    int fail_count = 0;

    task automatic write_weight(int idx, int val);
        @(posedge clk);
        #1;
        weight_wr_idx  = IDX_W'(idx);
        weight_wr_data = DATA_WIDTH'(val);
        weight_wr_en   = 1;
        @(posedge clk);
        #1;
        weight_wr_en = 0;
    endtask

    // Shared stimulus buffer for run_dot_product() -- iverilog does not
    // support unpacked-array task ports, so the caller fills this array
    // before calling instead of passing it as an argument.
    int rdp_x [0:NUM_WEIGHTS-1];

    // Drives one full LOAD+COMPUTE sequence: preload acc with bias, then
    // MAC rdp_x[i] against weight[i] for i = 0..NUM_WEIGHTS-1, one per cycle.
    task automatic run_dot_product(int bias);
        bias_in = ACC_WIDTH'(bias);
        @(posedge clk);
        #1;
        acc_clear = 1;
        @(posedge clk);
        #1;
        acc_clear = 0;
        for (int i = 0; i < NUM_WEIGHTS; i++) begin
            mac_idx = IDX_W'(i);
            x_in    = DATA_WIDTH'(rdp_x[i]);
            mac_en  = 1;
            @(posedge clk);
            #1;
        end
        mac_en = 0;
    endtask

    initial begin
        clk = 0; rst_n = 0;
        weight_wr_en = 0; weight_wr_idx = 0; weight_wr_data = 0;
        acc_clear = 0; mac_en = 0; mac_idx = 0; x_in = 0; bias_in = 0;

        #20 rst_n = 1;
        #10;

        // ---- Test 1: eight distinct weights are held independently ----
        // (the "classic bug: one weight_reg per PE instead of eight" this
        // project's docs warn about -- verify all eight survive together,
        // not just the last write.)
        $display("Test 1: Eight independent weight registers");
        for (int i = 0; i < NUM_WEIGHTS; i++) write_weight(i, 10*(i+1));
        begin
            int all_ok;
            all_ok = 1;
            for (int i = 0; i < NUM_WEIGHTS; i++) begin
                if ($signed(dut.weight[i]) !== 10*(i+1)) all_ok = 0;
            end
            if (all_ok) begin
                $display("  PASS: weight[0..7] = 10,20,...,80 all retained");
                pass_count++;
            end else begin
                $display("  FAILED: not all eight weight registers held their value");
                fail_count++;
            end
        end

        // ---- Test 2: dot product with positive bias, all-ones x -------
        $display("Test 2: acc = bias + sum(x_i * w_i), x = all ones");
        begin
            int expected;
            for (int i = 0; i < 8; i++) rdp_x[i] = 1;
            expected = 0;
            for (int i = 0; i < 8; i++) expected += 10*(i+1);
            expected += 5;    // bias = 5
            run_dot_product(5);
            #1;
            $display("  acc_out = %0d (expected %0d)", acc_out, expected);
            if (acc_out !== expected) begin $display("  FAILED"); fail_count++; end
            else begin $display("  PASS"); pass_count++; end
        end

        // ---- Test 3: signed cross-sign product, negative bias ---------
        $display("Test 3: signed cross-sign products with negative bias");
        for (int i = 0; i < NUM_WEIGHTS; i++) write_weight(i, -5);
        begin
            int expected;
            for (int i = 0; i < 8; i++) rdp_x[i] = 3;
            expected = -100 + 8*(3 * -5);   // bias(-100) + 8 * (3 * -5)
            run_dot_product(-100);
            #1;
            $display("  acc_out = %0d (expected %0d)", acc_out, expected);
            if (acc_out !== expected) begin $display("  FAILED"); fail_count++; end
            else begin $display("  PASS"); pass_count++; end
        end

        // ---- Test 4: acc_clear reloads bias mid-stream (new inference) -
        $display("Test 4: acc_clear on a fresh start overwrites the old acc");
        begin
            for (int i = 0; i < 8; i++) rdp_x[i] = 0;
            run_dot_product(777);   // all x=0 -> acc should settle at bias
            #1;
            $display("  acc_out = %0d (expected 777)", acc_out);
            if (acc_out !== 777) begin $display("  FAILED"); fail_count++; end
            else begin $display("  PASS"); pass_count++; end
        end

        $display("----------------------------------------");
        $display("PASSED: %0d  FAILED: %0d", pass_count, fail_count);
        if (fail_count == 0) $display("ALL TESTS PASSED");
        else $display("SOME TESTS FAILED");
        $finish;
    end

    string dfile;
    initial begin
        dfile = `DUMPFILE;
        if ($value$plusargs("DUMPFILE=%s", dfile)) ;
        $dumpfile(dfile);
        $dumpvars(0, tb_processing_element);
    end

endmodule
