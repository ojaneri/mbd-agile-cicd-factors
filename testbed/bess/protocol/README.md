# Subject 3 (BESS rack thermal virtual sensor with derating) — protocol, ready to freeze

Prepared 2026-11-11 **before any mutant result** (only a 3-mutant runner smoke test, not recorded).
Built for E5 (platform sensitivity); usable for E1 with the same runner as subjects 1–2.
Files to freeze in the same commit: `common.py`, `identify.py`, `spec/baseline.json`,
`spec/identification.json`, `ref.py`, `gen.py`, `tests_req.py`, `stages.py`, `harness/*`, `mutate.py`,
`protocol/mutants.json`, `protocol/calibration.json`, `e1.py`, `analyze_e1.py`, `gen_vectors.py`,
`pil_stream.py`, `pil_real.py`. Exploration and checks kept for provenance: `inspect_data.py`,
`explore_derate.py`, `check_l475.sh`, `smoke_e1.py`.

## Data
Qu, J., "Dataset for: A Multi-Agent AI Framework for Explainable Battery System Maintenance", Zenodo,
doi 10.5281/zenodo.20094787, published 2026-06-01, **CC BY 4.0** (Zenodo records API, `license.id =
cc-by-4.0`, `access_right = open`, checked 2026-11-11 with an anonymous request). Converted by
genai-mbd-exp `convert_bess.py` in temp mode: 5 s grid, racks 1/5/9, TCELL = rack sensor 109 (middle),
TREF = mean of the other 7 rack sensors, CURRENT [A]. Local `data_besstemp/dataset.csv`: 2,264,252 rows,
1,332 segments, sha256 7249bace…3b38e (equal to the hash pinned by genai-mbd-exp `prep_bess_temp.sh`).
dt = 5 s on every row, no NaN; **TCELL is quantised to 1 °C** (median 26, p99 32, max 33 °C).
Identification: months 2024-10…2025-01, all racks (705 segments, 1,091,521 rows). Field (held-out):
months 2025-02…2025-05, rack 5 only (209 segments, 390,859 rows).

## Subject
Thermal model (identified): t_est follows tref + c0 + k_h·I² with time constant tau, 4 Euler sub-steps per
5 s row, current clamp ±400 A, temperature clamp [−40, 90] °C. Identified by Nelder-Mead on the vectorised
simulation: tau = 201.5 s, k_h = 2.565e-5 °C/A², c0 = 0.081 °C. Train RMSE 0.625 °C (naive t_est = TREF:
0.702); field RMSE 0.458 °C (naive: 0.449). **The thermal model does not beat the naive estimate on the
held-out months**; the 1 °C quantisation of TCELL bounds what any estimator can show. This does not affect
E1/E5, whose oracles are requirement tests and relative field degradation, but it must not be presented as
a good virtual sensor.
Derating (design constants, not fitted): first-order filter tau_f 60 s; latch on t_filt > 31.0 °C; release
when t_filt < 29.0 °C and latched ≥ 300 s; derated factor 0.5; recovery ramp 0.002/s. Thresholds chosen
from the TCELL distribution so the derating is exercised on real data (field rack 5: 6.5 % of rows derated
by the estimate, 3.7 % by the measured-temperature reference; `explore_derate.py`).
State `bess_t {float t_est, t_filt, der; int latch; uint32_t dwell_ms}`, all five set in
`bess_init(bess_t *o, float tref)`. Step `float bess_step(bess_t *o, float cur, float tref)` = 
`bess_therm(te0, cur, tref)` (locals `ic`, `acc`; `acc` is the sub-step accumulator) + `bess_derate(o, te)`
(local `tgt`). Locals are declared first and assigned later, so a deleted assignment leaves them
uninitialised. One spec generates the Modelica model (MIL) and the C (SIL/PIL).

## Stages and oracles
| Stage | Executes | Oracle |
|---|---|---|
| UNIT | host gcc, `harness/unit.c` | thermal row, derating step, init vs spec-derived expectations |
| MIL | OpenModelica 1.27.2 native simulation, CombiTimeTable testbench | REQ-1..5 (`tests_req.py`) |
| SIL | host gcc -O2 | REQ-1..5 + back-to-back vs MIL: t_est 2.1e-3 °C, der 1e-5 |
| PIL | Cortex-M4; dev target QEMU mps2-an386; real st-iotnode / NUCLEO-L476RG | REQ-1..5 + back-to-back vs SIL 1e-5 + timing ≤ 2× baseline max |
| FIELD | QEMU build of the target code on the held-out vector | fail if any month RMSE > baseline + 0.10 °C, or derating mismatch > baseline + 1.0 pp, or invalid |

Field baseline (RMSE °C / derating mismatch %): 2025-02 0.507 / 3.12; 2025-03 0.477 / 2.68;
2025-04 0.416 / 2.38; 2025-05 0.419 / 3.70. The derating reference is the baseline derating logic driven by
the measured TCELL.

## Calibration (10 reps, baseline passes every stage 10/10)
SIL−MIL max diff: t_est 2.1e-4 °C, der 4.8e-7; PIL−SIL 0. QEMU baseline max 144 ticks per step, budget
288. Median wall times: UNIT 0.29 s, MIL 2.49 s (build 2.30 s), SIL 0.28 s, PIL(QEMU) 0.77 s, field 7.9 s
(1 sample). Taken while other jobs ran on the same PC.

## Mutants
93 (28 model: MP 14, MS 2, MK 4, MSAT 4, MDT 2, MRST 2; 65 code: AOR 17, ROR 20, SDL 24, FPP 3, TW 1).
Exhaustive per operator, `protocol/mutants.json`. Initialisation-deletion mutants: SDL-001…005 (the five
`bess_init` assignments); local-initialisation deletions: SDL-006 (`ic = cur`), SDL-009 (`acc = te0`),
SDL-018 (`tgt = 1.0f`), SDL-023 (`te = bess_therm(...)`).

## Analysis
`analyze_e1.py`, identical to subjects 1–2.

## Known limits / deviations at freeze time
- Field vector (390,859 rows × 3 inputs ≈ 4.7 MB) does not fit in the boards' 1 MB flash: the field oracle
  runs on the QEMU build of the target code (as subject 2).
- Real-target firmware embeds only the 7 requirement vectors (6,642 rows, 82 KB); validated in QEMU
  b-l475e-iot01a: CRC ok on all vectors, max |PIL−SIL| 5e-8 (SIL decimal output rounding).
- REQ-2 allows up to 3 rows of derating mismatch per test (float32/float64 tie at a threshold crossing);
  fixed before any mutant.
- Requirement thresholds and derating constants are our design choices, set before mutants; not from a standard.
- The thermal model is no better than the naive estimate on held-out data (see Subject).
