"""Requirement-based tests for subject 2 (design requirements set by us, thresholds fixed before any mutant).

Expected values come from the float64 reference with the BASELINE spec (the design intent), computed on
the inputs exactly as written to the vector files (6 decimals).
REQ-1 range: every rate and volume finite, 0 <= rate <= 400 ml/min, volume never decreases (> -1e-6 ml).
REQ-2 accuracy: at every row |rate - exp| <= 0.005*|exp| + 0.01 ml/min and
      |vol - exp| <= 0.005*|exp| + 0.05 ml                                   (all tests except T7).
REQ-3 DFCO: rate <= 1e-6 on every DFCO row of T2.
REQ-4 gap handling: in T5 the volume increment at the 300 s gap row is <= rate*dt_max/60 + 0.05 ml and
      at the negative-dt row is <= 1e-6 ml.
Tests: T1 constant MAF, T2 DFCO window, T3 idle with trims, T4 irregular dt with varying MAF,
T5 long gap and out-of-order timestamp, T6 trims incl. clamp, T7 robustness (REQ-1 only),
T8 real-shaped drive (tank 8 rows 0-2999, an identification tank, never a field tank).
"""
import json

import numpy as np

import common
import ref

COLS = ("dt", "MAF", "RPM", "THR", "STFT", "LTFT")


def _vec(n, **kw):
    v = {c: np.full(n, 0.0) for c in COLS}
    for k, x in kw.items():
        v[k] = np.broadcast_to(np.asarray(x, float), (n,)).copy()
    return v


def build(baseline_spec, tank8=None):
    tests = []

    def add(name, v, extra=None, accuracy=True):
        v = {c: np.round(v[c], 6) for c in COLS}
        r, vol = ref.run(baseline_spec, v)
        tests.append(dict(name=name, v=v, rate=r, vol=vol, accuracy=accuracy, extra=extra or {}))

    add("T1_const_maf", _vec(600, dt=1.0, MAF=10.0, RPM=2500.0, THR=30.0))
    t2 = _vec(120, dt=1.0, MAF=8.0, RPM=2500.0, THR=30.0)
    t2["THR"][30:90], t2["MAF"][30:90] = 20.0, 5.0
    add("T2_dfco", t2, extra={"dfco_rows": list(range(30, 90))})
    add("T3_idle_trims", _vec(300, dt=1.0, MAF=2.0, RPM=750.0, THR=19.0, STFT=3.0, LTFT=2.0))
    rng = np.random.default_rng(204)
    k = np.arange(600)
    add("T4_irregular_dt", _vec(600, dt=rng.uniform(0.8, 1.6, 600), MAF=15.0 + 10.0 * np.sin(k / 40.0),
                                RPM=2000.0 + 500.0 * np.sin(k / 55.0), THR=35.0, STFT=1.0, LTFT=-1.0))
    t5 = _vec(200, dt=1.0, MAF=12.0, RPM=2200.0, THR=32.0)
    t5["dt"][100], t5["dt"][150] = 300.0, -2.0
    add("T5_gap_and_order", t5, extra={"gap_row": 100, "neg_row": 150})
    t6 = _vec(300, dt=1.0, MAF=9.0, RPM=2300.0, THR=31.0, STFT=10.0, LTFT=5.0)
    t6["STFT"][150:], t6["LTFT"][150:] = 60.0, 20.0
    add("T6_trims", t6)
    j = np.arange(300)
    t7 = _vec(300, dt=np.choose(j % 4, [0.0, 0.001, 5.0, 1e4]),
              MAF=np.choose(j % 3, [500.0, -5.0, 0.0]), RPM=(j * 37 % 8000).astype(float),
              THR=(j * 13 % 101).astype(float), STFT=np.where(j % 2, 100.0, -100.0), LTFT=np.where(j % 5, 100.0, -100.0))
    add("T7_robustness", t7, accuracy=False)
    if tank8 is None:
        tank8 = common.load_tanks([8])[8]
    add("T8_drive_tank8", {c: tank8[c][:3000] for c in COLS})
    return tests


def check(test, out):
    """out: dict(rate=array, vol=array). Returns a list of requirement violations (empty = pass)."""
    rate, vol = np.asarray(out.get("rate", []), float), np.asarray(out.get("vol", []), float)
    n = len(test["v"]["dt"])
    name = test["name"]
    if len(rate) != n or len(vol) != n:
        return [f"{name}: length {len(rate)}/{len(vol)} != {n}"]
    fails = []
    if (not np.all(np.isfinite(rate)) or not np.all(np.isfinite(vol)) or rate.min() < 0.0
            or rate.max() > 400.0 or np.any(np.diff(np.concatenate([[0.0], vol])) < -1e-6)):
        fails.append(f"{name}: REQ-1 range/finite/monotone")
        return fails
    if test["accuracy"]:
        er = np.abs(rate - test["rate"]) - (0.005 * np.abs(test["rate"]) + 0.01)
        ev = np.abs(vol - test["vol"]) - (0.005 * np.abs(test["vol"]) + 0.05)
        if er.max() > 0:
            fails.append(f"{name}: REQ-2 rate err max {np.max(np.abs(rate - test['rate'])):.4g}")
        if ev.max() > 0:
            fails.append(f"{name}: REQ-2 vol err max {np.max(np.abs(vol - test['vol'])):.4g}")
    rows = test["extra"].get("dfco_rows")
    if rows and np.max(rate[rows]) > 1e-6:
        fails.append(f"{name}: REQ-3 DFCO rate {np.max(rate[rows]):.4g}")
    if "gap_row" in test["extra"]:
        g, q = test["extra"]["gap_row"], test["extra"]["neg_row"]
        if vol[g] - vol[g - 1] > rate[g] * 5.0 / 60.0 + 0.05:
            fails.append(f"{name}: REQ-4 gap increment {vol[g] - vol[g - 1]:.4g}")
        if vol[q] - vol[q - 1] > 1e-6:
            fails.append(f"{name}: REQ-4 negative-dt increment {vol[q] - vol[q - 1]:.4g}")
    return fails


def write_vector(v, path):
    with open(path, "w") as f:
        f.write(f"{len(v['dt'])}\n")
        for row in zip(*(v[c] for c in COLS)):
            f.write(" ".join(f"{x:.6f}" for x in row) + "\n")


if __name__ == "__main__":
    import sys
    spec = json.load(open(sys.argv[1]))
    for t in build(spec):
        r, vol = ref.run(spec, t["v"])
        print(t["name"], len(r), check(t, dict(rate=r, vol=vol)) or "PASS (float64 reference)")
