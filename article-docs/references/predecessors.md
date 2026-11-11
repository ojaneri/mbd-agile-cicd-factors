# Predecessors — closest works and positioning (K03, R05)

Source: [[references/search-log-2026-11]] (2026-11-11). Metadata read from IEEE Xplore pages or OpenAlex,
as marked. **Nothing here is in the bibliography yet**: every entry still needs `bib-verify-entries`
against Crossref before it is cited (R01).

## Closest predecessors (abstract read)

| # | Work | What it does | Evaluation | Difference from this paper |
|---|---|---|---|---|
| P1 | Mörtstrand, Bucaioni, Ciccozzi, "Bringing a Continuous Integration and Delivery Pipeline into MoVES", ICECET 2023, doi 10.1109/ICECET58911.2023.10389472 (IEEE page) | CI/CD pipeline (GitHub Actions) added to a model-based timing-analysis methodology for automotive software | Use case: brake-by-wire and wiper motor | Builds a pipeline; abstract reports no defect-detection or cadence measurement |
| P2 | Dmitriev et al., "A Lean and Highly-automated Model-Based Software Development Process Based on DO-178C/DO-331", DASC 2020, doi 10.1109/DASC50938.2020.9256576 (IEEE page) | Automated MBD workflow derived from a subset of avionics certification objectives | Process and artefacts for research aircraft | Avionics, standards-driven; closest analogue for our ISO 26262 evidence angle (E3); no comparison of configurations in the abstract |
| P3 | Mills, Turin, Mangas, Ranville, "Innovation Welcome: An Agile Approach to Model-Based Development of Safety-Critical Embedded Systems", ICSA-C 2018, doi 10.1109/ICSA-C.2018.00045 (IEEE page) | Argues for combining agile freedom with disciplined MBD integration in automotive | Abstract truncated at retrieval; evaluation not seen | Position/approach; must read full text before stating what it lacks |
| P4 | Beheshtian, Bavand, Rigby, "Software Batch Testing to Save Build Test Resources and to Reduce Feedback Time", IEEE TSE (vol 48 no 8, 2022; online 2021), doi 10.1109/TSE.2021.3070269 (OpenAlex) | Evaluates six batching/bisection strategies on open-source projects (Travis CI) | Large-scale empirical | Same mechanism as our factor B (batch size vs feedback and bisection cost) but for general software, not MBD/embedded pipelines with MIL/SIL/PIL stages. **Our E2 should cite and position against it.** |
| P5 | Fu, Eldh, Wiklund, Ermedahl, Artho, "Prevalence of continuous integration failures in industrial systems with hardware-in-the-loop testing", ISSREW 2022, doi 10.1109/ISSREW55968.2022.00040 (OpenAlex) | 11,731 builds from four industrial HIL CI projects; failure distribution | Industrial mining study | Observational; measures pipeline failures, not injected defects per stage |
| P6 | Mathews et al., "Simulink DevOps Evolution", SAE 2026-01-0080 (OpenAlex) | Interview-based study of interactive DevOps for Simulink users | Interviews | Qualitative practitioner study; complementary |

## Candidates still to read (title-level only — do not characterise in the paper yet)
- "A Scalable Software-in-the-Loop Test Methodology for Early Integration Testing Using Virtual ECUs", ETFA 2026 (IEEE 11724816). **IES conference; possibly the closest work. Read first.**
- "Model-Based Fault Injection and Diagnostic Validation for AUTOSAR Software Components in Safety-Critical Automotive Systems", **ISIE 2025** (IEEE 11124734). Venue exemplar (P08) and possibly close to E1.
- "Enabling Credibility for Virtual Testing of Autonomous Vehicles by Adapting DevOps to Hardware-in-the-Loop Simulations", IV 2025 (IEEE 11097544).
- "A study on parallel virtual ECU build and SILS automation for SDV validation", Trans. KSAE 34(10) 2026 (open access, Korean).
- "CI-CD Workflow For Embedded System Design", ICCUBEA 2023 (IEEE 10392168).
- "Artshop: A continuous integration and quality assessment framework for model-based software artifacts", MBEES 2016.
- Simulink mutation tooling, for E1 method: SIMULTATE (ICSTW 2016, IEEE 7528959), MUT4SLX (ASE 2023, IEEE 10298490), timed mutation operators (ICSTW 2024, IEEE 10675884), fault injection for Simulink CPS (ASE 2025, IEEE 11334475).

## Provisional positioning (not yet a claim)
From the abstracts read, the closest works either **build** an MBD + CI/CD pipeline and demonstrate it on a
use case (P1, P2), **measure** CI behaviour without injected ground truth (P5) or outside embedded MBD (P4),
or **argue** for agile MBD (P3, P6). None of the abstracts read reports a paired comparison of
verification stages × integration cadence with known injected defects. That is the gap E1/E2 target.

This is **not** yet a "no prior work" claim (R05, K08): the ETFA 2026 and ISIE 2025 papers have not been
read and may already do part of it.

## Decisions

## Todos
- **[#t-0026]** status: open · author: osvaldo — Read the ETFA 2026 (11724816) and ISIE 2025 (11124734) papers in full via CAFe, by hand, and update P-table; they decide whether the gap statement holds.
- **[#t-0027]** status: open · author: osvaldo — Read the remaining title-level candidates' abstracts (IV 2025, KSAE 2026, ICCUBEA 2023, Artshop 2016) by hand; no scripted retrieval (IEEE returned 420).
- **[#t-0028]** status: open · author: osvaldo — Dissect the ISIE 2025 AUTOSAR fault-injection paper as the venue exemplar (`venue/exemplar.md`: structure, length, references, figures), check P08.
- **[#t-0029]** status: open · author: osvaldo — Run Q2–Q5 on Scopus and Q1/Q3 on ACM DL and SAE Mobilus to close coverage; rerun Q2 without "SAFe".
- **[#t-0030]** status: open · author: osvaldo — Verify every entry above against Crossref (`bib-verify-entries`) before it enters the .bib.
