# E5 protocol — platform sensitivity and the tiered pipeline (frozen before any E5 mutant run)

Memory note: `article-docs/experiments/e5-platform-sensitivity.md`. Claim: `article-docs/claims/c4-platform-tiering.md`.

## Why a new experiment
E1 found that emulated and real-board PIL disagreed only on deleted state initialisations (3/6 vs 0/199).
That was found on data already seen. E5 tests it on new mutants and an unseen subject, with the SAME
firmware binary on both platforms (E1 used a different harness on QEMU mps2-an386, which confounds
platform with harness and stack layout — reported as a limitation of the E1 comparison).

## Subjects
1. SoC observer (`testbed/soc`), 2. fuel-flow sensor (`testbed/fuel`), 3. BESS rack thermal sensor with
derating (`testbed/bess`, built after E1 and frozen with this protocol; unseen).

## Mutants (`mutate_e5.py`, files `e5_mutants_<subject>.json`)
- INIT: delete each assignment inside `*_init`. For subjects 1-2 these repeat E1 SDL mutants (`seen=true`).
- LUD: drop the initialiser of each local declaration (new for every subject).
- ALU / DIV ladders: E5_LOAD_ALU(n) / E5_LOAD_DIV(n) at the top of the step function, n = round(f·B) and
  round(f·B/14), f ∈ {0.25, 0.5, 0.9, 1.1, 1.5, 3.0}, B = board baseline max SysTick cycles per step
  (from `calibration_<subject>.json`, measured before any mutant).
- CONTROL (subject 3 only, H1): every live E1 mutant of subject 3 except deletions of assignments inside
  `*_init` and except mutants textually identical to an E5 mutant (`e5_control_bess.json`).

## Arms and oracles (`run_e5.py`)
Oracles, the same on every arm: the subject's frozen requirement checks, back-to-back against the
baseline host SIL outputs with the subject's E1 `tol_pil_sil`, and on targets a timing budget of 2× the
platform's own baseline max SysTick per step. An arm also detects when its runs of the same mutant
disagree with each other (poison patterns, paint passes, board captures), or when its tool reports an error
(Valgrind exit 99, MemorySanitizer report).
host_sil · host_poison (state memset 0x00/0xFF/0xAA/0x55 before init) · host_valgrind (memcheck) ·
host_msan (clang, secondary) · qemu (b-l475e-iot01a, -icount shift=6) · board (FIT IoT-LAB st-iotnode).
Target firmware (`fw/`): one ELF for both targets; INIT/LUD and baseline: 5 passes (0 = no paint;
1–4 = stack below main's SP painted 0x00000000, 0xFFFFFFFF, 0xAAAAAAAA, 0x55555555), board: 2 captures
(2 resets). Ladders and control: 1 pass, 1 capture. A broken board stream is re-run once.
Calibration (`run_e5.py <s> calibrate --board`): baseline 3× per arm; an arm whose baseline is not clean is
excluded (and reported); budgets and B are written then.

## Hypotheses and decision rules (`analyze_e5.py` docstring is normative)
H1 agreement QEMU vs board on subject 3 control mutants (pass 0), supported iff Wilson 95 % lower bound ≥ 0.95.
H2 every observable INIT/LUD mutant the board detects, QEMU detects; supported iff 0 counterexamples
   (primary on the unseen set).
H3 Valgrind detects every observable INIT/LUD mutant any target detects, at a lower median cost than QEMU;
   MSan secondary; poison predicted to catch INIT but not LUD (exploratory).
H4 per subject and ladder, QEMU and board flag the same levels; predicted equal for ALU, different for DIV.
Tiered pipeline (`e2_tiered.py`): A2, A3q, A3b, AT on subject 3; Cliff's delta AT vs A3b and AT vs A3q.

## State at the freeze
Baseline calibration done for all three subjects on every arm (IoT-LAB exp 458334, st-iotnode-1), all clean,
no arm excluded. Board baseline max SysTick cycles per step B = 107 / 119 / 131 (soc / fuel / bess); QEMU
68 / 64 / 93 ticks. Mutants: soc INIT 4, LUD 9; fuel INIT 2, LUD 4; bess INIT 5, LUD 4 (2 marked seen);
ALU 6 and DIV 6 per subject — 75 in all, every one compiles for host and target (compile-only check).

## Order of work
1. Freeze (this commit). 2. Subject 3 E1 campaign (host stages + QEMU, `testbed/bess/e1.py`), then
`make_control.py bess`. 3. E5 runs: host and QEMU arms, then the board arm in one reservation.
4. `analyze_e5.py`, `e2_tiered.py`.
Development checks done before the freeze touched only the baseline and the E1-seen mutants
E5-SOC-INIT-02/03 and E5-FUEL-INIT-01 (smoke files outside the results directory).
