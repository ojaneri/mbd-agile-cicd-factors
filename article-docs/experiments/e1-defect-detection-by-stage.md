# E1 — Which stage catches which defect (MBD axis, RQ1)

Status: **subject 1 frozen and running on the development PIL target (QEMU)**; subject 2 not built.
Shared setup in [[experiments/e0-testbed-and-protocol]]. Supports [[claims/c3-stage-detection]].
Code and frozen protocol: `testbed/soc/` (see `testbed/soc/protocol/README.md`).

## Subject 1 as built (2026-11-11)
- Luenberger-type SoC observer: 1RC + 11-knot piecewise-linear OCV, discrete 1 s, float32 C.
  Identified on LG HG2 25 degC UDDS, LA92, US06, Mixed1-4: OCV fit RMSE 11.2 mV, tau 40 s,
  R0 20.3 mOhm, R1 21.8 mOhm, L 0.1, L_rest 0.167 (`testbed/soc/spec/identification.json`).
- Field oracle: held-out Mixed5-8; baseline target build RMSE 0.75-0.96 % SoC, max 3.2-4.7 %.
- One spec generates the Modelica model (MIL) and the C code (SIL/PIL) — model mutants reach both,
  code mutants reach only the C.
- Requirements REQ-1..7 (range, 1C tracking, pulses, convergence, rest correction, robustness,
  near-empty), thresholds set by us before any mutant (`tests_req.py`).
- Calibration (10 reps, baseline passes every stage): back-to-back tol 1e-5 (SIL-MIL baseline diff
  4.4e-7, PIL-SIL 0); timing budget 2x baseline max; median wall times UNIT 0.29 s, MIL 2.45 s,
  SIL 0.29 s, PIL(QEMU) 0.79 s, field 0.57 s.
- Mutants: 130 = 46 model-level (MP 12, MS 5, MK 22, MSAT 1, MDT 2, MRST 4) + 84 code-level
  (AOR 35, ROR 18, SDL 15, FPP 13, TW 3), exhaustive per operator (`protocol/mutants.json`).

## Deviations from the plan (M10)
- MIL runs as a **native OpenModelica simulation** in a testbench, not an FMU under FMPy: the ME FMU
  did not process `sample()` events with FMPy inputs, and the CS build failed (d-0009).
- OpenModelica 1.27.2 dropped algorithm assignments to a variable alias-eliminated against the output;
  the generator assigns the output inside the `when` (found and fixed before the freeze).
- Requirement test T2 discharged more than the cell capacity in its first draft; fixed before the freeze.
- PIL is first run on **QEMU** (development target): functional verdicts only, ticks are an
  instruction proxy. Real-target PIL (NUCLEO-L476RG, IoT-LAB st-iotnode) replaces it for the paper (d-0010).
- Cost of the PIL stage on QEMU is not representative; E2 must use real-target costs.

## Results — subject 1, PIL on QEMU (development run, 2026-11-11; `results/e1_qemu.jsonl`, `_analysis.json`)
Pre-registered analysis, 130 live mutants (0 stillborn), 68 field-relevant:

| Config | Detected / 68 | Wilson 95 % CI | Median cost per run |
|---|---|---|---|
| A0 UNIT | 26 (38 %) | 28–50 % | 0.29 s |
| A1 +MIL | 52 (76 %) | 65–85 % | 2.74 s |
| A2 +SIL | 68 (100 %) | 95–100 % | 3.02 s |
| A3 +PIL | 68 (100 %) | 95–100 % | 3.81 s (QEMU cost, not representative) |

Exact McNemar: A0→A1 +26 (p = 3.0e-8), A1→A2 +16 (p = 3.1e-5), A2→A3 +0 (p = 1).
First detection: all 26 field-relevant model mutants at MIL; code mutants at UNIT (26) or SIL (16).
No escapes. Timing-only (PIL only, functional field oracle unaffected): FPP-003/004/005/007/009.

M11 audit of the 100 %: every field-relevant code mutant failed a **requirement** test at SIL
(not only back-to-back), so A2's rate is not a by-construction artefact of back-to-back; the
by-construction parts are that MIL cannot see code-level mutants and back-to-back cannot see
model-level ones. 21 non-field-relevant mutants were still flagged (requirements stricter than the
field oracle); 41 were flagged by nothing (equivalent or benign; list in the analysis file).

**Exploratory (post-hoc, not pre-registered):** SIL alone, running the requirement tests on the
generated code, detects all 68 (MIL alone: 26) at ~1/8 of MIL's cost here; MIL's contribution in an
automated-codegen pipeline is earlier feedback before code exists, not extra detection. PIL's unique
value on this subject: timing regressions (5) and one uninitialised-state defect (SDL-007, visible only
as PIL-vs-SIL back-to-back, because host and target leave different garbage in `rest_ms`).
Observation: halving or doubling Q (MP-Q) is not field-relevant — the high observer gain masks it.

Caveats: one subject; PIL functional verdicts from QEMU (real-target re-run on IoT-LAB st-iotnode in
progress, exp 458317); thresholds are our design requirements.

## Real target (FIT IoT-LAB st-iotnode-1, exp 458317, STM32L475VG @ 16 MHz)
Baseline calibration, 3 reps, all pass: max 107 DWT cycles per step (6.7 µs), budget 214 cycles;
per run: build 0.5 s, flash 18 s, serial capture 35 s (115200 baud, 44,636 rows, CRC-checked); queue
wait at submission 1 s. Field RMSE identical to QEMU. Mutant re-run in progress.

## Metrics
- Detection rate per configuration A0..A3 over field-relevant mutants (Wilson 95 % CI), exact McNemar
  between successive configurations, first-detecting stage per operator, stage-unique detections,
  timing-only detections reported apart.

## Decisions
- **[#d-0009]** date: 2026-11-11 · status: proposed · author: osvaldo
  **MIL = native OpenModelica simulation of the generated model in a CombiTimeTable testbench.**
  Why: the FMU route failed (events not processed under FMPy ME; CS build failed). Native simulation is
  also the closer analogue of simulating a Simulink model. Cost: the build must target the longest test
  (stopTime override was ignored at run time).
- **[#d-0010]** date: 2026-11-11 · status: proposed · author: osvaldo
  **Run E1 first with QEMU as the PIL target, then repeat PIL on NUCLEO-L476RG (and st-iotnode).**
  Why: the board is not connected yet; QEMU validates the whole pipeline and gives functional PIL
  verdicts. Only real-target PIL verdicts and costs go into the paper.

## Todos
- **[#t-0016]** status: done · author: osvaldo — Operators and counts fixed in `testbed/soc/mutate.py` and `protocol/mutants.json` (130 mutants).
- **[#t-0017]** status: done · author: osvaldo — Tolerances fixed by rule from the baseline in `protocol/calibration.json` (1e-5 both).
- **[#t-0018]** status: open · author: osvaldo — Subject 1 done (native MIL instead of FMU, d-0009). Subject 2 (fuel-flow sensor) still to model.
- **[#t-0041]** status: open · author: osvaldo — Real-target PIL harness for NUCLEO-L476RG (register-level startup, UART, DWT cycles) and IoT-LAB st-iotnode; rerun the PIL column of E1 on it.
