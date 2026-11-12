# E2 — Integration cadence and automation (Agile + CI axis, RQ2)

Status: **first run done for subject 1 (2026-11-11), as a trace-driven replay — a deviation from
the backlog plan below.** Shared setup in [[experiments/e0-testbed-and-protocol]].
Supports [[claims/c1-integration-gain]].

## Run 1 — subject 1, trace-driven replay with real-target PIL cost (`testbed/soc/e2.py`)
Deviation (M10): no real backlog of increments yet (t-0019 still open). Instead a synthetic stream of
N = 10 commits per sprint, one every 2 h, each defective with p = 0.3, defects drawn uniformly from E1's
live mutants with their E1 per-stage verdicts (real-board PIL verdicts); R = 2000 replays,
seed 20261111. Stage costs are E1 medians, PIL = **53.5 s per run on the IoT-LAB board** (flash +
capture), against 0.29 s UNIT, 2.45 s MIL, 0.29 s SIL. Output: `results/e1_qemu_e2.json`.
Medians per sprint (bootstrap 95 % CI of the median), automated trigger:

| Config | batch | feedback latency | escapes | compute per sprint |
|---|---|---|---|---|
| A2 | 1 | 3 s | 0 | 36 s |
| A2 | 10 | 9.0 h | 0 | 30 s |
| A3 | 1 | 57 s | 0 | 678 s |
| A3 | 5 | 4.0 h | 0 | 509 s |
| A3 | 10 | 9.0 h | 0 | 565 s |

A manual 8 h trigger adds 8 h to every cell. A0 lets 1 defect per sprint escape (median). **Correction
(number audit, 2026-11-11):** A1's median is 0 but S1 lets at least one field-relevant defect escape in 642 of
2000 sprints at A1 (mean 0.38); only from A2 on are escapes 0 in every replay.
Cliff's delta (planned contrasts): A3 auto b1 vs b10 latency −0.97; compute +0.32; A3 b1 auto vs
manual-8h lead time −1.0; b1 auto A2 vs A3 escapes 0.
Reading: latency is set by cadence and trigger, not by stage cost; the real PIL stage multiplies
compute by ~19× over A2 and buys no field escapes here (its gains in E1 were timing-only). Batching
saves little compute because a failing batch is re-run during bisection.
Caveats: synthetic commit stream; escapes inherit E1's mutant set, so 0 escapes from A1 up is
by construction of that set; a manual delay is a parameter (sweep 1/8/24 h in the file).
Subject 2, same replay (`testbed/fuel/e2.py`, copy of subject 1's; PIL 18.5 s per run): A2 b1 43.6 s of
compute, A3 b1 266 s (6.1×), latency 22 s at b1 and about 9 h at b10; 0 escapes from A1 up.
To check: in cell A0|b10|auto the reported median (8.67 h) lies outside its bootstrap CI
(9.33–10 h), a percentile-bootstrap artefact on discrete data; use a different CI before the paper
(t-0042).

## Robustness (exploratory, added 2026-11-11 after run 1; `testbed/e2_sweep.py`, `testbed/e2_sweep.json`)
- Interval fix (t-0042): medians now carry an order-statistic (binomial) 95 % CI, which always contains the
  median; the frozen `e2.py` model is imported unchanged.
- Sweep (t-0043): DT_COMMIT 0.5/2/8 h × P_DEFECT 0.1/0.3/0.5, both subjects. A3 batch-1 latency equals the
  stage cost in every cell (57 s S1, 22 s S2); batch-10 latency scales with the spacing (2.3, 9.0, 36 h);
  A3/A2 compute at batch 1 is 18.7–20.6 (S1) and 6.1 (S2); A2 escapes 0 everywhere; A1 escapes (S1) mean
  0.12–0.63 per sprint, rising with P_DEFECT. Conclusions of run 1 unchanged.

## Setup
- A **backlog of increments** per subject: a scripted sequence of feature changes (e.g., add
  temperature compensation, add a new drive mode, change a filter), each a real commit on the model.
- Defects from E1 are seeded into a known subset of increments, with the seeding plan fixed before runs.
- The backlog is replayed under factor B (batch 1, batch k, big-bang) × factor C (per-commit
  automated vs gated manual release with a stated simulated delay), with factor A at its full level.

## Metrics
- Feedback latency: time from the defective commit to the first failing stage.
- Localisation effort: number of candidate commits in the failing batch, and bisection steps to
  isolate the defective one.
- Escape rate to the field oracle.
- Lead time per increment: commit to signed release candidate.
- Pipeline cost: total runner minutes per backlog.

## Analysis
- Paired comparisons across configurations on the same seeded defects (Wilcoxon signed-rank for
  times, McNemar for escapes), effect size Cliff's delta, bootstrap CIs.
- The trade-off figure: pipeline cost vs feedback latency per configuration.

## Threat specific to E2
- The simulated delay for manual release is a parameter, not an observation; report a sensitivity
  sweep over it instead of a single value.

## Todos
- **[#t-0019]** status: open · author: osvaldo — Write the backlog of increments (at least 10 per subject) and the defect seeding plan; commit before runs.
- **[#t-0042]** status: done · author: osvaldo — Done 2026-11-11 in `testbed/e2_sweep.py` (order-statistic CI). Original: Replace the percentile bootstrap of the median in `e2.py` for discrete outcomes (median fell outside its CI in A0|b10|auto); rerun E2 after subject 2 real PIL.
- **[#t-0020]** status: open · author: osvaldo — Choose sprint batch size k and the manual-release delay range, with a reason recorded as a decision.
