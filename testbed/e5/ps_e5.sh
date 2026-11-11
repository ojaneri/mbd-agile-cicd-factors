#!/usr/bin/env bash
# List running E5 runner processes (pid and arguments).
ps -eo pid,args | grep 'run_e5.py' | grep -v grep
