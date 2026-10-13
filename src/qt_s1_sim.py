"""QT-S1 – Price of traceability in a single-photon learning agent.

See QT-S1_preregistration.md for design, hypotheses and criteria.
Usage:
  python qt_s1_sim.py pilot   # learning-rate pilot at gamma = 1, seeds 100–119
  python qt_s1_sim.py main LR # M1 ceilings + M2 REINFORCE, seeds 0–19
"""
import json
import sys
import time

import numpy as np

N = 4
MZI_PAIRS = [(0, 1), (2, 3), (1, 2), (0, 1), (2, 3), (1, 2)]  # Clements, 4 modes
NP_U = 16                                                       # 6 MZIs x 2 + 4 phases
NP = 2 * NP_U
GAMMAS = [1.0, 0.95, 0.9, 0.8, 0.6, 0.4, 0.2, 0.0]

PERC = [(0, 0), (0, 1), (1, 0), (1, 1)]
IN_MODE = np.array([b1 for b1, _ in PERC])
PHASE = np.array([[1, (-1) ** b2, 1, (-1) ** b2] for _, b2 in PERC], dtype=complex)
TARGET = np.array([2 * b1 + b2 for b1, b2 in PERC])


def unitary(p):
    """p: (B, 16) -> (B, 4, 4) unitary from a rectangular MZI mesh."""
    B = p.shape[0]
    U = np.broadcast_to(np.eye(N, dtype=complex), (B, N, N)).copy()
    for k, (i, j) in enumerate(MZI_PAIRS):
        th, ph = p[:, 2 * k], p[:, 2 * k + 1]
        e, c, s = np.exp(1j * ph), np.cos(th), np.sin(th)
        Ui, Uj = U[:, i, :].copy(), U[:, j, :].copy()
        U[:, i, :] = (e * c)[:, None] * Ui - s[:, None] * Uj
        U[:, j, :] = (e * s)[:, None] * Ui + c[:, None] * Uj
    return np.exp(1j * p[:, 12:16])[:, :, None] * U


def gram(g):
    G = np.full((N, N), g, dtype=float)
    np.fill_diagonal(G, 1.0)
    return G


def forward(params, G):
    """Returns action probabilities (B, 4 percepts, 4 actions) and internal amplitudes (B, 4, 4)."""
    U1, U2 = unitary(params[:, :NP_U]), unitary(params[:, NP_U:])
    psi = U1[:, :, IN_MODE].transpose(0, 2, 1) * PHASE[None]           # (B, S, modes)
    rho = G[None, None] * psi[..., :, None] * psi.conj()[..., None, :]  # logged internal state
    p = np.einsum('bij,bsjk,bik->bsi', U2, rho, U2.conj()).real
    return np.clip(p, 0.0, 1.0), psi


def accuracy(params, G):
    p, _ = forward(params, G)
    return p[:, np.arange(4), TARGET].mean(axis=1)


def logged_info(psi, G):
    """Conditional Holevo information of the log about the internal path, bits per decision."""
    pj = np.abs(psi) ** 2                                                # (B, S, modes)
    M = np.sqrt(pj[..., :, None] * pj[..., None, :]) * G[None, None]
    ev = np.clip(np.linalg.eigvalsh(M), 1e-15, 1.0)
    S = -(ev * np.log2(ev)).sum(axis=-1)
    return S.mean(axis=1)


def h2(x):
    x = np.clip(x, 1e-12, 1 - 1e-12)
    return -(x * np.log2(x) + (1 - x) * np.log2(1 - x))


def fd_grad(f, params, eps=1e-5):
    R, P = params.shape
    I = np.eye(P)
    pert = np.concatenate([params[:, None] + eps * I[None], params[:, None] - eps * I[None]], axis=1)
    vals = f(pert.reshape(-1, P)).reshape(R, 2 * P)
    return (vals[:, :P] - vals[:, P:]) / (2 * eps)


def ceiling(gamma, restarts=10, steps=1500, lr=0.05, seed=1000):
    """M1: direct maximisation of exact expected accuracy (Adam)."""
    G = gram(gamma)
    rng = np.random.default_rng(seed)
    x = rng.uniform(0, 2 * np.pi, (restarts, NP))
    m, v = np.zeros_like(x), np.zeros_like(x)
    b1, b2 = 0.9, 0.999
    for t in range(1, steps + 1):
        g = fd_grad(lambda X: accuracy(X, G), x)
        m = b1 * m + (1 - b1) * g
        v = b2 * v + (1 - b2) * g ** 2
        x += lr * (m / (1 - b1 ** t)) / (np.sqrt(v / (1 - b2 ** t)) + 1e-8)
    acc = accuracy(x, G)
    k = int(np.argmax(acc))
    _, psi = forward(x[k:k + 1], G)
    return float(acc[k]), float(logged_info(psi, G)[0]), acc.tolist()


