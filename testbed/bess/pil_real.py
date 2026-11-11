"""Real-target PIL for subject 3, reusing subject 1's IoT-LAB session (same node, same reservation).

Frozen oracles: REQ-1..5 (tests_req.check), back-to-back vs the SIL outputs that e1.py left in each
version dir (tol from calibration.json), timing budget = 2 x baseline max DWT cycles on the same board
(set by `calibrate` before any mutant). The field oracle stays the QEMU one recorded by e1.py
(the held-out vector does not fit in the boards flash; documented deviation).
Usage (WSL, with an IoT-LAB session file written by subject 1's runner; no other campaign on the node):
  python pil_real.py calibrate iotnode
  python pil_real.py run iotnode
"""
import json
import os
import subprocess
import sys
import time

import numpy as np

import common
import pil_stream
import stages
import tests_req

sys.path.insert(0, str(common.ROOT.parent / "soc"))
import pil_iotlab  # noqa: E402  (subject 1's IoT-LAB helpers, same lessons applied)

HERE = common.ROOT
VECDIR = stages.WORK / "stm32vec"
SESSION = common.ROOT.parent / "soc" / "results" / "iotlab_session.json"


def build(vdir, board, baud=115200):
    t0 = time.perf_counter()
    r = subprocess.run(["bash", str(HERE / "harness" / "stm32l4" / "build.sh"), str(vdir), board, str(baud)],
                       capture_output=True, text=True, env={**os.environ, "VECDIR": str(VECDIR)})
    return r.returncode == 0, time.perf_counter() - t0, r.stderr[-400:]


def run_iotnode(vdir, sess):
    elf, out = vdir / "fw_iotnode.elf", vdir / "pil_iotnode_stream.txt"
    t0 = time.time()
    ok, log = pil_iotlab.flash(sess["exp"], sess["node"], elf)
    if not ok:
        return dict(ok=False, error="flash: " + log[-200:]), out
    tf = time.time() - t0
    rep = pil_iotlab.capture(sess["exp"], sess["node"], out, run_timeout=120)
    rep["seconds_flash"] = tf
    return rep, out


def evaluate(vdir, stream, names, tests, cal, budget):
    res = pil_stream.parse(stream.read_text(errors="replace"), names)
    bad = [n for n in names if n not in res or not res[n]["crc_ok"]]
    if bad:
        return dict(valid=False, bad_vectors=bad)
    tol = cal["b2b"]["tol_pil_sil"]
    fails = []
    for t in tests:
        out = dict(te=res[t["name"]]["te"], der=res[t["name"]]["der"])
        fails += tests_req.check(t, out)
        sil, _ = stages._read_out(vdir / f"sil_{t['name']}.out")
        m = stages._b2b(t["name"], {t["name"]: out}, {t["name"]: sil}, tol)
        if m:
            fails.append("B2B-SIL " + m)
        if budget is not None and res[t["name"]]["max_cycles"] > budget:
            fails.append(f"{t['name']}: timing max cycles {res[t['name']]['max_cycles']} > {budget}")
    return dict(valid=True, passed=not fails, fails=fails[:6],
                max_cycles=max(res[t["name"]]["max_cycles"] for t in tests))


def main():
    mode, board = sys.argv[1], sys.argv[2]
    assert board == "iotnode", "subject 3 real PIL implemented for the IoT-LAB session only"
    spec = common.load_spec(HERE / "spec" / "baseline.json")
    cal = json.loads((HERE / "protocol" / "calibration.json").read_text())
    tests = stages.prepare_vectors(spec)[0]
    names = json.loads((VECDIR / "vectors.json").read_text())
    sess = json.loads(SESSION.read_text())
    calp = HERE / "protocol" / f"calibration_{board}.json"
    if mode == "calibrate":
        v = stages.WORK / "build" / "baseline"
        reps = []
        for _ in range(3):
            ok, tb, err = build(v, board)
            rep, sp = run_iotnode(v, sess)
            ev = evaluate(v, sp, names, tests, cal, None) if rep.get("ok") else dict(valid=False)
            reps.append(dict(build_s=tb, **rep, eval=ev))
            print(json.dumps(reps[-1])[:300], flush=True)
        good = [x for x in reps if x["eval"].get("valid")]
        if not good or not all(x["eval"]["passed"] for x in good):
            raise SystemExit("baseline did not pass on hardware; fix before any mutant")
        base = max(x["eval"]["max_cycles"] for x in good)
        calp.write_text(json.dumps(dict(board=board, baseline_max_cycles=base, cycle_budget=2 * base,
                                        session=sess, reps=reps), indent=1))
        print("budget", 2 * base)
        return
    budget = json.loads(calp.read_text())["cycle_budget"]
    out = HERE / "results" / f"e1_pil_{board}.jsonl"
    done = {json.loads(l)["id"] for l in out.read_text().splitlines()} if out.exists() else set()
    for line in (HERE / "results" / "e1_qemu.jsonl").read_text().splitlines():
        m = json.loads(line)
        if m.get("stillborn") or m["id"] in done:
            continue
        v = stages.WORK / "build" / "mut" / m["id"]
        ok, tb, err = build(v, board)
        rec = dict(id=m["id"], op=m["op"], level=m["level"], build_ok=ok, build_s=tb)
        if ok:
            for attempt in range(2):
                rep, sp = run_iotnode(v, sess)
                ev = evaluate(v, sp, names, tests, cal, budget) if rep.get("ok") else dict(valid=False)
                if ev.get("valid"):
                    break
            # field verdict: the QEMU field oracle recorded by e1.py (documented deviation)
            ev["field"] = m.get("field", {})
            rec.update(run=rep, eval=ev, attempts=attempt + 1)
        with out.open("a") as f:
            f.write(json.dumps(rec) + "\n")
        print(m["id"], rec.get("eval", {}).get("passed"), rec.get("eval", {}).get("max_cycles"), flush=True)


if __name__ == "__main__":
    main()
