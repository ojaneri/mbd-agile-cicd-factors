"""E5 runner (frozen with the protocol). One subject per process.

Arms (every arm uses the same oracles: the subject's frozen requirement checks REQ-*, plus back-to-back
against the BASELINE host SIL outputs with the subject's E1 tol_pil_sil, plus, on targets, the timing
budget = 2 x the platform's baseline max SysTick per step, set by `calibrate` before any mutant):
  host_sil        gcc -O2 SIL, as in E1
  host_poison     SIL with the state struct memset to 0x00 / 0xFF / 0xAA / 0x55 before init (4 runs)
  host_valgrind   the host_sil binary under Valgrind memcheck (--error-exitcode=99)
  host_msan       clang -O2 -fsanitize=memory build (secondary)
  qemu            the E5 firmware ELF on qemu-system-arm -M b-l475e-iot01a -icount shift=6
  board           the SAME ELF on FIT IoT-LAB st-iotnode (STM32L475VG); 2 captures (resets) for INIT/LUD
Target firmware: 5 passes (0 = no paint, 1..4 = stack painted 0x00000000/0xFFFFFFFF/0xAAAAAAAA/0x55555555)
for INIT/LUD mutants and the baseline; 1 pass for timing ladders and control mutants.
Usage (WSL, venv):
  python run_e5.py <subject> calibrate [--board]
  python run_e5.py <subject> run <init|ladder|control> <comma-separated arms>
"""
import json
import os
import pathlib
import re
import shutil
import struct
import subprocess
import sys
import time
import zlib

import numpy as np

E5 = pathlib.Path(__file__).resolve().parent
TB = E5.parent
SUBJ = {
    "soc": dict(dir=TB / "soc", work=pathlib.Path.home() / "cicd-work", src="soc_obs", step="soc_obs_step", fields=None),
    "fuel": dict(dir=TB / "fuel", work=pathlib.Path.home() / "cicd-work" / "fuel", src="fuel", step="fuel_step",
                 fields=("rate", "vol")),
    "bess": dict(dir=TB / "bess", work=pathlib.Path.home() / "cicd-work" / "bess", src="bess", step="bess_step",
                 fields=("te", "der")),
}
PATTERNS = ("0x00", "0xFF", "0xAA", "0x55")
HOST_ARMS = ("host_sil", "host_poison", "host_valgrind", "host_msan")

NAME = sys.argv[1]
S = SUBJ[NAME]
sys.path.insert(0, str(TB / "soc"))
sys.path.insert(0, str(S["dir"]))
import common  # noqa: E402
import stages  # noqa: E402
import tests_req  # noqa: E402

if (TB / "soc").resolve() != S["dir"].resolve():
    import importlib.util
    spec_ = importlib.util.spec_from_file_location("pil_iotlab", TB / "soc" / "pil_iotlab.py")
    pil_iotlab = importlib.util.module_from_spec(spec_)
    spec_.loader.exec_module(pil_iotlab)
else:
    import pil_iotlab  # noqa: E402

WORK = S["work"]
VECDIR = WORK / "e5vec"
BASE = WORK / "build" / "baseline"
OUTD = WORK / "e5"
RES = pathlib.Path(os.environ.get("E5_RESULTS", E5 / "results" / f"e5_{NAME}.jsonl"))
ONLY = set(filter(None, os.environ.get("E5_ONLY", "").split(",")))  # smoke tests: restrict to these ids
CALP = E5 / "protocol" / f"calibration_{NAME}.json"
SESSION = E5 / "results" / "iotlab_session.json"
CAL1 = json.loads((S["dir"] / "protocol" / "calibration.json").read_text())
TOL = CAL1["b2b"]["tol_pil_sil"]


def sh(cmd, cwd=None, timeout=600, env=None):
    return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=timeout, env=env)


# ---------------------------------------------------------------- setup
def tests_and_refs():
    spec = common.load_spec(S["dir"] / "spec" / "baseline.json")
    tests = stages.prepare_vectors(spec)[0]
    refs = {t["name"]: stages._read_out(BASE / f"sil_{t['name']}.out")[0] for t in tests}
    if not (VECDIR / "vectors.json").exists():
        r = sh([sys.executable, str(E5 / "gen_vec_e5.py"), str(S["dir"]), str(VECDIR)], cwd=S["dir"])
        assert r.returncode == 0, r.stderr
    names = json.loads((VECDIR / "vectors.json").read_text())
    assert names == [t["name"] for t in tests], "vector order differs from the requirement tests"
    return tests, refs, names


def prepare(vid, c_text):
    vdir = OUTD / vid
    if vdir.exists():
        shutil.rmtree(vdir)
    vdir.mkdir(parents=True)
    (vdir / f"{S['src']}.c").write_text(c_text)
    shutil.copy(BASE / f"{S['src']}.h", vdir)
    return vdir


