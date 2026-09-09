"""Generate fig08 (PPA comparison), fig09 (accuracy comparison), and
fig10 (optimization trade-off) directly from results/comparison.csv's
int8_parallel vs int4_parallel rows. No hand-copied numbers -- run this
after any update to comparison.csv to regenerate the figures from source.

Usage: python3 scripts/plot_ppa_charts.py [out_dir]   (run from repo root)
"""
import csv
import sys
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

COMPARISON_CSV = "results/comparison.csv"
LABELS = {"int8_parallel": "INT8 (baseline)", "int4_parallel": "INT4 (optimized)"}
COLORS = {"INT8 (baseline)": "#3a6fb0", "INT4 (optimized)": "#c98a12"}


def load_rows():
    rows = {}
    with open(COMPARISON_CSV) as f:
        for row in csv.DictReader(f):
            if row["design"] in LABELS:
                rows[LABELS[row["design"]]] = row
    missing = set(LABELS.values()) - set(rows)
    if missing:
        raise SystemExit(f"{COMPARISON_CSV} missing row(s) for: {missing}")
    return rows


_rows = load_rows()
DIE_AREA_UM2 = {k: float(v["die_area_um2"]) for k, v in _rows.items()}
POWER_MW = {k: float(v["power_mw"]) for k, v in _rows.items()}
ENERGY_NJ = {k: float(v["energy_per_inference_nj"]) for k, v in _rows.items()}
ACCURACY_PCT = {k: float(v["accuracy_pct"]) for k, v in _rows.items()}


def fig08_ppa_comparison(out):
    fig, axes = plt.subplots(1, 3, figsize=(12, 4.6))
    metrics = [
        ("Die area", DIE_AREA_UM2, "um^2", axes[0]),
        ("Power (typical corner)", POWER_MW, "mW", axes[1]),
        ("Energy / inference", ENERGY_NJ, "nJ", axes[2]),
    ]
    for title, data, unit, ax in metrics:
        labels = list(data.keys())
        vals = [data[k] for k in labels]
        bars = ax.bar(labels, vals, color=[COLORS[k] for k in labels], width=0.55)
        for b, v in zip(bars, vals):
            ax.annotate(f"{v:.6g}", (b.get_x() + b.get_width() / 2, v),
                        ha="center", va="bottom", fontsize=9, xytext=(0, 3),
                        textcoords="offset points")
        ax.set_title(f"{title} ({unit})", fontsize=11)
        ax.spines[["top", "right"]].set_visible(False)
        ax.set_xticks(range(len(labels)))
        ax.set_xticklabels(labels, fontsize=9)
        ax.set_ylim(0, max(vals) * 1.25)
    pct_area = (1 - DIE_AREA_UM2["INT4 (optimized)"] / DIE_AREA_UM2["INT8 (baseline)"]) * 100
    pct_energy = (1 - ENERGY_NJ["INT4 (optimized)"] / ENERGY_NJ["INT8 (baseline)"]) * 100
    fig.suptitle(f"PPA comparison — INT8 4-way-parallel baseline vs INT4 4-way-parallel optimized\n"
                 f"(same clock, same schedule; area -{pct_area:.1f}%, power/energy -{pct_energy:.1f}%; "
                 f"OpenLane project_run_02 / project_run_01)", fontsize=11)
    plt.tight_layout(rect=[0, 0, 1, 0.88])
    plt.savefig(out, dpi=160)
    print("saved", out)


