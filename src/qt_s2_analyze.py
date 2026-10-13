"""QT-S2 analysis: hypothesis tests, summary CSV and figure."""
import csv
import json

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from qt_s1_sim import h2

res = json.load(open("QT-S2_results.json"))
curves = json.load(open("QT-S2_curves.json"))
rows = res["rows"]
GAM = [1.0, 0.9, 0.6, 0.2, 0.0]
R = {(r["series"], r["gamma"], r["sigma"], r["epsilon"]): r for r in rows}


def setting(kind, level):
    """Ceiling rows over gamma for one hardware setting. kind 'sigma' or 'epsilon'."""
    if kind == "sigma":
        return [R[("N", g, level, 0.0)] for g in GAM]
    if level == 0.0:
        return [R[("N", g, 0.0, 0.0)] for g in GAM]
    return [R[("L", g, 0.0, level)] for g in GAM]


def price(rs):
    a = {r["gamma"]: r["acc_max"] for r in rs}
    i = {r["gamma"]: r["info_opt_bits"] for r in rs}
    C = a[1.0] - a[0.0]
    d_first, d_last = i[0.9] - i[1.0], i[0.2] - i[0.6]
    first = (a[1.0] - a[0.9]) / d_first if d_first > 0.01 else None
    last = (a[0.6] - a[0.2]) / d_last if d_last > 0.01 else None
    ratio = last / first if (first and last) else None
    return {"C_full_log_cost": C, "dI_first": d_first, "dI_last": d_last,
            "cost_per_bit_first": first, "cost_per_bit_last": last, "ratio_last_over_first": ratio,
            "note": None if ratio else "undefined: logged information does not grow across the segment "
                                       "(optimum shifts toward lossless paths)"}


settings = [("sigma", s) for s in [0.0, 0.05, 0.1, 0.2]] + [("epsilon", e) for e in [0.1, 0.3]]
prices = []
for kind, lvl in settings:
    p = price(setting(kind, lvl))
    p.update({"setting": f"{kind}={lvl}", "kind": kind, "level": lvl})
    prices.append(p)

# H1
h1_rows = [p for p in prices if p["C_full_log_cost"] >= 0.05 and p["ratio_last_over_first"] is not None]
h1_undefined = [p["setting"] for p in prices if p["ratio_last_over_first"] is None]
h1_pass = all(p["ratio_last_over_first"] >= 2 for p in h1_rows)
excluded = [p["setting"] for p in prices if p["C_full_log_cost"] < 0.05]

# H2
Cs = [p["C_full_log_cost"] for p in prices if p["kind"] == "sigma"]
Ce = [prices[0]["C_full_log_cost"]] + [p["C_full_log_cost"] for p in prices if p["kind"] == "epsilon"]
h2_sigma = all(Cs[k + 1] < Cs[k] + 0.01 for k in range(len(Cs) - 1)) and all(Cs[k + 1] < Cs[k] for k in range(len(Cs) - 1))
h2_eps = all(Ce[k + 1] < Ce[k] + 0.01 for k in range(len(Ce) - 1)) and all(Ce[k + 1] < Ce[k] for k in range(len(Ce) - 1))
h2_violations = [("sigma", k) for k in range(len(Cs) - 1) if Cs[k + 1] > Cs[k] + 0.01] + \
                [("epsilon", k) for k in range(len(Ce) - 1) if Ce[k + 1] > Ce[k] + 0.01]
h2_pass = len(h2_violations) == 0

# H3
rel = {s: R[("N", 1.0, s, 0.0)]["reinforce_final_median"] / R[("N", 1.0, s, 0.0)]["acc_max"] for s in [0.0, 0.05, 0.1, 0.2]}
h3_pass = rel[0.05] >= rel[0.0] - 0.02 and rel[0.1] >= rel[0.0] - 0.02

# E1, E2
e1 = [{"epsilon": e, **{k: R[("L" if e else "N", 1.0, 0.0, e)][k] for k in
       ("acc_max", "click_at_max", "cond_acc_at_max", "post_loss_balance_phase_over_plain")}} for e in [0.0, 0.1, 0.3]]
e2 = {g: {s: R[("N", g, s, 0.0)]["reinforce_info_end_median"] for s in [0.0, 0.05, 0.1, 0.2]} for g in [0.6, 0.2]}
e2_ceiling = {g: {s: R[("N", g, s, 0.0)]["info_opt_bits"] for s in [0.0, 0.05, 0.1, 0.2]} for g in [0.6, 0.2]}

tests = {
    "prices": prices,
    "H1_pass_on_defined_settings": h1_pass, "H1_defined_settings": len(h1_rows),
    "H1_undefined_settings": h1_undefined, "H1_excluded_settings(C<0.05)": excluded,
    "H2_C_by_sigma": Cs, "H2_C_by_epsilon(0,0.1,0.3)": Ce, "H2_violations(>0.01 rise)": h2_violations,
    "H2_strictly_decreasing_sigma": h2_sigma, "H2_strictly_decreasing_epsilon": h2_eps, "H2_pass": h2_pass,
    "H3_rel_final_over_ceiling_gamma1": rel, "H3_pass": h3_pass,
    "E1_gamma1_loss": e1, "E2_learner_info_end": e2, "E2_ceiling_info": e2_ceiling,
}
json.dump(tests, open("QT-S2_tests.json", "w"), indent=2)
print(json.dumps(tests, indent=2))

