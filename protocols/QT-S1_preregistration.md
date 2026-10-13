# QT-S1 – Price of traceability in a single-photon learning agent

Pre-registration, locked 2026-10-13 before any main run.
Authors: Julia Ryzhkova, with Claude (Opus 5.5).

## Question

A photonic learning agent (cf. Flamini et al., New J. Phys. 22, 045002, 2020) deliberates by sending one photon through a mesh of tunable beamsplitters. If we keep a log of which internal path the photon took, interference between paths is suppressed (Englert duality, D^2 + V^2 <= 1). How much task performance does the agent lose per bit of logged deliberation?

## Model

- 4 optical modes, one photon.
- Percept s = (b1, b2), b1, b2 in {0, 1}, uniform.
- b1 sets the input mode (classically readable). b2 is delivered only as a phase: diag(1, e^{i pi b2}, 1, e^{i pi b2}) on the internal paths.
- Agent = two learned 4x4 unitaries U1 (before the phase layer) and U2 (after it), each a Clements mesh of 6 MZIs plus 4 output phases (16 parameters each, 32 total).
- Log: each internal path j leaves a marker state |m_j> with uniform pairwise overlap gamma = <m_j|m_k>. gamma = 1: no log. gamma = 0: complete which-path log.
- Internal state after logging: rho_jk = psi_j psi_k* gamma_jk. Action a = detected output mode of U2.
- Reward 1 if a = 2*b1 + b2, else 0.
- gamma grid: 1.0, 0.95, 0.9, 0.8, 0.6, 0.4, 0.2, 0.0. Pairwise path distinguishability D = sqrt(1 - gamma^2).

## Measures

- M1 Ceiling: maximum expected accuracy at each gamma, by direct gradient ascent on the exact expected reward (Adam, 1500 steps, 10 random restarts, best restart reported).
- M2 Learning agent: REINFORCE with a running reward baseline, one episode per update, 4000 episodes, 20 seeds (0–19). Exact expected accuracy of the current policy recorded every 100 episodes.
- Logged information I: conditional Holevo information of the log about the internal path given the percept, I = E_s S( sum_j p_j(s) |m_j><m_j| ), in bits per decision, computed at the M1 optimum and at the end of M2.
- Episodes-to-criterion: first checkpoint where expected accuracy >= 0.9 x M1 ceiling at that gamma.

## Learning-rate pilot (declared)

Learning rate chosen from {0.02, 0.05, 0.1, 0.2} by best mean final accuracy at gamma = 1 only, on pilot seeds 100–119. Main seeds 0–19 are not used in the pilot.

## Hypotheses

- H1 (ceiling). Maximum accuracy = (1 + gamma)/2 at every gamma. Rejected if any |acc_max - (1 + gamma)/2| > 0.02.
- H2 (non-linear price). At the M1 optimum, I = H2(acc_max), with H2 the binary entropy. Rejected if any |I - H2(acc_max)| > 0.03 bits. Consequence to report: the first ~0.29 bit of log per decision costs at most 5 accuracy points; going from 0.5 to 1.0 bit costs at least 35 points.
- H3 (learning, directional, exploratory). Episodes-to-criterion grow as gamma falls (Spearman rho between gamma and median episodes-to-criterion < 0), and the median seed reaches criterion at all gamma >= 0.8.

## Declared limits

- Toy model: 4 modes, uniform marker overlaps, no optical loss or noise.
- The task bit b2 exists only as a phase by construction, so the measured price applies only to task information carried by interference. No claim of quantum advantage over classical agents in general.
- H1 and H2 follow analytically from the duality relation; the simulation checks the derivation and whether a reward-driven learner reaches the bound.
