# C1 — Cadence and trigger set when a defect is found; the stage set sets what is found

Statement (revised, d-0011, proposed): MBD stages, integration cadence and release automation act on separate axes. Which stages run determines which defects are detected; batch size and trigger determine how long detection takes, and the computing cost of the stages is small next to that wait unless real-board PIL runs on every commit.

Original statement (pre-registered, not measured as such): a combined MBD + Agile + CI/CD process shortens lead time compared with each method applied alone. Not testable in this design: no arm applies one method "alone" with a team.

Evidence today (E2 replay, both subjects, real-board PIL cost, 2026-11-11): A3 automated, 1 commit per run, latency under 1 min (57 s and 22 s); 10 commits per run, about 9 h; a manual 8 h gate adds 8 h. Real-board PIL multiplies compute per sprint by 18.7 (subject 1) and 6.1 (subject 2) over A2. Detection is unchanged by cadence.

**Weakness to state in the paper:** latency in the replay follows largely from the assumed commit spacing (2 h) and gate delay, so the measured content is the stage costs and the verdicts; the "9 h" is a model output. Needs a sensitivity sweep on the commit interval (t-0043) or a real commit history (t-0019).

Would falsify it: stage cost exceeding the cadence wait at realistic commit intervals, or cadence changing what is detected (defects masking each other, which the replay assumes away).

Planned measurement: lead time per increment, feedback latency, localisation effort and escape rate, across integration cadences. Design in [[experiments/e2-integration-cadence]] (paired factorial, two subjects from `D:\artigos\genai-mbd-exp`). Note: "HIL" above becomes PIL per d-0006, and "Agile" means integration cadence per d-0003.

Used in: [[sections/abstract]]. Venue: [[venue/isie-2027]].

## Decisions
- **[#d-0002]** date: 2026-11-10 · status: proposed · author: osvaldo
  **Frame C1 as a measured comparison, not a general claim.** Why: the sources are qualitative; a reviewer will ask for numbers. Rejected: stating the gain without measurement, because it is the first thing an ISIE reviewer would reject. Cost: a case study is needed in about 5 weeks.

## Todos
- **[#t-0043]** status: open · author: osvaldo — Add a sensitivity sweep on DT_COMMIT and P_DEFECT to `e2.py`, labelled as added after run 1.
- **[#t-0006]** status: open · author: osvaldo — Choose the case study (ECU/ADAS model, or a non-automotive proxy) and confirm it can be run in the time left.
- **[#t-0007]** status: open · author: osvaldo — Define how lead time and defect escape are measured before any run.
