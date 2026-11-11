"""Identify the baseline observer spec from the TRAIN cycles only.

1. For each time constant tau on a grid, fit OCV knots (hat basis), R0 and R1 by linear least squares
   on V = OCV(soc_ref) - R0*i_d - R1*f_tau(i_d). Keep the tau with the lowest residual.
2. Choose the observer gain L on a grid by simulating the float64 reference observer on TRAIN cycles,
   from the OCV-based initial value and from a -0.2 initial error; minimise the mean RMSE.
   Grid limited by a stability rule (loop gain <= 0.5 on the steepest OCV segment); L_rest is the
   largest gain the rule allows. Rest threshold 0.05 A and rest time 1800 s are design choices.
Writes spec/baseline.json and spec/identification.json.
"""
import json
import math

import numpy as np

import common
import ref


def hat_basis(s, n):
    x = np.clip(s, 0, 1) * (n - 1)
    idx = np.clip(np.floor(x).astype(int), 0, n - 2)
    frac = x - idx
    B = np.zeros((len(s), n))
    B[np.arange(len(s)), idx] = 1 - frac
    B[np.arange(len(s)), idx + 1] += frac
    return B


def rc_filter(i_d, tau, dt):
    a = math.exp(-dt / tau)
    y = np.zeros_like(i_d)
    for j in range(1, len(i_d)):
        y[j] = a * y[j - 1] + (1 - a) * i_d[j]
    return y


def main():
    common.check_data()
    cyc = common.load_cycles(common.TRAIN)
    gaps = {n: c["gaps"] for n, c in cyc.items()}
    best = None
    for tau in [5, 10, 20, 40, 80, 160, 320, 640]:
        rows, ys = [], []
        for c in cyc.values():
            i_d = -c["I"]
            B = hat_basis(c["SOC"], common.N_KNOTS)
            rows.append(np.hstack([B, -i_d[:, None], -rc_filter(i_d, tau, common.DT)[:, None]]))
            ys.append(c["V"])
        A, y = np.vstack(rows), np.concatenate(ys)
        # Second-difference smoothness penalty on the OCV knots: knots below the lowest SoC in the
        # data (~0.14) are otherwise unconstrained and fall to 0 V. lam fixed, not tuned on results.
        lam = 1e-2 * np.sqrt(len(y))
        D = np.zeros((common.N_KNOTS - 2, A.shape[1]))
        for r in range(common.N_KNOTS - 2):
            D[r, r:r + 3] = [1.0, -2.0, 1.0]
        theta, *_ = np.linalg.lstsq(np.vstack([A, lam * D]),
                                    np.concatenate([y, np.zeros(common.N_KNOTS - 2)]), rcond=None)
        A_fit = A
        rmse = float(np.sqrt(np.mean((A_fit @ theta - y) ** 2)))
        if best is None or rmse < best[0]:
            best = (rmse, tau, theta)
    rmse_v, tau, theta = best
    knots = [float(v) for v in theta[: common.N_KNOTS]]
    R0, R1 = float(theta[common.N_KNOTS]), float(theta[common.N_KNOTS + 1])

    spec = {
        "name": "soc_obs", "version": "baseline",
        "params": {"dt": common.DT, "Q": common.Q_AH, "R0": R0, "R1": R1, "tau": float(tau),
                   "L": None, "L_rest": None, "rest_i": 0.05, "rest_ms": 1800000, "knots": knots},
        "eq": {"s_id": -1.0, "s_cc": -1.0, "s_r0": -1.0, "s_v1": -1.0, "s_corr": 1.0,
               "sat": True, "dt_int": common.DT},
    }
    # Stability rule (design, not fitted): the correction loop gain L * dOCV/dSoC must stay <= 0.5 on
    # the steepest OCV segment, for both L and L_rest. L_rest takes the largest gain allowed by the rule.
    max_slope = max((knots[j + 1] - knots[j]) * (common.N_KNOTS - 1) for j in range(common.N_KNOTS - 1))
    l_max = 0.5 / max_slope
    scores = {}
    for L in [g for g in [1e-4, 3e-4, 1e-3, 3e-3, 1e-2, 3e-2, 1e-1, 3e-1] if g <= l_max]:
        spec["params"]["L"], spec["params"]["L_rest"] = L, l_max
        r = []
        for c in cyc.values():
            for ov in (-1.0, min(1.0, c["SOC"][0]) - 0.2):
                est = ref.observer(spec, c["I"], c["V"], ov)
                r.append(float(np.sqrt(np.mean((est - c["SOC"]) ** 2))))
        scores[L] = float(np.mean(r))
    L = min(scores, key=scores.get)
    spec["params"]["L"], spec["params"]["L_rest"] = L, l_max

    (common.ROOT / "spec").mkdir(exist_ok=True)
    (common.ROOT / "spec" / "baseline.json").write_text(json.dumps(spec, indent=1))
    ident = {"data_sha256": common.DATA_SHA256, "train": common.TRAIN, "gaps": gaps,
             "fit_rmse_V": rmse_v, "tau": tau, "R0": R0, "R1": R1, "knots": knots,
             "L_grid_mean_rmse": {str(k): v for k, v in scores.items()}, "L": L,
             "max_ocv_slope_V_per_unit": max_slope, "L_rest": l_max}
    (common.ROOT / "spec" / "identification.json").write_text(json.dumps(ident, indent=1))
    print(json.dumps(ident, indent=1))


if __name__ == "__main__":
    main()
