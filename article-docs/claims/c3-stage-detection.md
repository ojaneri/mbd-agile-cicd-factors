# C3 — Functional detection saturates before the target; each stage changes when, not whether

Statement (revised, d-0011, proposed): adding stages raises the detection of field-relevant defects
significantly up to SIL (or MIL), after which it saturates; the target stage adds no functional field
detection and contributes platform checks (timing, memory state).

Original pre-registered statement, **partly refuted and to be reported as such**: MIL, SIL and PIL
stages are complementary: each detects at least one defect class that the earlier stages do not, so
removing a stage raises the escape rate by a measurable amount.

Final E1 numbers, real-board PIL, both subjects: subject 1 A0 26/68, A1 52/68, A2 68/68, A3 68/68;
subject 2 A0 23/34, A1 34/34, A2 34/34, A3 34/34. "Only PIL sees timing" is true by construction (no
other stage measures cycles): report the counts (5 and 6), not as a discovery.

Evidence today (subject 1 only, PIL on QEMU, 2026-11-11 — provisional): **C3 holds only in part.**
- Cumulative stages raise detection significantly up to SIL (38 % → 76 % → 100 %, McNemar p ≤ 3e-5).
- But no stage was *unique* for field-relevant defects: SIL running the requirement tests caught all
  68, including every model-level one (exploratory analysis). As stated, "removing a stage raises the
  escape rate" is **false for MIL** in this pipeline: removing MIL loses earliness, not detection.
- PIL was unique only for non-functional defects: 5 timing regressions and 1 uninitialised-state
  defect (non-field-relevant under the functional oracle).
Suggested restatement (proposed, for the author): "each stage changes *when* a defect is caught and
what it costs; only the target stage sees platform defects (timing, uninitialised state)".
Real target (IoT-LAB st-iotnode, subject 1, all 130 mutants): same rates, same five timing-only
mutants; the uninitialised-state detection moved from SDL-007 (QEMU) to SDL-006 (board), so that
part of PIL's value is platform-dependent and must be stated as such.
Subject 2 on QEMU: same pattern (MIL raises detection, no unique functional stage, 6 timing-only).
Subject 2 real-target column: complete, same rates, same six timing-only mutants (see E1). Source: [[experiments/e1-defect-detection-by-stage]].

Evidence 2026-11-13 (exploratory suite split, experiments/e1 "Detection by test suite"): the stage gain is the
requirement suite's. On host C the requirement tests alone caught all field-relevant mutants (68/68, 34/34);
the unit suite (97-100 % line coverage) caught 26 and 23 and no model-level mutant. Stage and suite are
confounded in factor A; the paper now says so.

Would falsify it: one stage (e.g., MIL) detects every mutant the later stages detect, within the CI;
then the later stages add cost without detection, and the paper must say so.

Note: this result is not guaranteed by design; the falsifying outcome is publishable and must be
reported if it happens (M03).

## Todos
- **[#t-0024]** status: done · author: osvaldo — Closed 2026-11-15 as done: C3 is stated with intervals and the exploratory label in the paper. Original: After E1, state C3 at the strength the CIs support; do not round "most" to "all".
