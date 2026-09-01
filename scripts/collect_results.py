#!/usr/bin/env python3
"""Copy OpenLane metrics.csv into results/<variant>/ for the lab notebook."""
from __future__ import annotations

import argparse
import shutil
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--run-dir",
        required=True,
        type=Path,
        help="OpenLane run directory, e.g. OpenLane/designs/adder_8bit/runs/RUN_...",
    )
    parser.add_argument(
        "--variant",
        default="baseline",
        help="Destination folder under results/",
    )
    args = parser.parse_args()
    src = args.run_dir / "reports" / "metrics.csv"
    if not src.is_file():
        raise SystemExit(f"metrics.csv not found: {src}")
    dest_dir = Path(__file__).resolve().parents[1] / "results" / args.variant
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / "metrics.csv"
    shutil.copy2(src, dest)
    print(f"Copied {src} -> {dest}")


if __name__ == "__main__":
    main()
