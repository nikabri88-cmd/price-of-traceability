# QT-S2 – Results

Price of traceability under realistic optics. Run 2026-10-13 against the pre-registration locked the same day (QT-S2_preregistration.md). 30 conditions, 20 learner seeds each.

## Built-in replication check

With sigma = 0 and epsilon = 0 the learner results reproduce QT-S1 exactly (median final accuracy 0.949, 0.932, 0.734, 0.547, 0.498 at gamma_log 1, 0.9, 0.6, 0.2, 0), as expected from identical seeds and code path.

## Price of traceability by hardware setting (ceilings)

| setting | ceiling, no log | full-log cost C | cost per bit, first segment | cost per bit, last segment | ratio |
|---|---|---|---|---|---|
| sigma 0 | 1.000 | 0.500 | 0.175 | 0.803 | 4.60 |
| sigma 0.05 | 0.983 | 0.486 | 0.170 | 0.776 | 4.57 |
| sigma 0.1 | 0.936 | 0.447 | 0.157 | 0.710 | 4.54 |
| sigma 0.2 | 0.777 | 0.318 | 0.113 | 0.523 | 4.65 |
| epsilon 0.1 | 0.950 | 0.450 | 0.166 | 0.906 | 5.46 |
| epsilon 0.3 | 0.850 | 0.350 | 0.148 | undefined | undefined |

First segment: gamma_log 1.0 → 0.9. Last segment: gamma_log 0.6 → 0.2. Cost per bit = accuracy drop per bit of added path log.

## Hypotheses

- **H1 supported on 5 of 6 settings, undefined on 1.** Ratios 4.5–5.5 against the threshold of 2. At epsilon = 0.3 the ratio is undefined: between gamma_log 0.6 and 0.2 the loggable information falls (0.68 → 0.63 bit), because the optimal agent moves amplitude away from the lossy phase-carrying paths. This setting is reported as undefined and kept out of the pass count.
- **H2 supported.** C falls with sigma (0.500, 0.486, 0.447, 0.318) and with epsilon (0.500, 0.450, 0.350). Under loss, C = 0.5 - epsilon/2 to numerical precision.
- **H3 rejected, by 0.001.** Median learner accuracy relative to the ceiling at gamma_log = 1: sigma 0 → 0.949, sigma 0.05 → 0.928 (threshold 0.929), sigma 0.1 → 0.948, sigma 0.2 → 0.946. Substantively, noise up to 0.2 rad keeps learners within 2.1 points of their noiseless relative performance. This replicates the tolerance part of Flamini et al. (2020); the benefit part was not observed. The learning rate was reused from QT-S1 without re-tuning.

## Exploratory

- **E1, loss compensation.** With no log, the optimal agent takes an intermediate strategy: it puts less amplitude into the lossy path (pre-loss weight ratio about 1 - epsilon; post-loss balance 0.81 at epsilon 0.1 and 0.49 at 0.3), trading a little interference for more clicks. Ceiling = 1 - epsilon/2; accuracy given a click 0.997 and 0.970. A heavier log strengthens the retreat (post-loss balance 0.14 at gamma_log 0.2, epsilon 0.3).
- **E2, classical drift of learners.** End-of-training loggable information shows no trend with sigma (gamma_log 0.6: 0.72–0.74 bit; gamma_log 0.2: 0.52–0.61 bit against ceilings of 0.97–1.01). The QT-S1 drift toward classical deliberation under a heavy log replicates at every noise level.
- At gamma_log = 0 the optimum stays degenerate (any path distribution gives accuracy 0.5), so logged information there carries no meaning. With sigma = 0.2 the noisy optimum spreads amplitude over more than two paths, so its loggable information slightly exceeds 1 bit (the measure allows up to 2 bits with 4 paths).

## Post-hoc check (not pre-registered)

A dense grid of log strength (steps of 0.05, exact ceilings, sigma = 0) for epsilon = 0 and 0.3 (src/qt_s2_posthoc_dense.py). With 30% loss, loggable path information peaks at 0.77 bit at gamma_log = 0.4 and falls to 0.13 bit at gamma_log = 0.05; the retreat is smooth across levels. The pre-registered values at gamma_log 0.6 and 0.2 are reproduced with 16 restarts and 1500 steps. With ideal optics the ceiling matches I = H2(accuracy) at all 20 levels.

## Findings

1. **The shape of the price survives mirror noise.** Noise scales the price curve down and keeps its convexity: the last bits cost about 4.6 times more per bit than the first ones at every sigma tested.
2. **Imperfect hardware is cheaper to audit in absolute terms.** It has less interference to lose: at sigma = 0.2 rad a complete log costs 0.32 accuracy instead of 0.50.
3. **Photon loss makes the agent retreat from superposition earlier.** In QT-S1 the retreat appeared only under a complete log. With 30% loss on the phase-carrying paths it starts already at a partial log.
4. **Learning tolerates mirror noise up to 0.2 rad.**

## Reading for agent governance

Audit demands and hardware imperfections interact. The more imperfect the hardware, the cheaper a complete audit, and the sooner the agent answers audit pressure by deliberating classically. On lossy hardware, a per-decision log buys traceability partly by shrinking what there is to trace.

## Limits

Same toy limits as QT-S1. Simple noise model (independent Gaussian on mesh parameters, redrawn per episode); no fabrication offsets, dark counts or multi-photon effects. sigma = 0.2 rad is large compared with phase errors typical for integrated photonics, so the numbers describe the model and carry no claim about specific chips. Learning rate not re-tuned for noisy conditions.

## Files

protocols/QT-S2_preregistration.md, src/qt_s2_sim.py, qt_s2_analyze.py, qt_s1_sim.py (shared model code), QT-S2_results.json, QT-S2_curves.json, QT-S2_summary.csv, QT-S2_tests.json, QT-S2_figure.png, qt_s2_log.txt. Reproduce: see "How to run" in the repository README.
