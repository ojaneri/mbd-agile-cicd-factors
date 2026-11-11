# ARTICLE-MEMORY — cicd-mbd-agile

Human-readable index of this article's durable memory.

## What this is
Comparative paper on Model-Based Design (MBD), Agile and CI/CD for automotive embedded and
Software-Defined Vehicle (SDV) development, proposing an integrated four-stage flow with
feedback loops. Target: IEEE ISIE 2027 (regular paper, 6 pages, IEEE two-column).
State: **E1, E2 (two subjects) and E5 (three subjects, confirmatory) run; manuscript draft v1 in `manuscript/` (5 of 6 pages).** Thesis under
revision (d-0011, proposed): stages set what is caught, cadence and trigger set when, the platform sets where.

## Memory map
| Area | File |
|------|------|
| Manuscript sections | `sections/` |
| Claims and hypotheses | `claims/` |
| Experiments and data | `experiments/` |
| Venue, format and deadlines | `venue/` |
| Bibliography | `references/` |
| Reviewer reports and rebuttals | `reviews/` |
| Procedures (build, figures, analysis) | `skills/skills.jsonl` |
| Authors & ownership | `identity/ownership.md` |
| Sessions | `sessions/` |
| Machine index | `index.jsonl` |

## Quick facts
- Title (accepted, d-0007): *MBD, Agile, or CI/CD? A Comparative Analysis and Integrated Pipeline for Automotive Embedded Systems*
- Venue: IEEE ISIE 2027. Regular paper deadline 2026-12-15. Track candidate: 06 (Industrial CPS), see `venue/isie-2027.md`.
- Authors: Osvaldo Janeri Filho (UTFPR) and Max Mauro Dias Santos (UTFPR-PG, advisor). Order and corresponding author not decided; see `identity/ownership.md`.
- Trap: the ISIE 2025 venue exemplar (doi 10.1109/ISIE62713.2025.11124734) is co-authored by the advisor. Citing it is self-citation; under double-anonymous review it must be cited in the third person.
- Source material from earlier work (not yet linked into this memory): `D:\artigos\genai-mbd-exp` (MBD/BESS data) and `D:\artigos\xai-sdv-artifact` (CAN intrusion XAI, OTA drift). Candidates for a case study, not decided.
- Framework source: `D:\artigos\article-docs-framework` (cloned from github.com/ojaneri/article-docs).
- Legacy hand-written notes kept at `D:\artigos\CICD\article-docs-legacy\` and folded into this structure. Delete only after the human agrees.
- Under git since 2026-11-10 (local only, no remote yet). Protocol pre-registered in commit e397dba.
- Testbed runs in WSL Ubuntu (default user root): see skill `testbed-toolchain-smoke`.
