"""E1 runner for subject 3 (adapted from testbed/fuel/e1.py): every mutant through UNIT, MIL, SIL, PIL and the field oracle. Resumable.

Writes one JSON line per mutant to results/e1_<target>.jsonl (no raw outputs, only verdicts and costs).
Usage: python e1.py [target]   (target: qemu = development run; real-target runs use the same file format)
"""
import json
import sys
import time

import common
import stages


def summarize(res):
    keep = {k: res.get(k) for k in ("passed", "wall_s", "build_s", "build_error")}
    keep["fails"] = (res.get("fails") or [])[:6]
    if res.get("ticks"):
        keep["max_ticks"] = max((v[0] for v in res["ticks"].values() if v), default=None)
    return keep


def field_fail(f, cal):
    """Frozen rule: any held-out month t_est RMSE > baseline + 0.10 degC, or derating mismatch >
    baseline + 1.0 pp, or invalid output."""
    if not f.get("valid", False):
        return True
    for n, m in f["metrics"].items():
        b = cal["field"]["baseline"][n]
        if not (m["rmse"] <= b["rmse"] + 0.10 and m["der_mismatch_pct"] <= b["der_mismatch_pct"] + 1.0):
            return True
    return False


def main(target="qemu"):
    common.check_data()
    spec = common.load_spec(common.ROOT / "spec" / "baseline.json")
    cal = json.loads((common.ROOT / "protocol" / "calibration.json").read_text())
    man = json.loads((common.ROOT / "protocol" / "mutants.json").read_text())
    tests, field_cycles = stages.prepare_vectors(spec)  # field_cycles = held-out vector
    out = common.ROOT / "results" / f"e1_{target}.jsonl"
    out.parent.mkdir(exist_ok=True)
    done = {json.loads(l)["id"] for l in out.read_text().splitlines()} if out.exists() else set()
    tol_sm, tol_ps = cal["b2b"]["tol_sil_mil"], cal["b2b"]["tol_pil_sil"]
    budget = cal["timing"]["tick_budget"]
    muts = man["model"] + man["code"]
    for k, m in enumerate(muts):
        if m["id"] in done:
            continue
        t0 = time.perf_counter()
        vdir = stages.WORK / "build" / "mut" / m["id"]
        if m["level"] == "model":
            stages.prepare_version(m["spec"], vdir)
        else:
            stages.prepare_version(spec, vdir, c_text=m["c_text"])
        u = stages.stage_unit(vdir)
        rec = dict(id=m["id"], level=m["level"], op=m["op"], desc=m["desc"], unit=summarize(u))
        if u.get("build_error"):
            rec["stillborn"] = True
        else:
            mil = stages.stage_mil(vdir, tests)
            sil = stages.stage_sil(vdir, tests, mil.get("out"), tol_sm)
            pil = stages.stage_pil(vdir, tests, sil.get("out"), tol_ps, budget, target)
            fld = stages.field(vdir, field_cycles, target)
            rec.update(stillborn=False, mil=summarize(mil), sil=summarize(sil), pil=summarize(pil),
                       field=dict(fail=field_fail(fld, cal), metrics=fld["metrics"], wall_s=fld["wall_s"]))
        rec["total_s"] = time.perf_counter() - t0
        with out.open("a") as f:
            f.write(json.dumps(rec) + "\n")
        det = "".join(s[0].upper() if (s in rec and not rec[s]["passed"]) else "." for s in ("unit", "mil", "sil", "pil"))
        print(f"[{k + 1}/{len(muts)}] {m['id']:<16} {det} field_fail={rec.get('field', {}).get('fail')} "
              f"{'STILLBORN' if rec.get('stillborn') else ''} {rec['total_s']:.1f}s", flush=True)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "qemu")