def oracle(t, out, ref):
    fails = list(tests_req.check(t, out))
    m = stages._b2b(t["name"], {t["name"]: out}, {t["name"]: ref}, TOL)
    if m:
        fails.append("B2B-REF " + m)
    return fails


def _conv(rows):
    if S["fields"] is None:
        return rows[:, 0] if rows.size else np.array([])
    return {f: (rows[:, i] if rows.size else np.array([])) for i, f in enumerate(S["fields"])}


# ---------------------------------------------------------------- host arms
def _poison_harness(vdir):
    txt = (S["dir"] / "harness" / "harness.c").read_text()
    m = re.search(r"^(\s*)(\w+_t)\s+(\w+);\s*$", txt, re.M)
    assert m, "state declaration not found in harness"
    ins = f"{m.group(0)}\n{m.group(1)}memset(&{m.group(3)}, E5_POISON, sizeof {m.group(3)});"
    txt = "#include <string.h>\n" + txt[:m.start()] + ins + txt[m.end():]
    (vdir / "harness_poison.c").write_text(txt)


def host_arm(arm, vdir, tests, refs):
    t0 = time.perf_counter()
    h = str(S["dir"] / "harness" / "harness.c")
    inc = ["-I.", f"-I{E5 / 'fw'}"]
    src = f"{S['src']}.c"
    rep = dict(arm=arm, valid=True)
    if arm in ("host_sil", "host_valgrind"):
        variants = [("sil", ["gcc", "-O2", "-std=c11", "-g", *inc, h, src, "-lm", "-o", "sil"])]
    elif arm == "host_poison":
        _poison_harness(vdir)
        variants = [(f"poison_{p}", ["gcc", "-O2", "-std=c11", *inc, f"-DE5_POISON={p}", "harness_poison.c", src,
                                     "-lm", "-o", f"poison_{p}"]) for p in PATTERNS]
    elif arm == "host_msan":
        variants = [("msan", ["clang", "-O2", "-g", "-fsanitize=memory", "-fno-omit-frame-pointer", *inc, h, src,
                              "-lm", "-o", "msan"])]
    else:
        raise ValueError(arm)
    runs = []
    for exe, cmd in variants:
        b = sh(cmd, cwd=vdir)
        if b.returncode != 0:
            return dict(arm=arm, valid=False, build_error=b.stderr[-300:], wall_s=time.perf_counter() - t0)
        fails, tool_err, outs = [], False, {}
        for t in tests:
            of = vdir / f"{exe}_{t['name']}.out"
            run = [f"./{exe}", str(stages.VEC / f"{t['name']}.txt"), str(of)]
            if arm == "host_valgrind":
                run = ["valgrind", "-q", "--error-exitcode=99", "--track-origins=no"] + run
            try:
                r = sh(run, cwd=vdir, timeout=600)
            except subprocess.TimeoutExpired:
                fails.append(f"{t['name']}: timeout")
                continue
            if arm == "host_valgrind" and r.returncode == 99:
                tool_err = True
            if arm == "host_msan" and "MemorySanitizer" in r.stderr:
                tool_err = True
            out = stages._read_out(of)[0] if of.exists() else _conv(np.zeros((0, 1)))
            outs[t["name"]] = out
            fails += oracle(t, out, refs[t["name"]])
        runs.append(dict(variant=exe, passed=not fails, fails=fails[:4], tool_error=tool_err,
                         digest=_digest(outs)))
    rep.update(runs=runs, wall_s=time.perf_counter() - t0,
               detect_oracle=any(not r["passed"] for r in runs),
               detect_tool=any(r["tool_error"] for r in runs),
               differential=len({r["digest"] for r in runs}) > 1)
    rep["detected"] = rep["detect_oracle"] or rep["detect_tool"] or rep["differential"]
    return rep


def _digest(outs):
    h = zlib.crc32(b"")
    for k in sorted(outs):
        v = outs[k]
        arrs = [v] if isinstance(v, np.ndarray) else [v[f] for f in sorted(v)]
        for a in arrs:
            h = zlib.crc32(np.asarray(a, dtype=np.float32).tobytes(), h)
    return h


# ---------------------------------------------------------------- target arms
def build_fw(vdir, passes):
    r = sh(["bash", str(E5 / "fw" / "build_fw.sh"), str(vdir), NAME, str(VECDIR), "iotnode", str(passes)])
    return r.returncode == 0, r.stderr[-400:]


