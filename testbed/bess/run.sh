#!/usr/bin/env bash
# Run a python script of this subject inside WSL with the project venv: run.sh <script.py> [args]
cd "$(dirname "$0")" && exec /root/venvs/cicd/bin/python "$@"
