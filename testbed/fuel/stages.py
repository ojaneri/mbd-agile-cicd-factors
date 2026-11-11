"""Pipeline stages for subject 2 (same structure as testbed/soc/stages.py).
Each stage returns a dict with: passed, wall_s, fails, out (per test: dict(rate, vol)).

UNIT  host gcc, unit tests of the generated C against spec expectations.
MIL   native OpenModelica simulation of the spec's model in a CombiTimeTable testbench.
SIL   host gcc build; requirement checks + back-to-back vs MIL (rate and volume, per-signal tol).
PIL   Cortex-M4 build; dev target QEMU mps2-an386; requirement checks + back-to-back vs SIL + timing.
FIELD QEMU target build replayed on held-out tanks 18-22; per-tank volume error vs refuelled litres.
      (Field tanks are ~194k rows x 6 inputs: too large to embed in the 1 MB flash of the real boards,
      so the field oracle runs on the QEMU build of the same target code.)
"""
import pathlib
import subprocess
import time

import numpy as np

import common
import gen
import tests_req

H = common.ROOT / "harness"
WORK = pathlib.Path.home() / "cicd-work" / "fuel"
VEC = WORK / "vectors"
MIL_STOP = 3100  # >= longest requirement test (3000 rows)
ARM = ["arm-none-eabi-gcc", "-mcpu=cortex-m4", "-mthumb", "-mfloat-abi=hard", "-mfpu=fpv4-sp-d16",
       "-O2", "-std=c11", "-DPIL_TIMING"]
SIG = ("rate", "vol")

