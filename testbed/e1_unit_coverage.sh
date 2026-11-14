#!/usr/bin/env bash
# Descriptive (virtual review r1, VR-K-03): gcov line and branch coverage of the E1 hand-written unit suites
# (harness/unit.c) on the baseline generated C. Run in WSL; baselines are the E1 build directories.
T=/mnt/d/artigos/CICD/testbed
run() {  # subject  source-stem  baseline-dir
  d=$(mktemp -d); cp "$3"/*.c "$3"/*.h "$d"/; cd "$d" || exit 1
  gcc -O0 --coverage -std=c11 -I. -c "$2.c"
  gcc -O0 -std=c11 -I. -c "$T/$1/harness/unit.c"
  gcc --coverage unit.o "$2.o" -lm -o unit
  ./unit > /dev/null; echo "== $1 unit exit=$?"
  gcov -b -c "$2.c" | head -6
  echo "functions in $2.c:"; gcov -f "$2.c" | grep -E "^Function|Lines executed" | paste - - | sed "s/Lines executed://"
}
run soc soc_obs /root/cicd-work/build/baseline
run fuel fuel /root/cicd-work/fuel/build/baseline
