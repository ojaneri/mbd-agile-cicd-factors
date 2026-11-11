# E5 — Platform sensitivity and the tiered pipeline (RQ3, confirmatory)

Status: **built and frozen 2026-11-11; not run.** 75 E5 mutants + subject 3's control set (after its E1 run). Design, mutants and analysis are frozen in the commit
that adds `testbed/e5/` and `testbed/bess/` (protocol: `testbed/e5/protocol/README.md`, normative rules in
`testbed/e5/analyze_e5.py`). Tests [[claims/c4-platform-tiering]], which is exploratory until this runs.

## Why
The host/emulator/board disagreements in E1 came from data already seen, and E1's QEMU run used a different
harness (mps2-an386, semihosting) than the board, so platform and harness were confounded. E5 repeats the
question on new mutants and an unseen subject with **one ELF for both targets** (QEMU b-l475e-iot01a and the
st-iotnode), and tests whether a host check can replace the board.

## Setup (as built)
- Subjects: SoC observer, fuel-flow sensor, and subject 3 = BESS rack thermal sensor with derating
  (Zenodo 10.5281/zenodo.20094787 temperature data; licence to be checked at the source, t-0045).
- Mutants: INIT (deletion inside `*_init`; subjects 1–2 repeat E1 and are marked seen), LUD (drop a local's
  initialiser; new), ALU/DIV timing ladders (+25…300 % of the board baseline cycles; DIV costs 14 cycles per
  instruction on the M4 but counts as one instruction on QEMU), CONTROL (subject 3's E1 mutants, for H1).
  Counts: subject 1 INIT 4, LUD 9; subject 2 INIT 2, LUD 4; subject 3 INIT 5, LUD 4 (INIT-04 and LUD-02
  marked seen: same lines as SDL-004/SDL-009, run in subject 3's smoke test); ladders 12 per subject.
- Subject 3 as built (`testbed/bess/protocol/README.md`): 1st-order thermal model (tau 201.5 s) plus a
  derating latch; CC BY 4.0 verified at the source 2026-11-11; 93 E1 mutants. **Its thermal model is no
  better than the naive estimate on the held-out months** (field RMSE 0.458 vs 0.449 °C; sensor quantised to
  1 °C): fine as a test subject, must not be presented as a good virtual sensor.
- Arms: host SIL; host SIL with the state poisoned (4 patterns); Valgrind memcheck; MemorySanitizer
  (secondary); QEMU; board. Targets run 5 passes (no paint, then the stack painted with 4 patterns).
- Oracles as E1 (requirements, back-to-back against the baseline SIL, timing budget 2× the platform's baseline),
  plus "the arm's own runs disagree" and tool errors.

## Hypotheses (decision rules frozen in `analyze_e5.py`)
- H1: QEMU and board agree on subject 3's control mutants; Wilson 95 % lower bound ≥ 0.95.
- H2: every INIT/LUD mutant the board detects, QEMU (5 passes) detects. Zero counterexamples.
- H3: Valgrind at SIL detects every INIT/LUD mutant any target detects, at a lower median cost than QEMU.
- H4: QEMU and board flag the same ladder levels; predicted equal for ALU, different for DIV.
- Tiered pipeline AT (host + QEMU per commit, board per sprint) vs A3b (board per commit) in the E2 replay.

## Development notes before the freeze (M10)
- The first stack-paint routine left the 128 bytes below main's SP unpainted, exactly where the state
  frame lives; found on the E1-seen mutant E5-SOC-INIT-02 and fixed with a naked assembly routine.
- Baseline calibration clean on every arm for all three subjects (IoT-LAB exp 458334): board baseline
  107 / 119 / 131 cycles per step (subject 1 equals its E1 DWT figure), QEMU 68 / 64 / 93 ticks; a board run
  with 5 passes takes about 64–75 s.
- Smoke runs before the freeze used only the baseline and E1-seen mutants (E5-SOC-INIT-02/03, E5-FUEL-INIT-01).

## Threats
One MCU family and one emulator; initial RAM contents depend on the board and its power history (passes
and two resets are reported); paint reaches only the first vector of each pass (later vectors reuse the same
frame); mutants as proxies, as in E1.

## Todos
- **[#t-0044]** status: done · author: osvaldo — E5 generator, RAM-paint firmware, host arms, runner and analysis written (`testbed/e5/`).
- **[#t-0045]** status: done · author: osvaldo — Subject 3 built in `testbed/bess/`; licence CC BY 4.0 checked at the Zenodo API on 2026-11-11.
- **[#t-0046]** status: open · author: osvaldo — Check whether a NUCLEO-L476RG run can be added as a second real board (see t-0038).
- **[#t-0047]** status: open · author: osvaldo — Run E5 after the freeze: subject 3 E1 campaign, board calibration of subject 3, then all arms (one IoT-LAB reservation of about 3 h).