def parse_stream(text, names):
    k = len(S["fields"]) if S["fields"] else 1
    passes, cur_p, cur, vals = {}, None, None, []
    for raw in text.splitlines():
        line = raw.strip()
        if line.startswith("@P "):
            cur_p = int(line.split()[1])
            passes[cur_p] = {}
        elif line.startswith("@T ") and cur_p is not None:
            _, idx, n = line.split()
            cur, vals, n_exp = int(idx), [], int(n)
        elif line.startswith("@S ") and cur is not None:
            parts = line.split()
            if len(parts) == 5:
                _, idx, crc, st, dw = parts
                words = [w for row in vals for w in row]
                data = b"".join(struct.pack("<I", w) for w in words)
                ok = int(idx) == cur and len(vals) == n_exp and (zlib.crc32(data) & 0xFFFFFFFF) == int(crc, 16)
                rows = np.array([[struct.unpack("<f", struct.pack("<I", w))[0] for w in row] for row in vals],
                                dtype=np.float64).reshape(-1, k)
                passes[cur_p][names[cur]] = dict(rows=rows, crc_ok=ok, st_max=int(st), dw_max=int(dw),
                                                 raw=data)
            cur = None
        elif cur is not None:
            parts = line.split()
            if len(parts) == k and all(len(p) == 8 for p in parts):
                try:
                    vals.append([int(p, 16) for p in parts])
                except ValueError:
                    pass
    return passes


