# Search log — closest predecessors (t-0010)

Purpose: find the 3–5 works closest to this paper, for the comparison table (K03) and to test any
"no prior work" sentence (R05). Not a systematic review; a targeted, logged search.

Access: Portal de Periódicos CAPES via CAFe (UTFPR), proxy ez48.periodicos.capes.gov.br, in the
author's Chrome session. Interactive, human pace, no bulk download (skill `lit-search-paywalled-db`).

Queries written 2026-11-11, before running. Years 2015–2026 unless stated.

| Id | Topic | Query |
|---|---|---|
| Q1 | MBD + CI/CD in automotive | ("model-based design" OR "model-based development" OR Simulink) AND ("continuous integration" OR "continuous delivery" OR DevOps) AND (automotive OR vehicle OR ECU) |
| Q2 | Agile + functional safety | (agile OR scrum OR SAFe) AND ("ISO 26262" OR "functional safety") AND automotive |
| Q3 | CI with X-in-the-loop stages | ("continuous integration" OR DevOps) AND ("hardware-in-the-loop" OR "software-in-the-loop" OR "processor-in-the-loop") |
| Q4 | Mutation / fault injection in model-based pipelines | ("mutation testing" OR "fault injection") AND (Simulink OR "model-based") |
| Q5 | Integration cadence effects | ("continuous integration") AND ("build frequency" OR "commit size" OR "batch size" OR "integration frequency") AND (defect OR feedback) |

Inclusion for the comparison table: proposes or evaluates a pipeline or process combining at least
two of MBD, Agile, CI/CD for embedded/automotive software, **with an evaluation** (case study or
measurement). Exclusion: opinion pieces without evaluation, non-embedded domains (kept as background only).

## Runs (2026-11-11, IEEE Xplore and Scopus via CAPES/CAFe proxy, filter 2015–2026)

| Query | Database | Hits | Screened (title + venue) | Kept as candidates |
|---|---|---|---|---|
| Q1 | IEEE Xplore | 7 | 7 | 3 (MoVES CI/CD; DO-178C lean MBD; Haghighatkhah 2017 as background) |
| Q1 | Scopus (TITLE-ABS-KEY, PUBYEAR > 2014) | 11 | 10 (page 2 did not load) | 3 new (Simulink DevOps SAE 2026; virtual-ECU SILS for SDV KSAE 2026; Artshop MBEES 2016) |
| Q2 | IEEE Xplore | 253 | first 50 | 4 (agile MBD ICSA-C 2018; MBD + ISO 26262 ECU ICECET 2023; "Waterfall is too slow" ICCAD 2018; RoHo-ASI SDV 2025) |
| Q3 | IEEE Xplore | 29 | 29 | 6 (DevOps for HIL IV 2025; SIL virtual ECUs ETFA 2026; CI failures with HIL ISSREW 2022; CI/CD in 20 OSS CPS MSR 2022; CI of HIL firmware tests PCIM 2023; IECON 2024 CPS validation) |
| Q4 | IEEE Xplore | 182 | first 50 | 5 (SIMULTATE 2016; MUT4SLX 2023; Simulink fault injection ASE 2025; timed Simulink mutation operators 2024; **ISIE 2025 AUTOSAR fault injection**) |
| Q5 | IEEE Xplore | 2 | 2 | 1 (batch testing, IEEE TSE) |

Notes on the runs:
- Q2 is noisy: "SAFe" appears to match "safe" (most hits are pure functional-safety hardware papers). Rerun without SAFe if Q2 matters.
- Q2 and Q4 were screened only on the first 50 of 253 and 182 results (sorted by relevance). Not exhaustive.
- Scopus Q2–Q5 not run. IEEE abstract retrieval was rate-limited (HTTP 420) after three documents, and
  OpenAlex returned HTTP 429; scripted retrieval was stopped. Remaining abstracts must be read by hand.
- Abstract-level reading done for: MoVES CI/CD, DO-178C lean MBD, agile MBD ICSA-C 2018, MBD + ISO 26262
  ECU, CI failures with HIL, Simulink DevOps SAE 2026, batch testing TSE. Everything else is title-level only.

Not searched yet: SAE Mobilus directly, ACM DL, Springer (MBEES, Software and Systems Modeling), arXiv.
Grey literature (MathWorks, dSPACE white papers) deliberately not used as evidence.
