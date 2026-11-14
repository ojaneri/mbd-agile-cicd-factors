# Manuscript — source, build and state of the draft

Source: `manuscript/main.tex` (IEEEtran conference) and `manuscript/refs.bib`. Build in WSL with
`bash /mnt/d/artigos/CICD/manuscript/build.sh` (latexmk; TeX Live with texlive-publishers, installed
2026-11-11). Draft v1 written 2026-11-11 and compiles to **5 of 6 pages**; with Fig. 2 about half a page
is free on p. 5. Fig. 2 is regenerated with `wsl -- /root/venvs/cicd/bin/python /mnt/d/artigos/CICD/manuscript/figs/fig_h4.py`
from `testbed/e5/results/e5_analysis.json` and the calibration budgets; never edit the PDF by hand.

## What each section argues and where its numbers come from
| Section | Argues | Evidence |
|---|---|---|
| Abstract | same text as [[sections/abstract]] v1 | C1, C3, C4 |
| I Introduction | the methods are turned into factors; RQ1–RQ3, RQ3 added after E1 and confirmed in E5; 4 contributions | [[experiments/e0-testbed-and-protocol]] |
| II Related Work | P1–P8 by what they measure; dated-search wording only, never "first" | [[references/predecessors]] |
| III Design | pipeline (Fig. 1), subjects S1–S3, mutants, factors, replay, statistics | E0, E1, E5, `testbed/*/protocol/README.md` |
| IV-A RQ1 | Table I; the A2 100 % audit; the SIL-alone result marked exploratory; timing-only counts | [[experiments/e1-defect-detection-by-stage]], [[claims/c3-stage-detection]] |
| IV-B | E1 platform disagreement 202/205, harness confound | E1, [[claims/c4-platform-tiering]] |
| IV-C RQ2 | Table II (medians from `testbed/{soc,fuel}/results/e1_qemu_e2.json`); latency is a model output | [[experiments/e2-integration-cadence]], [[claims/c1-integration-gain]] |
| IV-D RQ3 | E5 design, H1–H4, Table III, Fig. 2 (H4 ladders, step max / own budget), the tiered replay | [[experiments/e5-platform-sensitivity]] |
| V Discussion | the factors and what each changed; practical placement; threats (construct, internal, external) | C1, C3, C4 |
| VI Conclusion | summary plus future work (real history, second board, ISO 26262 evidence) | — |

## Placeholders left in the text
None since 2026-11-13. Filled from sources read that day: author block (ISIE page counts authors in the 6
pages and asks no anonymisation, t-0036 done; ORDER PROVISIONAL, d-0015, t-0037); repository URL (the repo is
public since 2026-11-13, verified unauthenticated via the GitHub API; t-0060 done); Kaggle reference (t-0049 done); AI-use acknowledgment (IEEE policy, wording d-0016).

## Validation round 2026-11-11 (after draft v1)
- Number audit (`manuscript/audit/number-audit.md`, rerun `python manuscript/audit/check_numbers.py`): 117 numbers,
  2 mismatches (A1 escapes, 36.8→36.7 s) and 5 over-strong wordings, all fixed in main.tex; 3 unsourced versions
  now recorded in E0.
- E2 sweep and CI fix (E2 Robustness), Valgrind cause (E5 t-0048), equivalent-mutant screening (E1), added to the
  text as post-run analyses.
- E5b (second board nRF52840, -O0/-Os, timing noise): run 2026-11-11/12, all rules supported; in IV-D
  "Robustness (addendum)", abstract, discussion, threats and conclusion. The paper is now **6 of 6 pages**.

## Humanizer pass 2026-11-12
Prose only, no number changed, still 6 of 6 pages: the abstract's long parenthetical split into sentences;
a duplicated RQ1 sentence ("No field-relevant mutant escaped from A2") cut; "What is true by construction"
and "pure cost" rewritten as plain statements; the addendum's "a reviewer may ask about" replaced by the
three things it varies; the Discussion's repeated "only on the production board" kept once (Practical
placement); the conclusion's run-on sentence split; Fig. 2 caption no longer names the internal "E5".

