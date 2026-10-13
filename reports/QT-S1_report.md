# QT-S1 – Results

Price of traceability in a single-photon learning agent. Run 2026-10-13 against the pre-registration locked the same day (QT-S1_preregistration.md).

## Pilot

Learning rate chosen at gamma = 1 on seeds 100–119, mean final accuracy: 0.02 → 0.852, 0.05 → 0.784, 0.1 → 0.683, 0.2 → 0.662. Chosen: 0.02. It sits at the lower edge of the declared grid, so a smaller rate may learn better; this was left untested by protocol.

## Price of traceability (M1 ceiling)

| gamma | pairwise D | logged path info, bits/decision | max accuracy | cost, points |
|---|---|---|---|---|
| 1.0 | 0.00 | 0.00 | 1.000 | 0 |
| 0.95 | 0.31 | 0.17 | 0.975 | 2.5 |
| 0.9 | 0.44 | 0.29 | 0.950 | 5 |
| 0.8 | 0.60 | 0.47 | 0.900 | 10 |
| 0.6 | 0.80 | 0.72 | 0.800 | 20 |
| 0.4 | 0.92 | 0.88 | 0.700 | 30 |
| 0.2 | 0.98 | 0.97 | 0.600 | 40 |
| 0.0 | 1.00 | 0.00 (see H2) | 0.500 | 50 |

## Hypotheses

- **H1 supported.** Maximum accuracy equals (1 + gamma)/2 at all eight gamma values, to numerical precision.
- **H2 rejected as pre-registered.** For every gamma > 0 the optimum satisfies I = H2(accuracy) to 1e-12 bits. At gamma = 0 the best optimum holds 0 bits instead of 1 bit (deviation 1.0 > 0.03). Cause: with a complete log, interference brings no benefit, so a single-path deliberation is equally optimal, and the optimiser settled on it. The bound holds for agents that keep a superposition; gamma = 0 is a degenerate optimum.
- **H3a formally supported, weak.** Spearman rho between gamma and median episodes-to-criterion = -0.19. The relation is non-monotone: slowest learning at gamma = 0.4 (3800 episodes) and 0.6 (1550), fast at 0.2 (1050) and 0.0 (250), where the criterion is relative to a low ceiling.
- **H3b supported.** At gamma >= 0.8, 17–18 of 20 seeds reach 90% of the ceiling.

## Findings

1. **The price is non-linear.** The first 0.29 bit of path log per decision costs 5 accuracy points. Going from 0.47 to 0.97 bit costs 30 points. Partial traceability is cheap; the last bits are expensive.
2. **A complete log turns the optimal agent classical.** At gamma = 0 the best agent stops using superposition: its deliberation becomes a single path, fully traceable and blind to phase-carried task information.
3. **Exploratory, not pre-registered: learners under heavy logging drift classical.** At gamma = 0.2 learning agents end with 0.55 bit of loggable path information versus 0.97 at the ceiling; at gamma = 0 they end at 0.07 bit. Median learners reach 91–100% of their ceiling at every gamma.

## Reading for agent governance

Requiring a complete record of a quantum agent's deliberation does two things at once: it removes the part of performance carried by interference, and it pushes the agent toward classical deliberation. Requiring a partial record is cheap. In this toy, auditing at the level of inputs, outputs, learned parameters and run statistics costs nothing, and each bit of per-decision path record has a measurable price set by the Englert duality relation.

## Limits

Toy model: 4 modes, uniform marker overlaps, no loss or noise, one task bit carried only by phase by construction. The price applies only to task information carried by interference; no claim of quantum advantage over classical agents in general. H1 and the gamma > 0 part of H2 follow analytically from the duality relation; the new content is the degenerate optimum at gamma = 0 and the behaviour of reward-driven learners.

## Files

protocols/QT-S1_preregistration.md, src/qt_s1_sim.py, qt_s1_analyze.py, QT-S1_pilot.json, QT-S1_results.json, QT-S1_curves.json, QT-S1_summary.csv, QT-S1_tests.json, QT-S1_figure.png. Reproduce: see "How to run" in the repository README.
