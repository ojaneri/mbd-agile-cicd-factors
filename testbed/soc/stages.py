"""Pipeline stages for subject 1. Each stage returns a dict with: passed, wall_s, fails, out (per test).

UNIT  host gcc, unit tests of the generated C against spec expectations.
MIL   native OpenModelica simulation of the spec's model in a testbench (CombiTimeTable inputs,
      constant segments); requirement checks. (An FMU route via FMPy was tried first and dropped:
      the ME FMU did not process the sample() events with FMPy inputs, and the CS build failed.)
SIL   host gcc build of the production C; requirement checks + back-to-back against MIL (same version).
PIL   cross-compiled C on a Cortex-M4 target; requirement checks + back-to-back against SIL + timing.
      Target 'qemu' (development only: tick counts are an instruction proxy, not time).
FIELD target build replayed on the held-out real cycles (25degC Mixed5-8); oracle for escapes.
"""
import json
import pathlib
import subprocess
import time

import numpy as np

import common
import gen
import tests_req

H = common.ROOT / "harness"
WORK = pathlib.Path.home() / "cicd-work"      # Linux filesystem: builds are much faster than on /mnt/d
VEC = WORK / "vectors"
MIL_STOP = 3700  # >= longest requirement test (3660 rows)

TB_MODEL = """model SocObsTB
  parameter Real ov = -1.0;
  Modelica.Blocks.Sources.CombiTimeTable tab(tableOnFile = true, tableName = "u", fileName = "vec.txt",
    columns = {2, 3}, smoothness = Modelica.Blocks.Types.Smoothness.ConstantSegments,
    extrapolation = Modelica.Blocks.Types.Extrapolation.HoldLastPoint);
  SocObs obs(socOverride = ov);
equation
  obs.I = tab.y[1];
  obs.V = tab.y[2];
end SocObsTB;
"""
ARM = ["arm-none-eabi-gcc", "-mcpu=cortex-m4", "-mthumb", "-mfloat-abi=hard", "-mfpu=fpv4-sp-d16",
       "-O2", "-std=c11", "-DPIL_TIMING"]


def _run(cmd, cwd, timeout=900):
    return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=timeout)


def _read_out(path):
    vals, ticks = [], None
    for line in pathlib.Path(path).read_text().splitlines():
        if line.startswith("#ticks"):
            _, tmax, ttot = line.split()
            ticks = (int(tmax), int(ttot))
        elif line.strip():
            vals.append(float(line))
    return np.array(vals), ticks


def prepare_vectors(baseline_spec):
    """Write requirement-test vectors and field cycles once (shared by all versions)."""
    VEC.mkdir(parents=True, exist_ok=True)
    tests = tests_req.build(baseline_spec)
    for t in tests:
        tests_req.write_vector(t, VEC / f"{t['name']}.txt")
        n = len(t["I"])
        with open(VEC / f"{t['name']}.om.txt", "w") as f:
            f.write(f"#1\ndouble u({n},3)\n")
            for j, (i, v) in enumerate(zip(t["I"], t["V"])):
                f.write(f"{j} {i:.6f} {v:.6f}\n")
    field = common.load_cycles(common.FIELD)
    for n, c in field.items():
        tests_req.write_cycle(c["I"], c["V"], VEC / f"field_{n}.txt")
    return tests, field


def prepare_version(spec, vdir, c_text=None):
    vdir = pathlib.Path(vdir)
    gen.generate(spec, vdir)
    if c_text is not None:
        (vdir / "soc_obs.c").write_text(c_text)
    return vdir


