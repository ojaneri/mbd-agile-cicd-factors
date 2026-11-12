"""Equivalent-mutant screening for subject 1 -- EXPLORATORY, added 2026-11-11 AFTER the E1 runs.

Not part of the frozen protocol (it imports frozen modules, changes none of them).
Scope: every live mutant that no stage (UNIT, MIL, SIL, PIL) and not the field oracle flagged in
results/e1_qemu_analysis.json ('non_field_relevant.unflagged').

Method: host gcc -O2 -std=c11 build of harness/harness.c + the mutant's soc_obs.c (exactly the SIL build;
model-level mutants use the C that gen.py generates from the mutant spec, i.e. the pipeline's own C).
Outputs are the harness's '%.9g' text lines (round-trip exact for float32), compared line by line with
the baseline build: identical text on every input = bit-identical outputs.
Input sets
  REQ    requirement-test vectors T1..T6 (tests_req.build on the baseline spec, as in E1).
  FIELD  all LG HG2 25 degC cycles: identification (TRAIN, 7) + held-out (FIELD, 4), unperturbed.
  STRESS generated with SEED (definitions in stress_set(); recorded in the output JSON). Stress vectors are
         written with float32-exact '%.9g' values, so exact boundary values (knot voltages, rest_i,
         override 0.0/1.0) reach the C unrounded. Includes out-of-range robustness traces (class 'oor').
Classes: EQUIVALENT (identical everywhere), NON-EQUIVALENT BENIGN (differs somewhere; it already passed
every E1 oracle on REQ/FIELD). Stress requirement check: REQ-1 range/finite on every stress trace; on
plant-generated traces with known truth: |err| <= 0.03 (0.05 where truth < 0.1) outside the first 1200 rows
when the initial estimate is overridden, and |err| <= 0.01 after >= 2400 s of commanded rest (REQ-5
analogue). A mutant is reported as breaking a requirement only on a check that the baseline passes on the
same trace. These stress thresholds reuse the REQ tolerances; the windows were set here, after the runs.
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
WORK = pathlib.Path.home() / "cicd-work" / "equiv" / "soc"
OUT = common.ROOT / "results" / "equiv_screen.json"
EDGE_I = [0.0, 0.05, 0.005, 0.5, 0.0499, 0.0501, 0.00499, 0.00501, 0.499, 0.501]


# ---------------------------------------------------------------- vectors
def write_vec(path, I, V, ov, exact):
    with open(path, "w") as f:
        f.write(f"{len(I)} {ov:.9g}\n" if exact else f"{len(I)} {ov:.6f}\n")
        if exact:
            for i, v in zip(np.float32(I), np.float32(V)):
                f.write(f"{float(i):.9g} {float(v):.9g}\n")
        else:
            for i, v in zip(I, V):
                f.write(f"{i:.6f} {v:.6f}\n")
    return hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest()


def rand_profile(rng, n, soc0, imax, Q, p_rest=0.2, p_edge=0.1):
    """Piecewise-constant current; sign flipped when the coulomb-counted SoC leaves [0.03, 0.97]."""
    I, s, j = np.empty(n), soc0, 0
    while j < n:
        u = rng.random()
        if u < p_rest:
            i, d = 0.0, int(rng.integers(60, 2400))
        elif u < p_rest + p_edge:
            i, d = float(rng.choice(EDGE_I)) * float(rng.choice([-1, 1])), int(rng.integers(30, 2400))
        else:
            i, d = float(rng.uniform(-imax, imax)), max(1, int(rng.exponential(120)))
        for _ in range(min(d, n - j)):
            if (s < 0.03 and i < 0) or (s > 0.97 and i > 0):
                i = -i
            I[j], s, j = i, s + i / (3600.0 * Q), j + 1
    return I


def seg(parts):
    return np.concatenate([np.full(int(d), float(i)) for d, i in parts])


def stress_set(p):
    """Returns list of dict(name, cls, I_cmd, I, V, truth, ov, noise, defn)."""
    rng = np.random.default_rng(SEED)
    out = []

    def plant(name, cls, Icmd, soc0, ov, noise, defn):
        S, V, Im = ref.plant(p, Icmd, soc0, rng if noise else None, sigma_v=0.002, sigma_i=0.01)
        out.append(dict(name=name, cls=cls, I_cmd=Icmd, I=Im, V=V, truth=S, ov=ov, noise=noise, defn=defn))

    for k in range(10):
        soc0 = float(rng.uniform(0.1, 0.9))
        ov = -1.0 if k % 2 == 0 else float(np.clip(soc0 + rng.uniform(-0.3, 0.3), 0.0, 1.0))
        plant(f"rand_dyn_{k:02d}", "random", rand_profile(rng, 7200, soc0, 20.0, p["Q"]), soc0, ov, True,
              "7200 rows, piecewise-constant I in [-20,20] A (20 % rests, 10 % rest-threshold edge currents), "
              "plant noise 2 mV / 10 mA, soc0 U(0.1,0.9), override -1 (even k) or soc0+U(-0.3,0.3)")
    for k in range(4):
        soc0 = float(rng.uniform(0.1, 0.9))
        plant(f"rand_lowcur_{k:02d}", "random", rand_profile(rng, 7200, soc0, 1.0, p["Q"], 0.3, 0.4), soc0,
              -1.0, k < 2, "7200 rows, I in [-1,1] A, 30 % rests, 40 % edge currents near rest_i/10, rest_i, 10*rest_i; "
              "noise on k<2, noise-free k>=2")
    for k in range(4):
        soc0 = float(rng.uniform(0.6, 1.0))
        d = int(rng.integers(300, 2400))
        Icmd = seg([(60, 0), (d, -3.0), (10800, 0), (600, 1.5), (7200, 0)])
        ov = [-1.0, min(1.0, soc0 + 0.2), soc0 - 0.2, 0.0][k]
        plant(f"long_rest_{k:02d}", "long_rest", Icmd, soc0, ov, k % 2 == 0,
              "60 s rest, -3 A for U(300,2400) s, 3 h rest, +1.5 A 600 s, 2 h rest; override -1/+0.2/-0.2/0.0 exact")
    for k, (soc0, i, ov) in enumerate([(0.97, 6.0, -1.0), (0.97, 6.0, 1.0), (0.995, 20.0, 1.0)]):
        plant(f"sat_high_{k:02d}", "saturation", seg([(30, 0), (1800, i), (600, 0)]), soc0, ov, k == 0,
              f"overcharge past SoC 1: soc0 {soc0}, +{i} A 1800 s, rest 600 s, override {ov}")
    for k, (soc0, i, ov) in enumerate([(0.08, -6.0, -1.0), (0.08, -6.0, 0.0), (0.02, -20.0, 0.0)]):
        plant(f"sat_low_{k:02d}", "saturation", seg([(30, 0), (1800, i), (600, 0)]), soc0, ov, k == 0,
              f"over-discharge past SoC 0: soc0 {soc0}, {i} A 1800 s, rest 600 s, override {ov}")
    # exact edge cases, noise-free
    for k, ov in enumerate([0.0, 1.0, -1.0, 0.5]):
        Icmd = np.repeat(np.array(EDGE_I + [-x for x in EDGE_I[1:]]), 40)
        plant(f"edge_cur_{k:02d}", "edge", Icmd, 0.5, ov, False,
              f"each edge current (+-{EDGE_I}) for 40 rows, exact float32 values, override {ov}")
    knots = np.float32(p["knots"])
    vlist = list(knots) + [np.float32((knots[j] + knots[j + 1]) / 2) for j in range(len(knots) - 1)] + \
        [np.float32(x) for x in (0.0, 2.0, 2.5, 2.78, 4.16, 4.2, 4.3, 5.0)]
    for k, v0 in enumerate(vlist):
        for ov in (-1.0, 0.0):
            V = np.full(300, float(v0))
            out.append(dict(name=f"edge_v_{k:02d}_ov{int(ov)}", cls="edge", I_cmd=np.zeros(300), I=np.zeros(300),
                            V=V, truth=None, ov=ov, noise=False,
                            defn=f"constant V={float(v0):.9g} (knot values, knot midpoints, out-of-range), I=0, override {ov}"))
    for k in range(4):
        n = 3600
        I = rng.uniform(-30.0, 30.0, n) if k < 2 else rng.choice([-500.0, -50.0, 0.0, 50.0, 500.0], n)
        V = rng.uniform(2.5, 4.3, n) if k < 2 else rng.uniform(0.0, 5.0, n)
        out.append(dict(name=f"oor_{k:02d}", cls="oor", I_cmd=I, I=I, V=V, truth=None, ov=float(rng.uniform(0, 1)),
                        noise=False, defn="out-of-range robustness: iid I U(-30,30) A, V U(2.5,4.3) V (k<2); "
                        "I in {+-500,+-50,0} A, V U(0,5) V (k>=2); REQ-1 only"))
    return out


def perturbed_field(cycles):
    rng = np.random.default_rng(SEED + 1)
    out = []
    for n, c in cycles.items():
        g, off = float(rng.uniform(0.98, 1.02)), float(rng.uniform(-0.03, 0.03))
        I = c["I"] * g + off + rng.normal(0, 0.01, len(c["I"]))
        V = c["V"] + rng.normal(0, 0.002, len(c["V"]))
        out.append(dict(name=f"pert_{n}", cls="perturbed_field", I_cmd=None, I=I, V=V, truth=None, ov=-1.0,
                        noise=True, defn=f"cycle {n}: I*{g:.4f}{off:+.4f} A + N(0,10 mA), V + N(0,2 mV)"))
    return out


# ---------------------------------------------------------------- build / run
def build(vdir):
    r = stages._run(["gcc", "-O2", "-std=c11", "-I.", str(stages.H / "harness.c"), "soc_obs.c", "-lm", "-o", "sil"],
                    vdir)
    if r.returncode != 0:
        raise RuntimeError(f"build failed {vdir}: {r.stderr[-400:]}")


def run_all(vdir, vecs):
    res = {}
    for name, path in vecs.items():
        of = vdir / "o.txt"
        try:
            r = stages._run(["./sil", str(path), str(of)], vdir, timeout=300)
            lines = of.read_text().split("\n") if r.returncode == 0 and of.exists() else []
        except Exception:
            lines = []
        res[name] = [l for l in lines if l.strip()]
    return res


def to_float(lines):
    return np.array([float(x) for x in lines]) if lines else np.zeros(0)


# ---------------------------------------------------------------- stress requirement checks
def stress_checks(tr, out):
    """List of (check_id, violated) for one stress trace."""
    res = []
    n = len(tr["I"])
    ok_len = len(out) == n
    res.append(("REQ1", bool((not ok_len) or (not np.all(np.isfinite(out))) or out.min() < 0 or out.max() > 1), None))
    if tr["truth"] is None or not ok_len or not np.all(np.isfinite(out)):
        return res
    S = tr["truth"]
    err = np.abs(out - S)
    m = (S >= 0) & (S <= 1)
    if tr["ov"] >= 0:
        m[:1200] = False
    tol = np.where(S < 0.1, 0.05, 0.03)
    res.append(("TRACK", bool(np.any(err[m] > tol[m])), float(np.max(err[m] - tol[m])) if m.any() else None))
    if tr["I_cmd"] is not None:
        rest_len = np.zeros(n, int)
        for j in range(1, n):
            rest_len[j] = rest_len[j - 1] + 1 if tr["I_cmd"][j] == 0.0 else 0
        r = (rest_len >= 2400) & m
        if r.any():
            res.append(("REST", bool(np.any(err[r] > 0.01)), float(np.max(err[r] - 0.01))))
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
    for t in tests_req.build(spec):
        p = WORK / "vec" / f"{t['name']}.txt"
        h = write_vec(p, t["I"], t["V"], float(t["override"]), exact=False)
        sets["REQ"][t["name"]] = p
        defs.append(dict(set="REQ", name=t["name"], n=len(t["I"]), sha256=h, defn="tests_req.build (frozen)"))
    cycles = common.load_cycles(common.TRAIN + common.FIELD)
    for n, c in cycles.items():
        p = WORK / "vec" / f"field_{n}.txt"
        h = write_vec(p, c["I"], c["V"], -1.0, exact=False)
        sets["FIELD"][n] = p
        defs.append(dict(set="FIELD", name=n, n=len(c["I"]), sha256=h,
                         defn=("held-out" if n in common.FIELD else "identification") + " cycle, unperturbed"))
    for tr in stress_set(spec["params"]) + perturbed_field(cycles):
        p = WORK / "vec" / f"{tr['name']}.txt"
        h = write_vec(p, tr["I"], tr["V"], tr["ov"], exact=True)
        sets["STRESS"][tr["name"]] = p
        traces[tr["name"]] = tr
        defs.append(dict(set="STRESS", name=tr["name"], cls=tr["cls"], n=len(tr["I"]), override=tr["ov"],
                         sha256=h, defn=tr["defn"]))
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

    with cf.ThreadPoolExecutor(10) as ex:
        outs = dict(ex.map(job, ["baseline"] + ids))
    base = outs["baseline"]
    base_chk = {k: {c: (b, w) for c, b, w in stress_checks(traces[k.split("/", 1)[1]], to_float(v))}
                for k, v in base.items() if k.startswith("STRESS/")}

    results = []
    for mid in ids:
        o = outs[mid]
        per_set, req_breaks = {}, []
        for s in sets:
            keys = [k for k in allvec if k.startswith(s + "/")]
            ndiff, maxd, where, sz = 0, 0.0, None, 0
            for k in keys:
                a, b = o[k], base[k]
                if a == b:
                    continue
                fa, fb = to_float(a), to_float(b)
                if len(fa) != len(fb):
                    ndiff, maxd, where = ndiff + max(len(fa), len(fb)), float("inf"), k
                    continue
                dif = [i for i in range(len(a)) if a[i] != b[i]]
                ndiff += len(dif)
                d = np.abs(fa - fb)
                d = np.where(np.isnan(d), np.inf, d)
                if d.max() >= maxd:
                    maxd, where = float(d.max()), f"{k} row {int(np.argmax(d))}"
                if d.max() == 0:
                    sz += len(dif)   # e.g. -0 vs 0
            per_set[s] = dict(identical=ndiff == 0, rows_diff=ndiff, max_abs_diff=maxd, at=where,
                              signed_zero_only_rows=sz)
        for k in sets["STRESS"]:
            kk = f"STRESS/{k}"
            if o[kk] == base[kk]:
                continue
            for cid, bad, worst in stress_checks(traces[k], to_float(o[kk])):
                if bad and not base_chk[kk].get(cid, (False, None))[0]:
                    req_breaks.append(dict(trace=k, check=cid, mutant_excess=worst,
                                           baseline_excess=base_chk[kk][cid][1]))
        stress_diff_cls = sorted({traces[k]["cls"] for k in sets["STRESS"] if o[f"STRESS/{k}"] != base[f"STRESS/{k}"]})
        eq = all(v["identical"] for v in per_set.values())
        results.append(dict(id=mid, level=muts[mid]["level"], op=muts[mid]["op"], desc=muts[mid]["desc"],
                            cls="EQUIVALENT" if eq else "NON-EQUIVALENT BENIGN", sets=per_set,
                            stress_classes_differing=stress_diff_cls, stress_requirement_breaks=req_breaks,
                            flagged_by_real_board_pil=mid in real_fail))
        print(f"{mid:<20} {results[-1]['cls']:<22} " + " ".join(
            f"{s}:{'=' if v['identical'] else format(v['max_abs_diff'], '.3g')}" for s, v in per_set.items()),
            (" BREAKS " + ",".join(f"{b['trace']}:{b['check']}({b['mutant_excess']:.3g})" for b in req_breaks[:5])) if req_breaks else "", flush=True)

    counts = {}
    for r in results:
        counts[r["cls"]] = counts.get(r["cls"], 0) + 1
    rep = dict(
        status="EXPLORATORY, added 2026-11-11 after the E1 runs; not part of the frozen protocol",
        subject="soc", seed=SEED, perturbed_field_seed=SEED + 1,
        source_list="results/e1_qemu_analysis.json non_field_relevant.unflagged",
        build="gcc -O2 -std=c11 harness/harness.c soc_obs.c -lm (the SIL build), host x86-64 WSL",
        compare="harness '%.9g' output text lines, exact string equality (float32 round-trip exact)",
        model_level="C generated by gen.py from the mutant spec (pipeline C); MIL model not re-simulated",
        stress_requirement_rule=("excess = max(|err| - tol) on the check window; REQ-1 range/finite on all stress traces; plant traces: |err|<=0.03 "
                                 "(0.05 where truth<0.1), first 1200 rows skipped when override>=0; "
                                 "|err|<=0.01 after >=2400 s commanded rest; a break counts only if the "
                                 "baseline passes the same check on the same trace"),
        baseline_stress_check_failures=sorted(f"{k}:{c}" for k, d in base_chk.items() for c, v in d.items() if v[0]),
        note_real_board=("the screened list comes from the QEMU-PIL analysis; flagged_by_real_board_pil marks "
                         "mutants the IoT-LAB st-iotnode PIL run failed (results/e1_pil_iotnode_vs_qemu.json)"),
        n_screened=len(results), counts=counts,
        input_sets=defs, mutants=results)
    OUT.write_text(json.dumps(_clean(rep), indent=1))
    print(json.dumps(counts))


if __name__ == "__main__":
    main()
