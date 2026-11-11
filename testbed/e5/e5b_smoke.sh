#!/usr/bin/env bash
# Run the E5b smoke test for every subject and variant (no board).
cd "$(dirname "$0")"
PY=/root/venvs/cicd/bin/python
for s in soc fuel bess; do
  for v in O0 Os nrf; do
    echo "== $s $v"; $PY e5b_smoke.py "$s" "$v" 2>&1 | tail -3
  done
done
arm-none-eabi-size ~/cicd-work/e5b/nrf/host/smoke_baseline/e5_nrf52840.elf 2>/dev/null || true
