# Number audit: manuscript/main.tex (draft v1)

Date: 2026-11-11. Scope: every number in the abstract, text, Tables I–III, captions and the Fig. 2 sentence,
compared with the raw results under `testbed/`. Nothing in `main.tex` or `testbed/` was changed.
To recompute: `python manuscript/audit/check_numbers.py`. It reads raw records only. The E2 replay is
re-simulated in memory with `testbed/<s>/e2.py` and reproduces the stored medians exactly, and no file
is written.

Status key: **OK** means the value matches, or matches after normal rounding. **ROUNDING** means the
value is loose or approximate but defensible, with a note. **MISMATCH** means the value or claim is
contradicted by the data. **NO SOURCE** means no file in this repository records the value.

Counts: **OK 109 · ROUNDING 3 · MISMATCH 2 · NO SOURCE 3** (117 rows).

## Table

| # | Location (line) | As written | Source | Recomputed | Status |
|---|---|---|---|---|---|
| 1 | Abstract L30 | 205 mutants | e1_qemu.jsonl S1+S2 live | 130+75 = 205 | OK |
| 2 | Abstract L30 | 102 field-relevant | board field oracle, e1_pil_iotnode | 68+34 = 102 | OK |
| 3 | Abstract L31 | 38–68 % | A0 / field-relevant | 38.2 %, 67.6 % | OK |
| 4 | Abstract L32 | 100 % | A2 S1, S2 | 68/68, 34/34 | OK |
| 5 | Abstract L32 | CI lower bounds 90–95 % | Wilson | 89.85 %, 94.65 % | OK |
| 6 | Abstract L33 | under a minute | e1_qemu_e2.json A3\|b1\|auto latency | S1 56.5 s, S2 22.2 s | OK |
| 7 | Abstract L34 | about 9 h | A2/A3 b10 auto latency | 9.00–9.34 h | OK |
| 8 | Abstract L34 | 6 to 19 | compute A3 b1 / A2 b1 | 6.11 (S2), 18.69 (S1) | OK |
| 9 | Abstract L36 | 84 of 84 | e5_bess.jsonl CONTROL pass 0 | 84/84 | OK |
| 10 | Abstract L36 | 26 of 26 | e5 qemu / msan detected | 26/26 | OK |
| 11 | Abstract L37 | Valgrind missed one | e5 host_valgrind | E5-SOC-LUD-04 | OK |
| 12 | Abstract L41 | 397 s to 77 s | e5_bess_tiered.json A3b, AT compute | 396.69, 77.11 | OK |
| 13 | Intro L82 | three subjects | soc, fuel, bess | 3 | OK |
| 14 | Intro L83 | 205 mutants | as #1 | 205 | OK |
| 15 | Related L93 | two use cases | references/predecessors.md P1 | brake-by-wire, wiper | OK |
| 16 | Related L100 | six virtual ECUs | predecessors.md P3 | 6 V-ECUs | OK |
| 17 | Related L109 | November 2026 search | e0 t-0010, search-log-2026-11.md | 2026-11-11 | OK |
| 18 | Pipeline L146 | OpenModelica 1.27.2 | protocol READMEs | 1.27.2 | OK |
| 19 | Pipeline L148 | gcc 15.2 | none in repo | WSL `gcc --version` = 15.2.0 | NO SOURCE |
| 20 | Pipeline L149 | arm-none-eabi-gcc 14.2.1 | e0 note | 14.2.1 | OK |
| 21 | Pipeline L151 | budget twice baseline max | soc/protocol README, calibration_iotnode | 107 → 214 | OK |
| 22 | Pipeline L151–152 | STM32L475VG, 16 MHz, 0 wait states | harness/stm32l4/board.h | same | OK |
| 23 | Pipeline L153 | QEMU 10.2.1 | experiments/labs-access.md | 10.2.1 | OK |
| 24 | Subjects L158 | 11-knot OCV, 1 s | soc README | 11, 1 s | OK |
| 25 | Subjects L159 | 25 °C | soc README | 25 degC | OK |
| 26 | Subjects L160 | four held-out cycles | soc README | Mixed5–8 | OK |
| 27 | Subjects L160 | 2012 passenger car | e0 note | 2012 Opel Corsa | OK |
| 28 | Subjects L162 | five tanks, 2 pp | fuel README | tanks 18–22, 2.0 pp | OK |
| 29 | Subjects L165 | RMSE 0.458 vs 0.449; 1 °C | bess/spec/identification.json; bess README | 0.4578, 0.4490; 1 °C | OK |
| 30 | Subjects L166 | 7, 4, 5 requirements | READMEs REQ-1..7/1..4/1..5 | 7, 4, 5 | OK |
| 31 | Defects L174 | 130, 75, 93 live | e1_qemu.jsonl, bess analysis | 130, 75, 93 | OK |
| 32 | Defects L175 | 68, 34 field-relevant | board field oracle | 68, 34 | OK |
| 33 | Replay L180 | 10 commits, 2 h, 0.3 | e2 params | N 10, 2.0 h, 0.3 | OK |
| 34 | Replay L182 | b ∈ {1,5,10} | e2.py BATCH | (1,5,10) | OK |
| 35 | Replay L183 | 8 h; 1, 8, 24 h | e2.py TRIGGER | 1/8/24 h | OK |
| 36 | Replay L184 | 2000 replays | params R | 2000 | OK |
| 37 | Replay L188 | AMD Ryzen 5 5500 | not recorded in this project. The only mention is docs/labs-from-server (another paper) | — | NO SOURCE |
| 38 | Table I S1 | det. 26/52/68/68 | recomputed from raw (board PIL) | 26/52/68/68 | OK |
| 39 | Table I S1 | CI 28–50, 65–85, 95–100, 95–100 | Wilson | 27.6–50.1, 65.1–85.0, 94.7–100 | OK |
| 40 | Table I S1 | p 3.0×10⁻⁸ | exact McNemar 26/0 | 2.98e-8 | OK |
| 41 | Table I S1 | p 3.1×10⁻⁵ | exact McNemar 16/0 | 3.05e-5 | OK |
| 42 | Table I S1 | p 1 (A3) | 0/0 | 1 | OK |
| 43 | Table I S2 | det. 23/34/34/34 | raw | 23/34/34/34 | OK |
| 44 | Table I S2 | CI 51–81, 90–100 | Wilson | 50.8–80.9, 89.8–100 | OK |
| 45 | Table I S2 | p 0.001 | McNemar 11/0 | 0.00098 | OK |
| 46 | Table I S2 | p 1, 1 | 0/0 | 1, 1 | OK |
| 47 | Table I footnote | UNIT 0.29 s | soc calibration.json median (= e2 stage_cost) | 0.287 | OK |
| 48 | Table I footnote | MIL 2.45 s | same | 2.450 | OK |
| 49 | Table I footnote | SIL 0.29 s | same | 0.286 | OK |
| 50 | Table I footnote | board PIL 53.5 s | calibration_iotnode median build+flash+run | 53.48 | OK |
| 51 | Table I footnote | S2 18.5 s | fuel calibration_iotnode | 18.55 | OK |
| 52 | RQ1 L218 | 38 %, 68 % | A0 rates | 38.2, 67.6 | OK |
| 53 | RQ1 L220 | 16 code-level added by SIL | first detection at SIL | 16, all code-level | OK |
| 54 | RQ1 L221–223 | 100 %; audit | field-relevant code mutants failing a requirement test at SIL | 42/42 | OK |
| 55 | RQ1 L229 | SIL alone all 68 | sil.passed on field-relevant | 68/68 | OK |
| 56 | RQ1 L229 | about one eighth of MIL's cost | SIL/MIL calibration medians | 0.286/2.450 = 0.117 (≈1/8.6) | ROUNDING |
| 57 | RQ1 L231 | 5 (S1), 6 (S2) timing | board PIL-only with timing fails | 5, 6 | OK |
| 58 | RQ1 L233 | 21 non-field-relevant flagged | raw, board or QEMU PIL | 21 | OK |
| 59 | RQ1 L234 | 41 flagged by no stage | raw | 41 | OK |
| 60 | Platform L237 | 202 of 205 | QEMU vs board PIL verdicts | 128+74 = 202 | OK |
| 61 | Platform L238 | Wilson 95.8–99.5 % | Wilson 202/205 | 95.79–99.50 | OK |
| 62 | Platform L239 | 3 of 6 vs 0 of 199 | init deletions S1 SDL-005..008, S2 SDL-001..002 | 3/6, 0/199 | OK |
| 63 | Platform L239 | Fisher p = 1.4×10⁻⁵ | two-sided Fisher | 1.41e-5 | OK |
| 64 | Platform L240 | two swapped in S1 | SDL-006 board-only, SDL-007 QEMU-only | yes | OK |
| 65 | Table II A2 b1 S1 | 3 s / 36 s | e1_qemu_e2 summary median | 3.0 s / 36.3 s | OK |
| 66 | Table II A2 b1 S2 | 4 s / 44 s | same | 3.6 s / 43.6 s | OK |
| 67 | Table II A2 b10 S1 | 9.0 h / 30 s | same | 9.00 h / 30.2 s | OK |
| 68 | Table II A2 b10 S2 | 9.2 h / 36 s | same | 9.20 h / 36.3 s | OK |
| 69 | Table II A3 b1 S1 | 57 s / 678 s | same | 56.5 s / 678.0 s | OK |
| 70 | Table II A3 b1 S2 | 22 s / 266 s | same | 22.2 s / 266.1 s | OK |
| 71 | Table II A3 b5 S1 | 4.0 h / 509 s | same | 4.02 h / 508.5 s | OK |
| 72 | Table II A3 b5 S2 | 4.0 h / 222 s | same | 4.01 h / 221.8 s | OK |
| 73 | Table II A3 b10 S1 | 9.0 h / 565 s | same | 9.02 h / 565.0 s | OK |
| 74 | Table II A3 b10 S2 | 9.3 h / 222 s | same | 9.34 h / 221.8 s | OK |
| 75 | RQ2 L270–271 | within a minute; about 9 h | as #6, #7 | yes | OK |
| 76 | RQ2 L274 | δ −0.97 latency | cliffs_delta | −0.969 (S1), −0.968 (S2) | OK |
| 77 | RQ2 L274 | δ +0.32 compute | cliffs_delta | +0.324 (S1); S2 +0.157 | OK (S1 only, see W3) |
| 78 | RQ2 L275 | from A1 on, no defect escaped in any configuration | re-simulated per-replay escapes | S1 A1: 642/2000 sprints had ≥1 escape (max 3), at every batch size. Only the median is 0. S2 A1 and A2+ in both: 0 | **MISMATCH** |
| 79 | RQ2 L275 | S1 at A0: one escape per sprint, median | summary A0 escapes | 1 (S2 A0 median 0) | OK |
| 80 | RQ2 L277 | 18.7 (S1), 6.1 (S2) | 678.0/36.3, 266.1/43.6 | 18.69, 6.11 | OK |
| 81 | RQ2 L272 | gate adds its delay | A3 b1 manual − auto | +1.0, +8.0, +24.0 h | OK |
| 82 | RQ3 L284–287 | b-l475e-iot01a; 5 passes; 4 patterns; two resets | e5 protocol README | same | OK (see W5) |
| 83 | RQ3 L288 | clang 21 | none in repo | WSL `clang --version` = 21.1.8 | NO SOURCE |
| 84 | RQ3 L290 | 28, 26 observable, 19 unseen | e5 records | 28 (11 INIT + 17 LUD), 26, 19 | OK |
| 85 | RQ3 L291 | single-cycle (ALU), 14-cycle (divide) | e5 protocol (n = round(f·B/14)); measured st_max | ALU +cycles ≈ n. DIV level 3.0: 346/23 = 15.0, 391/26 = 15.0, 423/28 = 15.1 cycles per added division (loop overhead included) | ROUNDING |
| 86 | RQ3 L292 | 0.25 to 3.0 × baseline | e5 mutants levels | 0.25…3.0 | OK |
| 87 | RQ3 L293 | 84 of 93 | e5_control_bess.json | 93 − 5 init − 4 duplicates = 84 | OK |
| 88 | RQ3 L294 | Wilson lower bound ≥ 0.95 | analyze_e5 rule | same | OK |
| 89 | Table III Host SIL | 22, 66–94, 18, 0.29 s | e5 records / e5_analysis | 22, 66.5–93.9, 18, 0.289 | OK |
| 90 | Table III poisoned | 25, 81–99, 18, 1.12 s | same | 25, 81.1–99.3, 18, 1.118 | OK |
| 91 | Table III Valgrind | 25, 81–99, 18, 3.13 s | same | 25, 81.1–99.3, 18, 3.128 | OK |
| 92 | Table III MSan | 26, 87–100, 19, 0.34 s | same | 26, 87.1–100, 19, 0.342 | OK |
| 93 | Table III QEMU | 26, 87–100, 19, 1.91 s | same | 26, 87.1–100, 19, 1.913 | OK |
| 94 | Table III Board | 26, 87–100, 19, 135 s | same | 26, 87.1–100, 19, 135.47 | OK |
| 95 | Table III caption | 26 observable, 19 unseen | same | 26, 19 | OK |
| 96 | RQ3 L319 | 552 records valid | e5_*.jsonl | 150+108+294 = 552, all valid | OK |
| 97 | RQ3 L320 | 84 of 84; 95.6–100 % | control pass-0 agreement | 84/84; 95.63–100 | OK |
| 98 | RQ3 L321 | 25 of 26 without painting | detect_p0 qemu/board | 25, 25 | OK |
| 99 | RQ3 L326 | MSan all 26, 0.34 s, ~400× less than board | 135.47/0.342 | 396× | OK |
| 100 | RQ3 L328 | 16 of 17 (LUD, poison) | host_poison by family | 16/17 (INIT 9/9) | OK |
| 101 | RQ3 L329 | plain SIL 22 of 26 | host_sil | 22/26 | OK |
| 102 | H4 L341 | board flags 1.1, 1.5, 3.0 (+0.9 in S2); QEMU none | st_max > budget, recomputed | same | OK |
| 103 | H4 L342 | 28 divisions ≈ 400 cycles, count as 28 instructions | e5_mutants_bess DIV-06 n = 28; st_max | S3 only: +423 cycles, +30 ticks. S1: 23 div, +346 cycles, +26 ticks. S2: 26 div, +391, +29 | ROUNDING (see W4) |
| 104 | H4 L343 | QEMU one level more (0.9) in all three | recomputed flags | 0.9 in soc, fuel, bess | OK |
| 105 | H4 L344–345 | ~1.6 CPI; 107 cycles, 68 instructions | calibration_soc.json | 107/68 = 1.57 | OK |
| 106 | Fig. 2 sentence L348 | S1 ALU 0.9: 0.95 board, 1.22 QEMU | 204/214, 166/136 | 0.953, 1.221 | OK |
| 107 | Fig. 2 sentence L348–349 | S1 DIV 3.0: 2.12 board, 0.69 QEMU | 453/214, 94/136 | 2.117, 0.691 | OK |
| 108 | Tiered L352 | UNIT 0.29, MIL 2.49, SIL 0.28, QEMU 0.86, board 30.0 s | e5_bess_tiered cost_s | 0.286, 2.494, 0.282, 0.864, 29.995 | OK |
| 109 | Tiered L353–354 | board alone 0; zero escapes | board_only_defects, escapes | 0; 0 | OK |
| 110 | Tiered L355 | A2 36.8 s | A2\|auto compute_s | **36.7498 → 36.7** | **MISMATCH** |
| 111 | Tiered L355 | A3q 47.1 s | same | 47.116 | OK |
| 112 | Tiered L355 | AT 77.1 s | same | 77.111 | OK |
| 113 | Tiered L355 | A3b 396.7 s | same | 396.692 | OK |
| 114 | Tiered L355–356 | Cliff's δ AT vs A3b −1.0 | cliffs_delta | −1.0 | OK |
| 115 | Tiered L356 | latency 4 s (AT, A3q), 33 s (A3b) | latency_h × 3600 | 3.93, 3.93, 33.06 | OK |
| 116 | Conclusion L398 | 205 injected defects | as #1 | 205 | OK |
| 117 | Conclusion L402–403 | about a fifth of per-commit board compute | 77.11/396.69 | 0.194 | OK |

