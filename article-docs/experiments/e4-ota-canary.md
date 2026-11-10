# E4 — Canary OTA rollout on a replayed fleet (optional, RQ4)

Status: **planned, optional.** Run only if E1–E3 are complete by week 4.

## Setup
- A "virtual fleet": each recorded drive or tank in the subject datasets is one vehicle.
- Releases from E2 are rolled out to a 10 % canary, monitored with a residual check against
  recorded data, then to 100 %.
- On the MCU: size of full vs delta update packages and signature-verification time
  (e.g., Ed25519) on nRF52840, measured, not estimated.

## Metrics
- Escaped mutants caught at canary vs at full rollout; fleet exposure before rollback.
- Delta vs full package size; verification time on MCU.

## Relation to earlier work
- `D:\artigos\xai-sdv-artifact` measured OTA drift for an intrusion detector. Reuse of scripts must
  be disclosed; results from that paper must not be reused here (V09).

## Todos
- **[#t-0023]** status: open · author: osvaldo — Decide by 2026-12-01 whether E4 runs or is listed as future work.
