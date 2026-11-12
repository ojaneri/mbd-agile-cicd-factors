#!/usr/bin/env bash
# t-0048: why Valgrind memcheck missed E5-SOC-LUD-04 (`float lo;` in soc_obs_ocv_inv).
# Compiles the mutant's inverse alone at -O0/-O1/-O2, dumps the -O2 assembly and runs memcheck on a
# tiny driver that calls soc_obs_ocv_inv, so the result does not depend on the E5 harness.
set -u
D=$(cd "$(dirname "$0")" && pwd)
W=~/cicd-work/diag_lud04; rm -rf "$W"; mkdir -p "$W"; cd "$W"
cp "$D/lud04.c" .
cp ~/cicd-work/e5/host/E5-SOC-LUD-04/soc_obs.h . 2>/dev/null || cp ~/cicd-work/e5/board/E5-SOC-ALU-03/soc_obs.h .
cat > drv.c <<'EOF'
#include <stdio.h>
#include "soc_obs.h"
int main(void) {
    volatile float v = 3.70f;
    float s = soc_obs_ocv_inv(v);
    printf("inv(3.70)=%.9g\n", s);
    return s > 0.5f ? 0 : 1;   /* control flow depends on the result */
}
EOF
for O in O0 O1 O2; do
  gcc -$O -g -std=c11 -I. drv.c lud04.c -lm -o drv_$O 2> build_$O.err || { echo "build $O failed"; cat build_$O.err; continue; }
  echo "== -$O: run"; ./drv_$O
  echo "== -$O: valgrind"; valgrind --error-exitcode=99 --track-origins=yes -q ./drv_$O > vg_$O.out 2>&1; echo "valgrind exit=$?"; head -12 vg_$O.out
done
echo "== -O2 -Wall warning"; gcc -O2 -Wall -Wmaybe-uninitialized -c -I. lud04.c -o /dev/null 2>&1 | head -5
echo "== -O2 assembly of soc_obs_ocv_inv"
gcc -O2 -S -std=c11 -I. lud04.c -o lud04_O2.s
awk '/^soc_obs_ocv_inv:/,/\.size\tsoc_obs_ocv_inv/' lud04_O2.s | head -60
