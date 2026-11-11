# Manuscript — source, build and state of the draft

Source: `manuscript/main.tex` (IEEEtran conference) and `manuscript/refs.bib`. Build in WSL with
`bash /mnt/d/artigos/CICD/manuscript/build.sh` (latexmk; TeX Live with texlive-publishers, installed
2026-11-11). Draft v1 written 2026-11-11 and compiles to **5 of 6 pages**, so about 0.7 page is free.

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
| IV-D RQ3 | E5 design, H1–H4, Table III, the tiered replay | [[experiments/e5-platform-sensitivity]] |
| V Discussion | the answer to the title; practical placement; threats (construct, internal, external) | C1, C3, C4 |
| VI Conclusion | summary plus future work (real history, second board, ISO 26262 evidence) | — |

## Placeholders left in the text (must not be filled by guessing)
- Author block (order and corresponding author t-0037; anonymity t-0036).
- Repository URL and external timestamp of the pre-registration (t-0025).
- Kaggle dataset citation title/year (t-0049).
- The AI-use disclosure, if ISIE requires one (t-0036).

## Known weak points for review
- No recorded commit history: the RQ2 latency is a replay output (t-0019, t-0043).
- E2 bootstrap CIs are not reported in Table II because of t-0042; medians only.
- The Valgrind miss is reported without a cause (t-0048).
- Related work search did not cover ACM DL / SAE (t-0029); P1, P2 read at abstract level only (t-0034).

## Decisions
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
- **[#t-0049]** status: open · author: osvaldo — Check the dataset citations: Kaggle OBD-II title and year, and the LG HG2 author list (DataCite lists only M. Naguib; the Mendeley page lists four authors).
- **[#t-0050]** status: open · author: osvaldo — Use the free ~0.7 page: candidate figure is the H4 ladder (cycles on the board vs QEMU ticks per level), generated from `testbed/e5/results/`.
- **[#t-0051]** status: open · author: osvaldo — Run `/artdocs:virtual-review` on draft v1 and a humanizer pass on the prose before showing it to the co-author.
- **[#t-0052]** status: open · author: osvaldo — Co-author (Max Mauro Dias Santos) to read draft v1, in particular the reframed thesis (d-0011) and the self-citation of [9] (P8).
