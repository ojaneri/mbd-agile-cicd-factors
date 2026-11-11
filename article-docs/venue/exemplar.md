# Venue exemplar — ISIE 2025 (P08)

Paper: Manuel, Franco, Silva, Santos, dos Santos, Dias Santos, "Model-Based Fault Injection and
Diagnostic Validation for AUTOSAR Software Components in Safety-Critical Automotive Systems",
2025 IEEE 34th ISIE, pp. 1–6, doi 10.1109/ISIE62713.2025.11124734. Read in full via CAFe on 2026-11-11.

## Shape
- Length: 6 pages (the standard ISIE limit; no extra pages bought).
- Sections: Introduction · Related Work and Key Challenges · Implementation (method) · Experimental
  Evaluation · Results and Discussions · Conclusion.
- Figures: the IEEE page lists 13 figure anchors (may include sub-figures; count in the PDF). Tables: 1.
- References: count not available on the IEEE page (check in the PDF).
- Affiliations: industry (OpenCadd, São Paulo) + UTFPR-PG + Toronto Metropolitan University.

## What it does that tells us about the bar
- One Simulink model (throttle position, redundant sensors), faults injected via AUTOSAR Dem Status
  Override blocks, evaluation by Simulink coverage before and after adding test cases (visual).
- No statistics, no comparison of configurations, no external dataset.
- So ISIE accepts demonstration-level MBD/automotive papers. Our factorial design with paired statistics,
  real-data oracles and an open toolchain would be **above** this bar; the risk for us is not rigour but
  fitting E1+E2(+E3) into 6 pages.

## What this paper does that ours does not (yet)
- Uses an industry-standard architecture (AUTOSAR) and tool (Simulink); reviewers from industry
  recognise it immediately. Our open toolchain needs one sentence mapping each stage to its
  Simulink/TargetLink/dSPACE equivalent (d-0004).

## Todos
- **[#t-0028]** status: done · author: osvaldo — Exemplar dissected from the IEEE HTML on 2026-11-11.
- **[#t-0035]** status: open · author: osvaldo — Open the PDF to count references and real figures, and note the template details (abstract length, keywords, figure style).
