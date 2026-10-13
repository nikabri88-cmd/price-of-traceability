# QT-S2 – Price of traceability under realistic optics

Pre-registration, locked 2026-10-13 before any main run. Follows QT-S1 (same day).
Authors: Julia Ryzhkova, with Claude (Opus 5.5).

## Question

QT-S1 found a non-linear price of traceability in an ideal single-photon learning agent: the first ~0.29 bit of path log per decision cost 5 accuracy points, the last bits cost most. Does this survive realistic photonic hardware, does noisy hardware make auditing cheaper, and does the Flamini et al. (2020) observation that moderate noise is tolerated by learning replicate in this model?

## Model

Identical to QT-S1 (4 modes, one photon, percept s = (b1, b2), b1 sets input mode, b2 delivered only as a phase, learned Clements meshes U1 and U2, log with uniform marker overlap gamma_log, reward 1 if action = 2*b1 + b2), plus two imperfections:

- **Dynamic noise sigma:** on every episode, every mesh parameter (beamsplitter angles and phases of U1 and U2) is perturbed by independent Gaussian noise N(0, sigma^2) rad. U1 output phases are internal path phases, so this includes path dephasing.
- **Path-dependent loss epsilon:** after the phase layer, internal paths 1 and 3 (the paths that carry the b2 phase) transmit with probability 1 - epsilon; paths 0 and 2 are lossless. A lost photon gives no click, no action and reward 0. The log records the path before the loss.

## Conditions

- Series N (noise): gamma_log in {1.0, 0.9, 0.6, 0.2, 0.0} x sigma in {0, 0.05, 0.1, 0.2}, epsilon = 0. 20 conditions.
- Series L (loss): gamma_log in {1.0, 0.9, 0.6, 0.2, 0.0} x epsilon in {0.1, 0.3}, sigma = 0. 10 conditions (epsilon = 0 is shared with series N, sigma = 0).

## Measures

- Ceiling: maximum expected unconditional accuracy (P(click and correct)). Noise is handled by sample-average approximation with 16 fixed noise draws per condition, Adam, 800 steps, 4 restarts; the best restart is re-evaluated on 4000 fresh noise draws. For sigma = 0 the ceiling is exact.
- Logged information I at the ceiling: conditional Holevo information of the log about the internal path given the percept (as QT-S1), from the noiseless path distribution of the optimised parameters.
- Learning agent: REINFORCE, learning rate 0.02 (reused from the QT-S1 pilot, no new tuning), running baseline, 4000 episodes, 20 seeds (0–19). Noise is redrawn each episode; no click means reward 0 and no update. Expected accuracy (64 fresh noise draws) recorded every 100 episodes.
- Also reported: conditional accuracy given a click; at the series L ceilings, the post-loss amplitude balance between the phase-carrying paths and the lossless paths.

## Hypotheses

- **H1 (non-linearity survives).** In every condition with a meaningful price, the cost per logged bit on the last segment (gamma_log 0.6 → 0.2) exceeds the cost per bit on the first segment (gamma_log 1.0 → 0.9) by a factor >= 2. Cost per bit = accuracy drop / increase in I between the two ceilings. QT-S1 reference: about 4.6. Rejected if any condition falls below 2. Conditions where the full-log cost C (below) is under 0.05 are excluded as having no measurable price, and reported separately.
- **H2 (noisy hardware makes auditing cheaper).** The full-log cost C = ceiling(gamma_log = 1) - ceiling(gamma_log = 0) decreases strictly with sigma (series N) and with epsilon (series L). Rejected if any step increases C by more than 0.01.
- **H3 (Flamini replication).** At gamma_log = 1, epsilon = 0, the median learner's final accuracy relative to its ceiling at sigma = 0.05 and at sigma = 0.1 is at least the sigma = 0 value minus 0.02.

## Exploratory (declared, no directional prediction)

- E1: Under path-dependent loss, does the optimal agent rebalance amplitudes to restore interference after loss, and at what cost in click probability?
- E2: Do learners drift further toward classical deliberation (lower loggable path information at the end of training) as sigma grows, at gamma_log in {0.6, 0.2}?

## Declared limits

Same toy limits as QT-S1. Noise model: independent Gaussian on mesh parameters, redrawn per episode; no fabrication offsets, no multi-photon effects, no detector dark counts. Learning rate reused from QT-S1 without re-tuning, which may disadvantage noisy conditions.