def stage_unit(vdir):
    t0 = time.perf_counter()
    b = _run(["gcc", "-O2", "-std=c11", "-I.", str(H / "unit.c"), "soc_obs.c", "-lm", "-o", "unit"], vdir)
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
    (mil / "SocObsTB.mo").write_text(TB_MODEL)
    (mil / "build.mos").write_text(
        'loadModel(Modelica); getErrorString();\n'
        'loadFile("../SocObs.mo"); loadFile("SocObsTB.mo"); getErrorString();\n'
        # stopTime cannot be overridden at run time here (the override was ignored), so the model is
        # built for the longest test; shorter tests hold their last row and are truncated on read.
        f'buildModel(SocObsTB, stopTime={MIL_STOP}, numberOfIntervals={MIL_STOP}, outputFormat="csv", '
        'variableFilter="time|obs.soc"); getErrorString();\n')
    exe = mil / "SocObsTB"
    if exe.exists():
        exe.unlink()
    b = _run(["omc", "build.mos"], mil)
    if not exe.exists():
        return dict(passed=False, wall_s=time.perf_counter() - t0, fails=["model build"],
                    build_error=True, log=b.stdout[-800:])
    t_build = time.perf_counter() - t0
    outs, fails = {}, []
    for t in tests:
        n = len(t["I"])
        run = mil / t["name"]
        run.mkdir(exist_ok=True)
        link = run / "vec.txt"
        if not link.exists():
            link.symlink_to(VEC / f"{t['name']}.om.txt")
        try:
            r = _run([str(exe), f"-inputPath={mil}", "-noEventEmit",
                      f"-override=ov={float(t['override'])}",
                      "-r=out.csv"], run, timeout=300)
            d = np.genfromtxt(run / "out.csv", delimiter=",", names=True)
            out = np.interp(np.arange(1, n + 1, dtype=float), d["time"], d["obssoc"])
        except Exception as e:  # a model that fails to simulate is a detection
            fails.append(f"{t['name']}: simulation error {type(e).__name__}")
            continue
        outs[t["name"]] = out
        fails += tests_req.check(t, out)
    return dict(passed=not fails, wall_s=time.perf_counter() - t0, build_s=t_build, fails=fails, out=outs)


def _b2b(name, a, b, tol):
    if name not in a or name not in b or len(a[name]) != len(b[name]):
        return f"{name}: back-to-back missing/length"
    d = np.abs(a[name] - b[name])
    if not np.all(np.isfinite(d)) or d.max() > tol:
        return f"{name}: back-to-back max {np.nanmax(d):.3g} > {tol:.3g}"
    return None


def stage_sil(vdir, tests, mil_out=None, tol=None):
    t0 = time.perf_counter()
    b = _run(["gcc", "-O2", "-std=c11", "-I.", str(H / "harness.c"), "soc_obs.c", "-lm", "-o", "sil"], vdir)
    if b.returncode != 0:
        return dict(passed=False, wall_s=time.perf_counter() - t0, fails=["build"], build_error=True)
    outs, fails = {}, []
    for t in tests:
        of = pathlib.Path(vdir) / f"sil_{t['name']}.out"
        try:
            r = _run(["./sil", str(VEC / f"{t['name']}.txt"), str(of)], vdir, timeout=120)
            out, _ = _read_out(of) if r.returncode == 0 else (np.array([]), None)
        except subprocess.TimeoutExpired:
            out = np.array([])
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
                       str(q / "startup.c"), str(H / "harness.c"), "soc_obs.c", "-lm", "-o", "pil.elf"], vdir)


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
        try:
            r = run_target(vdir, str(VEC / f"{t['name']}.txt"), str(of), target)
            out, tk = _read_out(of) if of.exists() else (np.array([]), None)
        except subprocess.TimeoutExpired:
            out, tk = np.array([]), None
        outs[t["name"]], ticks[t["name"]] = out, tk
        fails += tests_req.check(t, out)
        if sil_out is not None and tol is not None:
            m = _b2b(t["name"], outs, sil_out, tol)
            if m:
                fails.append("B2B-SIL " + m)
        if tick_budget is not None and (tk is None or tk[0] > tick_budget):
            fails.append(f"{t['name']}: timing max ticks {tk[0] if tk else None} > {tick_budget}")
    return dict(passed=not fails, wall_s=time.perf_counter() - t0, fails=fails, out=outs, ticks=ticks)


def field(vdir, cycles, target="qemu"):
    """Replay the target build on held-out real cycles. Returns per-cycle RMSE/max and validity."""
    t0 = time.perf_counter()
    if not (pathlib.Path(vdir) / "pil.elf").exists():
        b = build_target(vdir, target)
        if b.returncode != 0:
            return dict(valid=False, wall_s=time.perf_counter() - t0, metrics={}, reason="build")
    metrics, valid = {}, True
    for n, c in cycles.items():
        of = pathlib.Path(vdir) / f"field_{n}.out"
        try:
            run_target(vdir, str(VEC / f"field_{n}.txt"), str(of), target, timeout=600)
            out, _ = _read_out(of) if of.exists() else (np.array([]), None)
        except subprocess.TimeoutExpired:
            out = np.array([])
        if len(out) != len(c["SOC"]) or not np.all(np.isfinite(out)):
            metrics[n], valid = dict(rmse=float("inf"), maxabs=float("inf"), in_range=False), False
            continue
        e = out - c["SOC"]
        metrics[n] = dict(rmse=float(np.sqrt(np.mean(e ** 2))), maxabs=float(np.max(np.abs(e))),
                          in_range=bool(out.min() >= 0 and out.max() <= 1))
    return dict(valid=valid, wall_s=time.perf_counter() - t0, metrics=metrics)
