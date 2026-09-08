# Verification

Hierarchical testbenches. Experiment 0 adder TB is here and also under `../testbench/` (original path).

| File | Status |
|---|---|
| `tb_adder_8bit.v` | Present |
| `tb_mac_unit.sv` | Phase 2 |
| `tb_processing_element.sv` | Phase 2 |
| `tb_accelerator.sv` | Phase 2 |
| `tb_accelerator_int4.sv` | Sprint 6 — same `accelerator_top` RTL, `DATA_WIDTH=4`; see `docs/optimization_plan.md` |
| `reference/` | Python-generated expected vectors (`vectors.{csv,hex}` INT8, `vectors_int4.{csv,hex}` INT4) |

See [docs/verification.md](../docs/verification.md).
