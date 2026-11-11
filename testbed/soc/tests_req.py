"""Requirement-based tests for subject 1 (design requirements set by us, thresholds fixed before any mutant).

REQ-1 range: every output finite and 0 <= soc <= 1 (all tests).
REQ-2 tracking at 1C discharge:      T1, |err| <= 0.03 after the initial rest.
REQ-3 dynamic pulses:                T2, |err| <= 0.03 over the whole profile.
REQ-4 convergence from +0.3 error:   T3, |err| <= 0.03 for t >= 1200 s.
REQ-5 correction at prolonged rest:  T4, |err| <= 0.01 for t >= 2400 s.
REQ-6 robustness, extreme inputs:    T5, REQ-1 only.
REQ-7 near-empty operation:          T6, |err| <= 0.05 over the whole profile.
Vectors come from the synthetic plant with the BASELINE identified parameters (the "real cell"),
measurement noise sigma_V = 2 mV, sigma_I = 10 mA, fixed seeds. Truth = plant SoC.
"""
import json

import numpy as np

import ref


def _profile(segments):
    return np.concatenate([np.full(int(d), float(i)) for d, i in segments])


def build(baseline_spec):
    p = baseline_spec["params"]
    tests = []

    def add(name, I, soc0, override, window, tol, seed, extra=None):
        rng = np.random.default_rng(seed)
        S, Vm, Im = ref.plant(p, I, soc0, rng, sigma_v=0.002, sigma_i=0.01)
        tests.append(dict(name=name, I=Im, V=Vm, truth=S, override=override,
                          window=window, tol=tol, extra=extra or {}))

    add("T1_1C_discharge", _profile([(60, 0), (2400, -3.0)]), 1.0, -1.0, (60, None), 0.03, 101)
    # Net -90 As per 120 s period -> 0.75 Ah over 30 periods (0.90 -> 0.65). An earlier draft discharged
    # 3.75 Ah (more than the cell) and drove the true SoC negative; fixed before the protocol freeze.
    pulse = np.tile(_profile([(30, -6.0), (30, 6.0), (30, -12.0), (30, 9.0)]), 30)
    add("T2_pulses", np.concatenate([np.zeros(60), pulse]), 0.9, -1.0, (0, None), 0.03, 102)
    add("T3_convergence", _profile([(10, 0), (2400, -1.5)]), 0.6, 0.9, (1200, None), 0.03, 103)
    add("T4_rest_correction", np.zeros(3600), 0.5, 0.7, (2400, None), 0.01, 104)
    t5 = np.where((np.arange(600) // 10) % 2 == 0, 20.0, -20.0)
    tests.append(dict(name="T5_robustness", I=t5,
                      V=np.where((np.arange(600) // 7) % 2 == 0, 2.5, 4.3),
                      truth=None, override=0.5, window=None, tol=None, extra={}))
    add("T6_near_empty", _profile([(60, 0), (600, -3.0), (300, 0)]), 0.15, -1.0, (0, None), 0.05, 106)
    return tests


def check(test, out):
    """Return a list of requirement violations (empty = pass)."""
    out = np.asarray(out, float)
    fails = []
    if len(out) != len(test["I"]):
        return [f"{test['name']}: length {len(out)} != {len(test['I'])}"]
    if not np.all(np.isfinite(out)) or out.min() < 0.0 or out.max() > 1.0:
        fails.append(f"{test['name']}: REQ-1 range/finite")
    if test["truth"] is not None and np.all(np.isfinite(out)):
        a, b = test["window"]
        err = np.abs(out - test["truth"])[a:b]
        if err.max() > test["tol"]:
            fails.append(f"{test['name']}: |err| max {err.max():.4f} > {test['tol']}")
    return fails


def write_vector(test, path):
    with open(path, "w") as f:
        f.write(f"{len(test['I'])} {test['override']:.6f}\n")
        for i, v in zip(test["I"], test["V"]):
            f.write(f"{i:.6f} {v:.6f}\n")


def write_cycle(I, V, path, override=-1.0):
    with open(path, "w") as f:
        f.write(f"{len(I)} {override:.6f}\n")
        for i, v in zip(I, V):
            f.write(f"{i:.6f} {v:.6f}\n")


if __name__ == "__main__":
    import sys
    spec = json.load(open(sys.argv[1]))
    for t in build(spec):
        est = ref.observer(spec, t["I"], t["V"], t["override"])
        print(t["name"], len(t["I"]), check(t, est) or "PASS (float64 reference)")
