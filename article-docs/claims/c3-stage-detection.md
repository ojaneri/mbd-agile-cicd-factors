# C3 — Each MBD verification stage detects defect classes the others miss

Statement: MIL, SIL and PIL stages are complementary: each detects at least one defect class that
the earlier stages do not, so removing a stage raises the escape rate by a measurable amount.

Evidence today: **none measured.** Planned in [[experiments/e1-defect-detection-by-stage]].

Would falsify it: one stage (e.g., MIL) detects every mutant the later stages detect, within the CI;
then the later stages add cost without detection, and the paper must say so.

Note: this result is not guaranteed by design; the falsifying outcome is publishable and must be
reported if it happens (M03).

## Todos
- **[#t-0024]** status: open · author: osvaldo — After E1, state C3 at the strength the CIs support; do not round "most" to "all".
