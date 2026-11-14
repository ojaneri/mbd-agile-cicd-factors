# Git history rewrite, 2026-11-14

At the owner's request, `docs/labs-from-server/` (notes from other projects with the first author's institutional e-mail, IoT-LAB login and server paths; no passwords, tokens or keys) was removed from every commit with `git filter-branch --index-filter` and `main` was force-pushed. File contents and author/commit dates are unchanged; only the hashes changed. Memory files and the paper's threats section refer to the old hashes: use this table to translate them. The pre-rewrite history was kept locally as a git bundle outside the repository.

| old | new | date | subject |
|---|---|---|---|
| `e397dba` | `e397dba` | 2026-11-10 | chore: add article-docs memory and pre-register experiment protocol (E0-E4) |
| `e09e466` | `e09e466` | 2026-11-10 | feat: accept title, add verified MBD toolchain smoke test |
| `40a2eb2` | `40a2eb2` | 2026-11-10 | docs: record first literature search and dataset provenance |
| `9e0e286` | `9e0e286` | 2026-11-10 | docs: read closest predecessors and record venue exemplar |
| `d878460` | `d878460` | 2026-11-10 | docs: record co-author and self-citation rules |
| `40a4064` | `64816c3` | 2026-11-10 | exp: freeze subject-1 E1 protocol before any mutant run |
| `03f768f` | `56c59e9` | 2026-11-10 | exp: E1 subject-1 results (QEMU PIL), real-target PIL harness, E2 pre-registration |
| `d7f8239` | `963a9e2` | 2026-11-10 | exp: freeze subject-2 (fuel-flow sensor) E1 protocol before any mutant run |
| `ed79253` | `2994687` | 2026-11-11 | exp: E1 real-board PIL for both subjects, E2 replay, revised thesis and RQs |
| `df154a4` | `8d73f66` | 2026-11-11 | exp: freeze E5 (platform sensitivity, tiered pipeline) and subject 3 before any E5 run |
| `dd254ab` | `e515822` | 2026-11-11 | exp: E5 results (platform sensitivity) and subject 3 E1 campaign |
| `5f1f2e6` | `df6e93c` | 2026-11-11 | paper: manuscript draft v1 (IEEEtran, 5 of 6 pages) with verified bibliography |
| `d11bf25` | `b50683b` | 2026-11-11 | exp: freeze E5b robustness addendum (-O0/-Os, board timing noise, nRF52840 second board) before any run |
| `f6ec5b7` | `721b291` | 2026-11-11 | exp+paper: validation round (number audit, E2 sweep, Valgrind cause, equivalent mutants, E5b) and Fig. 2 |
| `9523025` | `78f62b7` | 2026-11-13 | paper+memory: virtual review r1 and its fixes (abstract, Agile framing, suite split, filled placeholders) |
| `0bb36c4` | `55c700a` | 2026-11-13 | paper+memory: virtual review r2 and r3, r2 wording package, final author block and acknowledgment |
| `84887b2` | `93fbb2b` | 2026-11-13 | chore: drop LaTeX build files of the r3 report |
| `811b1f1` | `fd96ff6` | 2026-11-14 | paper+memory: new title, r4 review, AI acknowledgment, r3+r4 wording package and suite figure |
| `c939244` | `3f2e000` | 2026-11-14 | paper+memory: virtual review r5 and its wording package |
| `941da51` | `62fddd5` | 2026-11-14 | chore: remove docs/labs-from-server; record the new Overleaf project |