TB_MODEL = """model FuelFlowTB
  Modelica.Blocks.Sources.CombiTimeTable tab(tableOnFile = true, tableName = "u", fileName = "vec.txt",
    columns = {2, 3, 4, 5, 6, 7}, smoothness = Modelica.Blocks.Types.Smoothness.ConstantSegments,
    extrapolation = Modelica.Blocks.Types.Extrapolation.HoldLastPoint);
  FuelFlow ff;
equation
  ff.dtIn = tab.y[1];
  ff.maf = tab.y[2];
  ff.rpm = tab.y[3];
  ff.thr = tab.y[4];
  ff.stft = tab.y[5];
  ff.ltft = tab.y[6];
end FuelFlowTB;
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
    return dict(rate=arr[:, 0], vol=arr[:, 1]), ticks


def prepare_vectors(baseline_spec):
    VEC.mkdir(parents=True, exist_ok=True)
    tests = tests_req.build(baseline_spec)
    for t in tests:
        tests_req.write_vector(t["v"], VEC / f"{t['name']}.txt")
        n = len(t["v"]["dt"])
        with open(VEC / f"{t['name']}.om.txt", "w") as f:
            f.write(f"#1\ndouble u({n},7)\n")
            for j, row in enumerate(zip(*(t["v"][c] for c in tests_req.COLS))):
                f.write(f"{j} " + " ".join(f"{x:.6f}" for x in row) + "\n")
    tanks = common.load_tanks(common.FIELD)
    for sid, v in tanks.items():
        p = VEC / f"field_{sid}.txt"
        if not p.exists():
            tests_req.write_vector(v, p)
    return tests, tanks


def prepare_version(spec, vdir, c_text=None):
    vdir = pathlib.Path(vdir)
    gen.generate(spec, vdir)
    if c_text is not None:
        (vdir / "fuel.c").write_text(c_text)
    return vdir


def stage_unit(vdir):
    t0 = time.perf_counter()
    b = _run(["gcc", "-O2", "-std=c11", "-I.", str(H / "unit.c"), "fuel.c", "-lm", "-o", "unit"], vdir)
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
    (mil / "FuelFlowTB.mo").write_text(TB_MODEL)
    (mil / "build.mos").write_text(
        'loadModel(Modelica); getErrorString();\n'
        'loadFile("../FuelFlow.mo"); loadFile("FuelFlowTB.mo"); getErrorString();\n'
        # stopTime override is ignored at run time (found on subject 1): build for the longest test.
        f'buildModel(FuelFlowTB, stopTime={MIL_STOP}, numberOfIntervals={MIL_STOP}, outputFormat="csv", '
        'variableFilter="time|ff.rate|ff.vol"); getErrorString();\n')
    exe = mil / "FuelFlowTB"
    if exe.exists():
        exe.unlink()
    b = _run(["omc", "build.mos"], mil)
    if not exe.exists():
        return dict(passed=False, wall_s=time.perf_counter() - t0, fails=["model build"],
                    build_error=True, log=b.stdout[-800:])
    t_build = time.perf_counter() - t0
    outs, fails = {}, []
    for t in tests:
        n = len(t["v"]["dt"])
        run = mil / t["name"]
        run.mkdir(exist_ok=True)
        link = run / "vec.txt"
        if not link.exists():
            link.symlink_to(VEC / f"{t['name']}.om.txt")
        try:
            _run([str(exe), f"-inputPath={mil}", "-noEventEmit", "-r=out.csv"], run, timeout=300)
            d = np.genfromtxt(run / "out.csv", delimiter=",", names=True)
            tt = np.arange(1, n + 1, dtype=float)
            out = dict(rate=np.interp(tt, d["time"], d["ffrate"]), vol=np.interp(tt, d["time"], d["ffvol"]))
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
    b = _run(["gcc", "-O2", "-std=c11", "-I.", str(H / "harness.c"), "fuel.c", "-lm", "-o", "sil"], vdir)
    if b.returncode != 0:
        return dict(passed=False, wall_s=time.perf_counter() - t0, fails=["build"], build_error=True)
    outs, fails = {}, []
    for t in tests:
        of = pathlib.Path(vdir) / f"sil_{t['name']}.out"
        try:
            r = _run(["./sil", str(VEC / f"{t['name']}.txt"), str(of)], vdir, timeout=120)
            out, _ = _read_out(of) if r.returncode == 0 else (dict(rate=np.array([]), vol=np.array([])), None)
        except subprocess.TimeoutExpired:
            out = dict(rate=np.array([]), vol=np.array([]))
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
                       str(q / "startup.c"), str(H / "harness.c"), "fuel.c", "-lm", "-o", "pil.elf"], vdir)


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
            out, tk = _read_out(of) if of.exists() else (dict(rate=np.array([]), vol=np.array([])), None)
        except subprocess.TimeoutExpired:
            out, tk = dict(rate=np.array([]), vol=np.array([])), None
        outs[t["name"]], ticks[t["name"]] = out, tk
        fails += tests_req.check(t, out)
        if sil_out is not None and tol is not None:
            m = _b2b(t["name"], outs, sil_out, tol)
            if m:
                fails.append("B2B-SIL " + m)
        if tick_budget is not None and (tk is None or tk[0] > tick_budget):
            fails.append(f"{t['name']}: timing max ticks {tk[0] if tk else None} > {tick_budget}")
    return dict(passed=not fails, wall_s=time.perf_counter() - t0, fails=fails, out=outs, ticks=ticks)


def field(vdir, tanks, target="qemu"):
    """Replay the target build on held-out tanks; relative volume error vs refuelled litres [%]."""
    t0 = time.perf_counter()
    if not (pathlib.Path(vdir) / "pil.elf").exists():
        b = build_target(vdir, target)
        if b.returncode != 0:
            return dict(valid=False, wall_s=time.perf_counter() - t0, metrics={}, reason="build")
    refuel = common.refuel_litres()
    metrics, valid = {}, True
    for sid, v in tanks.items():
        of = pathlib.Path(vdir) / f"field_{sid}.out"
        if of.exists():
            of.unlink()
        try:
            run_target(vdir, str(VEC / f"field_{sid}.txt"), str(of), target, timeout=900)
            out, _ = _read_out(of) if of.exists() else (dict(rate=np.array([]), vol=np.array([])), None)
        except subprocess.TimeoutExpired:
            out = dict(rate=np.array([]), vol=np.array([]))
        vol = out["vol"]
        if len(vol) != len(v["dt"]) or not np.all(np.isfinite(vol)) or not np.all(np.isfinite(out["rate"])):
            metrics[str(sid)], valid = dict(rel_err_pct=float("inf"), litres=float("nan")), False
            continue
        litres = float(vol[-1]) / 1000.0
        metrics[str(sid)] = dict(litres=litres, rel_err_pct=(litres - refuel[sid]) / refuel[sid] * 100.0)
    return dict(valid=valid, wall_s=time.perf_counter() - t0, metrics=metrics)
