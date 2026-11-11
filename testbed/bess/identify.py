"""Identify the thermal part (tau, k_h, c0) of subject 3 on the training months (all racks) by least
squares of the simulated middle-sensor temperature against TCELL (Nelder-Mead on a vectorised Euler
simulation, same sub-stepping as the model). Each segment starts at t_est = TREF[0] + c0.

Design constants (not fitted; fixed here before any mutant):
  n_sub 4 Euler sub-steps per 5 s row; current clamp +-400 A; temperature clamp [-40, 90] degC;
  derating: filter tau_f 60 s, latch on t_filt > t_hi = 31.0 degC, release when t_filt < t_lo = 29.0 degC
  and latched >= dwell_s 300 s, derated factor d_lim 0.5, recovery ramp 0.002 per s (0.5 -> 1 in 250 s).
  t_hi/t_lo are set from the TCELL distribution (inspect_data.py: median 26, p90 30, p99 32, max 33 degC)
  so that the derating is exercised on real data.
Writes spec/baseline.json and spec/identification.json.
"""
import json

import numpy as np
from scipy.optimize import minimize

import common
import ref

N_SUB = 4


def pad(segs):
    L = max(len(s["I"]) for s in segs)
    M = np.zeros((len(segs), L), bool)
    I, R, C = (np.zeros((len(segs), L)) for _ in range(3))
    for k, s in enumerate(segs):
        n = len(s["I"])
        M[k, :n], I[k, :n], R[k, :n], C[k, :n] = True, s["I"], s["TREF"], s["TCELL"]
    return M, I, R, C


def sim(theta, I, R):
    tau, k_h, c0 = theta
    h = ref.DT / N_SUB
    te = R[:, 0] + c0
    out = np.empty_like(I)
    for j in range(I.shape[1]):
        ic = np.clip(I[:, j], -400.0, 400.0)
        for _ in range(N_SUB):
            te = te + h / tau * (R[:, j] + c0 + k_h * ic * ic - te)
        out[:, j] = te
    return out


def rmse(theta, M, I, R, C):
    if theta[0] <= 1.0:
        return 1e9
    e = (sim(theta, I, R) - C)[M]
    return float(np.sqrt(np.mean(e ** 2)))


def main():
    common.check_data()
    tr = list(common.load_segments(common.TRAIN_MONTHS).values())
    fd = list(common.load_segments(common.FIELD_MONTHS, [common.FIELD_RACK]).values())
    M, I, R, C = pad(tr)
    x0 = np.array([600.0, 1e-4, 0.3])
    res = minimize(rmse, x0, args=(M, I, R, C), method="Nelder-Mead",
                   options=dict(xatol=1e-7, fatol=1e-6, maxiter=600))
    tau, k_h, c0 = (float(x) for x in res.x)
    Mf, If, Rf, Cf = pad(fd)
    base_tr = float(np.sqrt(np.mean((R - C)[M] ** 2)))
    base_fd = float(np.sqrt(np.mean((Rf - Cf)[Mf] ** 2)))
    spec = {"name": "bess_therm", "version": "baseline",
            "params": {"tau": tau, "k_h": k_h, "c0": c0, "n_sub": N_SUB, "i_max": 400.0, "t_min": -40.0,
                       "t_max": 90.0, "tau_f": 60.0, "t_hi": 31.0, "t_lo": 29.0, "dwell_s": 300.0,
                       "d_lim": 0.5, "ramp": 0.002},
            "eq": {"s_heat": 1.0, "s_c0": 1.0, "dt_scale": 1.0, "sat": True, "iclamp": True, "ramp": True,
                   "hyst": True, "rel_rule": "both"}}
    ident = {"data_sha256": common.DATA_SHA256, "train_months": common.TRAIN_MONTHS,
             "field_months": common.FIELD_MONTHS, "field_rack": common.FIELD_RACK,
             "n_train_segments": len(tr), "n_train_rows": int(M.sum()),
             "n_field_segments": len(fd), "n_field_rows": int(Mf.sum()),
             "optimizer": dict(success=bool(res.success), nit=int(res.nit), message=str(res.message)),
             "tau_s": tau, "k_h_degC_per_A2": k_h, "c0_degC": c0,
             "train_rmse_degC": rmse(res.x, M, I, R, C), "field_rmse_degC": rmse(res.x, Mf, If, Rf, Cf),
             "naive_tref_rmse_train_degC": base_tr, "naive_tref_rmse_field_degC": base_fd,
             "x0": x0.tolist()}
    (common.ROOT / "spec" / "baseline.json").write_text(json.dumps(spec, indent=1))
    (common.ROOT / "spec" / "identification.json").write_text(json.dumps(ident, indent=1))
    print(json.dumps(ident, indent=1))


if __name__ == "__main__":
    main()
