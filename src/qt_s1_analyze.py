"""QT-S1 analysis: hypothesis tests, summary CSV and figure."""
import csv
import json

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

res = json.load(open("QT-S1_results.json"))
curves = {float(k): np.array(v) for k, v in json.load(open("QT-S1_curves.json")).items()}
rows = res["rows"]
T_CK = 100


def h2(x):
    x = np.clip(x, 1e-12, 1 - 1e-12)
    return -(x * np.log2(x) + (1 - x) * np.log2(1 - x))


def rank(a):
    a = np.asarray(a, float)
    order = a.argsort()
    r = np.empty_like(a)
    r[order] = np.arange(len(a))
    for v in np.unique(a):                      # average ties
        idx = a == v
        r[idx] = r[idx].mean()
    return r


def spearman(x, y):
    rx, ry = rank(x), rank(y)
    return float(np.corrcoef(rx, ry)[0, 1])


# ---- per-gamma episodes-to-criterion, non-reaching seeds counted as T + 100 ----
summary = []
for r in rows:
    g = r["gamma"]
    c = curves[g]                                # (ckpts, seeds)
    hit = c >= 0.9 * r["acc_max"]
    ep = np.where(hit.any(axis=0), (hit.argmax(axis=0) + 1) * T_CK, c.shape[0] * T_CK + T_CK)
    summary.append({
        "gamma": g,
        "D_pairwise": round(r["D"], 4),
        "acc_max_M1": round(r["acc_max"], 4),
        "acc_pred_(1+gamma)/2": round(r["acc_pred"], 4),
        "logged_info_bits_M1": round(r["info_opt_bits"], 4),
        "H2(acc_max)": round(r["h2_acc_max"], 4),
        "reinforce_final_median": round(r["reinforce_final_median"], 4),
        "reinforce_final_q25": round(r["reinforce_final_q25"], 4),
        "reinforce_final_q75": round(r["reinforce_final_q75"], 4),
        "reinforce_final_over_ceiling": round(r["reinforce_final_median"] / r["acc_max"], 4),
        "reinforce_logged_info_end_median": round(r["reinforce_info_end_median"], 4),
        "seeds_reaching_criterion_of_20": int(hit.any(axis=0).sum()),
        "episodes_to_criterion_median": float(np.median(ep)),
    })

with open("QT-S1_summary.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(summary[0].keys()))
    w.writeheader()
    w.writerows(summary)

# ---- hypothesis tests ----
d1 = max(abs(s["acc_max_M1"] - s["acc_pred_(1+gamma)/2"]) for s in summary)
d2 = max(abs(s["logged_info_bits_M1"] - s["H2(acc_max)"]) for s in summary)
gam = [s["gamma"] for s in summary]
eps = [s["episodes_to_criterion_median"] for s in summary]
rho = spearman(gam, eps)
reach_hi = all(s["seeds_reaching_criterion_of_20"] >= 10 for s in summary if s["gamma"] >= 0.8)
tests = {
    "H1_max_abs_dev": d1, "H1_pass": d1 <= 0.02,
    "H2_max_abs_dev_bits": d2, "H2_pass": d2 <= 0.03,
    "H3_spearman_gamma_vs_episodes": rho, "H3a_pass(rho<0)": rho < 0,
    "H3b_median_seed_reaches_at_gamma>=0.8": reach_hi,
}
json.dump(tests, open("QT-S1_tests.json", "w"), indent=2)
print(json.dumps(tests, indent=2))
for s in summary:
    print(s)

# ---- figure ----
INK, INK2, MUTED, GRID, AXIS, SURF = "#0b0b0b", "#52514e", "#898781", "#e1e0d9", "#c3c2b7", "#fcfcfb"
S1, S2 = "#2a78d6", "#eb6834"
RAMP = ["#86b6ef", "#6da7ec", "#5598e7", "#3987e5", "#2a78d6", "#256abf", "#184f95", "#0d366b"]
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10, "axes.edgecolor": AXIS,
                     "axes.labelcolor": INK2, "xtick.color": MUTED, "ytick.color": MUTED})

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4.8), facecolor=SURF)
for ax in (ax1, ax2):
    ax.set_facecolor(SURF)
    ax.grid(True, color=GRID, lw=0.8)
    ax.set_axisbelow(True)
    for sp in ("top", "right"):
        ax.spines[sp].set_visible(False)

# Panel A: accuracy vs logged information
acc_line = np.linspace(0.5, 1.0, 400)
ax1.plot(h2(acc_line), acc_line, color=INK2, lw=2, label="Bound: I = H2(accuracy)")
I1 = [s["logged_info_bits_M1"] for s in summary]
A1 = [s["acc_max_M1"] for s in summary]
ax1.scatter(I1, A1, s=60, color=S1, edgecolor=SURF, linewidth=2, zorder=3, label="Ceiling (direct optimisation)")
I2 = [s["reinforce_logged_info_end_median"] for s in summary]
A2 = [s["reinforce_final_median"] for s in summary]
lo = [s["reinforce_final_median"] - s["reinforce_final_q25"] for s in summary]
hi = [s["reinforce_final_q75"] - s["reinforce_final_median"] for s in summary]
ax1.errorbar(I2, A2, yerr=[lo, hi], fmt="o", ms=7, color=S2, mec=SURF, mew=2, elinewidth=2, capsize=0,
             zorder=4, label="Learning agent, median ± IQR")
for s in summary:
    if s["gamma"] in (0.95, 0.9, 0.6, 0.2):
        ax1.annotate(f"γ = {s['gamma']}", (s["logged_info_bits_M1"], s["acc_max_M1"]),
                     xytext=(8, 6), textcoords="offset points", color=INK2, fontsize=9)
ax1.annotate("γ = 0: degenerate optimum at 50%; this solver run found a single-path agent", (0.0, 0.5),
             xytext=(10, -14), textcoords="offset points", color=INK2, fontsize=9)
ax1.set_xlabel("Path information in the which-path marker (Holevo χ, bits per decision)")
ax1.set_ylabel("Expected accuracy")
ax1.set_xlim(-0.03, 1.05)
ax1.set_ylim(0.42, 1.03)
ax1.set_title("A. Price of traceability", loc="left", color=INK, fontsize=11)
ax1.legend(frameon=False, loc="upper right", fontsize=9, labelcolor=INK2)

# Panel B: learning curves (median over seeds)
x = (np.arange(curves[1.0].shape[0]) + 1) * T_CK
for i, g in enumerate(sorted(curves)):
    ax2.plot(x, np.median(curves[g], axis=1), color=RAMP[i], lw=2, label=f"γ = {g}")
ax2.set_xlabel("Episodes")
ax2.set_ylabel("Expected accuracy, median of 20 seeds")
ax2.set_ylim(0.0, 1.02)
ax2.set_title("B. Learning curves by log completeness", loc="left", color=INK, fontsize=11)
ax2.legend(frameon=False, ncol=4, fontsize=9, loc="lower right", labelcolor=INK2,
           title="γ = 1: no log; γ = 0: full log", title_fontsize=9)

fig.tight_layout()
fig.savefig("QT-S1_figure.png", dpi=180, facecolor=SURF)
print("figure saved")
