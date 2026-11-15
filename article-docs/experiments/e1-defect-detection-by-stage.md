# E1 — Which stage catches which defect (MBD axis, RQ1)

Status: **both subjects complete on QEMU and on the real board (IoT-LAB st-iotnode)**, 2026-11-11. NUCLEO-L476RG not run.
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
by-construction part is that MIL cannot see code-level mutants. Back-to-back was expected not to see
model-level ones, but it caught one in S1 (MS-s_corr, saturation: max diff 2.4e-4 on T1 above the 1e-5
tolerance; corrected 2026-11-14, VR5-M-01, e1_decompose.json soc model b2b = 1). 21 non-field-relevant mutants were still flagged (requirements stricter than the
field oracle); 41 were flagged by nothing (equivalent or benign; list in the analysis file).

**Exploratory (post-hoc, not pre-registered):** SIL alone, running the requirement tests on the
generated code, detects all 68 (MIL alone: 26) at ~1/8 of MIL's cost here; MIL's contribution in an
automated-codegen pipeline is earlier feedback before code exists, not extra detection. PIL's unique
value on this subject: timing regressions (5) and one uninitialised-state defect (SDL-007, visible only
as PIL-vs-SIL back-to-back, because host and target leave different garbage in `rest_ms`).
Observation: halving or doubling Q (MP-Q) is not field-relevant — the high observer gain masks it.

Caveats: one subject; PIL functional verdicts from QEMU (real-target re-run on IoT-LAB st-iotnode in
progress, exp 458317); thresholds are our design requirements.

## Results — subject 2 (fuel-flow sensor), PIL on QEMU (`testbed/fuel/results/e1_qemu*`)
Frozen in commit d7f8239 (built by a parallel agent, reviewed before freeze). Physics model:
k_cal·MAF·60/(AFR·rho)·(1+trim), DFCO, dt-clamped integrator; k_cal 1.018 identified on tanks 8–17
(train mean |error| 7.63 % per tank); field oracle = held-out tanks 18–22, fail if any tank's error
worsens by > 2 pp vs baseline (baseline −2.97, +1.14, −3.80, +10.70, −1.84 %). 75 mutants, 34 field-relevant.

| Config | Detected / 34 | Wilson 95 % CI |
|---|---|---|
| A0 UNIT | 23 (68 %) | 51–81 % |
| A1 +MIL | 34 (100 %) | 90–100 % |
| A2 +SIL | 34 (100 %) | 90–100 % |
| A3 +PIL | 34 (100 %) | 90–100 % |

McNemar A0→A1 +11 (p = 0.001); later steps +0. Model mutants first caught at MIL; all field-relevant
code mutants already at UNIT. No escapes. Timing-only (PIL): FPP-001/002/003/004/010/011.
Deviation: the field oracle runs on the QEMU build (held-out tanks ~4.6 MB exceed 1 MB flash).

Cross-subject pattern (both subjects, QEMU PIL): stages up to SIL raise detection significantly; no
stage is unique for functional field defects; PIL is the only stage that sees timing regressions
(5 and 6 mutants) and, in subject 1, an uninitialised-state defect.

## Real target (FIT IoT-LAB st-iotnode-1, exp 458317, STM32L475VG @ 16 MHz)
Baseline calibration, 3 reps, all pass: max 107 DWT cycles per step (6.7 µs), budget 214 cycles;
per run: build 0.5 s, flash 18 s, serial capture 35 s (115200 baud, 44,636 rows, CRC-checked); queue
wait at submission 1 s. Field RMSE identical to QEMU.

### Subject 1 on the real target — complete (2026-11-11, 01:10–03:33 UTC; `testbed/soc/results/e1_pil_iotnode*.json*`)
All 130 live mutants ran, 130 valid streams (CRC-checked, no retry needed), comparison by `compare_pil.py`.
- PIL verdicts agree with QEMU on 128/130. Field verdicts agree on 130/130.
- Configurations with the real PIL column: A0 26/68, A1 52/68, A2 68/68, A3_real 68/68
  (Wilson 95–100 %); A2→A3_real +0 (McNemar p = 1). The QEMU table above stands.
- Timing-only on the real board: the same five (FPP-003/004/005/007/009); max DWT cycles over all
  mutants 64–883 against a 214-cycle budget.
