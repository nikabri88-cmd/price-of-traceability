"""Two single-message charts for the X post, drawn from the saved results. Run from the repository root:
   python social/x_figures.py
"""
import json
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

sys.path.insert(0, "src")
from qt_s1_sim import h2  # noqa: E402

INK, INK2, MUTED, GRID, AXIS, SURF = "#0b0b0b", "#52514e", "#898781", "#e1e0d9", "#c3c2b7", "#fcfcfb"
BLUE, ORANGE = "#2a78d6", "#eb6834"
FOOT = "Toy simulation: single-photon agent, 4 optical modes.  Code and data: github.com/nikabri88-cmd/price-of-traceability"
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 14, "axes.edgecolor": AXIS,
                     "axes.labelcolor": INK2, "xtick.color": MUTED, "ytick.color": MUTED})


def frame(title, subtitle):
    fig = plt.figure(figsize=(12, 6.75), facecolor=SURF)
    ax = fig.add_axes([0.08, 0.16, 0.88, 0.62])
    ax.set_facecolor(SURF)
    ax.grid(True, color=GRID, lw=1)
    ax.set_axisbelow(True)
    for sp in ("top", "right"):
        ax.spines[sp].set_visible(False)
    fig.text(0.08, 0.92, title, fontsize=21, color=INK, weight="bold")
    fig.text(0.08, 0.865, subtitle, fontsize=14, color=INK2)
    fig.text(0.08, 0.035, FOOT, fontsize=11, color=MUTED)
    ax.set_xlabel("Path information held by the which-path marker (Holevo χ, bits per decision)")
    ax.set_ylabel("Best achievable accuracy")
    ax.set_xlim(-0.02, 1.02)
    ax.set_ylim(0.48, 1.03)
    return fig, ax


# ---- Image 1: the price is non-linear (QT-S1 ceilings) ----
s1 = json.load(open("results/QT-S1/QT-S1_results.json"))["rows"]
pts = [(r["info_opt_bits"], r["acc_max"]) for r in s1 if r["gamma"] > 0]
fig, ax = frame("The price of watching a quantum agent think",
                "Line: analytical curve. Dots: optimised agents. First bits are cheap, the last ones expensive")
acc = np.linspace(0.5, 1.0, 4000)
h2_inv_half = acc[np.argmin(np.abs(h2(acc) - 0.5))]          # accuracy where 0.5 bit is reached (0.89)
ax.plot(h2(acc), acc, color=INK2, lw=2, zorder=2)
cheap = acc >= 0.95
dear = acc <= h2_inv_half
ax.plot(h2(acc[cheap]), acc[cheap], color=BLUE, lw=9, alpha=0.35, solid_capstyle="round", zorder=1)
ax.plot(h2(acc[dear]), acc[dear], color=ORANGE, lw=9, alpha=0.35, solid_capstyle="round", zorder=1)
ax.scatter(*zip(*pts), s=90, color=INK2, edgecolor=SURF, linewidth=2, zorder=3)
ax.annotate("First 0.29 bit\ncosts 5 points", (0.14, 0.976), xytext=(0.06, 0.80), color=BLUE, fontsize=15,
            weight="bold", arrowprops=dict(arrowstyle="-", color=BLUE, lw=1.5))
ax.annotate("The last half bit\ncosts 39 points", (0.80, 0.765), xytext=(0.42, 0.62), color=ORANGE, fontsize=15,
            weight="bold", arrowprops=dict(arrowstyle="-", color=ORANGE, lw=1.5))
def bracket(x0, x1, y, col, text):
    ax.annotate("", (x0, y), (x1, y), arrowprops=dict(arrowstyle="|-|", color=col, lw=2, mutation_scale=6))
    ax.text((x0 + x1) / 2, y + 0.012, text, ha="center", color=col, fontsize=13, weight="bold")


bracket(0.0, 0.286, 0.515, BLUE, "first 0.29 bit")
bracket(0.5, 1.0, 0.515, ORANGE, "last 0.5 bit")
ax.text(1.0, 1.0, "Complete monitoring: accuracy falls to\nthe fully dephased baseline of 50%.\nThere the optimum is degenerate,\nso χ depends on the chosen solution",
        ha="right", va="top", fontsize=12, color=INK2, transform=ax.transAxes)
fig.savefig("social/X_image1_price.png", dpi=150, facecolor=SURF)

# ---- Image 2: under photon loss the agent backs off (QT-S2 post-hoc dense grid) ----
d = json.load(open("results/QT-S2/QT-S2_posthoc_dense_loss.json"))["rows"]
fig, ax = frame("Lossy optics: monitoring pushes the best agent off lossy paths",
                "Dots: optimised agents, monitoring step 0.05 (post-hoc grid). Lost photons count as failures")
for eps, col, lab, xy in ((0.0, BLUE, "Ideal optics", (0.40, 0.935)), (0.3, ORANGE, "30% photon loss", (0.02, 0.765))):
    rows = [r for r in d if r["epsilon"] == eps]
    ax.plot([r["info_opt_bits"] for r in rows], [r["acc_max"] for r in rows], "-o", color=col, lw=2.5, ms=6,
            mec=SURF, mew=1.5, zorder=3)
    ax.text(*xy, lab, color=col, fontsize=15, weight="bold")
peak = max((r for r in d if r["epsilon"] == 0.3), key=lambda r: r["info_opt_bits"])
ax.annotate("Beyond this point, stronger monitoring yields less path\ninformation as the optimum shifts further toward lossless paths",
            (peak["info_opt_bits"], peak["acc_max"]), xytext=(0.06, 0.635), color=INK2, fontsize=14,
            arrowprops=dict(arrowstyle="->", color=MUTED, lw=1.5))
end = next(r for r in d if r["epsilon"] == 0.3 and abs(r["gamma"] - 0.2) < 1e-9)
ax.annotate("Here still 53.7%, above the fully dephased 50% baseline:\ninterference is used less, not abandoned", (end["info_opt_bits"], end["acc_max"]),
            xytext=(0.06, 0.545), color=INK2, fontsize=12, arrowprops=dict(arrowstyle="-", color=MUTED, lw=1))
fig.savefig("social/X_image2_loss.png", dpi=150, facecolor=SURF)
print("saved")
