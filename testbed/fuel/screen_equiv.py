"""Equivalent-mutant screening for subject 2 -- EXPLORATORY, added 2026-11-11 AFTER the E1 runs.

Not part of the frozen protocol (it imports frozen modules, changes none of them). Same method as
testbed/soc/screen_equiv.py: every mutant in results/e1_qemu_analysis.json 'non_field_relevant.unflagged'
is built exactly like SIL (host gcc -O2 -std=c11, harness/harness.c + fuel.c; model-level mutants use the
C that gen.py generates from the mutant spec) and its '%.9g' output lines ('rate vol', float32 round-trip
exact) are compared as text with the baseline build on:
  REQ    requirement vectors T1..T8 (tests_req.build, as in E1);
  FIELD  all tanks 8-22 (identification 8-17 + held-out 18-22), unperturbed, written as in E1;
  STRESS generated with SEED (stress_set(), perturbed_field()); written float32-exact ('%.9g') so exact
         boundary values (thr 21.0, rpm 1600, trim sum +-25, dt 5.0, dt 0/-0, rate at 400) reach the C.
Stress requirement check (baseline-relative): REQ-1 range/finite/monotone volume; REQ-2 accuracy against the
float64 reference of the BASELINE spec on the float32 inputs (tolerances of tests_req.check); REQ-3 rate <= 1e-6
on every DFCO row (thr <= 21 and rpm > 1600); REQ-4 volume increment <= rate*5/60 + 0.05 ml on dt > 5 s rows
and <= 1e-6 ml on dt < 0 rows. A break counts only if the baseline passes the same check on the same trace.
Usage (WSL): /root/venvs/cicd/bin/python screen_equiv.py
"""
import concurrent.futures as cf
import hashlib
import json
import math
import pathlib
import shutil

import numpy as np

import common
import ref
import stages
import tests_req

SEED = 20261111
WORK = pathlib.Path.home() / "cicd-work" / "equiv" / "fuel"
OUT = common.ROOT / "results" / "equiv_screen.json"
COLS = tests_req.COLS


def write_vec(path, v, exact):
    if not exact:
        tests_req.write_vector(v, path)
    else:
        with open(path, "w") as f:
            f.write(f"{len(v['dt'])}\n")
            for row in zip(*(np.float32(v[c]) for c in COLS)):
                f.write(" ".join(f"{float(x):.9g}" for x in row) + "\n")
    return hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest()


def mix(rng, n, parts):
    """parts: list of (prob, sampler(k) -> array of k). Row-wise mixture."""
    probs = np.array([p for p, _ in parts], float)
    pick = rng.choice(len(parts), n, p=probs / probs.sum())
    out = np.empty(n)
    for k, (_, f) in enumerate(parts):
        idx = np.where(pick == k)[0]
        out[idx] = f(len(idx))
    return out


