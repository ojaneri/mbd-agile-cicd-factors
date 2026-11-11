# C4 — An emulator can carry per-commit PIL; the real board is needed only for memory state and exact timing

Statement (new, d-0011, proposed): for generated control code on a Cortex-M target, emulated PIL gives
the same verdict as real-board PIL except for defects that depend on the initial memory state, so a
tiered pipeline (host and emulator per commit, real board at a slower cadence) keeps the detection at
a fraction of the cost.

Status: **exploratory.** Found after E1 on data already seen. It needs E5 (new mutants, new subject)
before the paper may present it as confirmed: [[experiments/e5-platform-sensitivity]].

Evidence today (2026-11-11, `testbed/*/results/e1_pil_iotnode_vs_qemu.json`; 205 live mutants, 2 subjects,
QEMU vs FIT IoT-LAB st-iotnode STM32L475VG, all 205 board runs valid and CRC-checked, no retries):
- Verdicts agree on 202/205 (98.5 %, Wilson 95 % CI 95.8–99.5 %).
- All 3 disagreements are among the 6 mutants that delete a state initialisation (3/6, against 0/199
  for the other mutants; Fisher exact p = 1.4e-5, post-hoc).
- They go both ways: SDL-006 (subject 1) and SDL-001 (subject 2) fail only on the board, SDL-007
  (subject 1) only on QEMU. SDL-006 is flagged by no other stage.
- The timing-only mutants coincide between QEMU tick counts and board DWT cycles: 5/5 and 6/6. These
  mutants have large effects (up to 883 and 978 cycles against budgets of 214 and 246), so this says
  nothing yet about small regressions.
- Cost per PIL run: QEMU 0.79 s / 1.01 s; board 53.5 s / 18.5 s, i.e. about 68× and 18×.

Would falsify it: non-initialisation mutants disagreeing between emulator and board on new data, or
small timing regressions invisible to the emulator being common enough to need the board per commit.

Caveats: one board family (one core, 16 MHz, zero wait states, no cache effects), one emulator; the
tiered pipeline itself has not been run or costed yet.

Used in: [[sections/abstract]]. Source: [[experiments/e1-defect-detection-by-stage]].
