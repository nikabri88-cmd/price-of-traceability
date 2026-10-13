# Price of traceability

What happens to a quantum learning agent when you keep a record of how it decides?

This repository holds two small simulation studies of a photonic learning agent in the spirit of Flamini et al. (New J. Phys. 22, 045002, 2020). The agent deliberates by sending one photon through a mesh of tunable beamsplitters; the detected output mode is its action. We add a which-path marker that becomes correlated with the photon's internal path, with adjustable strength, and measure how much task performance the best agent loses per bit of path information the marker holds. That information is the Holevo quantity χ: an upper bound on what any readout of the marker could extract. The marker readout itself is not simulated.

The trade-off itself follows from the Englert duality relation (D² + V² ≤ 1): recording the path suppresses interference. The studies ask what that means for a reward-driven agent, and how it behaves on imperfect hardware.

## Results in brief

**QT-S1, ideal optics** ([report](reports/QT-S1_report.md))

- The first bits are cheap: a marker holding up to 0.29 bit per decision costs 5 accuracy points.
- The last bits are expensive: the last half bit (0.5 → 1 bit) costs 39 points.
- Under complete monitoring the best accuracy is 50%, no better than a classical agent. The optimum is degenerate there: single-path and superposed agents score the same, so superposition becomes useless without being forced out.
- Learning agents end with less path superposition under heavy monitoring than the optimum uses (exploratory).

![QT-S1](results/QT-S1/QT-S1_figure.png)

**QT-S2, mirror noise and photon loss** ([report](reports/QT-S2_report.md))

- The shape of the price survives mirror noise: the last bits cost about 4.6 times more per bit than the first ones at every noise level tested.
- Imperfect hardware loses less to complete monitoring in absolute terms: at 0.2 rad of noise it costs 0.32 accuracy instead of 0.50.
- With 30% photon loss on the phase-carrying paths, stronger monitoring shifts the optimum toward the lossless paths (share of probability on the lossy paths 41% with no monitoring, 17% at gamma_log = 0.2) and reduces its use of interference. Accuracy stays above the classical 50% (53.7% at gamma_log = 0.2).
- Learning tolerates mirror noise up to 0.2 rad.

![QT-S2](results/QT-S2/QT-S2_figure.png)

**Post-hoc check, not pre-registered** (`src/qt_s2_posthoc_dense.py`, `results/QT-S2/QT-S2_posthoc_dense_loss.json`)

The pre-registered grid had four log levels, so a chart connecting them hid the shape of the loss curve. A dense grid (log strength in steps of 0.05, exact ceilings) shows it: with 30% loss the path information held by the marker rises to 0.77 bit at gamma_log = 0.4 and then falls to 0.13 bit at gamma_log = 0.05, as the optimum moves the photon off the lossy paths. With ideal optics the ceiling follows the QT-S1 bound at all 20 levels.

## Closed form

For the noiseless model the ceiling has a closed form, found in an independent review of this repository:

A_max = (2 - ε + sqrt(ε² + 4γ²(1 - ε))) / 4,

with ε the loss on the phase-carrying paths and γ the coherence the marker leaves. It matches all 63 stored noiseless ceilings to 5e-12 and reduces to (1 + γ)/2 at ε = 0. The shift of the optimum under loss therefore follows from the optics of the task itself; the figures show direct optimisation, not learning trajectories.

## Corrections after independent review (2026-10-13)

1. **Axis meaning.** Earlier text called the x-axis "logged bits". It is the Holevo information χ of the which-path marker, an upper bound on extractable path information; no readout is simulated.
2. **Complete monitoring.** Earlier text said the optimal agent "drops superposition". The optimum is degenerate: QT-S1 found a single-path solution (0 bit), QT-S2 under identical conditions found one holding 0.49 bit, and an equal two-path superposition (1 bit) scores the same 50%. Interference becomes useless; superposition is not forced out.
3. **Loss.** Earlier text said the agent "retreats from superposition". It shifts probability toward lossless paths and uses interference less, while staying above 50%.
4. **Arithmetic.** Earlier text said "the next half bit costs 30 points". From 0.29 to 0.79 bit the cost is 18.5 points; the 30 points belong to the step from 0.47 to 0.97 bit, and the last half bit (0.5 → 1) costs 39.
5. **Learning under loss (code bug).** `reinforce2()` skipped episodes where the photon was lost. With a reward baseline b this adds a bias of -b ∇P(click). Fixed by including the no-click outcome in the score function; the loss-series learners were re-run (`results/QT-S2/QT-S2_L_learners_fixed.json`). Ceilings and all lossless results are unaffected; the fixed code reproduces the lossless learner curves exactly.

