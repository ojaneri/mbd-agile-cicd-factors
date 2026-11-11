# Subject 2 (fuel-flow virtual sensor) — protocol for E1, ready to freeze

Prepared 2026-11-11 **before any mutant result** (only a 3-mutant runner smoke test, not recorded).
Files to freeze in the same commit: `common.py`, `identify.py`, `spec/baseline.json`,
`spec/identification.json`, `ref.py`, `gen.py`, `tests_req.py`, `stages.py`, `harness/*`, `mutate.py`,
`protocol/mutants.json`, `protocol/calibration.json`, `e1.py`, `analyze_e1.py`, `gen_vectors.py`,
`pil_stream.py`. Exploration scripts kept for provenance: `inspect_data.py`, `explore_ident.py`,
`check_l475.sh`, `smoke_e1.py`.

## Data
Kaggle pedro2025/obd2-panel-opel-2012 (CC BY 4.0). Local `dataset.csv` sha256 27e6b070… (789,373 rows;
the same file genai-mbd-exp pinned) and `refueling_history.csv` sha256 e0f70623…. Tanks 8–22 all have a
refuelled volume. Median sampling 1.15–1.23 s; gaps > 5 s only between trips. NaN < 0.7 % (LTFT),
replaced by 0. Identification tanks 8–17, field (held-out) tanks 18–22.

## Subject
Physics model: rate = k_cal·MAF·60/(AFR·rho)·(1 + trim/100), trim = STFT+LTFT clamped to ±25 %, DFCO
(THR ≤ 21.0 % and RPM > 1600) → 0, rate clamped to [0, 400] ml/min, volume += rate·clamp(dt,0,5 s)/60,
float32 C. Design constants AFR 14.7, rho 0.745 g/ml. Identified k_cal = 1.01800 (train mean |error|
7.63 % per tank, max 15.1 %, dominated by refuel-volume scatter). DFCO thresholds not identifiable from
the refuel oracle (≤ 0.05 pp change over a grid) → fixed by design. One spec generates the Modelica model
(MIL) and the C (SIL/PIL).

## Stages and oracles
| Stage | Executes | Oracle |
|---|---|---|
| UNIT | host gcc, `harness/unit.c` | rate function and one integration step vs spec-derived expectations |
| MIL | OpenModelica 1.27.2 native simulation, CombiTimeTable testbench | REQ-1..4 (`tests_req.py`) |
| SIL | host gcc -O2 | REQ-1..4 + back-to-back vs MIL: rate 2.2e-4 ml/min, volume 0.048 ml |
| PIL | Cortex-M4; dev target QEMU mps2-an386; real NUCLEO-L476RG / IoT-LAB st-iotnode | REQ-1..4 + back-to-back vs SIL 1e-5 + timing ≤ 2× baseline max |
| FIELD | QEMU build of the target code on tanks 18–22 | fail if any tank \|rel. volume error\| > \|baseline\| + 2.0 pp, or invalid |

Baseline field errors: 18 −2.97 %, 19 +1.14 %, 20 −3.80 %, 21 +10.70 %, 22 −1.84 %.

## Mutants
75 (23 model: MP 12, MS 2, MK 4, MSAT 3, MDT 2; 52 code: AOR 14, ROR 16, SDL 11, FPP 11, TW 0 — the
code has no integer type). Exhaustive per operator, `protocol/mutants.json`.

## Analysis
`analyze_e1.py`, identical to subject 1's.

## Known limits / deviations at freeze time
- Field tanks (~194k rows × 6 inputs ≈ 4.6 MB) do not fit in the boards' 1 MB flash: the field oracle
  runs on the QEMU build of the target code, not on silicon (subject 1 runs it on silicon).
- Real-target firmware embeds only the 8 requirement vectors (5,420 rows, 132 KB); validated in QEMU
  b-l475e-iot01a: CRC ok on all vectors, max |PIL−SIL| 5e-6 (SIL decimal output rounding).
- SIL vs MIL volume differs by up to 4.8e-3 ml on the 3000-row test (float32 accumulation vs Modelica
  double) — the tolerance rule absorbs it; it is a real embedded effect, not an error.
- Calibration wall times were taken while other jobs ran on the same PC (subject-1 E1, IoT-LAB runs).
- Requirement thresholds are our design requirements, set before mutants; not from a standard.
