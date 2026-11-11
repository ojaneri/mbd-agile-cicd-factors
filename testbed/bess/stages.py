"""Pipeline stages for subject 3 (same structure as testbed/fuel/stages.py).
Each stage returns a dict with: passed, wall_s, fails, out (per test: dict(te, der)).

UNIT  host gcc, unit tests of the generated C against spec expectations.
MIL   native OpenModelica simulation of the spec's model in a CombiTimeTable testbench.
SIL   host gcc build; requirement checks + back-to-back vs MIL (t_est and der, per-signal tol).
PIL   Cortex-M4 build; dev target QEMU mps2-an386; requirement checks + back-to-back vs SIL + timing.
FIELD QEMU target build replayed on the held-out months (rack 5, 209 segments, 390,859 rows, one
      vector with a reset row at each segment start); per month: RMSE of t_est vs the measured middle
      sensor TCELL and the fraction of rows where der differs from the baseline derating driven by TCELL.
      (390k rows x 3 inputs = 4.7 MB: too large for the boards' 1 MB flash, so, as for subject 2, the
      field oracle runs on the QEMU build of the same target code.)
"""
import pathlib
import subprocess
import time

import numpy as np

import common
import gen
import tests_req

H = common.ROOT / "harness"
WORK = pathlib.Path.home() / "cicd-work" / "bess"
VEC = WORK / "vectors"
MIL_STOP = 3100  # >= longest requirement test (<= 3000 rows)
ARM = ["arm-none-eabi-gcc", "-mcpu=cortex-m4", "-mthumb", "-mfloat-abi=hard", "-mfpu=fpv4-sp-d16",
       "-O2", "-std=c11", "-DPIL_TIMING"]
SIG = ("te", "der")

TB_MODEL = """model BessThermTB
  Modelica.Blocks.Sources.CombiTimeTable tab(tableOnFile = true, tableName = "u", fileName = "vec.txt",
    columns = {2, 3, 4}, smoothness = Modelica.Blocks.Types.Smoothness.ConstantSegments,
    extrapolation = Modelica.Blocks.Types.Extrapolation.HoldLastPoint);
  BessTherm bt;
equation
  bt.rst = tab.y[1];
  bt.cur = tab.y[2];
  bt.tref = tab.y[3];
end BessThermTB;
"""


def _run(cmd, cwd, timeout=900):
    return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=timeout)


def _read_out(path):
    rows, ticks = [], None
    for line in pathlib.Path(path).read_text().splitlines():
        if line.startswith("#ticks"):
            _, tmax, ttot = line.split()
            ticks = (int(tmax), int(ttot))
        elif line.strip():
            a, b = line.split()
            rows.append((float(a), float(b)))
    arr = np.array(rows) if rows else np.zeros((0, 2))
    return dict(te=arr[:, 0], der=arr[:, 1]), ticks


def field_vector():
    """Held-out segments concatenated in file order, rst = 1 at each segment start."""
    segs = common.load_segments(common.FIELD_MONTHS, [common.FIELD_RACK])
    parts = {c: [] for c in ("rst", "I", "TREF", "TCELL")}
    month = []
    for s in segs.values():
        r = np.zeros(len(s["I"]))
        r[0] = 1.0
        for c, a in (("rst", r), ("I", s["I"]), ("TREF", s["TREF"]), ("TCELL", s["TCELL"])):
            parts[c].append(a)
        month += [s["month"]] * len(s["I"])
    v = {c: np.round(np.concatenate(a), 6) for c, a in parts.items()}
    v["month"] = np.array(month)
    return v


def prepare_vectors(baseline_spec):
    VEC.mkdir(parents=True, exist_ok=True)
    tests = tests_req.build(baseline_spec)
    for t in tests:
        tests_req.write_vector(t["v"], VEC / f"{t['name']}.txt")
        n = len(t["v"]["I"])
        with open(VEC / f"{t['name']}.om.txt", "w") as f:
            f.write(f"#1\ndouble u({n},4)\n")
            for j, row in enumerate(zip(*(t["v"][c] for c in tests_req.COLS))):
                f.write(f"{j} " + " ".join(f"{x:.6f}" for x in row) + "\n")
    fv = field_vector()
    p = VEC / "field.txt"
    if not p.exists():
        tests_req.write_vector(fv, p)
    return tests, fv