## Virtual review r1 fixes 2026-11-13 (`reviews/virtual/2026-11-12-r1.md`)
- RQ1 split by test suite (exploratory, `testbed/e1_decompose.py` -> `e1_decompose.json`, re-analysis of E1
  records): on host C the requirement tests caught 68/68 (S1) and 34/34 (S2) field-relevant mutants, the unit
  tests 26 and 23; unit tests caught 0 model-level mutants because their expectations are generated from the
  (mutated) spec. Unit suites: 6 checks (S1), 4 (S2); gcov on the baseline (`testbed/e1_unit_coverage.sh`,
  output `e1_unit_coverage.txt`): lines 97.4 % / 100 %, branches taken 83.3 % / 100 %.
- Text: abstract rewritten (228 words; Agile as increment size, suite > stage, no-masking replay, latency at an
  assumed 2 h spacing; tiered 397->77 s dropped from the abstract); intro reframes Agile with the Agile
  Manifesto principle (agilemanifesto, read 2026-11-13); RQ1 asks about stage and suite; "pre-registered"
  for RQ1/RQ2 replaced by "committed before their runs (locally)"; III states parallel model/code generation
  (no translation faults), unit-suite size and spec-derived expectations, S1 field-oracle thresholds
  (+0.005 RMSE, +0.02 max, from soc/protocol/README.md), the no-masking assumption, what the Wilson CIs cover;
  IV-A suite split; IV-C no-masking wording, Cliff's delta on latency dropped, A0 escape is S1's, sweep 36-37 h;
  tiered "not tested on the class it exists for"; nRF "fewer levels on 4 of 6 ladders"; Discussion answer
  reworded; threats add translation faults, one team wrote tests and oracles, no-masking; "both without
  cache" replaced (STM32L4 cache state unsourced, t-0057); conclusion rewritten; MIL/SIL/PIL/HIL expanded.
- Lint: gate open (S0 0, S1 0); 6 of 6 pages.

## Known weak points for review
- No recorded commit history: the RQ2 latency is a replay output (t-0019, t-0043).
- Table II still shows medians only; order-statistic CIs now exist in `testbed/e2_sweep.json` (t-0042 done).
- The Valgrind miss is now explained in the text (t-0048 done).
- Related work search did not cover ACM DL / SAE (t-0029); P1, P2 read at abstract level only (t-0034).

