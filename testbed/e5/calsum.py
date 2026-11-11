"""Summarise E5 calibration files. Usage: python calsum.py soc fuel bess"""
import json
import pathlib
import sys

E5 = pathlib.Path(__file__).resolve().parent
for s in sys.argv[1:]:
    p = E5 / "protocol" / f"calibration_{s}.json"
    if not p.exists():
        print(s, "missing")
        continue
    c = json.loads(p.read_text())
    print(s, "clean", c["clean"], "excluded", c["excluded_arms"])
    print("   qemu st", c.get("qemu_baseline_st_max"), "board st", c.get("board_baseline_st_max"),
          "budget", c.get("board_budget"), "dwt", c.get("board_baseline_dw_max"),
          "board walls", [round(r.get("wall_s", 0), 1) for r in c["board"]],
          "board valid", [r.get("valid") for r in c["board"]])
