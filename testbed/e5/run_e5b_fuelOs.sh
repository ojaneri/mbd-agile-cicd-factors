#!/usr/bin/env bash
# Deviation (2026-11-12): subject 2 at -Os lost its board arm because one of the 3 calibration captures had a
# broken serial stream (calibrate has no retry). Keep that attempt, recalibrate, run the board arm only.
cd "$(dirname "$0")"
PY=/root/venvs/cicd/bin/python
cp results/e5b/calibration_fuel_Os.json results/e5b/calibration_fuel_Os_attempt1.json
$PY e5b_open.py iotnode 40 /root/cicd-work/e5b/O0/host/smoke_baseline/e5_iotnode.elf
$PY e5b.py fuel Os calibrate
$PY e5b.py fuel Os run init board
$PY e5b_open.py stop iotnode
$PY analyze_e5b.py > /dev/null
$PY e5b_view.py | head -40
echo E5B_FUELOS_DONE
