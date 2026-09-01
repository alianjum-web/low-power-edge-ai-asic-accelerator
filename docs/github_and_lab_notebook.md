# GitHub as laboratory notebook

## Decision

Create the GitHub repository **now**, before the accelerator gets complicated. Commit milestones. Do not upload 700 files named `final_final_REAL_final.v` after six weeks.

This workspace was not a git repository when documentation was added. Initialize git on the **project files only**; keep the nested OpenLane clone out via `.gitignore`.

## Suggested milestone commits

1. Baseline 8-bit adder RTL
2. Adder functional verification
3. Adder OpenLane config + curated metrics/GDS
4. Documentation set (`docs/`, README)
5. Initial Python INT8 reference model
6. Corrected accelerator RTL
7. Bit-exact RTL verification
8. Accelerator OpenLane implementation
9. INT8 parallel results
10. INT4 implementation
11. Architecture comparison
12. Final research results

## Upload

`rtl/`, `algorithm/`, `verification/`, `designs/` (configs + small RTL copies), `docs/`, `results/` (curated), `scripts/`, `README.md`, `LICENSE`, `.gitignore`.

A **final** GDS per variant is a reasonable release artifact (`results/baseline/adder_8bit.klayout.gds` is ~192 KB). Intermediate OpenLane `runs/` trees stay out of Git.

## Do not upload

- `OpenLane/` (full upstream clone + runs, ~1.2 GB)
- `.venv/`, PDK trees (`~/.ciel`)
- Docker caches
- `*.vcd`, simulator binaries (`adder_sim`, `synth_sim`)
- Logs from every failed experiment

## README homepage

Lead with one sentence, the Python→GDS chain, a results table, then hardware/verification/PD. Reviewers skim the first ten seconds. See the root `README.md`.

## Remote

Do not force-push to `main`. Do not commit secrets. OpenLane remains a dependency you clone separately and point at `designs/`.
