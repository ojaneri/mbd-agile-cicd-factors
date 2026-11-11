"""Float64 reference of the fuel-flow sensor (same operation order as the generated Modelica and C).
Used for identification and to derive requirement-test expectations. Not a pipeline stage.

rate [ml/min] = k_cal * MAF * 60 / (AFR * rho) * (1 + s_trim * trim / 100),
  trim = clamp(STFT + LTFT, -trim_lim, +trim_lim);   rate = 0 under DFCO (THR <= thr_dfco and RPM > rpm_dfco);
  saturation: rate in [0, rate_max].
volume [ml] += s_int * rate * dt_c * dt_scale / 60,  dt_c = clamp(dt, 0, dt_max).
"""
import numpy as np


def step(spec, vol, dt, maf, rpm, thr, stft, ltft):
    p, e = spec["params"], spec["eq"]
    trim = stft + ltft
    if e["trim_clamp"]:
        trim = min(p["trim_lim"], max(-p["trim_lim"], trim))
    rate = p["k_cal"] * maf * 60.0 / (p["AFR"] * p["rho"]) * (1.0 + e["s_trim"] * trim / 100.0)
    if e["dfco"] and thr <= p["thr_dfco"] and rpm > p["rpm_dfco"]:
        rate = 0.0
    if e["sat"]:
        rate = min(p["rate_max"], max(0.0, rate))
    dtc = min(p["dt_max"], max(0.0, dt))
    vol = vol + e["s_int"] * rate * dtc * e["dt_scale"] / 60.0
    return vol, rate


def run(spec, v):
    n = len(v["dt"])
    R, Vo = np.empty(n), np.empty(n)
    vol = 0.0
    for j in range(n):
        vol, rate = step(spec, vol, v["dt"][j], v["MAF"][j], v["RPM"][j], v["THR"][j], v["STFT"][j], v["LTFT"][j])
        R[j], Vo[j] = rate, vol
    return R, Vo
