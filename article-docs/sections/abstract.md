# Abstract — draft v0 (viability only)

Status: draft. Not a final abstract. Every claim below must stay within [[claims/c1-integration-gain]] and [[claims/c2-standards-traceability]]. Neither is measured yet, so the abstract must not state results.

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
- **[#t-0009]** status: open · author: osvaldo — Rewrite the abstract only after C1 has measured numbers. Until then, keep it as a framing paragraph with no results.
