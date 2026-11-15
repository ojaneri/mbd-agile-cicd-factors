# E5c — tiered placement on the timing class (exploratory re-analysis)

Status: designed 2026-11-15, after the E5 and E5b results were known; committed to git before it runs.
Labelled **exploratory** in the paper. No new run on any target: it re-reads existing E5/E5b records.

## Question
The tiered placement AT (host stages and QEMU PIL on every commit, board PIL once per sprint) was replayed in
E5 only on subject 3's control pool, which holds no board-only defect, so it was "not tested on the class it
exists for". E5c replays the same four placements on the multi-cycle timing class: does AT catch the timing
regressions that the board flags and the emulator misses, at what compute and latency, and how many false
alarms does per-commit QEMU timing raise?

## Pool and verdicts
- Pool per subject (soc, fuel, bess): the 12 timing-ladder mutants of E5 (6 ALU, 6 DIV levels 0.25–3.0),
  `results/e5_<subject>.jsonl`.
- UNIT, MIL, SIL: never flag timing (they measure no cycles). Checked in the script: every ladder's
  `host_sil` record must have `detected` = false, else the script aborts.
- QEMU PIL: flagged iff the level is in `e5_analysis.json` H4 `qemu_flags`.
- Board PIL (reference, primary): flagged iff the level is in H4 `board_flags` (STM32L475 st-iotnode).
- Secondary reference: the nRF52840 flags of E5b (`e5b_analysis.json` R4 H4n `nrf_flags`), as the board both
  for detection and for ground truth.
- Ground truth: a ladder level is a timing regression iff the reference board flags it.

## Replay
Same model and constants as `e2_tiered.py`: N = 10 commits per sprint, 2 h apart, each defective with
probability 0.3, the defect drawn uniformly from the subject's ladder pool; R = 2000; seed 20261111; automatic
trigger only. Placements:
- A2: UNIT+MIL+SIL per commit (no timing check);
- A3q: A2 + QEMU PIL per commit;
- A3b: A2 + board PIL per commit;
- AT: A3q per commit + one board run per sprint; a regression the board flags and QEMU missed is localised by
  bisection with ceil(log2 N) extra board runs, as in `e2_tiered.py`.
A QEMU flag on a level the reference does not flag is a **false alarm**: it costs one extra QEMU run
(investigation) and no latency.

## Costs
UNIT, MIL, SIL: medians of `testbed/<subject>/protocol/calibration.json` `cost_s`. QEMU and board: median
`wall_s` of the subject's ladder records on that arm (board = build + flash + capture), as in E5.

## Metrics
Per sprint: timing escapes (reference-flagged, not caught by the placement within the sprint), false alarms,
mean latency of caught regressions [h], compute [s]. Median and bootstrap 95 % CI over the 2000 sprints, per
subject and pooled over subjects. Pool counts reported: reference-flagged, QEMU-flagged, both.

## Output
`results/e5c_timing_tiered.json`, written by `e2_timing_tiered.py`.
