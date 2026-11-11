# Abstract

Status: draft v1 (2026-11-11, thesis per d-0011, proposed). Every number comes from E1/E2 scripts; bracketed items are placeholders. Must stay within [[claims/c1-integration-gain]], [[claims/c3-stage-detection]], [[claims/c4-platform-tiering]].

> Model-based design (MBD), Agile iteration and CI/CD are usually compared qualitatively, as if they were alternatives. We treat them as factors of one controlled pipeline: verification stages (unit, MIL, SIL, PIL), integration cadence (the only Agile property measured here) and release trigger. On two automotive estimators built from public field data, we injected 205 mutants, 102 of them field-relevant, and ran each on a host, an emulator and a real STM32L4 board. Unit tests alone detected 38–68 % of the field-relevant mutants; adding MIL and SIL reached 100 % (95 % CI lower bounds 90–95 %), and PIL added no functional detection. Emulator and board verdicts agreed on 202 of 205 mutants; all three disagreements were deleted state initialisations. In a trace-driven replay, per-commit runs returned feedback in under a minute against about 9 h for ten-commit batches, while board PIL multiplied compute per sprint by 6 to 19. The methods are therefore not alternatives: stages set what is caught, cadence and trigger set when, and the platform sets where a stage must run. A tiered pipeline [E5: result on an unseen subject] keeps detection at [E5: cost].

Abstract v0 argument, kept for the framing only:

Title (chosen by the author on 2026-11-10, see d-0007): *MBD, Agile, or CI/CD? A Comparative Analysis and Integrated Pipeline for Automotive Embedded Systems*

Title constraints (K06): "Comparative Analysis" must be the measured factorial comparison (E1, E2), not a literature opinion; "Integrated Pipeline" must be the pipeline actually built and run; "Agile" is operationalised as integration cadence (d-0003) and the abstract must say so. The question in the title must be answered in the abstract.

Argument:
1. MBD gives early, rigorous validation (MIL/SIL/HIL/VIL) but has high upfront cost and weak change flow.
2. Agile gives flexibility and feedback but is informal for safety evidence.
3. CI/CD automates integration, testing and OTA release but needs toolchain and governance.
4. The paper compares the three on target, artifacts, validation, time to deliver, change management and tooling, then proposes a four-stage flow (model and design, plan and develop, integrate and test, release and deploy) with feedback loops.

Gap: most comparisons in the sources are qualitative; there is no quantified case for SDV with standards traceability.

## Decisions
- **[#d-0007]** date: 2026-11-10 · status: accepted · author: osvaldo · promoted_by: osvaldo on 2026-11-11
  **Title: "MBD, Agile, or CI/CD? A Comparative Analysis and Integrated Pipeline for Automotive Embedded Systems".**
  Chosen by the author from five candidates (option 3). Fits the factorial design better than the SDV-centred options, because the subjects are powertrain/energy estimators on embedded MCUs, not a full SDV. Cost: the question form invites an answer; if results show the methods are complementary, the abstract must say "complementary" explicitly rather than pick a winner.

## Todos
- **[#t-0009]** status: done · author: osvaldo — Draft v1 written with measured numbers; the tiered-pipeline sentence stays a placeholder until E5.
