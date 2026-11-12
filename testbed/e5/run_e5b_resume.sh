#!/usr/bin/env bash
# After the st-iotnode campaign ends, resume subject 3 at -O0 (stopped by the truncated-output crash).
cd "$(dirname "$0")"
until grep -q E5B_IOTNODE_DONE /root/e5b_iotnode.log; do sleep 20; done
/root/venvs/cicd/bin/python e5b.py bess O0 run init host_sil,host_poison,host_valgrind,host_msan,qemu,board
echo E5B_RESUME_DONE