## MISMATCH and NO SOURCE, with suggested corrections (not applied)

1. **#78, L275, MISMATCH.** The draft says "from A1 on, no defect escaped in any configuration". The
   data say otherwise for S1 at A1: 642 of 2000 replayed sprints had at least one field-relevant escape
   (max 3), at every batch size. A1 detects only 52/68 in S1, so escapes are expected. Only the
   median is 0. Suggested text: "from A2 on, no defect escaped in any replay (at A1, S1 let at least one
   defect escape in 642 of 2000 sprints; S1 at A0: one escape per sprint, median)". The memory note
   `e2-integration-cadence.md` ("A1 and up, 0") needs the same qualifier.
2. **#110, L355, MISMATCH (rounding).** A2 compute is 36.7498 s, which rounds to **36.7 s**, not 36.8 s.
   The memory note `e5-platform-sensitivity.md` repeats 36.8.
3. **#19, L148, NO SOURCE.** gcc 15.2. The installed WSL compiler is 15.2.0, but no file in the repo
   records it. Record it in e0 or the skill `testbed-toolchain-smoke`, or in a results header.
4. **#83, L288, NO SOURCE.** clang 21. Installed: Ubuntu clang 21.1.8. Not recorded in the repo. Record it
   as in item 3.
5. **#37, L188, NO SOURCE.** AMD Ryzen 5 5500 under WSL Ubuntu. The only record is in another project's lab
   note (`docs/labs-from-server/ieee-its-xai-sdv-explain__labs-and-equipment.md`). Add the host spec to
   e0 or `labs-access.md`. (e0 also says "WSL Ubuntu 26.04", which the manuscript does not state.)

