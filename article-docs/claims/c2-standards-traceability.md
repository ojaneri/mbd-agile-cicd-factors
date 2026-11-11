# C2 — The integrated pipeline keeps ISO 26262 / ISO 21434 traceability

Statement: Model versioning, requirement links and signed release packages let the integrated pipeline produce the evidence that functional-safety and cybersecurity standards require, without slowing the OTA cadence.

Status (d-0011, proposed): **out of the main line**; future work unless the ISO texts are available by week 3. The abstract must not mention it.

Evidence today: **none.** No standards mapping written yet.

Would falsify it: a mandatory safety work product for each release cannot be generated automatically from the pipeline, so manual steps are needed on every release.

Planned measurement: a table mapping each pipeline stage to the work products it produces; count manual steps per release. Design in [[experiments/e3-traceability-evidence]].

Used in: [[sections/abstract]]. Venue: [[venue/isie-2027]].

## Todos
- **[#t-0008]** status: open · author: osvaldo — Build the standards mapping table (stage to work product) from ISO 26262 and ISO 21434 text, not from memory. Mark each entry as unverified until checked against the standard.
