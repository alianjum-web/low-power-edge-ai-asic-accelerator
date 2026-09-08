# Baseline reference (inherited SiliconNPU / OpenMAC-PD)

This consolidates the useful technical content that used to live in `docs1/` (the original SiliconNPU baseline's own docs — `README_baseline.md`, `developer_guide.md`, `user_guide.md`, `install_guide.md`, `final_report.md`), merged into this repository on 2026-09-06 and removed after this migration so there is one documentation set instead of two. Every claim below was checked against the files actually in this repo as of the migration date — anything the original docs claimed that could **not** be verified here is labeled as such. See [architecture.md](architecture.md)'s "Baseline" section for how this fits the project's own RTL plan, and [physical_design.md](physical_design.md) for the OpenLane-config caveats.

## Attribution

The baseline RTL, OpenLane flow, and Python tooling (`rtl/mac_core*.sv`, `rtl/silicon_npu.sv`, `flow/`, `openmac/`, `scripts/{bmp2png,dashboard,explore,gen_constraints,parse_reports,render_pil}.py`, `tests/`) originate from the open-source **SiliconNPU** project by **Ansh Verma**, MIT-licensed. No source repository URL was present in the original docs to link back to — only the project name and author are recorded here, as stated in the original `README_baseline.md`'s own "Author" section before it was removed. This project is a modified/extended derivative of that baseline, not original work in those files; see the root [README.md](../README.md) and [LICENSE](../LICENSE) for this project's own terms.

## Known contradiction in the original docs (flagged, not resolved)

The original `README_baseline.md` claimed **"WNS = 0.00 ns, TNS = 0.00 ns"** (perfect timing closure) and **"14 simulation tests, all passing (4 NPU + 5 basic + 5 pipelined)"**. The original `final_report.md` claimed **WNS = −1.50 ns / −0.47 ns, TNS = −7.58 ns / −0.81 ns** (i.e. timing was *not* closed) and **"6/6 RTL sim tests passing"** plus **"34/34 unit tests passing"** (a different count, and for Python unit tests, not RTL sim tests). These two original documents disagree with each other on whether timing closed and on the test count. Both are reproduced below for completeness, but neither should be treated as ground truth until this project re-runs the flow and measures it directly.

## What the baseline actually is

Three RTL modules, inherited as-is (not yet modified):

| File | What it does | Verified by reading the file |
|---|---|---|
| `rtl/mac_core.sv` | Parameterized (`WIDTH`, `ARRAY_SIZE`) dot product: `result = Σ operand_a[i] * operand_b[i]`. FSM `IDLE → ACCUM → DONE_S`, one multiply-accumulate per cycle. Outputs `done`, `overflow`, `zero`. | Yes |
| `rtl/mac_core_pipelined.sv` | Same interface, pipelined multiplier (`PIPELINE_DEPTH` param, per `docs1`). | Not read in detail during this migration — audit before use |
| `rtl/silicon_npu.sv` | Wraps a `weight_mem[DEPTH][ARRAY_SIZE]` / `act_mem[DEPTH][ARRAY_SIZE]` pair (row/col-addressed write ports) around the same MAC idea. **Sums every row and column into one scalar `accumulator`** — it does not produce 4 independent per-neuron outputs. FSM `IDLE → COMPUTE → DONE_S`. | Yes, full file read line-by-line |

**Not implemented anywhere in the baseline:** signed arithmetic (all operands are plain unsigned `logic`), bias add, ReLU, requantize-to-INT8, or multiple independent output accumulators. These are exactly what this project's Version 1 accelerator (`architecture.md`) still needs to add.

## Ports (mac_core.sv / silicon_npu.sv family)

| Port | Direction | Width | Notes |
|---|---|---|---|
| `clk`, `rst_n` | in | 1 | active-low reset |
| `start` | in | 1 | pulse to begin a computation |
| `operand_a`, `operand_b` (mac_core) | in | `WIDTH*ARRAY_SIZE` | flattened vectors, sliced `WIDTH` bits at a time |
| `weight_wr_*`, `act_wr_*` (silicon_npu) | in | see RTL | row/col-addressed memory writes |
| `result` | out | `WIDTH*2+clog2(ARRAY_SIZE)[+clog2(DEPTH)]` | accumulator readout — per the actual `silicon_npu.sv` parameter formula, default `WIDTH=8, ARRAY_SIZE=4, DEPTH=4` gives a **20-bit** result (`16+2+2`), not the "26-bit accumulator" the original `README_baseline.md` diagram claims. Computed from the RTL formula, not re-verified by simulation. |
| `done` | out | 1 | asserted in `DONE_S` |
| `overflow`, `zero` (mac_core only) | out | 1 | see RTL for exact condition |
| `busy` (silicon_npu only) | out | 1 | `state != IDLE` |

Default parameters per the original docs (`user_guide.md` + `README_baseline.md`): `WIDTH=8` (range 4–16), `ARRAY_SIZE=4` (range 2–8), `PIPELINE_DEPTH=2` (range 1–4, pipelined variant only), `DEPTH=4` (range 2–16, `silicon_npu` only — number of memory rows). Not re-verified against RTL parameter defaults during this migration.

## Toolchain and PDK — as used by the original authors, not reproduced here

| Stage | Tool | Version claimed in `docs1` |
|---|---|---|
| Simulation | iverilog | 12.0 |
| Synthesis | Yosys | 0.38 |
| P&R | OpenLane | 1.1.1 |
| P&R | OpenROAD | b16bda7e |
| DRC | Magic | — |
| LVS | Netgen | — |
| PDK | Sky130A | 0fe599b (2024.08.17) |

This project's own `docs/physical_design.md` and `docs/00_project_overview.md` already commit to SKY130 / `sky130_fd_sc_hd` / Yosys / OpenROAD / Magic / Netgen / KLayout / Icarus Verilog, so the stack matches — only exact tool point-versions above are unverified in this environment.

## Baseline OpenLane configs — what's real vs. what needs fixing

`flow/config.tcl` and `flow/openlane_config/*.tcl` are real files, not reconstructed from prose. Checked directly:

| Config | Design | `CLOCK_PERIOD` | Notes |
|---|---|---|---|
| `flow/openlane_config/mac_basic_15ns.tcl` | `mac_core` | 15.0 ns | filename matches content |
| `flow/openlane_config/mac_pipe_10ns.tcl` | `mac_core_pipelined` | 10.0 ns | filename matches content |
| `flow/openlane_config/npu_15ns.tcl` | `silicon_npu` | **20.0 ns** | filename says 15ns — **mismatch, verified by reading the file**; the number in the filename is wrong |
| `flow/config.tcl` | `silicon_npu` | 20.0 ns | duplicate of `npu_15ns.tcl`'s actual setting |

**Fixed 2026-09-07:** all four originally hardcoded `VERILOG_FILES` as `/workspace/flow/src/...` — an absolute path assuming the original authors' Docker-mounted WSL2 setup (`docs1/install_guide.md`: WSL2 + Docker Desktop + `efabless/openlane:latest`, PDK installed inside the container). This repo instead treats OpenLane as a **local install** (`docs/physical_design.md`), which is incompatible as originally configured. All four `.tcl` files (`flow/config.tcl` + the three under `flow/openlane_config/`) now use OpenLane's `dir::` prefix (resolved relative to the config file's own directory, not cwd) pointing directly at `rtl/*.sv` — e.g. `dir::../rtl/silicon_npu.sv`. The `flow/src/*.sv` copies these paths used to point at (verified identical to `rtl/*.sv` via `diff` before removal) have been deleted rather than kept in sync by hand. `openmac/tclgen.py`'s `gen_openlane_config()` (the Python generator behind the `openmac.py flow`/`explore` commands) was updated the same way: its default now resolves an absolute path to this repo's real local `rtl/` directory instead of the `/workspace/flow/src/...` default. `scripts/explore.py`'s `run_backend_variant()` is a separate, still-Docker-specific code path (it `docker cp`s RTL into a running container and also references a hardcoded Windows/WSL path from the original author's machine, `/mnt/c/Projects/OpenMAC-PD/...`) — left as-is, out of scope for this fix, and not usable here regardless.

Shared knobs across all four configs: `PDK=sky130A`, `STD_CELL_LIBRARY=sky130_fd_sc_hd`, `FP_CORE_UTIL=50`, `FP_ASPECT_RATIO=1`, `PL_TARGET_DENSITY=0.6`, `SYNTH_DRIVING_CELL=sky130_fd_sc_hd__inv_2`, `MAX_FANOUT_CONSTRAINT=6`, `RUN_KLAYOUT=0`, `RUN_LINTER=0`.

## Results reported by the original authors — NOT verified or reproduced in this repository

Two original documents (`README_baseline.md` and `final_report.md`) each give a PPA table for these variants, and **they disagree with each other**. **No `metrics.csv`, STA report, or DRC/LVS log backing either table exists anywhere in this repo** — only the final `.gds` files are present (`results/mac_basic/mac_core.gds`, `results/mac_pipe/mac_core_pipelined.gds`, `results/silicon_npu/silicon_npu.gds`). Treat every number below as **unverified / not yet reproduced**, per this project's own no-fabricated-results rule.

`README_baseline.md`'s table (the more complete one — it's the only original doc that covers `silicon_npu` at all):

| Variant (W8/A4[/D4]) | Clock | Setup WNS | TNS | Hold slack | Power (typ) | Core area | Cells | DRC / LVS |
|---|---|---:|---:|---:|---:|---:|---:|---|
| `mac_core` ("MAC Basic") | 15 ns | 0.00 ns | 0.00 ns | +0.12 ns | 0.45 mW | 14,424 µm² | 690 | Clean / Clean |
| `mac_core_pipelined` | 10 ns | −0.47 ns | −0.81 ns | +0.12 ns | 1.04 mW | 15,655 µm² | 715 | Clean / Clean |
| `silicon_npu` | 20 ns | 0.00 ns | 0.00 ns | +0.12 ns | 12.3 mW | 61,256 µm² (0.070 mm² die) | 2,856 | Clean / Clean |

`final_report.md`'s table for the same two non-NPU variants **disagrees on every timing and power number** (it never covers `silicon_npu` at all):

| Variant (W8_A4) | Setup WNS | TNS | Total power | Core area |
|---|---:|---:|---:|---:|
| `mac_core` | **−1.50 ns** (not 0.00) | **−7.58 ns** (not 0.00) | **697 µW** (not 450 µW) | 14,424 µm² (area agrees) |
| `mac_core_pipelined` | −0.47 ns (agrees) | −0.81 ns (agrees) | **1,041 µW** (not 1.04 mW ≈ 1040 µW — close, roughly consistent) | 15,655 µm² (agrees) |

So `mac_core_pipelined` numbers roughly agree between the two original documents; `mac_core`'s timing does **not** — one document claims it closed (WNS 0.00), the other claims a large violation (WNS −1.50 ns, TNS −7.58 ns). This is a genuine contradiction in the original project's own reporting, not something introduced by this migration. Do not cite either "basic" MAC timing number as fact until this project reruns the flow and measures it directly.

Simulation test counts also disagree: `README_baseline.md` claims 14 tests total (4 NPU + 5 basic + 5 pipelined, all passing); `final_report.md` claims "6/6" RTL sim tests plus a separate "34/34" for the Python `openmac/` unit test suite (`tests/test_*.py`). The Python unit tests can be re-run locally (`python3 run_tests.py`); whether they currently pass in this repo's environment has not been checked as part of this migration.

Also note: the `mac_core` ("MAC Basic") clock period is reported as 15 ns above, matching `flow/openlane_config/mac_basic_15ns.tcl`'s actual content — but `final_report.md`'s executive summary describes results as "at 100 MHz" (10 ns), which matches neither 15 ns nor `mac_core_pipelined`'s 10 ns config. Another prose/config mismatch inherited from the original project.

## Python tooling (reusable as-is)

| Module | File | Role |
|---|---|---|
| CLI orchestrator | `openmac.py` | Subcommands: `sim`, `syn`, `flow`, `explore`, `parse`, `analyze`, `dash`, `all` |
| Report parser | `scripts/parse_reports.py` | OpenLane `metrics.csv`, multi-corner STA, DRC/LVS → JSON |
| Design-space explorer | `scripts/explore.py` | Preset and custom parameter sweeps |
| Timing analyzer | `openmac/analyze.py` | Setup/hold violation detection, critical-path analysis |
| TCL generator | `openmac/tclgen.py` | Generates `config.tcl` / SDC from config objects |
| Logger | `openmac/logger.py` | Stage-aware logging, JSON summaries |
| Dashboard | `scripts/dashboard.py` | HTML + PNG PPA comparison dashboard |

CLI usage (paths unchanged by the merge — run from the repo root):

```bash
python3 openmac.py sim --width 8 --array-size 4
python3 openmac.py flow --width 8 --array-size 4      # full OpenLane backend
python3 openmac.py explore --preset pipelined_vs_basic --mode backend
python3 openmac.py parse
python3 openmac.py analyze
python3 openmac.py dash
```

Design-space presets: `timing_4x4`, `width_sweep`, `clock_sweep`, `pipelined_vs_basic` (defined in `scripts/explore.py`).

## Code conventions (inherited, worth keeping)

- RTL: SystemVerilog-2012, `lowercase_snake_case`.
- Python: PEP 8, type hints, dataclasses.
- TCL: OpenLane conventions, `::env()` for variables.
- Tests: descriptive names, assert-based.

## Local simulation quick-start (no Docker)

Via the Makefile (paths unchanged by the merge — `verification/Makefile` references `../rtl/mac_core.sv`, which resolves correctly in the new layout):

```bash
cd verification
make sim                        # WIDTH=8 ARRAY_SIZE=4 by default
make sim WIDTH=16 ARRAY_SIZE=8   # custom parameters
```

Or directly, per the original `README_baseline.md`, run from the repo root (each testbench pairs with exactly one RTL file — do not cross-wire them):

```bash
# silicon_npu (4 tests claimed)
iverilog -g2012 -o npu_tb.vvp verification/silicon_npu_tb.sv rtl/silicon_npu.sv
vvp npu_tb.vvp

# mac_core (5 tests claimed)
iverilog -g2012 -o mac_tb.vvp verification/mac_core_tb.sv rtl/mac_core.sv
vvp mac_tb.vvp

# mac_core_pipelined (5 tests claimed)
iverilog -g2012 -o mac_pipe_tb.vvp verification/mac_core_pipelined_tb.sv rtl/mac_core_pipelined.sv
vvp mac_pipe_tb.vvp
```

Requires `iverilog`; not confirmed installed in this environment as of this migration (`which iverilog` returned nothing here — install with `sudo apt install iverilog` before relying on this).

## Future-work ideas carried over from the original report

1. Timing closure — increase clock period or add deeper pipelining.
2. Wider `ARRAY_SIZE` sweeps (2/4/8) through the full backend.
3. Floorplan optimization — custom pin placement, higher utilization.
4. Multi-PDK port (e.g. ASAP7).
5. Extend to small convolution blocks.
6. Automated CI (GitHub Actions) for regression testing.

These are the *original* authors' backlog for their own scope (a standalone MAC core), not this project's sprint plan — cross-check against `docs/02_eight_week_sprint_plan.md` before picking any of these up.
