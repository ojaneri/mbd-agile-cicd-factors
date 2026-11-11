#!/usr/bin/env bash
# E5 progress: time, running processes, board record counts, partial analysis (overwritten by the final one).
cd "$(dirname "$0")"
date -u +%H:%M
bash ps_e5.sh
/root/venvs/cicd/bin/python count.py | tr ',' '\n' | grep -A1 board | tr -d '\n'; echo
/root/venvs/cicd/bin/python analyze_e5.py soc fuel bess > /root/cicd-work/e5_partial.txt 2>&1
/root/venvs/cicd/bin/python - <<'EOF'
import json
a = json.load(open("results/e5_analysis.json"))
print("sets", a["sets"]["F"], a["sets"]["U"], a["sets"]["U_unseen"], "unobserved", a["sets"]["equivalent_or_unobserved"])
for arm, r in a["arms"].items():
    print(arm, r["U"], "unseen", r["U_unseen"]["detected"], "/", r["U_unseen"]["of"], "wall", r["median_wall_s"],
          {k: r[k] for k in ("detect_p0", "detect_paint", "differential_paint", "differential_any", "by_family") if k in r})
print("H1", {k: a["H1"][k] for k in ("n", "agree", "wilson95", "supported")})
print("H2", a["H2"])
for t in ("host_valgrind", "host_msan"):
    print("H3", t, a["H3"][t])
for k, v in a["H4"].items():
    print("H4", k, "ran", v["ran"], "qemu", v["qemu_flags"], "board", v["board_flags"])
EOF
