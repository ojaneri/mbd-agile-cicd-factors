"""Float64 reference implementations: the observer algorithm (same order as the generated
Modelica and C) and the synthetic plant used to create requirement-test voltages.

The reference observer is used for identification and design only. It is NOT a pipeline stage.
"""
import math

import numpy as np


def ocv(s, knots):
    n = len(knots)
    x = s * (n - 1)
    idx = int(x)
    idx = max(0, min(idx, n - 2))
    frac = x - idx
    return knots[idx] + (knots[idx + 1] - knots[idx]) * frac


def ocv_inv(v, knots):
    lo, hi = 0.0, 1.0
    for _ in range(30):
        mid = 0.5 * (lo + hi)
        if ocv(mid, knots) < v:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)


def observer(spec, I, V, soc_override=-1.0):
    p, e, k = spec["params"], spec["eq"], spec["params"]["knots"]
    out = np.empty(len(I))
    soc = soc_override if soc_override >= 0 else ocv_inv(V[0], k)
    v1, rest_ms = 0.0, 0
    a = math.exp(-p["dt"] / p["tau"])
    out[0] = soc
    for j in range(1, len(I)):
        i_d = e["s_id"] * I[j]
        v1 = a * v1 + p["R1"] * (1.0 - a) * i_d
        soc = soc + e["s_cc"] * i_d * e["dt_int"] / (3600.0 * p["Q"])
        rest_ms = rest_ms + int(round(p["dt"] * 1000)) if abs(I[j]) < p["rest_i"] else 0
        gain = p["L_rest"] if rest_ms >= p["rest_ms"] else p["L"]
        vm = ocv(soc, k) + e["s_r0"] * p["R0"] * i_d + e["s_v1"] * v1
        soc = soc + e["s_corr"] * gain * (V[j] - vm)
        if e["sat"]:
            soc = min(1.0, max(0.0, soc))
        out[j] = soc
    return out


def plant(params, I, soc0, rng=None, sigma_v=0.0, sigma_i=0.0, i_offset=0.0):
    """Synthetic cell (baseline identified parameters) -> true SoC, measured V and measured I."""
    k = params["knots"]
    a = math.exp(-params["dt"] / params["tau"])
    soc, v1 = soc0, 0.0
    S, Vm = np.empty(len(I)), np.empty(len(I))
    for j in range(len(I)):
        i_d = -I[j]
        if j > 0:
            v1 = a * v1 + params["R1"] * (1.0 - a) * i_d
            soc = soc - i_d * params["dt"] / (3600.0 * params["Q"])
        S[j] = soc
        Vm[j] = ocv(min(1.0, max(0.0, soc)), k) - params["R0"] * i_d - v1
    Im = np.asarray(I, float).copy()
    if rng is not None:
        Vm = Vm + rng.normal(0.0, sigma_v, len(I))
        Im = Im + i_offset + rng.normal(0.0, sigma_i, len(I))
    return S, Vm, Im