## Wording stronger than the data, or imprecise

- **W1 (#78)**: "no defect escaped in any configuration". See item 1 above.
- **W2, Abstract L32–33 "PIL added no functional detection"; L221 "PIL added none".** On the board, S1
  SDL-006 was a functional failure (T2 and back-to-back) that only PIL flagged. It is not
  field-relevant, so the statements hold only for field-relevant mutants. Suggested text: "PIL added no
  detection of field-relevant mutants". The L277 phrase "bought no functional detection" refers to
  escapes and is fine.
- **W3, L274**: the Cliff's δ of +0.32 for compute is S1 only (S2 +0.16). Write "(S1; S2: −0.97 and +0.16)",
  or say "S1".
- **W4, L342**: "28 divisions cost about 400 cycles but count as 28 instructions" holds only for S3
  (+423 cycles, +30 ticks). The next sentence and Fig. 2 use S1, where the 3.0 level has 23 divisions
  (+346 cycles, +26 ticks). Suggested text: "in S3, the 28 divisions of the 3.0 level add 423 cycles but
  only 30 ticks".
- **W5, L287**: "the board run is repeated after two resets". The protocol specifies 2 captures (2 resets)
  in total, so the board ran twice, each run after a reset. The current wording can be read as three
  runs. Suggested text: "the board run is made twice, each after a reset".
- **W6, Table I footnote**: the times are medians of the 10 baseline calibration runs (the values E2
  uses), not of the mutant runs. Over mutant runs, S1 MIL is 2.52 s and board PIL is 53.6 s. Consider
  "median baseline wall time per run".
- **W7, L291 "14-cycle (divide)"**: 14 is the protocol's design constant for sizing the ladder. The measured
  increment is about 15 cycles per added division. Acceptable, but say "about 14".
- Checked and found sound: "every field-relevant code mutant failed a requirement test at SIL" (42/42 in S1,
  23/23 in S2). "SIL ... detected everything MIL detected" (no mutant fails MIL and passes SIL in any of
  the three subjects). "No control mutant was caught by the board alone" (0). "nor the reverse" for H2
  (0 QEMU-only). "with the same binary an emulator reproduced every functional verdict of the board"
  (E5: control 84/84; INIT/LUD 0 disagreements).