with open("QT-S2_summary.csv", "w", newline="") as f:
    keys = ["series", "gamma", "sigma", "epsilon", "acc_max", "click_at_max", "cond_acc_at_max", "info_opt_bits",
            "post_loss_balance_phase_over_plain", "reinforce_final_median", "reinforce_final_q25",
            "reinforce_final_q75", "reinforce_info_end_median"]
    w = csv.DictWriter(f, fieldnames=keys, extrasaction="ignore")
    w.writeheader()
    for r in rows:
        w.writerow({k: (round(r[k], 4) if isinstance(r[k], float) else r[k]) for k in keys})

# ---- figure ----
INK, INK2, MUTED, GRID, AXIS, SURF = "#0b0b0b", "#52514e", "#898781", "#e1e0d9", "#c3c2b7", "#fcfcfb"
RAMP4 = ["#0d366b", "#256abf", "#5598e7", "#86b6ef"]
RAMP3 = ["#0d366b", "#3987e5", "#86b6ef"]
S1 = "#2a78d6"
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10, "axes.edgecolor": AXIS,
                     "axes.labelcolor": INK2, "xtick.color": MUTED, "ytick.color": MUTED})
fig, axs = plt.subplots(2, 2, figsize=(12, 9.5), facecolor=SURF)
for ax in axs.flat:
    ax.set_facecolor(SURF)
    ax.grid(True, color=GRID, lw=0.8)
    ax.set_axisbelow(True)
    for sp in ("top", "right"):
        ax.spines[sp].set_visible(False)

accl = np.linspace(0.5, 1.0, 300)


def price_panel(ax, kind, levels, ramp, title, lab):
    ax.plot(h2(accl), accl, color=GRID, lw=6, solid_capstyle="round", label="Ideal bound (QT-S1)")
    for c, lvl in zip(ramp, levels):
        rs = [r for r in setting(kind, lvl) if r["gamma"] > 0]          # gamma = 0 is degenerate (0 bits)
        ax.plot([r["info_opt_bits"] for r in rs], [r["acc_max"] for r in rs], "-o", color=c, lw=2, ms=7,
                mec=SURF, mew=2, label=f"{lab} = {lvl}")
    ax.set_xlabel("Path information in the which-path marker (Holevo χ, bits per decision)")
    ax.set_ylabel("Ceiling accuracy")
    ax.set_xlim(-0.03, 1.03)
    ax.set_ylim(0.45, 1.03)
    ax.set_title(title, loc="left", color=INK, fontsize=11)
    ax.legend(frameon=False, fontsize=9, labelcolor=INK2, loc="lower left")


price_panel(axs[0, 0], "sigma", [0.0, 0.05, 0.1, 0.2], RAMP4, "A. Price of traceability under mirror noise", "σ")
price_panel(axs[0, 1], "epsilon", [0.0, 0.1, 0.3], RAMP3, "B. Price under path-dependent photon loss", "ε")
_r = R[("L", 0.2, 0.0, 0.3)]
axs[0, 1].annotate("ε = 0.3, γ = 0.2: optimum shifts toward\nlossless paths, marker holds less", (_r["info_opt_bits"], _r["acc_max"]),
                   xytext=(0.12, 0.69), textcoords="data", color=INK2, fontsize=9,
                   arrowprops=dict(arrowstyle="-", color=MUTED, lw=1))

ax = axs[1, 0]
labels = ["σ 0", "σ 0.05", "σ 0.1", "σ 0.2", "ε 0.1", "ε 0.3"]
vals = Cs + Ce[1:]
xs = np.arange(len(vals)) + np.array([0, 0, 0, 0, 0.6, 0.6])
ax.bar(xs, vals, width=0.6, color=S1, edgecolor=SURF, linewidth=2)
for xx, v in zip(xs, vals):
    ax.text(xx, v + 0.008, f"{v:.3f}", ha="center", color=INK2, fontsize=9)
ax.set_xticks(xs, labels)
ax.set_ylabel("Accuracy lost to a complete log")
ax.set_ylim(0, max(vals) * 1.2)
ax.set_title("C. Full-log cost by hardware imperfection", loc="left", color=INK, fontsize=11)

ax = axs[1, 1]
for c, s in zip(RAMP4, [0.0, 0.05, 0.1, 0.2]):
    cv = np.array(curves[f"N|1.0|{s}|0.0"])
    x = (np.arange(cv.shape[0]) + 1) * 100
    ax.plot(x, np.median(cv, axis=1), color=c, lw=2, label=f"σ = {s}")
ax.set_xlabel("Episodes")
ax.set_ylabel("Expected accuracy, median of 20 seeds")
ax.set_ylim(0.3, 1.02)
ax.set_title("D. Learning without a log, by mirror noise", loc="left", color=INK, fontsize=11)
ax.legend(frameon=False, fontsize=9, labelcolor=INK2, loc="lower right")

fig.tight_layout()
fig.savefig("QT-S2_figure.png", dpi=170, facecolor=SURF)
print("figure saved")
