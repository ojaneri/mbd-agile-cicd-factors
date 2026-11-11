#!/usr/bin/env bash
# E5 board arm, INIT/LUD then ladders, for the three subjects (one IoT-LAB reservation). Resumable.
cd "$(dirname "$0")"
PY=/root/venvs/cicd/bin/python
for S in soc fuel bess; do
  $PY run_e5.py $S run init board
  $PY run_e5.py $S run ladder board
done
date -u +%H:%M
