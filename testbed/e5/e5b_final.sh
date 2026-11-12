#!/usr/bin/env bash
# Close E5b: stop the st-iotnode reservation, run the frozen analysis, print the compact view and invalid counts.
cd "$(dirname "$0")"
PY=/root/venvs/cicd/bin/python
tail -4 /root/e5b_resume.log
$PY e5b_open.py stop iotnode
$PY analyze_e5b.py > /dev/null
$PY e5b_view.py
echo "invalid records per file:"
grep -c '"valid": false' results/e5b/*.jsonl
wc -l results/e5b/*.jsonl | tail -1
