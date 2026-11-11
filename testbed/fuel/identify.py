"""Identify k_cal on tanks 8-17 against refuelled litres (least squares through the origin).

Design constants (not fitted): AFR 14.7 (stoichiometric gasoline), rho 0.745 g/ml, dt_max 5 s (gaps
> 5 s only occur between trips), trim clamp +-25 %, rate_max 400 ml/min, DFCO when THR <= 21.0 % and
RPM > 1600 rpm. DFCO thresholds are NOT identified: a grid (THR 21-24 %, RPM 1300-2000) changed the
mean train error by <= 0.05 pp (explore_ident.py), i.e. the refuel oracle cannot resolve them; they are
set from the throttle distribution (idle median 19.2 %, 1st percentile above 1500 rpm 21.6 %).
Writes spec/baseline.json and spec/identification.json.
"""
import json

import numpy as np

import common
import ref


def main():
    common.check_data()
    r = common.refuel_litres()
    tanks = common.load_tanks(common.TRAIN + common.FIELD)
    spec = {"name": "fuel_flow", "version": "baseline",
            "params": {"k_cal": 1.0, "AFR": 14.7, "rho": 0.745, "dt_max": 5.0, "trim_lim": 25.0,
                       "rate_max": 400.0, "thr_dfco": 21.0, "rpm_dfco": 1600.0},
            "eq": {"s_trim": 1.0, "s_int": 1.0, "dt_scale": 1.0, "dfco": True, "sat": True, "trim_clamp": True}}
    vol1 = {t: ref.run(spec, tanks[t])[1][-1] / 1000.0 for t in tanks}   # litres at k_cal = 1
    tr = common.TRAIN
    k = float(sum(vol1[t] * r[t] for t in tr) / sum(vol1[t] ** 2 for t in tr))
    spec["params"]["k_cal"] = k
    rel = {t: (k * vol1[t] - r[t]) / r[t] * 100.0 for t in tanks}
    ident = {"data_sha256": common.DATA_SHA256, "refuel_sha256": common.REFUEL_SHA256,
             "train": tr, "field": common.FIELD, "k_cal": k,
             "train_rel_err_pct": {t: rel[t] for t in tr},
             "train_mean_abs_err_pct": float(np.mean([abs(rel[t]) for t in tr])),
             "field_rel_err_pct": {t: rel[t] for t in common.FIELD},
             "rows": {t: int(len(tanks[t]["dt"])) for t in tanks}}
    (common.ROOT / "spec").mkdir(exist_ok=True)
    (common.ROOT / "spec" / "baseline.json").write_text(json.dumps(spec, indent=1))
    (common.ROOT / "spec" / "identification.json").write_text(json.dumps(ident, indent=1))
    print(json.dumps(ident, indent=1))


if __name__ == "__main__":
    main()
