# E1 — Which stage catches which defect (MBD axis, RQ1)

Status: **planned, not run.** Shared setup in [[experiments/e0-testbed-and-protocol]].
Supports [[claims/c3-stage-detection]].

## Setup
- Subjects: SoC estimator (LG HG2) and fuel-flow sensor (Opel Corsa).
- Defects: mutants injected at two levels.
  - Model level (Modelica): wrong gain/constant, sign flip, saturation limit changed, unit or scale
    error, lookup-table breakpoint shift, wrong initial condition, sample-time change.
  - Code level (generated or hand C): integer overflow / fixed-point scaling, wrong data type,
    uninitialised state, off-by-one in buffers, timing (missed deadline on MCU).
  - Each mutant tagged with a class: functional, numerical, timing, integration/interface.
- Stages, each with its own oracle:
  - Unit: tests on functions in isolation.
  - MIL: FMU simulation vs requirement-derived checks on the drive cycles.
  - SIL: back-to-back C vs MIL outputs, tolerance stated in advance.
  - PIL: same C on nRF52840 / NUCLEO-L476RG via FIT IoT-LAB; back-to-back plus execution time vs
    deadline.
  - Field oracle (escape): replay on held-out real recorded data; a mutant that changes field output
    beyond tolerance but passed all enabled stages is an **escape**.

## Metrics
- Detection rate per stage and per defect class (Wilson 95 % CI).
- First stage of detection; escape rate per configuration of factor A.
- Cost: wall-clock and compute per stage per run (median, IQR, R ≥ 10).
- Marginal value of each stage = mutants detected only by that stage.

## Expected figure / table (placeholders, no values)
- Heatmap: defect class × stage, cell = detection rate.
- Table: configuration of factor A → escape rate, total pipeline time.

## Todos
- **[#t-0016]** status: open · author: osvaldo — Write the mutation operators and state the number of mutants per class before running.
- **[#t-0017]** status: open · author: osvaldo — Fix the SIL and PIL back-to-back tolerances in advance and justify them.
- **[#t-0018]** status: open · author: osvaldo — Port both models to Modelica and confirm FMU export runs under FMPy.
