"""Baseline calibration for subject 2, run BEFORE any mutant (same rules as testbed/soc/calibrate.py).
Fixes in protocol/calibration.json:
- back-to-back tolerances per signal (rate, vol): tol = max(1e-5, 10 x baseline max |diff|), SIL-vs-MIL
  and PIL-vs-SIL;
- PIL timing budget: 2 x baseline max ticks per step (QEMU instruction proxy; real targets recalibrate);
- field-oracle rule: fail if any held-out tank |relative volume error| > |baseline error| + 2.0 pp, or the
  output is invalid (non-finite / wrong length);
- stage cost samples: R repetitions (wall-clock s).
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
    tests, tanks = stages.prepare_vectors(spec)
    vdir = stages.prepare_version(spec, stages.WORK / "build" / "baseline")
    cost = {"unit": [], "mil": [], "mil_build": [], "sil": [], "pil": [], "field": []}
    for r in range(reps):
        u = stages.stage_unit(vdir)
        m = stages.stage_mil(vdir, tests)
        s = stages.stage_sil(vdir, tests)
        p = stages.stage_pil(vdir, tests)
        f = stages.field(vdir, tanks) if r == 0 else dict(wall_s=float("nan"))
        for k, res in (("unit", u), ("mil", m), ("sil", s), ("pil", p), ("field", f)):
            cost[k].append(res["wall_s"])
        cost["mil_build"].append(m.get("build_s"))
        print(f"rep {r}: unit {u['passed']} mil {m['passed']} sil {s['passed']} pil {p['passed']} "
              f"walls u{u['wall_s']:.2f} m{m['wall_s']:.2f} s{s['wall_s']:.2f} p{p['wall_s']:.2f}", flush=True)
        if r == 0:
            first = dict(unit=u, mil=m, sil=s, pil=p, field=f)
    u, m, s, p, f = (first[k] for k in ("unit", "mil", "sil", "pil", "field"))
    d_sm = {g: max(float(np.max(np.abs(s["out"][k][g] - m["out"][k][g]))) for k in m["out"]) for g in stages.SIG}
    d_ps = {g: max(float(np.max(np.abs(p["out"][k][g] - s["out"][k][g]))) for k in s["out"]) for g in stages.SIG}
    tmax = max(v[0] for v in p["ticks"].values())
    cal = {
        "baseline_pass": {"unit": u["passed"], "mil": m["passed"], "sil": s["passed"], "pil": p["passed"],
                          "field_valid": f["valid"],
                          "fails": {"unit": u["fails"], "mil": m["fails"], "sil": s["fails"], "pil": p["fails"]}},
        "b2b": {"sil_vs_mil_max": d_sm, "pil_vs_sil_max": d_ps,
                "tol_sil_mil": {g: max(1e-5, 10 * d_sm[g]) for g in stages.SIG},
                "tol_pil_sil": {g: max(1e-5, 10 * d_ps[g]) for g in stages.SIG}},
        "timing": {"target": "qemu (instruction proxy, development only)",
                   "baseline_max_ticks": tmax, "tick_budget": 2 * tmax},
        "field": {"baseline": f["metrics"],
                  "rule": "fail if any tank |rel_err_pct| > |baseline| + 2.0, or invalid"},
        "cost_s": {k: [x for x in v if x is not None and x == x] for k, v in cost.items()},
        "env": {"python": sys.version.split()[0], "machine": platform.machine(),
                "node": "author PC (WSL Ubuntu 26.04)", "reps": reps,
                "note": "field replayed once (deterministic, ~194k rows); cost of field is 1 sample"},
    }
    out = common.ROOT / "protocol"
    out.mkdir(exist_ok=True)
    (out / "calibration.json").write_text(json.dumps(cal, indent=1))
    print(json.dumps({k: cal[k] for k in ("baseline_pass", "b2b", "timing", "field")}, indent=1))


if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 10)
