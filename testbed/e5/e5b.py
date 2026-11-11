"""E5b — robustness addendum to E5 (written and frozen 2026-11-11 BEFORE any E5b run; protocol in
protocol/ADDENDUM-E5b.md, decision rules in analyze_e5b.py). Reuses run_e5.py unchanged, by patching its
module-level settings, so every arm, oracle and stream parser is the frozen E5 code.

Variants:
  O0, Os  same E5 firmware and host arms built with -O0 / -Os instead of -O2; targets QEMU + st-iotnode
  nrf     -O2 firmware on a second, different board: nRF52840-DK on FIT IoT-LAB (Cortex-M4F, 64 MHz, HFXO,
          flash cache off). QEMU has no nRF52 machine, so the nRF board is compared with E5's QEMU records.
  noise   -O2 baseline repeated 10x on the st-iotnode (timing noise of the board oracle)
Usage (WSL venv):
  python e5b.py <subject> <variant> calibrate            O0/Os: host x3, QEMU x3, board x3; nrf: board x10
  python e5b.py <subject> noise noise                    st-iotnode baseline x10 (-O2)
  python e5b.py <subject> <variant> run <init|ladder|control> <arms>
"""
import json
import os
import pathlib
import shutil
import sys

SUBJECT, VARIANT, MODE = sys.argv[1], sys.argv[2], sys.argv[3]
sys.argv = [sys.argv[0], SUBJECT] + sys.argv[3:]          # run_e5 reads the subject from argv[1]
E5 = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(E5))
import run_e5 as R  # noqa: E402

OPT = {"O0": "-O0", "Os": "-Os", "nrf": "-O2", "noise": "-O2"}[VARIANT]
BOARD = "nrf52840" if VARIANT == "nrf" else "iotnode"
OUT = E5 / "results" / "e5b"
OUT.mkdir(parents=True, exist_ok=True)

R.OUTD = R.WORK / "e5b" / VARIANT
R.CALP = OUT / f"calibration_{SUBJECT}_{VARIANT}.json"
R.RES = OUT / f"e5b_{SUBJECT}_{VARIANT}.jsonl"
R.SESSION = OUT / f"session_{BOARD}.json"
if BOARD == "nrf52840":
    R.pil_iotlab.ARCHI = "nrf52840dk"

_sh = R.sh


def sh(cmd, cwd=None, timeout=600, env=None):
    if cmd and cmd[0] in ("gcc", "clang"):
        cmd = [OPT if c == "-O2" else c for c in cmd]
    return _sh(cmd, cwd=cwd, timeout=timeout, env=env)


def build_fw(vdir, passes):
    env = dict(os.environ, E5_OPT=OPT)
    r = _sh(["bash", str(E5 / "fw" / "build_fw.sh"), str(vdir), R.NAME, str(R.VECDIR), BOARD, str(passes)], env=env)
    if r.returncode == 0 and BOARD != "iotnode":
        # run_e5 flashes / emulates "e5_iotnode.elf"; for the nRF build only the file name is reused.
        shutil.copy(vdir / f"e5_{BOARD}.elf", vdir / "e5_iotnode.elf")
    return r.returncode == 0, r.stderr[-400:]


R.sh = sh
R.build_fw = build_fw


def board_baseline(reps, out_path):
    tests, refs, names = R.tests_and_refs()
    vdir = R.prepare("baseline", (R.BASE / f"{R.S['src']}.c").read_text(), "board")
    runs = [R.target_arm("board", vdir, tests, refs, names, 5, 1, None) for _ in range(reps)]
    clean = all(r["valid"] and not r["detected"] for r in runs)
    st = [r.get("st_max") for r in runs]
    dw = [r.get("dw_max") for r in runs]
    cal = dict(subject=SUBJECT, variant=VARIANT, board=BOARD, opt=OPT, reps=reps, runs=runs, host={}, qemu=[],
               clean={"board": clean}, excluded_arms=[] if clean else ["board"],
               board_st_max_reps=st, board_dw_max_reps=dw)
    if clean:
        cal["board_baseline_st_max"] = max(st)
        cal["board_budget"] = 2 * max(st)
        cal["board_baseline_dw_max"] = max(dw)
    out_path.write_text(json.dumps(cal, indent=1, default=str))
    print(json.dumps({k: v for k, v in cal.items() if k not in ("runs",)}, indent=1, default=str))


if __name__ == "__main__":
    if VARIANT == "noise":
        board_baseline(10, OUT / f"noise_{SUBJECT}_iotnode.json")
    elif MODE == "calibrate":
        if VARIANT == "nrf":
            board_baseline(10, R.CALP)
        else:
            R.calibrate(True)
    elif MODE == "run":
        R.run(sys.argv[3], sys.argv[4].split(","))
    else:
        raise SystemExit(__doc__)