def prepare_version(spec, vdir, c_text=None):
    vdir = pathlib.Path(vdir)
    gen.generate(spec, vdir)
    if c_text is not None:
        (vdir / "bess.c").write_text(c_text)
    return vdir


def stage_unit(vdir):
    t0 = time.perf_counter()
    b = _run(["gcc", "-O2", "-std=c11", "-I.", str(H / "unit.c"), "bess.c", "-lm", "-o", "unit"], vdir)
    if b.returncode != 0:
        return dict(passed=False, wall_s=time.perf_counter() - t0, fails=["build"], build_error=True)
    try:
        r = _run(["./unit"], vdir, timeout=60)
        ok, detail = r.returncode == 0, r.stdout.strip().splitlines()[-5:]
    except subprocess.TimeoutExpired:
        ok, detail = False, ["timeout"]
    return dict(passed=ok, wall_s=time.perf_counter() - t0, fails=[] if ok else detail)


def stage_mil(vdir, tests):
    t0 = time.perf_counter()
    mil = pathlib.Path(vdir) / "mil"
    mil.mkdir(exist_ok=True)
    (mil / "BessThermTB.mo").write_text(TB_MODEL)
    (mil / "build.mos").write_text(
        'loadModel(Modelica); getErrorString();\n'
        'loadFile("../BessTherm.mo"); loadFile("BessThermTB.mo"); getErrorString();\n'
        # stopTime override is ignored at run time (found on subject 1): build for the longest test.
        f'buildModel(BessThermTB, stopTime={MIL_STOP}, numberOfIntervals={MIL_STOP}, outputFormat="csv", '
        'variableFilter="time|bt.tEst|bt.derate"); getErrorString();\n')
    exe = mil / "BessThermTB"
    if exe.exists():
        exe.unlink()
    b = _run(["omc", "build.mos"], mil)
    if not exe.exists():
        return dict(passed=False, wall_s=time.perf_counter() - t0, fails=["model build"],
                    build_error=True, log=b.stdout[-800:])
    t_build = time.perf_counter() - t0
    outs, fails = {}, []
    for t in tests:
        n = len(t["v"]["I"])
        run = mil / t["name"]
        run.mkdir(exist_ok=True)
        link = run / "vec.txt"
        if not link.exists():
            link.symlink_to(VEC / f"{t['name']}.om.txt")
        try:
            _run([str(exe), f"-inputPath={mil}", "-noEventEmit", "-r=out.csv"], run, timeout=300)
            d = np.genfromtxt(run / "out.csv", delimiter=",", names=True)
            tt = np.arange(1, n + 1, dtype=float)
            out = dict(te=np.interp(tt, d["time"], d["bttEst"]), der=np.interp(tt, d["time"], d["btderate"]))
        except Exception as e:  # a model that fails to simulate is a detection
            fails.append(f"{t['name']}: simulation error {type(e).__name__}")
            continue
        outs[t["name"]] = out
        fails += tests_req.check(t, out)
    return dict(passed=not fails, wall_s=time.perf_counter() - t0, build_s=t_build, fails=fails, out=outs)


def _b2b(name, a, b, tol):
    for s in SIG:
        if name not in a or name not in b or len(a[name][s]) != len(b[name][s]) or len(a[name][s]) == 0:
            return f"{name}: back-to-back missing/length"
        d = np.abs(a[name][s] - b[name][s])
        if not np.all(np.isfinite(d)) or d.max() > tol[s]:
            return f"{name}: back-to-back {s} max {np.nanmax(d):.3g} > {tol[s]:.3g}"
    return None


def stage_sil(vdir, tests, mil_out=None, tol=None):
    t0 = time.perf_counter()
    b = _run(["gcc", "-O2", "-std=c11", "-I.", str(H / "harness.c"), "bess.c", "-lm", "-o", "sil"], vdir)
    if b.returncode != 0:
        return dict(passed=False, wall_s=time.perf_counter() - t0, fails=["build"], build_error=True)
    outs, fails = {}, []
    for t in tests:
        of = pathlib.Path(vdir) / f"sil_{t['name']}.out"
        try:
            r = _run(["./sil", str(VEC / f"{t['name']}.txt"), str(of)], vdir, timeout=120)
            out, _ = _read_out(of) if r.returncode == 0 else (dict(te=np.array([]), der=np.array([])), None)
        except subprocess.TimeoutExpired:
            out = dict(te=np.array([]), der=np.array([]))
        outs[t["name"]] = out
        fails += tests_req.check(t, out)
        if mil_out is not None and tol is not None:
            m = _b2b(t["name"], outs, mil_out, tol)
            if m:
                fails.append("B2B-MIL " + m)
    return dict(passed=not fails, wall_s=time.perf_counter() - t0, fails=fails, out=outs)


