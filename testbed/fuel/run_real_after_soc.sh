#!/usr/bin/env bash
# Wait until subject 1's IoT-LAB campaign (PID given) releases the node, then run subject 2 on the
# same node and reservation: calibrate the baseline first, then the mutants.
#   run_real_after_soc.sh <pid_of_subject1_campaign>
set -u
while kill -0 "$1" 2>/dev/null; do sleep 30; done
cd /mnt/d/artigos/CICD/testbed/fuel
~/venvs/cicd/bin/python pil_real.py calibrate iotnode && ~/venvs/cicd/bin/python pil_real.py run iotnode
