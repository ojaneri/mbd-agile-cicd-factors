#!/usr/bin/env bash
# E5 host and QEMU arms (sequential, so wall times are comparable). Resumable.
cd "$(dirname "$0")"
PY=/root/venvs/cicd/bin/python
ARMS=host_sil,host_poison,host_valgrind,host_msan,qemu
for S in soc fuel bess; do
  $PY run_e5.py $S run init $ARMS
  $PY run_e5.py $S run ladder $ARMS
done
$PY run_e5.py bess run control qemu
date -u +%H:%M
