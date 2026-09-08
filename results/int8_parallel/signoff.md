# INT8 parallel signoff

- OpenLane: v1.0.2, run tag `project_run_02`
- Top module: `accelerator_top`
- PDK/library: SKY130A / `sky130_fd_sc_hd`
- Clock: 20 ns (50 MHz target)
- Die area: 0.246796414625 mm^2
- Total cells: 28,761
- DRC: 0 Magic violations
- LVS: clean, 0 errors
- KLayout versus Magic XOR: 0 differences
- TritonRoute violations: 0
- Setup/hold violations: 0/0 at the typical corner
- Antenna: 23 pin and 19 net violations reported by ARC
- Max fanout: violations reported in typical-corner STA checks
- IR drop: run completed, but `VSRC_LOC_FILES` was not defined, so values may be inaccurate

The raw OpenLane run remains under the local ignored `runs/` tree. This directory contains only the curated summary and final GDS artifact.