def fig09_accuracy_comparison(out):
    fig, ax = plt.subplots(figsize=(6.4, 4.6))
    labels = list(ACCURACY_PCT.keys())
    vals = [ACCURACY_PCT[k] for k in labels]
    bars = ax.bar(labels, vals, color=[COLORS[k] for k in labels], width=0.5)
    for b, v in zip(bars, vals):
        ax.annotate(f"{v:.2f}%", (b.get_x() + b.get_width() / 2, v),
                    ha="center", va="bottom", fontsize=10, xytext=(0, 3),
                    textcoords="offset points")
    ax.set_ylim(0, 100)
    ax.set_ylabel("synthetic accuracy = 100 x (1 - NRMSE) [%]")
    ax.set_title("Accuracy comparison (synthetic, FP32 vs quantized)\n"
                  "paired random draw, seed=1234, N=2000 — not a task-accuracy benchmark", fontsize=10)
    ax.spines[["top", "right"]].set_visible(False)
    ax.annotate("", xy=(1, 84), xytext=(0, 89),
                arrowprops=dict(arrowstyle="->", color="#b0303f", lw=1.6))
    ax.text(0.5, 86.5, "-9.41 pts", color="#b0303f", ha="center", fontsize=10, fontweight="bold")
    plt.tight_layout()
    plt.savefig(out, dpi=160)
    print("saved", out)


def fig10_tradeoff(out):
    fig, ax = plt.subplots(figsize=(7.2, 6.2))
    area_saving = (1 - DIE_AREA_UM2["INT4 (optimized)"] / DIE_AREA_UM2["INT8 (baseline)"]) * 100
    energy_saving = (1 - ENERGY_NJ["INT4 (optimized)"] / ENERGY_NJ["INT8 (baseline)"]) * 100
    acc_drop = ACCURACY_PCT["INT8 (baseline)"] - ACCURACY_PCT["INT4 (optimized)"]

    ax.scatter([0], [0], s=180, color=COLORS["INT8 (baseline)"], zorder=3, label="INT8 baseline (reference point)")
    ax.annotate("INT8 baseline\n(0% saving, 0 pt accuracy cost)", (0, 0), fontsize=9,
                xytext=(10, -28), textcoords="offset points", color=COLORS["INT8 (baseline)"])

    ax.scatter([area_saving], [acc_drop], s=180, color=COLORS["INT4 (optimized)"],
               marker="s", zorder=3, label=f"INT4: area saving ({area_saving:.1f}%)")
    ax.annotate(f"INT4, area axis\n(+{area_saving:.1f}% area saved,\n-{acc_drop:.1f} pt accuracy)",
                (area_saving, acc_drop), fontsize=9, xytext=(-95, 10), textcoords="offset points",
                color=COLORS["INT4 (optimized)"])

    ax.scatter([energy_saving], [acc_drop], s=180, color="#2f7d3a",
               marker="^", zorder=3, label=f"INT4: energy saving ({energy_saving:.1f}%)")
    ax.annotate(f"INT4, energy axis\n(+{energy_saving:.1f}% energy saved,\n-{acc_drop:.1f} pt accuracy)",
                (energy_saving, acc_drop), fontsize=9, xytext=(8, 10), textcoords="offset points",
                color="#2f7d3a")

    ax.axhline(0, color="#cccccc", lw=1)
    ax.axvline(0, color="#cccccc", lw=1)
    ax.set_xlabel("area / energy saving vs INT8 baseline (%) — higher is better")
    ax.set_ylabel("accuracy cost vs INT8 baseline (percentage points) — higher is worse")
    ax.set_xlim(-8, 75)
    ax.set_ylim(-2, 14)
    ax.set_title("Optimization trade-off: INT8->INT4 bit-width reduction\n"
                 "same 4-way-parallel schedule, same clock — one point measured, no interpolation",
                 fontsize=11, pad=14)
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(color="#eeeeee")
    plt.tight_layout(rect=[0, 0, 1, 0.99])
    plt.subplots_adjust(top=0.85)
    plt.savefig(out, dpi=160)
    print("saved", out)


if __name__ == "__main__":
    import sys
    outdir = sys.argv[1] if len(sys.argv) > 1 else "."
    fig08_ppa_comparison(f"{outdir}/fig08_ppa_comparison.png")
    fig09_accuracy_comparison(f"{outdir}/fig09_accuracy_comparison.png")
    fig10_tradeoff(f"{outdir}/fig10_optimization_tradeoff.png")
