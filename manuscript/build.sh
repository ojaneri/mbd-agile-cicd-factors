#!/usr/bin/env bash
# Build main.pdf with latexmk (WSL, TeX Live incl. texlive-publishers) and print the warnings that matter.
cd "$(dirname "$0")"
latexmk -pdf -interaction=nonstopmode -halt-on-error main.tex > build.out 2>&1
echo "latexmk exit=$?"
grep -E 'LaTeX Warning|Error|Overfull|Output written|undefined' main.log | head -30
