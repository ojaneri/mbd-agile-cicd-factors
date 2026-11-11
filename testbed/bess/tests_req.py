"""Requirement-based tests for subject 3 (design requirements set by us, thresholds fixed before any mutant).

Expected values come from the float64 reference with the BASELINE spec (the design intent), computed on
the inputs exactly as written to the vector files (6 decimals).
REQ-1 range: every t_est and der finite, -40 <= t_est <= 90 degC, 0.5 - 1e-6 <= der <= 1 + 1e-6.
REQ-2 accuracy (all tests except T6): every row |t_est - exp| <= 0.01 + 1e-4*|exp| degC, and at most 3 rows
      with |der - exp| > 1e-3 (slack for a float32/float64 tie at a threshold crossing).
REQ-3 protection (T3, T5): at most 3 rows where the reference is derated (exp der <= 0.5) and der > 0.5 + 1e-6.
REQ-4 recovery ramp (all tests except T6): der never rises by more than 0.002*5 + 1e-6 per row.
REQ-5 reset (T5): der at the reset row 300 is 1 (>= 1 - 1e-6).
Tests: T1 rest, T2 constant 150 A, T3 heat soak and cool-down (latch, dwell, release), T4 charge/discharge
steps, T5 segment reset while derated, T6 robustness (REQ-1 only), T7 a real-shaped segment (the first
training segment of rack 1, rows 0-2999; an identification segment, never a field segment).
"""
import json

import numpy as np

import common
import ref

COLS = ("rst", "I", "TREF")
D_LIM, RAMP_ROW = 0.5, 0.002 * 5.0


def _vec(n, **kw):
    v = {c: np.full(n, 0.0) for c in COLS}
    v["rst"][0] = 1.0
    for k, x in kw.items():
        v[k] = np.broadcast_to(np.asarray(x, float), (n,)).copy()
    v["rst"][0] = 1.0
    return v


def build(baseline_spec, seg=None):
    tests = []

    def add(name, v, extra=None, accuracy=True):
        v = {c: np.round(v[c], 6) for c in COLS}
        t, d = ref.run(baseline_spec, v)
        tests.append(dict(name=name, v=v, te=t, der=d, accuracy=accuracy, extra=extra or {}))

    add("T1_rest", _vec(600, I=0.0, TREF=25.0))
    add("T2_const_current", _vec(1500, I=150.0, TREF=26.0))
    k = np.arange(1200, dtype=float)
    tr3 = np.interp(k, [0, 300, 500, 700, 1199], [26.0, 33.0, 33.0, 27.0, 27.0])
    add("T3_heat_soak", _vec(1200, I=100.0, TREF=tr3), extra={"protect": True})
    k4 = np.arange(800)
    add("T4_steps", _vec(800, I=np.choose((k4 // 100) % 3, [160.0, -160.0, 0.0]), TREF=28.0))
    t5 = _vec(600, I=80.0, TREF=33.0)
    t5["TREF"][300:], t5["rst"][300] = 25.0, 1.0
    add("T5_reset_derated", t5, extra={"protect": True, "reset_row": 300})
    j = np.arange(300)
    t6 = _vec(300, I=np.choose(j % 4, [1e4, -1e4, 0.0, 400.5]), TREF=np.choose(j % 3, [-60.0, 120.0, 25.0]))
    t6["rst"][::50] = 1.0
    add("T6_robustness", t6, accuracy=False)
    if seg is None:
        segs = common.load_segments(("202410",), ["1"])
        seg = next(iter(segs.values()))
    n = min(3000, len(seg["I"]))
    v7 = dict(rst=np.zeros(n), I=seg["I"][:n], TREF=seg["TREF"][:n])
    v7["rst"][0] = 1.0
    add("T7_real_segment", v7)
    return tests


def check(test, out):
    """out: dict(te=array, der=array). Returns a list of requirement violations (empty = pass)."""
    te, der = np.asarray(out.get("te", []), float), np.asarray(out.get("der", []), float)
    n = len(test["v"]["I"])
    name = test["name"]
    if len(te) != n or len(der) != n:
        return [f"{name}: length {len(te)}/{len(der)} != {n}"]
    fails = []
    if (not np.all(np.isfinite(te)) or not np.all(np.isfinite(der)) or te.min() < -40.0 or te.max() > 90.0
            or der.min() < D_LIM - 1e-6 or der.max() > 1.0 + 1e-6):
        return [f"{name}: REQ-1 range/finite"]
    if test["accuracy"]:
        et = np.abs(te - test["te"]) - (0.01 + 1e-4 * np.abs(test["te"]))
        if et.max() > 0:
            fails.append(f"{name}: REQ-2 t_est err max {np.max(np.abs(te - test['te'])):.4g}")
        nd = int(np.sum(np.abs(der - test["der"]) > 1e-3))
        if nd > 3:
            fails.append(f"{name}: REQ-2 der mismatch rows {nd}")
        rise = np.diff(der)
        rst = test["v"]["rst"][1:] > 0.5
        if np.any(rise[~rst] > RAMP_ROW + 1e-6):
            fails.append(f"{name}: REQ-4 ramp rise max {rise[~rst].max():.4g}")
    if test["extra"].get("protect"):
        miss = int(np.sum((test["der"] <= D_LIM + 1e-9) & (der > D_LIM + 1e-6)))
        if miss > 3:
            fails.append(f"{name}: REQ-3 protection missed rows {miss}")
    r = test["extra"].get("reset_row")
    if r is not None and der[r] < 1.0 - 1e-6:
        fails.append(f"{name}: REQ-5 der at reset {der[r]:.4g}")
    return fails


def write_vector(v, path):
    with open(path, "w") as f:
        f.write(f"{len(v['I'])}\n")
        for row in zip(*(v[c] for c in COLS)):
            f.write(" ".join(f"{x:.6f}" for x in row) + "\n")


if __name__ == "__main__":
    import sys
    spec = json.load(open(sys.argv[1]))
    for t in build(spec):
        tt, d = ref.run(spec, t["v"])
        print(t["name"], len(tt), "derated rows", int(np.sum(d < 1)),
              check(t, dict(te=tt, der=d)) or "PASS (float64 reference)")
