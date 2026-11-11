"""Real-target PIL stage (NUCLEO-L476RG over USB, or FIT IoT-LAB st-iotnode). Re-runs the PIL column
of E1 on hardware, reusing the SIL outputs that e1.py left in each version directory.

Oracles are the frozen ones: REQ-1..7, back-to-back vs SIL (tol from calibration.json), timing budget,
and the field oracle on the same stream (field cycles are embedded in the firmware).
The timing budget on hardware = 2 x the baseline's max DWT cycles per step, measured on the same board
by `python pil_real.py calibrate <board>` BEFORE any mutant (rule from the frozen protocol).

Usage (WSL):
  python pil_real.py calibrate nucleo --drive F: --port COM3
  python pil_real.py run nucleo --drive F: --port COM3        (all live mutants of e1_qemu.jsonl)
"""
import argparse
import json
import pathlib
import subprocess
import time

import numpy as np

import common
import e1
import pil_stream
import stages
import tests_req

HERE = common.ROOT
VECDIR = stages.WORK / "stm32vec"
WIN_PY = "/mnt/c/Users/osvaldo/AppData/Local/Programs/Python/Launcher/py.exe"


def winpath(p):
    return subprocess.run(["wslpath", "-w", str(p)], capture_output=True, text=True).stdout.strip()


def build(vdir, board, baud):
    t0 = time.perf_counter()
    r = subprocess.run(["bash", str(HERE / "harness" / "stm32l4" / "build.sh"), str(vdir), board, str(baud)],
                       capture_output=True, text=True, env={**__import__("os").environ, "VECDIR": str(VECDIR)})
    return r.returncode == 0, time.perf_counter() - t0, r.stderr[-500:]


def run_nucleo(vdir, drive, port, baud, timeout=900):
    fw = vdir / "fw_nucleo.bin"
    out = vdir / "pil_nucleo_stream.txt"
    r = subprocess.run([WIN_PY, "-3", winpath(HERE / "harness" / "stm32l4" / "pil_nucleo_win.py"),
                        winpath(fw), drive, port, str(baud), winpath(out), str(timeout)],
                       capture_output=True, text=True)
    try:
        rep = json.loads(r.stdout.strip().splitlines()[-1])
    except Exception:
        rep = dict(ok=False, error=(r.stdout + r.stderr)[-300:])
    return rep, out


class IotlabSession:
    """Holds ONE st-iotnode for the whole campaign; flashes each firmware into the same experiment."""

    def __init__(self, first_elf, minutes):
        import pil_iotlab
        self.L = pil_iotlab
        self.node = pil_iotlab.alive_nodes()[0]
        self.exp = pil_iotlab.submit(str(first_elf), self.node, minutes)
        self.first = True

    def run(self, vdir):
        elf = vdir / "fw_iotnode.elf"
        out = vdir / "pil_iotnode_stream.txt"
        t0 = time.time()
        if not self.first:
            ok, log = self.L.flash(self.exp, self.node, elf)
            if not ok:
                return dict(ok=False, error="flash: " + log[-200:]), out
        self.first = False
        tf = time.time() - t0
        rep = self.L.capture(self.exp, self.node, out)
        rep["seconds_flash"], rep["experiment"], rep["node"] = tf, self.exp, self.node
        return rep, out