## Decisions
- **[#d-0015]** date: 2026-11-13 · status: proposed · author: osvaldo
  **Author block filled provisionally as "Osvaldo Janeri Filho and Max Mauro Dias Santos", UTFPR, no e-mails.**
  Why: the venue is not anonymous (t-0036) and a placeholder blocks submission. Order and corresponding
  author are still to be agreed with the co-author (t-0037); change the block if they differ.
  Update 2026-11-13: the first author gave the block: Osvaldo Janeri Filho, Max Mauro Dias Santos, Rafael
  Santos Dominguez, Jeferson José de Lima (in this order), with ORCIDs; affiliation Department of Electronics,
  UTFPR-PG (the source gave no affiliation mark for Rafael; João Francisco Justo, in the source block, was not in
  the requested list and is not included). Applied in main.tex; IEEE membership grades omitted (conference style).
  Update 2026-11-14: the owner moved the paper to a new Overleaf project, 6af7caef9184bd0d4133de43 ("forget the
  old one"); the co-authors will work from it. It held a copy from 2026-11-13 with two edits not in the repo:
  author order Osvaldo, Rafael, Jeferson, Max, and a section-roadmap paragraph at the end of the Introduction.
  At the owner's instruction ("pode sobreescrever totalmente") it was overwritten with commit c939244 (order
  Osvaldo, Max, Rafael, Jeferson; no roadmap); 6 pages on Overleaf. If that order change was intended, it has
  to be redone in main.tex (the roadmap costs about 10 lines; one sentence fits only with cuts elsewhere).
  From now on co-author edits arrive on Overleaf first: fetch and compare before any upload.
- **[#d-0016]** date: 2026-11-13 · status: proposed · author: osvaldo
  **AI-use acknowledgment: "The authors used Claude (Anthropic), through Claude Code, to draft the text of all
  sections from the authors' results and notes, to write the experiment and analysis scripts, and to check
  numbers and references against the data and bibliographic records."** Why: IEEE requires naming the system,
  sections and level of use in the acknowledgments. The authors confirm the wording matches their use.
  Update 2026-11-13: replaced by the first author's text (UTFPR-PG thanks; "Generative AI (Anthropic) was used,
  under the direction of the authors, to check and revise text in all sections … to generate and run the
  simulation and analysis code, and for language editing. The authors reviewed and edited all content and take
  full responsibility for it."). Note for the authors: the drafts of the text were produced with the tool
  (sessions in this repo); confirm that "check and revise" describes that use under the IEEE policy.
  Update 2026-11-14: replaced by the first author's text after comparing five published disclosures: "Claude
  (Anthropic), used under the authors' direction, drafted the text from the authors' results and notes, helped
  to write and run the simulation and analysis code that produces the results, and was used for language
  editing. The authors reviewed and edited all content and take full responsibility for it." Only change by
  the lead: "helped to wrote and ran" → "helped to write and run" (grammar). Names the system and the drafting,
  so it addresses VR4-E-01; still 6 pages.
- **[#d-0012]** date: 2026-11-11 · status: proposed · author: osvaldo
  **Manuscript source lives in `manuscript/` as IEEEtran LaTeX, built with latexmk in WSL.**
  Why: ISIE requires the IEEE two-column template and PDF; LaTeX keeps tables generated from the
  testbed numbers under version control next to the scripts. Rejected Word (no diffable source) and
  Overleaf as primary (no remote yet, t-0025; it can mirror the folder later). Cost: co-authors need
  TeX Live or Overleaf to build.
- **[#d-0013]** date: 2026-11-11 · status: proposed · author: osvaldo
  **Report the E2 replay as medians only (no CI) in Table II until t-0042 is fixed, and state in the text
  that latency is a model output.** Why: the percentile bootstrap gave a median outside its CI on discrete
  data. Rejected printing those CIs. Cost: Table II carries no uncertainty for now.

## Todos
- **[#t-0060]** status: done · author: osvaldo — The repository cited in main.tex (github.com/ojaneri/cicd-mbd-agile) is private: make it public, or archive a snapshot on Zenodo and cite its DOI, before submission (2026-12-15). Outward-facing: the owner decides.
- **[#t-0049]** status: done · author: osvaldo — Check the dataset citations (virtual review r1, 2026-11-12: Kaggle record shows title "OBD2_panel_opel_2012", creator "Pedro" (handle pedro2025), CC BY 4.0, v10 updated 2026-10-03; first-publication year still unread): Kaggle OBD-II title and year, and the LG HG2 author list (DataCite lists only M. Naguib; the Mendeley page lists four authors).
- **[#t-0050]** status: done · author: osvaldo — Fig. 2 (H4 ladders) added 2026-11-11, from `manuscript/figs/fig_h4.py`; text cites S1 values 0.95/1.22 (ALU 0.9) and 2.12/0.69 (DIV 3.0).
- **[#t-0051]** status: done · author: osvaldo — Done 2026-11-12 (humanizer pass, then `reviews/virtual/2026-11-12-r1.md`). Original: Run `/artdocs:virtual-review` on draft v1 and a humanizer pass on the prose before showing it to the co-author.
- **[#t-0052]** status: open · author: osvaldo — Co-author (Max Mauro Dias Santos) to read draft v1, in particular the reframed thesis (d-0011) and the self-citation of [9] (P8).
