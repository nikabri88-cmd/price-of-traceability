"""QT-S2 – Price of traceability under realistic optics (noise + path-dependent loss).

See QT-S2_preregistration.md. Reuses the QT-S1 model from qt_s1_sim.py.
Usage: python qt_s2_sim.py [smoke | rerun_loss]
"""
import os
os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")

import json
import sys
import time
from multiprocessing import Pool

import numpy as np

from qt_s1_sim import IN_MODE, NP, NP_U, PHASE, TARGET, gram, logged_info, unitary

GAMMAS = [1.0, 0.9, 0.6, 0.2, 0.0]
SIGMAS = [0.0, 0.05, 0.1, 0.2]
EPSILONS = [0.1, 0.3]
LR = 0.02


def forward2(params, G, eps_loss):
    """Unconditional action probabilities (B, S, A) (sum = click prob) and pre-loss path amplitudes."""
    U1, U2 = unitary(params[:, :NP_U]), unitary(params[:, NP_U:])
    psi = U1[:, :, IN_MODE].transpose(0, 2, 1) * PHASE[None]
    t = np.sqrt(np.array([1.0, 1.0 - eps_loss, 1.0, 1.0 - eps_loss]))
    psil = psi * t
    rho = G[None, None] * psil[..., :, None] * psil.conj()[..., None, :]
    p = np.einsum('bij,bsjk,bik->bsi', U2, rho, U2.conj()).real
    return np.clip(p, 0.0, 1.0), psi


def acc_and_click(params, G, eps_loss):
    p, _ = forward2(params, G, eps_loss)
    return p[:, np.arange(4), TARGET].mean(axis=1), p.sum(axis=2).mean(axis=1)


def noisy_expected_acc(X, G, eps_loss, sigma, Z):
    """Mean accuracy of each row of X over the noise draws Z (K, NP)."""
    if sigma == 0:
        return acc_and_click(X, G, eps_loss)[0]
    K = Z.shape[0]
    Xn = (X[:, None, :] + sigma * Z[None]).reshape(-1, NP)
    return acc_and_click(Xn, G, eps_loss)[0].reshape(-1, K).mean(axis=1)