def run_qemu(vdir, timeout=180):
    out = vdir / "qemu.txt"
    out.unlink(missing_ok=True)
    t0 = time.perf_counter()
    p = subprocess.Popen(["qemu-system-arm", "-M", "b-l475e-iot01a", "-nographic", "-monitor", "none",
                          "-icount", "shift=6", "-serial", f"file:{out}", "-kernel", str(vdir / "e5_iotnode.elf")],
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    ok = False
    while time.perf_counter() - t0 < timeout and p.poll() is None:
        time.sleep(0.2)
        if out.exists():
            with open(out, "rb") as f:
                f.seek(max(0, out.stat().st_size - 64))
                if b"@END" in f.read():
                    ok = True
                    break
    p.kill()
    p.wait()
    return [dict(text=out.read_text(errors="replace") if out.exists() else "", ok=ok,
                 seconds_run=time.perf_counter() - t0)]


def run_board(vdir, captures):
    sess = json.loads(SESSION.read_text())
    t0 = time.time()
    ok, log = pil_iotlab.flash(sess["exp"], sess["node"], vdir / "e5_iotnode.elf")
    if not ok:
        return [dict(text="", ok=False, error="flash: " + log[-200:])]
    tf = time.time() - t0
    caps = []
    for c in range(captures):
        f = vdir / f"board_{c}.txt"
        rep = pil_iotlab.capture(sess["exp"], sess["node"], f, run_timeout=240)
        caps.append(dict(text=f.read_text(errors="replace") if f.exists() else "", ok=rep.get("ok", False),
                         seconds_run=rep.get("seconds_run"), seconds_flash=tf if c == 0 else 0.0,
                         stale_nc=rep.get("stale_nc_after", "")))
    return caps


def target_arm(arm, vdir, tests, refs, names, passes, captures, budget):
    t0 = time.perf_counter()
    ok, err = build_fw(vdir, passes)
    if not ok:
        return dict(arm=arm, valid=False, build_error=err, wall_s=time.perf_counter() - t0)
    caps = run_qemu(vdir) if arm == "qemu" else run_board(vdir, captures)
    rep = dict(arm=arm, valid=True, captures=[])
    digests_paint, digests_all = set(), set()
    for ci, c in enumerate(caps):
        ps = parse_stream(c["text"], names) if c["ok"] else {}
        if sorted(ps) != list(range(passes)) or any(n not in ps[k] or not ps[k][n]["crc_ok"]
                                                     for k in ps for n in names):
            rep["valid"] = False
            rep["captures"].append(dict(ok=False, error=c.get("error", "stream incomplete or CRC")))
            continue
        cap = dict(ok=True, seconds_run=c.get("seconds_run"), seconds_flash=c.get("seconds_flash"), passes=[])
        for k in range(passes):
            fails, st, dw = [], 0, 0
            for t in tests:
                v = ps[k][t["name"]]
                fails += oracle(t, _conv(v["rows"]), refs[t["name"]])
                st, dw = max(st, v["st_max"]), max(dw, v["dw_max"])
                if budget is not None and v["st_max"] > budget:
                    fails.append(f"{t['name']}: timing max {v['st_max']} > {budget}")
            d = zlib.crc32(b"".join(ps[k][n]["raw"] for n in names))
            digests_all.add(d)
            if k > 0:
                digests_paint.add(d)
            cap["passes"].append(dict(k=k, passed=not fails, fails=fails[:4], st_max=st, dw_max=dw))
        rep["captures"].append(cap)
    good = [c for c in rep["captures"] if c.get("ok")]
    rep["wall_s"] = time.perf_counter() - t0
    if good:
        rep["detect_p0"] = any(not c["passes"][0]["passed"] for c in good)
        rep["detect_paint"] = any(not p["passed"] for c in good for p in c["passes"][1:])
        rep["differential_paint"] = len(digests_paint) > 1
        rep["differential_any"] = len(digests_all) > 1
        rep["detected"] = rep["detect_p0"] or rep["detect_paint"] or rep["differential_any"]
        rep["st_max"] = max(p["st_max"] for c in good for p in c["passes"])
        rep["dw_max"] = max(p["dw_max"] for c in good for p in c["passes"])
    return rep


# ---------------------------------------------------------------- modes
def calibrate(board):
    tests, refs, names = tests_and_refs()
    c_text = (BASE / f"{S['src']}.c").read_text()
    vdir = prepare("baseline", c_text)
    cal = dict(subject=NAME, host={}, qemu=[], board=[])
    for arm in HOST_ARMS:
        cal["host"][arm] = [host_arm(arm, vdir, tests, refs) for _ in range(3)]
    cal["qemu"] = [target_arm("qemu", vdir, tests, refs, names, 5, 1, None) for _ in range(3)]
    if board:
        cal["board"] = [target_arm("board", vdir, tests, refs, names, 5, 1, None) for _ in range(3)]
    clean = {arm: all(r["valid"] and not r["detected"] for r in reps) for arm, reps in cal["host"].items()}
    for arm in ("qemu", "board"):
        if cal[arm]:
            clean[arm] = all(r["valid"] and not r["detected"] for r in cal[arm])
    cal["clean"] = clean
    cal["excluded_arms"] = [a for a, ok in clean.items() if not ok]
    for arm in ("qemu", "board"):
        if cal[arm] and clean[arm]:
            cal[f"{arm}_baseline_st_max"] = max(r["st_max"] for r in cal[arm])
            cal[f"{arm}_budget"] = 2 * cal[f"{arm}_baseline_st_max"]
    if cal["board"] and clean.get("board"):
        cal["board_baseline_dw_max"] = max(r["dw_max"] for r in cal["board"])
    CALP.write_text(json.dumps(cal, indent=1, default=str))
    print(json.dumps({k: v for k, v in cal.items() if k not in ("host", "qemu", "board")}, indent=1))


def mutants(family):
    if family in ("init", "ladder"):
        d = json.loads((E5 / "protocol" / f"e5_mutants_{NAME}.json").read_text())
        fams = ("INIT", "LUD") if family == "init" else ("ALU", "DIV")
        return [(m["id"], m["family"], m["c"], m.get("seen", False)) for m in d["mutants"] if m["family"] in fams]
    ctl = json.loads((E5 / "protocol" / f"e5_control_{NAME}.json").read_text())
    return [(m["id"], "CONTROL", (WORK / "build" / "mut" / m["id"] / f"{S['src']}.c").read_text(), False)
            for m in ctl["mutants"]]


def run(family, arms):
    tests, refs, names = tests_and_refs()
    cal = json.loads(CALP.read_text())
    done = set()
    if RES.exists():
        done = {(json.loads(l)["id"], json.loads(l)["arm"]) for l in RES.read_text().splitlines() if l.strip()}
    passes, captures = (5, 2) if family == "init" else (1, 1)
    for mid, fam, c_text, seen in mutants(family):
        if ONLY and mid not in ONLY:
            continue
        todo = [a for a in arms if (mid, a) not in done and a not in cal["excluded_arms"]]
        if not todo:
            continue
        vdir = prepare(mid, c_text)
        for arm in todo:
            if arm in HOST_ARMS:
                rep = host_arm(arm, vdir, tests, refs)
            else:
                rep = target_arm(arm, vdir, tests, refs, names, passes, captures, cal.get(f"{arm}_budget"))
                if arm == "board" and not rep["valid"]:  # one retry on a broken stream (E1 lesson)
                    rep = target_arm(arm, vdir, tests, refs, names, passes, captures, cal.get(f"{arm}_budget"))
            rep.update(id=mid, family=fam, seen=seen, subject=NAME)
            with RES.open("a") as f:
                f.write(json.dumps(rep, default=str) + "\n")
            print(mid, arm, rep.get("valid"), rep.get("detected"), round(rep.get("wall_s", 0), 1), flush=True)


if __name__ == "__main__":
    mode = sys.argv[2]
    if mode == "calibrate":
        calibrate("--board" in sys.argv)
    elif mode == "run":
        run(sys.argv[3], sys.argv[4].split(","))
    else:
        raise SystemExit(__doc__)
