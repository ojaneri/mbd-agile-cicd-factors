# Subject 1 (SoC observer) — frozen protocol for E1

Frozen 2026-11-11 **before any mutant result**. Files frozen with this commit:
`spec/baseline.json`, `spec/identification.json`, `gen.py`, `ref.py`, `tests_req.py`, `stages.py`,
`harness/*`, `mutate.py`, `protocol/mutants.json`, `protocol/calibration.json`, `e1.py`, `analyze_e1.py`.
Any later change to these is a deviation and is recorded in `article-docs/experiments/e1-defect-detection-by-stage.md`.

## Subject
Luenberger-type SoC observer (1RC + piecewise-linear OCV, 11 knots), discrete at 1 s, float32 C.
Identified from LG HG2 25 degC UDDS, LA92, US06, Mixed1-4 (`identify.py`); held-out field cycles
Mixed5-8. OCV fit uses a fixed second-difference penalty; gains limited by a stability rule.
One spec generates both the Modelica model (MIL) and the C code (SIL/PIL) (`gen.py`).

## Stages and oracles
| Stage | Executes | Oracle |
|---|---|---|
| UNIT | host gcc, `harness/unit.c` | lookup/inverse/rest-hold/saturation vs spec-derived expectations |
| MIL | OpenModelica 1.27.2 native simulation, testbench with CombiTimeTable | requirement tests REQ-1..7 (`tests_req.py`) |
| SIL | host gcc -O2 | REQ-1..7 + back-to-back vs MIL, tol 1e-5 |
| PIL | Cortex-M4 build; dev target QEMU mps2-an386; real target NUCLEO-L476RG / IoT-LAB st-iotnode | REQ-1..7 + back-to-back vs SIL, tol 1e-5 + timing <= 2x baseline max |
| FIELD | target build on held-out real cycles | fail if any cycle RMSE > base+0.005, max > base+0.02, or invalid |

## Mutants
130 (46 model-level, 84 code-level), operators in `mutate.py`, applied exhaustively, listed in
`protocol/mutants.json`. Stillborn (non-compiling) mutants are excluded and counted.

## Analysis
`analyze_e1.py`, unchanged after results: Wilson 95 % CIs, exact McNemar between successive
configurations A0..A3, per-operator first-detection, stage-unique detections, and timing-only
detections reported apart (the field oracle is functional; timing regressions are not escapes).

## Smoke test before freeze (3 mutants, not recorded as results)
Runner checked on MP-R0-x0.5, AOR-007 and FPP-005 only to catch runner bugs; their verdicts are
recomputed in the recorded run like every other mutant.

## Known limits at freeze time
- PIL on QEMU is a development run: functional results only; ticks are an instruction proxy.
  The paper's PIL results must come from the NUCLEO-L476RG (and IoT-LAB replication).
- Requirement thresholds are our design requirements, set before mutants; not from a standard.
