# Predecessors — closest works and positioning (K03, R05)

Source: [[references/search-log-2026-11]]. Read 2026-11-11 by hand through CAFe (IEEE Xplore pages,
Scopus records) and OpenAlex, paced, no bulk download. **P1–P8 are in `manuscript/refs.bib`**, each fetched from Crossref by DOI on 2026-11-11 (titles, authors, pages
matched). P9 (Artshop, no DOI seen) is not cited. Also in refs.bib, Crossref/DataCite-checked: FIT IoT-LAB
(Adjih et al., WF-IoT 2015), Valgrind (PLDI 2007), MemorySanitizer (CGO 2015), Just et al. (FSE 2014), LG HG2 and
BESS datasets; the Kaggle OBD-II entry was checked on the Kaggle API on 2026-11-13 (title OBD2_panel_opel_2012, creator
Pedro, v1 2025-11-15, v10 2026-10-03; t-0049 done). Agile Manifesto (agilemanifesto.org, 2001) added for the
Agile framing, read 2026-11-13.

Reading depth: **F** = full text read (sections and conclusions), **A** = abstract only.

## Comparison table (draft for the paper's Related Work)

| # | Work | Depth | Pipeline / process | Stages | Ground-truth defects? | Measures cadence / lead time? | Evaluation |
|---|---|---|---|---|---|---|---|
| P1 | Mörtstrand, Bucaioni, Ciccozzi, ICECET 2023, doi 10.1109/ICECET58911.2023.10389472 | A | CI/CD (GitHub Actions) added to MoVES model-based timing analysis | model-level timing analysis | no (abstract) | no (abstract) | use case: brake-by-wire, wiper motor |
| P2 | Dmitriev et al., DASC 2020, doi 10.1109/DASC50938.2020.9256576 | A | lean, automated MBD process from DO-178C/DO-331 objectives | MBD artefacts and verification | no (abstract) | no (abstract) | process applied to research aircraft |
| P3 | Kavgic, Ecin (Porsche), Jesser, ETFA 2026, doi 10.1109/ETFA68377.2026.11724816 | F | multi-V-ECU SiL (6 Level-2 V-ECUs, dSPACE VEOS) with CI and test automation | SiL vs HiL | **no**: transferability of 200 existing HiL tests to SiL (~30 %); earlier defect detection is argued, not measured | no | one industrial project; authors state no scalability benchmark |
| P4 | Kim, Park, Kim, Oh, Jung (HL Mando), Trans. KSAE 34(10):1129–1137, 2026, doi 10.7467/KSAE.2026.34.10.1129 (Korean, open access) | A (Scopus) | Jenkins dual-build: real ECU and Level-3 V-ECU (virtual MCAL) in parallel, automated SILS | SILS vs real ECU | no: functional equivalence on ASW change scenarios | claims reduced verification time (method not seen) | representative ASW change scenarios |
| P5 | Schlatzer, Schade, Pannek, IEEE IV 2025, doi 10.1109/IV64158.2025.11097544 | F | DevOps platform for developing HiL simulations themselves | HiL | no | **no — the authors write that a KPI-based assessment "such as lead time, is still forthcoming"** | platform description |
| P6 | Beheshtian, Bavand, Rigby, IEEE TSE 48(8), 2022, doi 10.1109/TSE.2021.3070269 | A | batching and bisection strategies in CI | general software tests | real build failures | **yes, batch size vs test executions and feedback** | large open-source projects (Travis CI) |
| P7 | Fu, Eldh, Wiklund, Ermedahl, Artho, ISSREW 2022, doi 10.1109/ISSREW55968.2022.00040 | A | industrial CI with HIL | HIL | real failures (observational) | no | 11,731 builds, four projects |
| P8 | Manuel, Franco, Silva, Santos, dos Santos, **Dias Santos (UTFPR-PG)**, **ISIE 2025**, doi 10.1109/ISIE62713.2025.11124734 | F | model-based fault injection with AUTOSAR Dem blocks in Simulink | MIL only | injected sensor faults (stuck high/low) | no | one throttle-sensor model; coverage before/after (visual) |
| P9 | Gerlitz, Hansen, Dernehl, Kowalewski, MBEES 2016 (Artshop) | A (Scopus) | CI of static quality checks for Simulink, DOORS, pure::variants artefacts | static analysis only | no | no | framework description |

