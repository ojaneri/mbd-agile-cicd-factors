#!/usr/bin/env bash
# Build the subject-3 baseline firmware for both boards and run the st-iotnode build in QEMU
# b-l475e-iot01a; compare the stream with the SIL outputs of the baseline.
set -euo pipefail
cd "$(dirname "$0")"
PY=/root/venvs/cicd/bin/python
B=/root/cicd-work/bess/build/baseline
$PY gen_vectors.py /root/cicd-work/bess/stm32vec
bash harness/stm32l4/build.sh "$B" iotnode 115200
bash harness/stm32l4/build.sh "$B" nucleo 115200
rm -f "$B/l475.txt"
timeout 60 qemu-system-arm -M b-l475e-iot01a -nographic -monitor none -serial file:"$B/l475.txt" -kernel "$B/fw_iotnode.elf" > /dev/null 2>&1 || true
$PY - <<'PYEOF'
import json, numpy as np, stages, pil_stream
B = stages.WORK / "build" / "baseline"
names = json.load(open(stages.WORK / "stm32vec" / "vectors.json"))
res = pil_stream.parse((B / "l475.txt").read_text(errors="replace"), names)
for n in names:
    r = res.get(n)
    s, _ = stages._read_out(B / f"sil_{n}.out")
    if r is None:
        print(n, "MISSING"); continue
    d = max(float(np.max(np.abs(r[g] - s[g]))) for g in stages.SIG) if len(s["te"]) == len(r["te"]) else None
    print(n, "crc_ok", r["crc_ok"], "n", len(r["te"]), "max|PIL-SIL|", d, "maxcyc", r["max_cycles"])
PYEOF
