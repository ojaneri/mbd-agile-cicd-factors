# C4 — With the same binary, an emulator gives the board's functional verdicts; the board is needed for cycle-accurate timing

Statement (revised after E5, d-0011, proposed): for generated control code on a Cortex-M4 target, emulated PIL
running the same ELF gives the same functional verdict as the real board, including for uninitialised-state
defects once the stack is painted with several patterns; a host memory sanitiser catches that class at SIL
cost. The board remains necessary for timing, because the emulator counts instructions: it misses regressions
made of multi-cycle instructions and over-flags ones made of single-cycle instructions near the budget.

Status: **confirmatory for the functional part (E5 H1, H2), partly refuted for timing (H4), tool-dependent
for the host check (H3).** Source: [[experiments/e5-platform-sensitivity]]; exploratory origin in
[[experiments/e1-defect-detection-by-stage]].

Evidence:
- E1 (exploratory, different harnesses on QEMU and board): 202/205 agreement; the 3 disagreements were all
  deleted initialisations (3/6 vs 0/199, Fisher p = 1.4e-5, post-hoc).
- E5 H1: unseen subject 3, 84 control mutants, same ELF: 84/84 agreement (Wilson 95.6–100 %).
- E5 H2: 26 observable INIT/LUD mutants (19 unseen): 0 caught by the board and missed by QEMU, 0 the
  other way. The E1 disagreement came from harness/memory layout, not from something only the board sees.
- E5 H3: Valgrind (pre-registered) missed 1/26 and cost more than QEMU — not supported; MemorySanitizer
  (secondary) caught 26/26 at 0.34 s per mutant (board 135 s).
- E5 H4: DIV ladder — board flags it, QEMU never (as predicted); ALU ladder — QEMU flags one level more
  than the board in all subjects (not predicted; CPI explanation is post-hoc).
- Tiered replay (subject 3): host + QEMU per commit and the board once per sprint cost 77 s per sprint
  against 397 s with the board every commit, with 0 escapes in both; no control mutant needed the board.

- E5b (replication addendum, frozen and pushed before running): same functional result at -O0 and -Os and on a
  second board (nRF52840-DK): 84/84 control agreement, 0 counterexamples in both directions; board timing noise
  0 over 10 runs per subject on both boards; the two boards flag different ladder levels, so the timing check
  must run on the production board.

Would falsify it: functional disagreement between emulator and board on further subjects or compilers; a
defect class the board catches that neither painted QEMU nor a sanitiser catches.

Caveats: two Cortex-M4F boards (STM32L4 16 MHz, 0 wait states, flash instruction and data caches on at their
reset value; nRF52840 64 MHz, flash cache off) and one emulator; corrected 2026-11-15 (t-0057): RM0351 gives
FLASH_ACR reset 0x0000 0600 (ICEN, DCEN set, LATENCY 0) and 0 WS valid up to 16 MHz in range 1, and the
harness (testbed/*/harness/stm32l4/board.c) never writes FLASH_ACR, so "both uncached" was wrong; three subjects
of the same kind (estimators); MSan as a secondary arm; the replay pool held no multi-cycle timing defect.

Used in: [[sections/abstract]].
