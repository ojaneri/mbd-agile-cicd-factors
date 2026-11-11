"""Float64 reference of the BESS thermal sensor with derating (same operation order as the generated
Modelica and C). Used for identification and to derive requirement-test expectations. Not a pipeline stage.

Per row (fixed DT = 5 s), on rst = 1 first: t_est = tref + s_c0*c0, t_filt = t_est, latch = 0, dwell = 0,
der = 1. Then:
  ic = clamp(cur, -i_max, i_max)                                   (iclamp)
  n_sub Euler sub-steps, h = DT*dt_scale/n_sub:
      te += h/tau * (tref + s_c0*c0 + s_heat*k_h*ic*ic - te)
  te = clamp(te, t_min, t_max)                                     (sat)
  t_filt += alpha*(te - t_filt), alpha = DT/(tau_f + DT)
  latch off: if t_filt > t_hi -> latch on, dwell = 0
  latch on : dwell += DT; release if rule: 'both' t_filt < t_lo and dwell >= dwell_s;
             'temp' only t_filt < t_lo; 'dwell' only dwell >= dwell_s  (t_lo := t_hi if hyst removed)
  target = d_lim if latch else 1; der = target if target < der else min(target, der + ramp*DT)
            (no ramp: der = target)
Outputs per row: t_est, der.
"""
import numpy as np

DT = 5.0


def init(spec, tref):
    p, e = spec["params"], spec["eq"]
    te = tref + e["s_c0"] * p["c0"]
    return dict(te=te, tf=te, latch=False, dwell=0.0, der=1.0)


def therm(spec, te, cur, tref):
    """One 5 s row of the thermal model from te (current clamp, sub-steps, temperature clamp)."""
    p, e = spec["params"], spec["eq"]
    ic = cur
    if e["iclamp"]:
        ic = min(p["i_max"], max(-p["i_max"], ic))
    h = DT * e["dt_scale"] / p["n_sub"]
    for _ in range(int(p["n_sub"])):
        te = te + h / p["tau"] * (tref + e["s_c0"] * p["c0"] + e["s_heat"] * p["k_h"] * ic * ic - te)
    if e["sat"]:
        te = min(p["t_max"], max(p["t_min"], te))
    return te


def derate(spec, s, te):
    """Filter, latch with hysteresis and dwell, derating factor with recovery ramp (updates s)."""
    p, e = spec["params"], spec["eq"]
    alpha = DT / (p["tau_f"] + DT)
    s["tf"] = s["tf"] + alpha * (te - s["tf"])
    t_lo = p["t_lo"] if e["hyst"] else p["t_hi"]
    if not s["latch"]:
        if s["tf"] > p["t_hi"]:
            s["latch"], s["dwell"] = True, 0.0
    else:
        s["dwell"] = s["dwell"] + DT
        cold, waited = s["tf"] < t_lo, s["dwell"] >= p["dwell_s"]
        rel = {"both": cold and waited, "temp": cold, "dwell": waited}[e["rel_rule"]]
        if rel:
            s["latch"] = False
    tgt = p["d_lim"] if s["latch"] else 1.0
    if not e["ramp"] or tgt < s["der"]:
        s["der"] = tgt
    else:
        s["der"] = min(tgt, s["der"] + p["ramp"] * DT)


def step(spec, s, cur, tref):
    te = therm(spec, s["te"], cur, tref)
    s["te"] = te
    derate(spec, s, te)
    return te


def run(spec, v):
    """v: dict(rst, I, TREF) arrays. Returns (t_est, der) arrays."""
    n = len(v["I"])
    T, D = np.empty(n), np.empty(n)
    s = None
    for j in range(n):
        if v["rst"][j] > 0.5 or s is None:
            s = init(spec, v["TREF"][j])
        T[j] = step(spec, s, v["I"][j], v["TREF"][j])
        D[j] = s["der"]
    return T, D


def derate_from_temp(spec, rst, temp):
    """Field-oracle reference: the BASELINE derating logic driven by a measured temperature instead of
    the estimate (what the derating would do if the middle sensor were available). Returns der array."""
    n = len(temp)
    D = np.empty(n)
    s = None
    for j in range(n):
        if rst[j] > 0.5 or s is None:
            s = dict(te=temp[j], tf=temp[j], latch=False, dwell=0.0, der=1.0)
        p, e = spec["params"], spec["eq"]
        alpha = DT / (p["tau_f"] + DT)
        s["tf"] = s["tf"] + alpha * (temp[j] - s["tf"])
        if not s["latch"]:
            if s["tf"] > p["t_hi"]:
                s["latch"], s["dwell"] = True, 0.0
        else:
            s["dwell"] += DT
            if s["tf"] < p["t_lo"] and s["dwell"] >= p["dwell_s"]:
                s["latch"] = False
        tgt = p["d_lim"] if s["latch"] else 1.0
        s["der"] = tgt if tgt < s["der"] else min(tgt, s["der"] + p["ramp"] * DT)
        D[j] = s["der"]
    return D
