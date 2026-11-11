"""Smoke test of the E1 runner on three mutants, NOT recorded as results (runner-bug check only)."""
import json
import common, stages, e1
spec = common.load_spec(common.ROOT / "spec" / "baseline.json")
cal = json.loads((common.ROOT / "protocol" / "calibration.json").read_text())
man = json.loads((common.ROOT / "protocol" / "mutants.json").read_text())
tests, fv = stages.prepare_vectors(spec)
pick = [man["model"][0]] + [m for m in man["code"] if m["id"] in ("SDL-004", "SDL-009")]
for m in pick:
    v = stages.WORK / "build" / "smoke" / m["id"]
    stages.prepare_version(m.get("spec", spec), v, c_text=m.get("c_text"))
    u = stages.stage_unit(v); mil = stages.stage_mil(v, tests)
    sil = stages.stage_sil(v, tests, mil.get("out"), cal["b2b"]["tol_sil_mil"])
    pil = stages.stage_pil(v, tests, sil.get("out"), cal["b2b"]["tol_pil_sil"], cal["timing"]["tick_budget"])
    f = stages.field(v, fv)
    print(m["id"], "unit", u["passed"], "mil", mil["passed"], "sil", sil["passed"], "pil", pil["passed"],
          "field_fail", e1.field_fail(f, cal))
    print("   ", (u["fails"] + mil["fails"] + sil["fails"] + pil["fails"])[:3],
          {k: (round(x["rmse"], 3), round(x["der_mismatch_pct"], 2)) for k, x in f["metrics"].items()})