def reinforce(gamma, seeds, lr, T=4000, ckpt=100):
    """M2: REINFORCE with running baseline, one episode per update, vectorised over seeds."""
    G = gram(gamma)
    rngs = [np.random.default_rng(s) for s in seeds]
    B = len(seeds)
    x = np.stack([r.uniform(0, 2 * np.pi, NP) for r in rngs])
    base = np.full(B, 0.25)
    curve = []
    ar = np.arange(B)
    for t in range(1, T + 1):
        s = np.array([r.integers(4) for r in rngs])
        p, _ = forward(x, G)
        pa = p[ar, s]
        pa = pa / pa.sum(axis=1, keepdims=True)
        u = np.array([r.random() for r in rngs])
        a = np.minimum((pa.cumsum(axis=1) < u[:, None]).sum(axis=1), 3)
        rwd = (a == TARGET[s]).astype(float)

        P = NP
        I = np.eye(P)
        pert = np.concatenate([x[:, None] + 1e-5 * I[None], x[:, None] - 1e-5 * I[None]], axis=1)
        pp, _ = forward(pert.reshape(-1, P), G)
        pp = pp.reshape(B, 2 * P, 4, 4)[ar[:, None], np.arange(2 * P)[None], s[:, None], a[:, None]]
        lp = np.log(np.clip(pp, 1e-12, 1.0))
        g = (lp[:, :P] - lp[:, P:]) / 2e-5

        x += lr * (rwd - base)[:, None] * g
        base = 0.95 * base + 0.05 * rwd
        if t % ckpt == 0:
            curve.append(accuracy(x, G).tolist())
    _, psi = forward(x, G)
    return np.array(curve), logged_info(psi, G)


def pilot():
    out = {}
    for lr in [0.02, 0.05, 0.1, 0.2]:
        t0 = time.time()
        curve, _ = reinforce(1.0, list(range(100, 120)), lr)
        out[lr] = float(curve[-1].mean())
        print(f"lr={lr}: mean final acc={out[lr]:.3f} ({time.time() - t0:.0f}s)", flush=True)
    best = max(out, key=out.get)
    json.dump({"pilot_final_acc": out, "chosen_lr": best}, open("QT-S1_pilot.json", "w"), indent=2)
    print("chosen lr:", best)


def main(lr):
    res = {"lr": lr, "gammas": GAMMAS, "rows": []}
    curves = {}
    for g in GAMMAS:
        t0 = time.time()
        acc_max, info_opt, restarts = ceiling(g)
        curve, info_end = reinforce(g, list(range(20)), lr)
        crit = 0.9 * acc_max
        hit = curve >= crit                                               # (ckpts, seeds)
        ep = np.where(hit.any(axis=0), (hit.argmax(axis=0) + 1) * 100, np.nan)
        row = {
            "gamma": g,
            "D": float(np.sqrt(1 - g ** 2)),
            "acc_max": acc_max,
            "acc_pred": (1 + g) / 2,
            "info_opt_bits": info_opt,
            "h2_acc_max": float(h2(acc_max)),
            "reinforce_final_median": float(np.median(curve[-1])),
            "reinforce_final_mean": float(curve[-1].mean()),
            "reinforce_final_q25": float(np.quantile(curve[-1], 0.25)),
            "reinforce_final_q75": float(np.quantile(curve[-1], 0.75)),
            "reinforce_info_end_median": float(np.median(info_end)),
            "episodes_to_criterion_median": float(np.nanmedian(ep)) if np.isfinite(ep).any() else None,
            "seeds_reaching_criterion": int(np.isfinite(ep).sum()),
            "restart_accs": restarts,
        }
        res["rows"].append(row)
        curves[str(g)] = curve.tolist()
        print(json.dumps({k: v for k, v in row.items() if k != "restart_accs"}), f"({time.time() - t0:.0f}s)", flush=True)
    json.dump(res, open("QT-S1_results.json", "w"), indent=2)
    json.dump(curves, open("QT-S1_curves.json", "w"))


if __name__ == "__main__":
    if sys.argv[1] == "pilot":
        pilot()
    else:
        main(float(sys.argv[2]))
