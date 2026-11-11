# E5 — Platform sensitivity and the tiered pipeline (RQ3, confirmatory)

Status: **planned, not run.** Freeze this design, the new mutants and the analysis script in a commit
before any run. Tests [[claims/c4-platform-tiering]], which is exploratory until this runs.

## Why
The host/emulator/board disagreements came from data already seen. E5 repeats the question on data
that did not shape the hypothesis, and tests whether a cheap check can replace the board.

## Setup
- **Subject 3 (new, unseen):** candidate BESS field data (Zenodo 10.5281/zenodo.20094787, CC BY 4.0) or
  Itabira OBD-II (CC0); pick before any look at its results (t-0045).
- **Mutants, new and frozen:** every state-initialisation deletion, in all three subjects; a control
  sample of non-initialisation mutants from subject 3; graded timing regressions added to the step
  function (+10, +25, +50, +100 % of baseline cycles).
- **Platforms:** host SIL; host SIL under Valgrind memcheck; QEMU with RAM filled at start with
  0x00, 0xFF, 0xAA and random seeds; real board with the same fills, and with no fill across repeated resets.

## Hypotheses (decide the direction before running)
- H1: the non-initialisation mutants of subject 3 agree between QEMU and board; Wilson 95 % lower bound ≥ 95 %.
- H2: QEMU with RAM-pattern fill detects every initialisation mutant that the board detects under any fill.
- H3: Valgrind at SIL detects every initialisation mutant, at a cost below the QEMU PIL stage.
- H4: QEMU ticks and board cycles agree on which graded regressions exceed the budget. Report the smallest
  regression where they differ; this is the condition under which the board is needed.

## Tiered pipeline (the "Integrated Pipeline" of the title)
Configuration A_T: UNIT + MIL + SIL (with H3's check if it holds) + QEMU PIL on every commit; board PIL
per sprint. Compared in the E2 replay with A2 and A3, on detection, latency and compute. Must be added to
`e2.py` and frozen before the run on subject 3.

## Metrics
Agreement rate (Wilson 95 %); per-fill detection of initialisation mutants; cost per stage and platform;
A_T vs A3 compute and escapes.

## Threats
One MCU family and one emulator; initial RAM contents depend on the board and on the power history
(report resets vs cold boots); mutants as proxies, as in E1.

## Todos
- **[#t-0044]** status: open · author: osvaldo — Write the E5 generator of initialisation-deletion and graded-timing mutants and the RAM-fill startup; commit before any run.
- **[#t-0045]** status: open · author: osvaldo — Choose subject 3 and check its licence at the source.
- **[#t-0046]** status: open · author: osvaldo — Check whether a NUCLEO-L476RG run can be added as a second real board (see t-0038).