def evaluate(vdir, stream_path, names, tests, cal, budget, cycles):
    res = pil_stream.parse(stream_path.read_text(errors="replace"), names)
    fails, bad = [], [n for n in names if n not in res or not res[n]["crc_ok"]]
    if bad:
        return dict(valid=False, bad_vectors=bad)
    for t in tests:
        out = res[t["name"]]["out"]
        fails += tests_req.check(t, out)
        sil, _ = stages._read_out(vdir / f"sil_{t['name']}.out")
        if len(sil) != len(out) or not np.all(np.isfinite(out)) or np.max(np.abs(out - sil)) > cal["b2b"]["tol_pil_sil"]:
            d = np.nanmax(np.abs(out - sil)) if len(sil) == len(out) else float("nan")
            fails.append(f"B2B-SIL {t['name']}: {d:.3g}")
        if budget is not None and res[t["name"]]["max_cycles"] > budget:
            fails.append(f"{t['name']}: timing max cycles {res[t['name']]['max_cycles']} > {budget}")
    metrics, valid = {}, True
    for n, c in cycles.items():
        out = res[f"field_{n}"]["out"]
        if len(out) != len(c["SOC"]) or not np.all(np.isfinite(out)):
            metrics[n], valid = dict(rmse=float("inf"), maxabs=float("inf"), in_range=False), False
            continue
        e = out - c["SOC"]
        metrics[n] = dict(rmse=float(np.sqrt(np.mean(e ** 2))), maxabs=float(np.max(np.abs(e))),
                          in_range=bool(out.min() >= 0 and out.max() <= 1))
    maxcyc = max(res[t["name"]]["max_cycles"] for t in tests)
    return dict(valid=True, passed=not fails, fails=fails[:6], max_cycles=maxcyc,
                field=dict(fail=e1.field_fail(dict(valid=valid, metrics=metrics), cal), metrics=metrics))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=["calibrate", "run"])
    ap.add_argument("board", choices=["nucleo", "iotnode"])
    ap.add_argument("--minutes", type=int, default=240)
    ap.add_argument("--drive", default="F:")
    ap.add_argument("--port", default="COM3")
    ap.add_argument("--baud", type=int, default=115200)
    a = ap.parse_args()
    spec = common.load_spec(HERE / "spec" / "baseline.json")
    cal = json.loads((HERE / "protocol" / "calibration.json").read_text())
    tests, cycles = stages.prepare_vectors(spec)
    names = json.loads((VECDIR / "vectors.json").read_text())
    calp = HERE / "protocol" / f"calibration_{a.board}.json"
    if a.mode == "calibrate":
        v = stages.WORK / "build" / "baseline"
        reps = []
        sess = None
        if a.board == "iotnode":
            build(v, a.board, a.baud)
            sess = IotlabSession(v / "fw_iotnode.elf", a.minutes)
            (HERE / "results" / "iotlab_session.json").write_text(json.dumps(dict(exp=sess.exp, node=sess.node)))
        for r in range(3):
            ok, tb, err = build(v, a.board, a.baud)
            rep, sp = sess.run(v) if sess else run_nucleo(v, a.drive, a.port, a.baud)
            ev = evaluate(v, sp, names, tests, cal, None, cycles) if rep.get("ok") else dict(valid=False)
            reps.append(dict(build_s=tb, **rep, eval=ev))
            print(json.dumps(reps[-1])[:400], flush=True)
        good = [x for x in reps if x["eval"].get("valid")]
        if not good or not all(x["eval"]["passed"] for x in good):
            raise SystemExit("baseline did not pass on hardware; fix before any mutant")
        base = max(x["eval"]["max_cycles"] for x in good)
        calp.write_text(json.dumps(dict(board=a.board, baud=a.baud, baseline_max_cycles=base,
                                        cycle_budget=2 * base, reps=reps), indent=1))
        print("budget", 2 * base)
        return
    budget = json.loads(calp.read_text())["cycle_budget"]
    sess = None
    if a.board == "iotnode":
        s = json.loads((HERE / "results" / "iotlab_session.json").read_text())
        sess = IotlabSession.__new__(IotlabSession)
        import pil_iotlab
        sess.L, sess.node, sess.exp, sess.first = pil_iotlab, s["node"], s["exp"], False
    out = HERE / "results" / f"e1_pil_{a.board}.jsonl"
    done = {json.loads(l)["id"] for l in out.read_text().splitlines()} if out.exists() else set()
    for line in (HERE / "results" / "e1_qemu.jsonl").read_text().splitlines():
        m = json.loads(line)
        if m.get("stillborn") or m["id"] in done:
            continue
        v = stages.WORK / "build" / "mut" / m["id"]
        ok, tb, err = build(v, a.board, a.baud)
        rec = dict(id=m["id"], op=m["op"], level=m["level"], build_ok=ok, build_s=tb)
        if ok:
            for attempt in range(2):
                rep, sp = sess.run(v) if sess else run_nucleo(v, a.drive, a.port, a.baud)
                ev = evaluate(v, sp, names, tests, cal, budget, cycles) if rep.get("ok") else dict(valid=False)
                if ev.get("valid") or (rep.get("ok") and attempt == 1):
                    break
            rec.update(run=rep, eval=ev, attempts=attempt + 1)
        with out.open("a") as f:
            f.write(json.dumps(rec) + "\n")
        print(m["id"], rec.get("eval", {}).get("passed"), rec.get("eval", {}).get("max_cycles"), flush=True)


if __name__ == "__main__":
    main()