def noisy_eval(x, G, eps_loss, sigma, n=4000, seed=3000, chunk=1000):
    """Accuracy and click probability of a single parameter vector over fresh noise draws."""
    if sigma == 0:
        a, c = acc_and_click(x[None], G, eps_loss)
        return float(a[0]), float(c[0])
    rng = np.random.default_rng(seed)
    acc, clk = [], []
    for _ in range(n // chunk):
        Xn = x[None] + sigma * rng.standard_normal((chunk, NP))
        a, c = acc_and_click(Xn, G, eps_loss)
        acc.append(a.mean())
        clk.append(c.mean())
    return float(np.mean(acc)), float(np.mean(clk))


def ceiling2(gamma, sigma, eps_loss, restarts=4, steps=800, K=16, lr=0.05, fd=1e-5):
    G = gram(gamma)
    rng = np.random.default_rng(1000)
    Z = np.random.default_rng(2000).standard_normal((K, NP))
    x = rng.uniform(0, 2 * np.pi, (restarts, NP))
    m, v = np.zeros_like(x), np.zeros_like(x)
    I = np.eye(NP)
    for t in range(1, steps + 1):
        pert = np.concatenate([x[:, None] + fd * I[None], x[:, None] - fd * I[None]], axis=1).reshape(-1, NP)
        vals = noisy_expected_acc(pert, G, eps_loss, sigma, Z).reshape(restarts, 2 * NP)
        g = (vals[:, :NP] - vals[:, NP:]) / (2 * fd)
        m = 0.9 * m + 0.1 * g
        v = 0.999 * v + 0.001 * g ** 2
        x += lr * (m / (1 - 0.9 ** t)) / (np.sqrt(v / (1 - 0.999 ** t)) + 1e-8)
    saa = noisy_expected_acc(x, G, eps_loss, sigma, Z)
    k = int(np.argmax(saa))
    acc, click = noisy_eval(x[k], G, eps_loss, sigma)
    _, psi = forward2(x[k:k + 1], G, eps_loss)
    info = float(logged_info(psi, G)[0])
    pj = np.abs(psi[0]) ** 2                                             # (S, modes)
    phase_w = (pj[:, [1, 3]].sum(axis=1) * (1 - eps_loss))
    plain_w = pj[:, [0, 2]].sum(axis=1)
    balance = float(np.mean(phase_w / np.maximum(plain_w, 1e-12)))
    return {"acc_max": acc, "click_at_max": click, "cond_acc_at_max": acc / max(click, 1e-12),
            "info_opt_bits": info, "post_loss_balance_phase_over_plain": balance}


def reinforce2(gamma, sigma, eps_loss, seeds=range(20), T=4000, ckpt=100, n_eval=64, fd=1e-5):
    G = gram(gamma)
    seeds = list(seeds)
    rngs = [np.random.default_rng(s) for s in seeds]
    nrng = np.random.default_rng(10_000 + seeds[0])
    erng = np.random.default_rng(20_000)
    B = len(seeds)
    ar = np.arange(B)
    x = np.stack([r.uniform(0, 2 * np.pi, NP) for r in rngs])
    base = np.full(B, 0.25)
    I = np.eye(NP)
    curve = []
    for t in range(1, T + 1):
        s = np.array([r.integers(4) for r in rngs])
        xn = x + sigma * nrng.standard_normal(x.shape)
        p, _ = forward2(xn, G, eps_loss)
        pa = p[ar, s]                                                    # (B, A), sums to click prob
        u = np.array([r.random() for r in rngs])
        cum = pa.cumsum(axis=1)
        clicked = u < cum[:, -1]
        a = np.minimum((cum < u[:, None]).sum(axis=1), 3)
        rwd = (clicked & (a == TARGET[s])).astype(float)

        # Score function of the observed outcome: action a if the photon clicked, "no click" otherwise.
        # (Bug fix after independent review: the first version skipped no-click episodes, which adds a
        # bias of -b * grad P(click) under loss. With epsilon = 0 no-click never occurs and nothing changes.)
        pert = np.concatenate([xn[:, None] + fd * I[None], xn[:, None] - fd * I[None]], axis=1)
        pp, _ = forward2(pert.reshape(-1, NP), G, eps_loss)
        pp = pp.reshape(B, 2 * NP, 4, 4)[ar[:, None], np.arange(2 * NP)[None], s[:, None]]   # (B, 2NP, A)
        p_obs = np.where(clicked[:, None], pp[ar[:, None], np.arange(2 * NP)[None], a[:, None]],
                         1.0 - pp.sum(axis=2))
        lp = np.log(np.clip(p_obs, 1e-12, 1.0))
        g = (lp[:, :NP] - lp[:, NP:]) / (2 * fd)
        x += LR * (rwd - base)[:, None] * g
        base = 0.95 * base + 0.05 * rwd
        if t % ckpt == 0:
            if sigma == 0:
                curve.append(acc_and_click(x, G, eps_loss)[0].tolist())
            else:
                Z = erng.standard_normal((n_eval, NP))
                Xn = (x[:, None, :] + sigma * Z[None]).reshape(-1, NP)
                curve.append(acc_and_click(Xn, G, eps_loss)[0].reshape(B, n_eval).mean(axis=1).tolist())
    _, psi = forward2(x, G, eps_loss)
    return np.array(curve), logged_info(psi, G)


def run_condition(cond):
    series, gamma, sigma, eps_loss = cond
    t0 = time.time()
    row = {"series": series, "gamma": gamma, "sigma": sigma, "epsilon": eps_loss}
    row.update(ceiling2(gamma, sigma, eps_loss))
    curve, info_end = reinforce2(gamma, sigma, eps_loss)
    fin = curve[-1]
    row.update({
        "reinforce_final_median": float(np.median(fin)),
        "reinforce_final_q25": float(np.quantile(fin, 0.25)),
        "reinforce_final_q75": float(np.quantile(fin, 0.75)),
        "reinforce_info_end_median": float(np.median(info_end)),
        "seconds": round(time.time() - t0, 1),
    })
    print(json.dumps(row), flush=True)
    return row, curve.tolist()


def rerun_loss_learners():
    """Re-run only the series L learners after the baseline fix; ceilings are unaffected and reused."""
    conds = [("L", g, 0.0, e) for e in EPSILONS for g in GAMMAS]
    with Pool(2) as pool:
        out = pool.map(_learner_only, conds, chunksize=1)
    json.dump({"note": "series L learners re-run after the no-click baseline fix", "rows": [r for r, _ in out],
               "curves": {f"L|{r['gamma']}|0.0|{r['epsilon']}": c for r, c in out}},
              open("QT-S2_L_learners_fixed.json", "w"), indent=2)


def _learner_only(cond):
    series, gamma, sigma, eps_loss = cond
    curve, info_end = reinforce2(gamma, sigma, eps_loss)
    fin = curve[-1]
    row = {"series": series, "gamma": gamma, "sigma": sigma, "epsilon": eps_loss,
           "reinforce_final_median": float(np.median(fin)),
           "reinforce_final_q25": float(np.quantile(fin, 0.25)),
           "reinforce_final_q75": float(np.quantile(fin, 0.75)),
           "reinforce_info_end_median": float(np.median(info_end))}
    print(json.dumps(row), flush=True)
    return row, curve.tolist()


def conditions():
    out = [("N", g, s, 0.0) for s in SIGMAS for g in GAMMAS]
    out += [("L", g, 0.0, e) for e in EPSILONS for g in GAMMAS]
    return out


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "rerun_loss":
        rerun_loss_learners()
        sys.exit()
    if len(sys.argv) > 1 and sys.argv[1] == "smoke":
        t0 = time.time()
        print(ceiling2(1.0, 0.1, 0.0, steps=40), round(time.time() - t0, 1), "s ceiling(40 steps)")
        t0 = time.time()
        c, _ = reinforce2(1.0, 0.1, 0.3, T=200)
        print(c[-1][:3], round(time.time() - t0, 1), "s reinforce(200 eps)")
        sys.exit()
    conds = conditions()
    with Pool(2) as pool:
        out = pool.map(run_condition, conds, chunksize=1)
    rows = [r for r, _ in out]
    curves = {f"{r['series']}|{r['gamma']}|{r['sigma']}|{r['epsilon']}": c for r, c in out}
    json.dump({"lr": LR, "rows": rows}, open("QT-S2_results.json", "w"), indent=2)
    json.dump(curves, open("QT-S2_curves.json", "w"))
    print("done")
