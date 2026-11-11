"""Baseline calibration, run BEFORE any mutant. Fixes (and writes to protocol/calibration.json):
- back-to-back tolerances: tol = max(1e-5, 10 x baseline max |diff|) for SIL-vs-MIL and PIL-vs-SIL;
- PIL timing budget: 2 x baseline max ticks per step (regression guard);
- field-oracle thresholds: fail if any held-out cycle has RMSE > baseline RMSE + 0.005, or
  max|err| > baseline max + 0.02, or non-finite / out-of-range output;
- stage cost samples: R repetitions of each stage on the baseline (wall-clock seconds).
Also checks that the baseline passes every stage; if not, the design is fixed before the freeze.
"""
import json
import platform
import sys

import numpy as np

import common
import stages


def main(reps=10):
    common.check_data()
    spec = common.load_spec(common.ROOT / "spec" / "baseline.json")
    tests, field_cycles = stages.prepare_vectors(spec)
    vdir = stages.prepare_version(spec, stages.WORK / "build" / "baseline")

    cost = {"unit": [], "mil": [], "mil_build": [], "sil": [], "pil": [], "field": []}
    for r in range(reps):
        u = stages.stage_unit(vdir)
        m = stages.stage_mil(vdir, tests)
        s = stages.stage_sil(vdir, tests)
        p = stages.stage_pil(vdir, tests)
        f = stages.field(vdir, field_cycles)
        for k, res in (("unit", u), ("mil", m), ("sil", s), ("pil", p), ("field", f)):
            cost[k].append(res["wall_s"])
        cost["mil_build"].append(m.get("build_s"))
        print(f"rep {r}: unit {u['passed']} mil {m['passed']} sil {s['passed']} pil {p['passed']} "
              f"walls {[round(x[-1], 2) for x in cost.values() if x and x[-1] is not None]}", flush=True)
        if r == 0:
            first = dict(unit=u, mil=m, sil=s, pil=p, field=f)

    u, m, s, p, f = (first[k] for k in ("unit", "mil", "sil", "pil", "field"))
    d_sm = max(float(np.max(np.abs(s["out"][k] - m["out"][k]))) for k in m["out"])
    d_ps = max(float(np.max(np.abs(p["out"][k] - s["out"][k]))) for k in s["out"])
    tmax = max(v[0] for v in p["ticks"].values())
    cal = {
        "baseline_pass": {"unit": u["passed"], "mil": m["passed"], "sil": s["passed"], "pil": p["passed"],
                          "fails": {"unit": u["fails"], "mil": m["fails"], "sil": s["fails"], "pil": p["fails"]}},
        "b2b": {"sil_vs_mil_max": d_sm, "pil_vs_sil_max": d_ps,
                "tol_sil_mil": max(1e-5, 10 * d_sm), "tol_pil_sil": max(1e-5, 10 * d_ps)},
        "timing": {"target": "qemu (instruction proxy, development only)",
                   "baseline_max_ticks": tmax, "tick_budget": 2 * tmax},
        "field": {"baseline": f["metrics"],
                  "rule": "fail if any cycle rmse > base+0.005 or maxabs > base+0.02 or invalid"},
        "cost_s": cost,
        "env": {"python": sys.version.split()[0], "machine": platform.machine(),
                "node": "author PC (WSL Ubuntu 26.04)", "reps": reps},
    }
    out = common.ROOT / "protocol"
    out.mkdir(exist_ok=True)
    (out / "calibration.json").write_text(json.dumps(cal, indent=1))
    print(json.dumps({k: cal[k] for k in ("baseline_pass", "b2b", "timing", "field")}, indent=1))


if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 10)
