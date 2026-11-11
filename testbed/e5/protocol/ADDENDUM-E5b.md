# E5b — robustness addendum to E5 (frozen 2026-11-11, before any E5b run)

E5 ran on 2026-11-11 (commit dd254ab). E5b was designed AFTER seeing E5's results, to test whether its
conclusions survive three changes a reviewer would ask for. It is therefore a **replication addendum**, not
part of E5's confirmatory set; its decision rules are fixed here and in `analyze_e5b.py` before any E5b run,
and this file is pushed to the private GitHub remote before the run so the freeze has an external timestamp.

## Changes tested
1. **Optimisation level (R1, R2).** The same E5 firmware, host arms and INIT/LUD mutants (28, all subjects),
   built with `-O0` and with `-Os` instead of `-O2`. Targets: QEMU b-l475e-iot01a and the FIT IoT-LAB
   st-iotnode, same ELF, 5 passes, 2 captures (resets) on the board, as in E5. Each level is calibrated
   (host x3, QEMU x3, board x3) before its mutants. Motivation: uninitialised-state behaviour depends on the
   optimiser; the Valgrind miss in E5 was traced (t-0048) to `-O2` keeping the uninitialised local in a register
   that held a defined zero.
2. **Timing noise of the board oracle (R3).** The `-O2` baseline, 10 runs per subject on the st-iotnode
   (each run: build, flash, reset, 5 passes); the nRF52840 calibration below also has 10 runs.
3. **A second, different real board (R4).** nRF52840-DK on FIT IoT-LAB (Nordic, Cortex-M4F, 64 MHz from the
   crystal, flash cache in its reset state = off), `-O2`, BSP in `fw/nrf52840/`. QEMU has no nRF52 machine, so
   the nRF verdicts are compared with E5's QEMU records (same source and mutants, different ELF). Sets: all
   INIT/LUD mutants (5 passes, 2 captures), subject 3's 84 control mutants (1 pass), all ALU/DIV ladders
   (1 pass; ladder sizes stay those calibrated on the st-iotnode). Budget = 2x the nRF's own baseline maximum.

## Decision rules (normative copy in `analyze_e5b.py`)
- R1: per level, 0 INIT/LUD mutants detected by the board and missed by QEMU.
- R2: exploratory (Valgrind / MemorySanitizer counterexamples and cost per level).
- R3: (max − min) / min of the 10 baseline step maxima ≤ 0.05 for every subject, per board.
- R4 H1n: nRF vs E5 QEMU pass-0 verdict on the 84 control mutants, Wilson 95 % lower bound ≥ 0.95.
- R4 H2n: 0 INIT/LUD mutants detected by the nRF board and missed by E5's QEMU arm.
- R4 H4n: in every subject the nRF board flags at least one DIV level that QEMU does not flag.
  ALU ladder and nRF-vs-st-iotnode flag sets: exploratory.

## Changes to frozen code
- `fw/build_fw.sh`: new board `nrf52840` and env `E5_OPT` (default `-O2`, so E5 builds are unchanged).
- `run_e5.py` unchanged; `e5b.py` patches its module settings (output dirs, calibration and result files,
  optimisation flag, board, IoT-LAB archi). Results go to `results/e5b/`.
- Smoke test before freeze (baseline only, no mutant, no board): `-O0`/`-Os` QEMU baselines valid and clean
  for all subjects (step max 188/77, 183/92, 267/104 ticks), nRF ELFs build for all three subjects.

## Threats specific to E5b
Designed after E5's results; the nRF comparison is with a different ELF; the ladder sizes are those of the
st-iotnode; one reservation per board.