## Hypothesis verdicts

| Study | Hypothesis | Verdict |
|---|---|---|
| QT-S1 | H1 ceiling = (1 + gamma)/2 | supported |
| QT-S1 | H2 marker path information (χ) = H2(accuracy) at the optimum | rejected as stated: holds for every gamma > 0, fails at gamma = 0 (degenerate optimum) |
| QT-S1 | H3 learning slows as the log grows | formally supported, weak (rho = -0.19) |
| QT-S2 | H1 non-linear price survives noise and loss | supported on 5 of 6 settings, undefined on 1 |
| QT-S2 | H2 imperfect hardware lowers the full-log cost | supported |
| QT-S2 | H3 Flamini replication: noise tolerated by learning | rejected by 0.001; tolerance replicated in substance, no benefit observed |

## Read this before citing

- **Toy model.** 4 modes, one photon, uniform which-path marker overlaps. The task bit that the log destroys is delivered only as a phase by construction, so the price applies to task information carried by interference. No claim of quantum advantage over classical agents in general.
- **Protocols.** Each protocol in `protocols/` was written and fixed before its main run, within the same working session. It carries no external timestamp, so treat it as a protocol fixed before the run rather than an independently registered pre-registration.
- **Tooling.** The studies were designed, coded and analysed with Claude (Opus 5.5, Anthropic) under the direction of Julia Ryzhkova.
- **Hardware realism.** Noise of 0.2 rad is large compared with phase errors typical for integrated photonics; numbers describe the model and carry no claim about a specific chip.

## How to run

Python 3.10+, numpy, matplotlib (`pip install -r requirements.txt`). Scripts read and write in the current folder.

```bash
# QT-S1 (about 4 min pilot + 9 min main on one core)
cd results/QT-S1
python ../../src/qt_s1_sim.py pilot
python ../../src/qt_s1_sim.py main 0.02
python ../../src/qt_s1_analyze.py

# QT-S2 (about 18 min on two cores)
cd ../QT-S2
python ../../src/qt_s2_sim.py
python ../../src/qt_s2_analyze.py
python ../../src/qt_s2_sim.py rerun_loss   # series L learners after the baseline fix, about 15 min
python ../../src/qt_s2_posthoc_dense.py   # post-hoc dense grid, about 3 min

# Images for the X post
cd ../..
python social/x_figures.py
```

All randomness is seeded; with the same numpy version the results files are reproduced.

## Layout

```
protocols/   study protocols, fixed before each main run
src/         simulation and analysis code (QT-S2 reuses the QT-S1 model)
results/     raw results, learning curves, summaries, hypothesis tests, figures, run logs
reports/     results and interpretation for each study
social/      images used in public posts and the script that draws them from results/
```

## Related work

- F. Flamini et al., Photonic architecture for reinforcement learning, New J. Phys. 22, 045002 (2020).
- B.-G. Englert, Fringe visibility and which-way information: an inequality, Phys. Rev. Lett. 77, 2154 (1996).
- H. J. Briegel, G. De las Cuevas, Projective simulation for artificial intelligence, Sci. Rep. 2, 400 (2012).
- H. J. Briegel, T. Müller, A chance for attributable agency, Minds and Machines 25, 261 (2015).
- H.-Y. Huang et al., Quantum advantage in learning from experiments, Science 376, 1182 (2022).

## Feedback welcome

Physicists especially: is the shift of the optimum toward lossless paths under path monitoring already known from the which-path literature, and what would break first on a real integrated chip? Please open an issue.

## Citation and license

Cite via `CITATION.cff`. Code: MIT License. Protocols, reports and figures: CC BY 4.0.
