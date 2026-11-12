"""E2 robustness (added 2026-11-11 AFTER E2 run 1; exploratory, t-0042 + t-0043).

1. Interval fix (t-0042): run 1 used a percentile bootstrap of the median, which on these discrete,
   heavily tied outcomes can put the median outside its own interval. Here every median carries a
   distribution-free 95 % CI from order statistics (binomial method), which always contains the median.
2. Sensitivity sweep (t-0043): the replay's latency follows from the assumed commit spacing DT_COMMIT and
   defect probability P_DEFECT. Both are swept: DT_COMMIT in {0.5, 2, 8} h, P_DEFECT in {0.1, 0.3, 0.5}.
   Everything else is the frozen e2.py model (same seed, R, stage costs and E1 verdicts), imported unchanged.
Usage: python e2_sweep.py            (both subjects; writes e2_sweep.json next to this file in results/)
"""
import importlib.util
import json
import math
import pathlib
import sys

import numpy as np
from scipy.stats import binom

HERE = pathlib.Path(__file__).resolve().parent
SUBJECTS = {"S1": HERE / "soc", "S2": HERE / "fuel"}
DTS = (0.5, 2.0, 8.0)
PS = (0.1, 0.3, 0.5)
CELLS = ("A0|b1|auto", "A1|b1|auto", "A2|b1|auto", "A2|b10|auto", "A3|b1|auto", "A3|b5|auto",
         "A3|b10|auto", "A3|b1|manual_8h")


def load_e2(subject_dir):
    sys.path.insert(0, str(subject_dir))
    for m in ("common", "e2"):
        sys.modules.pop(m, None)
    spec = importlib.util.spec_from_file_location("e2", subject_dir / "e2.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    sys.path.pop(0)
    return mod


def median_ci(x, conf=0.95):
    """Median with an order-statistic CI (exact binomial, distribution-free, valid for ties)."""
    x = np.sort(np.asarray([v for v in x if not (isinstance(v, float) and math.isnan(v))], float))
    n = len(x)
    if n == 0:
        return [float("nan")] * 3
    a = (1 - conf) / 2
    lo = int(binom.ppf(a, n, 0.5))            # 0-based index of the lower order statistic
    hi = int(binom.ppf(1 - a, n, 0.5))
    lo, hi = max(lo - 1, 0), min(hi, n - 1)
    return [float(np.median(x)), float(x[lo]), float(x[hi])]


def main():
    out = {"note": __doc__.strip().splitlines()[0], "DT_COMMIT_h": DTS, "P_DEFECT": PS, "subjects": {}}
    for sname, sdir in SUBJECTS.items():
        e2 = load_e2(sdir)
        det, rel, cost, ids = e2.load(str(sdir / "results" / "e1_qemu.jsonl"),
                                      str(sdir / "protocol" / "calibration_iotnode.json"))
        sres = {"stage_cost_s": cost, "n": len(ids), "grid": {}}
        for dt in DTS:
            for p in PS:
                e2.DT_COMMIT, e2.P_DEFECT = dt, p
                res = e2.simulate(det, rel, cost, e2.SEED)
                cell = {}
                for k in CELLS:
                    cell[k] = {m: median_ci(res[k][m]) for m in ("latency_h", "escapes", "compute_s")}
                    cell[k]["escapes_mean"] = float(np.mean(res[k]["escapes"]))
                cell["A3_over_A2_compute_b1"] = cell["A3|b1|auto"]["compute_s"][0] / cell["A2|b1|auto"]["compute_s"][0]
                sres["grid"][f"dt{dt}|p{p}"] = cell
        out["subjects"][sname] = sres
        print(sname, "done")
    path = HERE / "e2_sweep.json"
    path.write_text(json.dumps(out, indent=1))
    # compact view
    for sname, s in out["subjects"].items():
        for key, c in s["grid"].items():
            f = lambda k, m: c[k][m]
            print(sname, key,
                  "lat b1 A3 %.0fs [%.0f,%.0f]" % tuple(3600 * v for v in f("A3|b1|auto", "latency_h")),
                  "lat b10 A3 %.1fh [%.1f,%.1f]" % tuple(f("A3|b10|auto", "latency_h")),
                  "comp A2 b1 %.0fs A3 b1 %.0fs ratio %.1f" % (f("A2|b1|auto", "compute_s")[0], f("A3|b1|auto", "compute_s")[0],
                                                             c["A3_over_A2_compute_b1"]),
                  "esc A0 %.1f A1 %.2f A2 %.2f" % (c["A0|b1|auto"]["escapes_mean"], c["A1|b1|auto"]["escapes_mean"],
                                                  c["A2|b1|auto"]["escapes_mean"]))
    print("wrote", path)


if __name__ == "__main__":
    main()