- **The two disagreements are both uninitialised-state mutants, and they swap:** SDL-006 is caught
  only on the real board (back-to-back and T2 fail), SDL-007 only on QEMU. Which garbage the target
  leaves in uninitialised state depends on the platform, so PIL detection of this class is
  **platform-dependent, not a property of the stage**. Paper must say this (do not claim "PIL catches
  uninitialised state" without the qualifier). Neither is field-relevant under the functional oracle.

### Subject 2 on the real target — complete (2026-11-11, 03:38–04:16 UTC; `testbed/fuel/results/e1_pil_iotnode*.json*`)
All 75 live mutants ran, 75 valid streams, no retry. Budget 246 cycles (baseline max 123); run about 18.5 s.
- PIL verdicts agree with QEMU on 74/75; A0 23/34, A1–A3_real 34/34; A2→A3_real +0.
- Timing-only on the board: FPP-001/002/003/004/010/011, the same six as QEMU.
- The disagreement is SDL-001 (`fuel_init` no longer zeroes `vol`): on QEMU passes, on the board fails
  with a volume error up to about 4700–5258 (UNIT also flags it).
- **Threat:** subject 2's field oracle runs on QEMU only (deviation above), so SDL-001 is counted as not
  field-relevant although the board shows a large error. Field relevance is platform-dependent for this class.

Pooled across subjects: 202/205 agreement; all 3 disagreements are initialisation deletions. See
[[claims/c4-platform-tiering]].

## Equivalent-mutant screening (exploratory, added 2026-11-11 after the runs)
The protocol (e0, rule 4) says equivalent mutants are screened and reported; that screening was not done
before the runs. Done afterwards, so it is **exploratory**. Scope: the mutants flagged by no stage and not
field-relevant in the QEMU analysis (`non_field_relevant.unflagged`): 41 in subject 1, 15 in subject 2.
Method: SIL build (host gcc -O2), output text `%.9g` (exact for float32) compared with the baseline on
REQ vectors, all field data (identification + held-out, unperturbed) and a seeded stress set (seed
20261111: random/edge/long-rest/saturation/out-of-range traces, perturbed field data; values written
float32-exact so boundary inputs reach the C). Model mutants: the C that gen.py generates from the mutant
spec; MIL not re-simulated. Code: `testbed/{soc,fuel}/screen_equiv.py`; results with seed and input-set
definitions (sha256 per vector) in `testbed/{soc,fuel}/results/equiv_screen.json`.

| Subject | Screened | EQUIVALENT | NON-EQUIVALENT BENIGN | of these, differ only on stress | break a requirement on stress |
|---|---|---|---|---|---|
| 1 SoC | 41 | 18 | 23 | 5 | 4 |
| 2 fuel | 15 | 11 | 4 | 3 | 3 |

- Subject 1 EQUIVALENT: AOR-023 (`*`→`/` by DT_INT_S = 1), FPP-001/002/006/008/010–013, ROR-001/003/015/017,
  SDL-001, SDL-006, TW-001/002/003. **SDL-006 is not a real equivalent**: it deletes the init of `v1`
  (an uninitialised read). It matches on the host by chance, and the real-board PIL flags it (see above).
- Subject 2 EQUIVALENT: AOR-013 (`*`→`/` by DT_SCALE = 1), FPP-005–009, ROR-001/003/009/013/015.
  ROR-011 differs only in the sign of zero in `rate` (−0 vs +0; numerically identical). It is counted
  as non-equivalent because the rule is bit-identity.
- Requirement breaks on stress (counted only where the baseline passes the same check on the same trace):
  subject 1 MS-s_cc (tracking, 5 random traces, up to 0.013 over the 0.03 tolerance), MK-2-+ (tracking,
  3 traces, up to 0.005 over), MK-1-+ and MK-1-- (rest correction at low SoC, 1 trace, up to 0.005/0.002
  over 0.01). Subject 2: MP-rate_max-x0.5 (REQ-2 whenever the rate is above 200 ml/min, 28 traces including
  perturbed real tanks; the frozen REQ vectors never exceed 200 ml/min outside T7), and ROR-005 and ROR-007
  (DFCO boundary THR = 21.0 / RPM = 1600 exactly: REQ-2, and ROR-005 also REQ-3). Those last two only
  fire on exact boundary inputs. So the requirement tests are weak for these 7 mutants.
- The baseline itself fails the stress tracking check on 4 of 10 random 20 A traces (subject 1), so the
  stress tracking windows are not requirements. The stress windows were set after the runs; the tolerances
  are the REQ ones.
- Limits: equivalence is on the host build only. The target (Cortex-M4) can differ, as SDL-006 shows and as
  the FPP timing-only mutants show. Inputs with NaN/Inf were not fed.

## Detection by test suite (exploratory, added 2026-11-13 after virtual review r1)
`testbed/e1_decompose.py` re-reads the frozen records (no new run). Field-relevant mutants caught, S1 (n=68) /
S2 (n=34): unit suite on host 26 / 23; requirement tests on the model (MIL) 26 / 11 (all model-level, no
code-level); requirement tests on host C (SIL, without back-to-back) 68 / 34; back-to-back host vs model 43 /
23; requirement tests on the board 68 / 34. The unit suite catches 0 model-level mutants by construction: its
expected values are generated from the mutated spec. Unit-suite size 4 test groups / 5 check call sites (S1), 3 / 3 (S2) (corrected 2026-11-13, VR2-X-01: the
earlier 6 / 4 counted the check() definition); gcov line coverage
97.4 % / 100 %, branches taken 83.3 % / 100 % (`testbed/e1_unit_coverage.sh`). Factor A therefore confounds
stage with suite; the gain is the requirement suite's.
Plotted (2026-11-14, d-0022) as the paper's Fig. 2 by `manuscript/figs/fig_suite.py` from
`testbed/e1_decompose.json`, split by model-/code-level; the McNemar p values left Table I and remain here.

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
- **[#t-0018]** status: done · author: osvaldo — Closed 2026-11-15 as done: S2 modelled and run in E1. Original: Subject 1 done (native MIL instead of FMU, d-0009). Subject 2 (fuel-flow sensor) still to model.
- **[#t-0041]** status: done · author: osvaldo — Closed 2026-11-15 as done for the IoT-LAB st-iotnode (E1 real-board PIL); NUCLEO not used. Original: Real-target PIL harness for NUCLEO-L476RG (register-level startup, UART, DWT cycles) and IoT-LAB st-iotnode; rerun the PIL column of E1 on it.
