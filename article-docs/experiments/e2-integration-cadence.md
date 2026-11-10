# E2 — Integration cadence and automation (Agile + CI axis, RQ2)

Status: **planned, not run.** Shared setup in [[experiments/e0-testbed-and-protocol]].
Supports [[claims/c1-integration-gain]].

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
- **[#t-0020]** status: open · author: osvaldo — Choose sprint batch size k and the manual-release delay range, with a reason recorded as a decision.
