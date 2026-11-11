#!/usr/bin/env bash
# Wait until run_board_main.sh has finished, then run subject 3's control mutants on the board.
cd "$(dirname "$0")"
while [ "$(ps -eo args | grep -c '[r]un_board_main.sh')" -gt 0 ]; do sleep 20; done
/root/venvs/cicd/bin/python run_e5.py bess run control board
date -u +%H:%M
