"""QT-S2 post-hoc check (not pre-registered): dense log-completeness grid for ideal optics and 30% path loss.

Purpose: check the shape of the loss curve between the pre-registered gamma levels (1.0, 0.9, 0.6, 0.2),
after the X-post figure was found to connect them with straight lines. Exact ceilings (no noise),
8 restarts x 1000 Adam steps per point.
Run from results/QT-S2:  python ../../src/qt_s2_posthoc_dense.py
"""
import json

import numpy as np

from qt_s2_sim import ceiling2

GRID = [round(g, 2) for g in np.arange(1.0, 0.0, -0.05)]
out = {"note": "post-hoc, not pre-registered", "restarts": 8, "steps": 1000, "rows": []}
for eps in (0.0, 0.3):
    for g in GRID:
        r = ceiling2(g, 0.0, eps, restarts=8, steps=1000)
        r.update({"gamma": g, "epsilon": eps})
        out["rows"].append(r)
        print(eps, g, round(r["acc_max"], 4), round(r["info_opt_bits"], 3), flush=True)
json.dump(out, open("QT-S2_posthoc_dense_loss.json", "w"), indent=2)