Background only (no evaluation, or position): Mills et al., ICSA-C 2018 (1-page presentation abstract,
p. 152); Talekar & Harpale, ICCUBEA 2023 (descriptive CI/CD workflow, no evaluation; low weight, R08);
Mathews et al., SAE 2026-01-0080 (interviews with Simulink users on interactive DevOps);
Haghighatkhah et al., IEEE Software 2017.

Method references for E1 (mutation of Simulink/model artefacts), title-level only: SIMULTATE (ICSTW 2016),
MUT4SLX (ASE 2023; SANER-C 2024), timed mutation operators for Simulink (ICSTW 2024), fault injection for
Simulink CPS models (ASE 2025).

## Positioning (provisional, for K03)
Across the nine works above, pipelines that combine model-based artefacts with CI/CD are **built and
demonstrated** (P1, P2, P4, P5, P9), and stage shifting from HiL to SiL is assessed by **test
transferability** (P3) or **functional equivalence** (P4). Batch size vs feedback is measured only for
general software (P6). Injected defects appear only at a single MIL stage (P8). None of the works read
reports a **paired measurement of defect detection per stage (MIL/SIL/PIL) × integration cadence with
known injected defects** in an embedded MBD pipeline, and P5 explicitly lists lead-time assessment as open.

Allowed wording (K08, R05): "In a dated search of IEEE Xplore and Scopus (November 2026) we did not find…".
Not allowed: "first", "no prior work". The search is not exhaustive (see search log limits).

## Consequences for the experiments
- E1 must report **detection**, not transferability or equivalence, to differ from P3/P4. Back-to-back
  SIL/PIL equivalence (as in P4) is a precondition check, not a result.
- E2 must cite P6 and explain what differs: MBD stages with different costs per stage (MIL cheap, PIL
  expensive), embedded target, injected ground truth.
- P8 is **self-citation**: Max Mauro Dias Santos, co-author and advisor of this paper, is its last author
  (confirmed by Osvaldo on 2026-11-11). Cite it because it is pertinent (closest MBD fault-injection work
  at this venue), not more than once per point, and in the third person if ISIE review is
  double-anonymous (R09, E02). Keep the comparison factual: it is MIL-only and demonstration-level, and
  the text should say so in neutral terms.

## Decisions

## Todos
- **[#t-0026]** status: done · author: osvaldo — ETFA 2026 (P3) and ISIE 2025 (P8) read in full on 2026-11-11; neither covers the E1/E2 measurement.
- **[#t-0027]** status: done · author: osvaldo — IV 2025, ICCUBEA 2023, ICSA-C 2018 read on IEEE; KSAE 2026 and Artshop abstracts read on Scopus.
- **[#t-0029]** status: done · author: osvaldo — Closed 2026-11-15: merged into t-0058 (related work). Original: Run Q2–Q5 on Scopus and Q1/Q3 on ACM DL and SAE Mobilus to close coverage; rerun Q2 without "SAFe".
- **[#t-0030]** status: done · author: osvaldo — P1–P8 verified against Crossref by DOI on 2026-11-11 and entered in `manuscript/refs.bib`; P9 left out.
- **[#t-0031]** status: open · author: osvaldo — Find Schwarzl et al. (Daimler test-distribution algorithm that shifts tests to earlier platforms), cited by P3 [8]; possibly the closest predecessor for E1. P3's reference list was not available on IEEE.
- **[#t-0032]** status: open · author: osvaldo — Find Moradi et al., virtual fault injection framework with model-based tools (cited by P8 [8]); relevant to E1 method.
- **[#t-0033]** status: open · author: osvaldo — Check SAE 2026-26-0683 "Virtual ECU: Development & Validation Platform" (vECU + CI/CD with Gerrit/Jenkins), found on the open web on 2026-11-11, title-level only.
- **[#t-0034]** status: open · author: osvaldo — Read P1 and P2 in full (only abstracts read) to confirm they report no defect-detection measurement.
