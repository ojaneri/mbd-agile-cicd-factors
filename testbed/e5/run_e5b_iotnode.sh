#!/usr/bin/env bash
# E5b on the st-iotnode: timing noise (-O2 baseline x10), then -O0 and -Os (calibrate + INIT/LUD, all arms).
cd "$(dirname "$0")"
PY=/root/venvs/cicd/bin/python
for s in soc fuel bess; do $PY e5b.py $s noise noise; done
for v in O0 Os; do
  for s in soc fuel bess; do
    $PY e5b.py $s $v calibrate
    $PY e5b.py $s $v run init host_sil,host_poison,host_valgrind,host_msan,qemu,board
  done
done
echo E5B_IOTNODE_DONE