def build_target(vdir, target="qemu"):
    if target != "qemu":
        raise NotImplementedError(target)
    q = H / "qemu"
    return _run(ARM + ["-I.", f"-I{q}", "--specs=rdimon.specs", "-T", str(q / "mps2.ld"),
                       str(q / "startup.c"), str(H / "harness.c"), "bess.c", "-lm", "-o", "pil.elf"], vdir)


def run_target(vdir, infile, outfile, target="qemu", timeout=300):
    if target != "qemu":
        raise NotImplementedError(target)
    cfg = f"enable=on,target=native,arg=pil.elf,arg={infile},arg={outfile}"
    return _run(["qemu-system-arm", "-M", "mps2-an386", "-cpu", "cortex-m4", "-nographic", "-monitor", "none",
                 "-serial", "none", "-icount", "shift=6", "-semihosting-config", cfg,
                 "-kernel", "pil.elf"], vdir, timeout=timeout)


def stage_pil(vdir, tests, sil_out=None, tol=None, tick_budget=None, target="qemu"):
    t0 = time.perf_counter()
    b = build_target(vdir, target)
    if b.returncode != 0:
        return dict(passed=False, wall_s=time.perf_counter() - t0, fails=["build"], build_error=True)
    outs, ticks, fails = {}, {}, []
    for t in tests:
        of = pathlib.Path(vdir) / f"pil_{t['name']}.out"
        if of.exists():
            of.unlink()
        try:
            run_target(vdir, str(VEC / f"{t['name']}.txt"), str(of), target)
            out, tk = _read_out(of) if of.exists() else (dict(te=np.array([]), der=np.array([])), None)
        except subprocess.TimeoutExpired:
            out, tk = dict(te=np.array([]), der=np.array([])), None
        outs[t["name"]], ticks[t["name"]] = out, tk
        fails += tests_req.check(t, out)
        if sil_out is not None and tol is not None:
            m = _b2b(t["name"], outs, sil_out, tol)
            if m:
                fails.append("B2B-SIL " + m)
        if tick_budget is not None and (tk is None or tk[0] > tick_budget):
            fails.append(f"{t['name']}: timing max ticks {tk[0] if tk else None} > {tick_budget}")
    return dict(passed=not fails, wall_s=time.perf_counter() - t0, fails=fails, out=outs, ticks=ticks)


def field(vdir, fv, target="qemu"):
    """Replay the target build on the held-out vector; per month RMSE [degC] and derating mismatch [%]."""
    import ref
    t0 = time.perf_counter()
    if not (pathlib.Path(vdir) / "pil.elf").exists():
        b = build_target(vdir, target)
        if b.returncode != 0:
            return dict(valid=False, wall_s=time.perf_counter() - t0, metrics={}, reason="build")
    of = pathlib.Path(vdir) / "field.out"
    if of.exists():
        of.unlink()
    try:
        run_target(vdir, str(VEC / "field.txt"), str(of), target, timeout=1800)
        out, _ = _read_out(of) if of.exists() else (dict(te=np.array([]), der=np.array([])), None)
    except subprocess.TimeoutExpired:
        out = dict(te=np.array([]), der=np.array([]))
    n = len(fv["I"])
    if len(out["te"]) != n or not np.all(np.isfinite(out["te"])) or not np.all(np.isfinite(out["der"])):
        return dict(valid=False, wall_s=time.perf_counter() - t0,
                    metrics={m: dict(rmse=float("inf"), der_mismatch_pct=float("inf")) for m in common.FIELD_MONTHS})
    base = common.load_spec(common.ROOT / "spec" / "baseline.json")
    dref = ref.derate_from_temp(base, fv["rst"], fv["TCELL"])
    metrics = {}
    for m in common.FIELD_MONTHS:
        k = fv["month"] == m
        e = out["te"][k] - fv["TCELL"][k]
        metrics[m] = dict(rmse=float(np.sqrt(np.mean(e ** 2))),
                          der_mismatch_pct=float(np.mean(np.abs(out["der"][k] - dref[k]) > 1e-3) * 100.0))
    return dict(valid=True, wall_s=time.perf_counter() - t0, metrics=metrics)
