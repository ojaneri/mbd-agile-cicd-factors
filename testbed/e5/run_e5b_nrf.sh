#!/usr/bin/env bash
# E5b on the nRF52840-DK: calibration x10 per subject, then INIT/LUD, ladders, and subject 3's controls.
cd "$(dirname "$0")"
PY=/root/venvs/cicd/bin/python
for s in soc fuel bess; do $PY e5b.py $s nrf calibrate; done
for s in soc fuel bess; do $PY e5b.py $s nrf run init board; done
for s in soc fuel bess; do $PY e5b.py $s nrf run ladder board; done
$PY e5b.py bess nrf run control board
echo E5B_NRF_DONE