def stress_set():
    rng = np.random.default_rng(SEED)
    out = []
    ch = lambda vals: (lambda k: rng.choice(np.array(vals, float), k))
    for k in range(10):
        n = 20000
        v = dict(
            dt=mix(rng, n, [(0.7, lambda m: rng.uniform(0, 2, m)), (0.2, lambda m: rng.uniform(-5, 20, m)),
                            (0.1, ch([0.0, -0.0, 5.0, 4.9999995, 5.0000005, -1.0, -1e-7, 300.0, 1e4]))]),
            MAF=mix(rng, n, [(0.6, lambda m: rng.uniform(0, 60, m)), (0.2, lambda m: rng.uniform(60, 300, m)),
                             (0.1, ch([0.0, -0.0, -1e-7, -5.0])), (0.1, lambda m: rng.uniform(-5, 0, m))]),
            RPM=mix(rng, n, [(0.85, lambda m: rng.uniform(0, 7000, m)),
                             (0.15, ch([1600.0, 1599.9999, 1600.0001, 0.0, 750.0, 8000.0]))]),
            THR=mix(rng, n, [(0.85, lambda m: rng.uniform(0, 100, m)),
                             (0.15, ch([21.0, 20.999998, 21.000002, 0.0, 19.0, 100.0]))]),
        )
        st = mix(rng, n, [(0.85, lambda m: rng.uniform(-40, 40, m)), (0.15, lambda m: rng.integers(-60, 61, m).astype(float))])
        lt = mix(rng, n, [(0.85, lambda m: rng.uniform(-40, 40, m)), (0.15, ch([0.0, 100.0, -100.0]))])
        exact = rng.random(n) < 0.15     # trim sum exactly +-25 (integer split, exact in float32)
        sgn = rng.choice([-1.0, 1.0], n)
        lt = np.where(exact, sgn * 25.0 - st.round(), lt)
        st = np.where(exact, st.round(), st)
        v.update(STFT=st, LTFT=lt)
        out.append(dict(name=f"rand_rows_{k:02d}", cls="random", v=v,
                        defn="20000 iid rows; dt U(0,2) 70 %, U(-5,20) 20 %, exact {0,-0,5,5+-ulp,-1,-1e-7,300,1e4} 10 %; "
                             "MAF U(0,60) 60 %, U(60,300) 20 %, {0,-0,-1e-7,-5} 10 %, U(-5,0) 10 %; RPM U(0,7000) or "
                             "{1600, 1600+-1e-4, 0, 750, 8000}; THR U(0,100) or {21, 21+-2e-6, 0, 19, 100}; STFT/LTFT "
                             "U(-40,40), integers, +-100, and 15 % rows with STFT+LTFT exactly +-25"))
    for k in range(4):
        n = 20000
        walk = lambda lo, hi, s: np.clip(np.cumsum(rng.normal(0, s, n)) + rng.uniform(lo, hi), lo, hi)
        dt = rng.uniform(0.9, 1.5, n)
        gaps = rng.random(n) < 0.002
        dt[gaps] = rng.choice([6.0, 30.0, 300.0, -2.0], gaps.sum())
        v = dict(dt=dt, MAF=walk(0.0, 120.0, 1.5), RPM=walk(700.0, 6500.0, 40.0), THR=walk(0.0, 100.0, 1.0),
                 STFT=walk(-30.0, 30.0, 0.5), LTFT=walk(-15.0, 15.0, 0.05))
        out.append(dict(name=f"drive_{k:02d}", cls="random", v=v,
                        defn="20000-row clipped random walks: MAF [0,120] g/s, RPM [700,6500], THR [0,100] %, "
                             "STFT [-30,30], LTFT [-15,15]; dt U(0.9,1.5) with 0.2 % gaps {6,30,300,-2} s"))
    n = 3000
    j = np.arange(n)
    out.append(dict(name="sat_rate", cls="saturation", v=dict(
        dt=np.ones(n), MAF=np.linspace(0.0, 300.0, n), RPM=np.full(n, 3000.0), THR=np.full(n, 50.0),
        STFT=np.where(j % 2, 25.0, -25.0), LTFT=np.zeros(n)),
        defn="MAF ramp 0-300 g/s (rate through 200 and 400 ml/min), trims +-25 alternating"))
    out.append(dict(name="long_dfco", cls="edge", v=dict(
        dt=np.ones(n), MAF=np.full(n, 6.0), RPM=np.where(j % 3 == 0, 1600.0, 2500.0), THR=np.where(j % 2, 21.0, 10.0),
        STFT=np.zeros(n), LTFT=np.zeros(n)), defn="DFCO boundary: THR in {21.0 exact, 10}, RPM in {1600 exact, 2500}"))
    out.append(dict(name="dt_edges", cls="edge", v=dict(
        dt=np.tile([5.0, 0.0, -0.0, 4.9999995, 5.0000005, -1.0, 1e4, 1.0], n // 8), MAF=np.full(n // 8 * 8, 10.0),
        RPM=np.full(n // 8 * 8, 2500.0), THR=np.full(n // 8 * 8, 30.0), STFT=np.zeros(n // 8 * 8),
        LTFT=np.zeros(n // 8 * 8)), defn="dt cycling {5, 0, -0, 5-ulp, 5+ulp, -1, 1e4, 1}, constant MAF 10"))
    out.append(dict(name="zero_rate", cls="edge", v=dict(
        dt=np.ones(n), MAF=np.tile([0.0, -0.0, -1e-7, 1e-7, -3.0], n // 5), RPM=np.full(n, 1000.0),
        THR=np.full(n, 30.0), STFT=np.tile([0.0, 25.0, -25.0, -100.0, 100.0, 50.0], n // 6), LTFT=np.zeros(n)),
        defn="MAF in {0, -0, +-1e-7, -3} with trims {0, +-25, +-100, 50}: rate at and below 0"))
    out.append(dict(name="oor_t7like", cls="oor", v=dict(
        dt=rng.choice([0.0, 0.001, 5.0, 1e4, -1e4], n), MAF=rng.uniform(-50, 1000, n), RPM=rng.uniform(-100, 20000, n),
        THR=rng.uniform(-10, 110, n), STFT=rng.uniform(-200, 200, n), LTFT=rng.uniform(-200, 200, n)),
        defn="out-of-range robustness (T7-like, wider): MAF U(-50,1000), RPM U(-100,2e4), THR U(-10,110), trims U(-200,200)"))
    return out


def perturbed_field(tanks):
    rng = np.random.default_rng(SEED + 1)
    out = []
    for sid, t in tanks.items():
        n = len(t["dt"])
        g = float(rng.uniform(0.8, 1.6))
        v = dict(dt=np.where(np.arange(n) == 0, 0.0, t["dt"] + rng.normal(0, 0.05, n)),
                 MAF=t["MAF"] * g + rng.normal(0, 0.2, n), RPM=t["RPM"] + rng.normal(0, 20, n),
                 THR=t["THR"] + rng.normal(0, 0.5, n), STFT=t["STFT"] + rng.normal(0, 2, n),
                 LTFT=t["LTFT"] + rng.normal(0, 0.5, n))
        out.append(dict(name=f"pert_tank{sid}", cls="perturbed_field", v=v,
                        defn=f"tank {sid}: MAF*{g:.3f} + N(0,0.2), dt + N(0,0.05), RPM + N(0,20), THR + N(0,0.5), "
                             "STFT + N(0,2), LTFT + N(0,0.5)"))
    return out


def build(vdir):
    r = stages._run(["gcc", "-O2", "-std=c11", "-I.", str(stages.H / "harness.c"), "fuel.c", "-lm", "-o", "sil"], vdir)
    if r.returncode != 0:
        raise RuntimeError(f"build failed {vdir}: {r.stderr[-400:]}")


def run_all(vdir, vecs):
    res = {}
    for name, path in vecs.items():
        of = vdir / "o.txt"
        try:
            r = stages._run(["./sil", str(path), str(of)], vdir, timeout=600)
            lines = of.read_text().split("\n") if r.returncode == 0 and of.exists() else []
        except Exception:
            lines = []
        res[name] = [l for l in lines if l.strip()]
    return res


def to_arr(lines):
    a = np.array([[float(x) for x in l.split()] for l in lines]) if lines else np.zeros((0, 2))
    return a[:, 0], a[:, 1]


def stress_checks(tr, lines, spec):
    v = tr["v"]
    n = len(v["dt"])
    rate, vol = to_arr(lines)
    if len(rate) != n:
        return [("REQ1", True, None)]
    res = []
    bad1 = (not np.all(np.isfinite(rate)) or not np.all(np.isfinite(vol)) or rate.min() < 0 or rate.max() > 400
            or np.any(np.diff(np.concatenate([[0.0], vol])) < -1e-6))
    res.append(("REQ1", bool(bad1), None))
    if bad1:
        return res
    er = np.abs(rate - tr["exp_rate"]) - (0.005 * np.abs(tr["exp_rate"]) + 0.01)
    ev = np.abs(vol - tr["exp_vol"]) - (0.005 * np.abs(tr["exp_vol"]) + 0.05)
    res.append(("REQ2_rate", bool(er.max() > 0), float(er.max())))
    res.append(("REQ2_vol", bool(ev.max() > 0), float(ev.max())))
    f32 = {c: np.float32(v[c]).astype(float) for c in COLS}
    dfco = (f32["THR"] <= spec["params"]["thr_dfco"]) & (f32["RPM"] > spec["params"]["rpm_dfco"])
    if dfco.any():
        res.append(("REQ3", bool(rate[dfco].max() > 1e-6), float(rate[dfco].max() - 1e-6)))
    inc = np.diff(np.concatenate([[0.0], vol]))
    gap, neg = f32["dt"] > 5.0, f32["dt"] < 0.0
    if gap.any():
        x = inc[gap] - (rate[gap] * 5.0 / 60.0 + 0.05)
        res.append(("REQ4_gap", bool(x.max() > 0), float(x.max())))
    if neg.any():
        x = inc[neg] - 1e-6
        res.append(("REQ4_neg", bool(x.max() > 0), float(x.max())))
    return res


def _clean(x):
    if isinstance(x, float) and not math.isfinite(x):
        return str(x)
    if isinstance(x, dict):
        return {k: _clean(v) for k, v in x.items()}
    if isinstance(x, list):
        return [_clean(v) for v in x]
    return x


def main():
    common.check_data()
    spec = common.load_spec(common.ROOT / "spec" / "baseline.json")
    man = json.loads((common.ROOT / "protocol" / "mutants.json").read_text())
    ana = json.loads((common.ROOT / "results" / "e1_qemu_analysis.json").read_text())
    ids = ana["non_field_relevant"]["unflagged"]
    real = common.ROOT / "results" / "e1_pil_iotnode_vs_qemu.json"
    real_fail = {d["id"] for d in json.loads(real.read_text())["disagreements"] if d["real_fail"]} if real.exists() else set()
    muts = {m["id"]: m for m in man["model"] + man["code"]}
    if WORK.exists():
        shutil.rmtree(WORK)
    (WORK / "vec").mkdir(parents=True)

    sets, defs, traces = {"REQ": {}, "FIELD": {}, "STRESS": {}}, [], {}
    tanks = common.load_tanks(common.TRAIN + common.FIELD)
    for t in tests_req.build(spec, tank8=tanks[8]):
        p = WORK / "vec" / f"{t['name']}.txt"
        sets["REQ"][t["name"]] = p
        defs.append(dict(set="REQ", name=t["name"], n=len(t["v"]["dt"]), sha256=write_vec(p, t["v"], False),
                         defn="tests_req.build (frozen)"))
    for sid, v in tanks.items():
        p = WORK / "vec" / f"field_{sid}.txt"
        sets["FIELD"][str(sid)] = p
        defs.append(dict(set="FIELD", name=f"tank{sid}", n=len(v["dt"]), sha256=write_vec(p, v, False),
                         defn=("held-out" if sid in common.FIELD else "identification") + " tank, unperturbed"))
    for tr in stress_set() + perturbed_field(tanks):
        p = WORK / "vec" / f"{tr['name']}.txt"
        h = write_vec(p, tr["v"], True)
        tr["exp_rate"], tr["exp_vol"] = ref.run(spec, {c: np.float32(tr["v"][c]).astype(float) for c in COLS})
        sets["STRESS"][tr["name"]] = p
        traces[tr["name"]] = tr
        defs.append(dict(set="STRESS", name=tr["name"], cls=tr["cls"], n=len(tr["v"]["dt"]), sha256=h, defn=tr["defn"]))
    allvec = {f"{s}/{k}": v for s, d in sets.items() for k, v in d.items()}

    def job(mid):
        vdir = WORK / "build" / mid
        if mid == "baseline":
            stages.prepare_version(spec, vdir)
        elif muts[mid]["level"] == "model":
            stages.prepare_version(muts[mid]["spec"], vdir)
        else:
            stages.prepare_version(spec, vdir, c_text=muts[mid]["c_text"])
        build(vdir)
        return mid, run_all(vdir, allvec)

    with cf.ThreadPoolExecutor(8) as ex:
        outs = dict(ex.map(job, ["baseline"] + ids))
    base = outs["baseline"]
    base_chk = {f"STRESS/{k}": {c: (b, w) for c, b, w in stress_checks(traces[k], base[f"STRESS/{k}"], spec)}
                for k in sets["STRESS"]}

    results = []
    for mid in ids:
        o = outs[mid]
        per_set, req_breaks = {}, []
        for s in sets:
            st = dict(identical=True, rows_diff=0, signed_zero_only_rows=0, max_abs_diff_rate=0.0,
                      max_abs_diff_vol=0.0, at_rate=None, at_vol=None)
            for k in [k for k in allvec if k.startswith(s + "/")]:
                a, b = o[k], base[k]
                if a == b:
                    continue
                st["identical"] = False
                if len(a) != len(b):
                    st.update(rows_diff=st["rows_diff"] + max(len(a), len(b)), max_abs_diff_rate=float("inf"),
                              max_abs_diff_vol=float("inf"), at_rate=k, at_vol=k)
                    continue
                dif = [i for i in range(len(a)) if a[i] != b[i]]
                st["rows_diff"] += len(dif)
                (ra, va), (rb, vb) = to_arr(a), to_arr(b)
                for sig, x, y in (("rate", ra, rb), ("vol", va, vb)):
                    d = np.abs(x - y)
                    d = np.where(np.isnan(d), np.inf, d)
                    if d.max() > st[f"max_abs_diff_{sig}"] or (d.max() > 0 and st[f"at_{sig}"] is None):
                        st[f"max_abs_diff_{sig}"], st[f"at_{sig}"] = float(d.max()), f"{k} row {int(np.argmax(d))}"
                st["signed_zero_only_rows"] += sum(1 for i in dif if all(
                    float(p) == float(q) for p, q in zip(a[i].split(), b[i].split())))
            per_set[s] = st
        for k in sets["STRESS"]:
            kk = f"STRESS/{k}"
            if o[kk] == base[kk]:
                continue
            for cid, bad, worst in stress_checks(traces[k], o[kk], spec):
                if bad and not base_chk[kk].get(cid, (False, None))[0]:
                    req_breaks.append(dict(trace=k, check=cid, mutant_excess=worst,
                                           baseline_excess=base_chk[kk].get(cid, (None, None))[1]))
        eq = all(v["identical"] for v in per_set.values())
        results.append(dict(id=mid, level=muts[mid]["level"], op=muts[mid]["op"], desc=muts[mid]["desc"],
                            cls="EQUIVALENT" if eq else "NON-EQUIVALENT BENIGN", sets=per_set,
                            stress_classes_differing=sorted({traces[k]["cls"] for k in sets["STRESS"]
                                                             if o[f"STRESS/{k}"] != base[f"STRESS/{k}"]}),
                            stress_requirement_breaks=req_breaks,
                            flagged_by_real_board_pil=mid in real_fail))
        print(f"{mid:<20} {results[-1]['cls']:<22} " + " ".join(
            f"{s}:{'=' if v['identical'] else format(v['max_abs_diff_rate'], '.3g') + '/' + format(v['max_abs_diff_vol'], '.3g')}"
            for s, v in per_set.items()),
            (" BREAKS " + ",".join(f"{b['trace']}:{b['check']}({b['mutant_excess']})" for b in req_breaks[:5]))
            if req_breaks else "", flush=True)

    counts = {}
    for r in results:
        counts[r["cls"]] = counts.get(r["cls"], 0) + 1
    rep = dict(
        status="EXPLORATORY, added 2026-11-11 after the E1 runs; not part of the frozen protocol",
        subject="fuel", seed=SEED, perturbed_field_seed=SEED + 1,
        source_list="results/e1_qemu_analysis.json non_field_relevant.unflagged",
        build="gcc -O2 -std=c11 harness/harness.c fuel.c -lm (the SIL build), host x86-64 WSL",
        compare="harness '%.9g %.9g' output text lines (rate, vol), exact string equality (float32 round-trip exact)",
        model_level="C generated by gen.py from the mutant spec (pipeline C); MIL model not re-simulated",
        stress_requirement_rule=("excess = max(err - tol); REQ-1 range/finite/monotone; REQ-2 vs float64 reference of "
                                 "the baseline spec on the float32 inputs, tol 0.5 %+0.01 ml/min (rate), 0.5 %+0.05 ml "
                                 "(vol); REQ-3 rate<=1e-6 on DFCO rows; REQ-4 gap/negative-dt increments; break counts "
                                 "only if the baseline passes the same check on the same trace"),
        baseline_stress_check_failures=sorted(f"{k}:{c}" for k, d in base_chk.items() for c, v in d.items() if v[0]),
        note_real_board=("the screened list comes from the QEMU-PIL analysis; flagged_by_real_board_pil marks "
                         "mutants the IoT-LAB st-iotnode PIL run failed (results/e1_pil_iotnode_vs_qemu.json)"),
        n_screened=len(results), counts=counts, input_sets=defs, mutants=results)
    OUT.write_text(json.dumps(_clean(rep), indent=1))
    print(json.dumps(counts))


if __name__ == "__main__":
    main()
