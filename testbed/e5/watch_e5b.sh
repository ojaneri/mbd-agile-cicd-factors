#!/usr/bin/env bash
# Emit one line per E5b failure (invalid record, traceback) or campaign end (for a session monitor).
tail -n0 -F /root/e5b_iotnode.log /root/e5b_nrf.log /root/e5b_resume.log 2>/dev/null \
  | grep --line-buffered -E 'Traceback|Error|^E5-[A-Z0-9-]+ [a-z_]+ False |E5B_.*DONE'
