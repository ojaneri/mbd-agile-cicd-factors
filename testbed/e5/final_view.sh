#!/usr/bin/env bash
# Print the tiered replay table and the timing-ladder cycle counts on QEMU and the board.
cd "$(dirname "$0")"
PY=/root/venvs/cicd/bin/python
$PY tiersum.py results/e5_bess_tiered.json
for s in soc fuel bess; do
  $PY show.py results/e5_$s.jsonl | grep -E -- '-(ALU|DIV)-' | grep -E ' (qemu|board) ' | sed -E "s/\{'valid'.*'st_max': ([0-9]+).*/st_max=\1/"
done
