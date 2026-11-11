# ARTICLE-MEMORY — cicd-mbd-agile

Human-readable index of this article's durable memory.

## What this is
Comparative paper on Model-Based Design (MBD), Agile and CI/CD for automotive embedded and
Software-Defined Vehicle (SDV) development, proposing an integrated four-stage flow with
feedback loops. Target: IEEE ISIE 2027 (regular paper, 6 pages, IEEE two-column).
State: **sketch / viability stage**. No manuscript source yet, no measurements yet.

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
| Authors & ownership | `identity/ownership.md` (not yet written) |
| Sessions | `sessions/` |
| Machine index | `index.jsonl` |

## Quick facts
- Title (accepted, d-0007): *MBD, Agile, or CI/CD? A Comparative Analysis and Integrated Pipeline for Automotive Embedded Systems*
- Venue: IEEE ISIE 2027. Regular paper deadline 2026-12-15. Track candidate: 06 (Industrial CPS), see `venue/isie-2027.md`.
- Authors: **not set**. Ask the human before writing any author list or `whoami`.
- Source material from earlier work (not yet linked into this memory): `D:\artigos\genai-mbd-exp` (MBD/BESS data) and `D:\artigos\xai-sdv-artifact` (CAN intrusion XAI, OTA drift). Candidates for a case study, not decided.
- Framework source: `D:\artigos\article-docs-framework` (cloned from github.com/ojaneri/article-docs).
- Legacy hand-written notes kept at `D:\artigos\CICD\article-docs-legacy\` and folded into this structure. Delete only after the human agrees.
- Under git since 2026-11-10 (local only, no remote yet). Protocol pre-registered in commit e397dba.
- Testbed runs in WSL Ubuntu (default user root): see skill `testbed-toolchain-smoke`.
