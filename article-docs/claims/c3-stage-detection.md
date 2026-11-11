# C3 — Each MBD verification stage detects defect classes the others miss

Statement: MIL, SIL and PIL stages are complementary: each detects at least one defect class that
the earlier stages do not, so removing a stage raises the escape rate by a measurable amount.

Evidence today (subject 1 only, PIL on QEMU, 2026-11-11 — provisional): **C3 holds only in part.**
- Cumulative stages raise detection significantly up to SIL (38 % → 76 % → 100 %, McNemar p ≤ 3e-5).
- But no stage was *unique* for field-relevant defects: SIL running the requirement tests caught all
  68, including every model-level one (exploratory analysis). As stated, "removing a stage raises the
  escape rate" is **false for MIL** in this pipeline: removing MIL loses earliness, not detection.
- PIL was unique only for non-functional defects: 5 timing regressions and 1 uninitialised-state
  defect (non-field-relevant under the functional oracle).
Suggested restatement (proposed, for the author): "each stage changes *when* a defect is caught and
what it costs; only the target stage sees platform defects (timing, uninitialised state)".
Pending: real-target PIL column (IoT-LAB), subject 2. Source: [[experiments/e1-defect-detection-by-stage]].

Would falsify it: one stage (e.g., MIL) detects every mutant the later stages detect, within the CI;
then the later stages add cost without detection, and the paper must say so.

Note: this result is not guaranteed by design; the falsifying outcome is publishable and must be
reported if it happens (M03).

## Todos
- **[#t-0024]** status: open · author: osvaldo — After E1, state C3 at the strength the CIs support; do not round "most" to "all".
