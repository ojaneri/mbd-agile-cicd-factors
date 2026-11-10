# C1 — Integrating MBD, Agile and CI/CD shortens the feature-to-release cycle

Statement: A combined process (MBD for models and MIL/SIL/HIL validation, Agile for backlog and sprints, CI/CD for build, test and OTA release) reduces the lead time from feature to validated release, compared with each method applied alone.

Evidence today: **none measured.** The infographics and the literature read so far are qualitative.

Would falsify it: equal or longer lead time for the integrated flow on the same feature set and team, or no drop in defects escaping to HIL.

Planned measurement: lead time per increment, feedback latency, localisation effort and escape rate, across integration cadences. Design in [[experiments/e2-integration-cadence]] (paired factorial, two subjects from `D:\artigos\genai-mbd-exp`). Note: "HIL" above becomes PIL per d-0006, and "Agile" means integration cadence per d-0003.

Used in: [[sections/abstract]]. Venue: [[venue/isie-2027]].

## Decisions
- **[#d-0002]** date: 2026-11-10 · status: proposed · author: osvaldo
  **Frame C1 as a measured comparison, not a general claim.** Why: the sources are qualitative; a reviewer will ask for numbers. Rejected: stating the gain without measurement, because it is the first thing an ISIE reviewer would reject. Cost: a case study is needed in about 5 weeks.

## Todos
- **[#t-0006]** status: open · author: osvaldo — Choose the case study (ECU/ADAS model, or a non-automotive proxy) and confirm it can be run in the time left.
- **[#t-0007]** status: open · author: osvaldo — Define how lead time and defect escape are measured before any run.
