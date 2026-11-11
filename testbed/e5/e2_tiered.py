"""E5 tiered-pipeline replay (frozen with the protocol; same replay model as E2, testbed/soc/e2.py).

Defect pool: subject 3's live E1 mutants with their E1 verdicts for UNIT, MIL, SIL, the E5 pass-0
verdicts on QEMU and on the board (control run), and the E1 field oracle (field relevance).
Stage costs: UNIT/MIL/SIL = subject 3's calibration medians; QEMU and BOARD = median wall time per run of
the E5 control runs (board = build + flash + capture).
Configurations (per-commit CI, batch 1, triggers auto and manual_8h):
  A2   UNIT+MIL+SIL per commit
  A3q  A2 + QEMU PIL per commit
  A3b  A2 + board PIL per commit
  AT   A3q per commit + one board PIL run per sprint (N commits); a board-only failure is localised by
       bisection over the sprint with ceil(log2 N) extra board runs.
Model constants as E2: N = 10, DT_COMMIT = 2 h, P_DEFECT = 0.3, R = 2000, SEED = 20261111.
Metrics per sprint: escapes (field-relevant and undetected), board-only detections, mean feedback
latency [h], compute [s]. Reported: median and bootstrap 95 % CI; Cliff's delta AT vs A3b (compute,
latency, escapes) and AT vs A3q (escapes).
Usage: python e2_tiered.py <subject3_e1.jsonl> <e5_results_subject3.jsonl> <subject3_calibration.json>
"""
import json
import math
import statistics
import sys

import numpy as np

N, DT_COMMIT, P_DEFECT, R, SEED = 10, 2.0, 0.3, 2000, 20261111
TRIGGER = {"auto": 0.0, "manual_8h": 8.0}


def load(e1_path, e5_path, cal_path):
    e1 = {json.loads(l)["id"]: json.loads(l) for l in open(e1_path) if l.strip()}
    e5 = {}
    for l in open(e5_path):
        if l.strip():
            r = json.loads(l)
            if r.get("valid") and r["family"] == "CONTROL":
                e5[(r["id"], r["arm"])] = r
    ids = [i for i, r in e1.items() if not r.get("stillborn") and (i, "qemu") in e5 and (i, "board") in e5]
    det = np.array([[not e1[i][s]["passed"] for s in ("unit", "mil", "sil")]
                    + [bool(e5[(i, "qemu")]["detect_p0"]), bool(e5[(i, "board")]["detect_p0"])] for i in ids], bool)
    rel = np.array([bool(e1[i].get("field", {}).get("fail")) for i in ids], bool)
    cal = json.loads(open(cal_path).read())
    cost = {s: statistics.median(cal["cost_s"][s]) for s in ("unit", "mil", "sil")}
    cost["qemu"] = statistics.median(e5[(i, "qemu")]["wall_s"] for i in ids)
    cost["board"] = statistics.median(e5[(i, "board")]["wall_s"] for i in ids)
    return ids, det, rel, cost


def simulate(det, rel, cost):
    rng = np.random.default_rng(SEED)
    backlogs = []
    for _ in range(R):
        has = rng.random(N) < P_DEFECT
        which = rng.integers(0, len(det), N)
        backlogs.append([int(which[i]) if has[i] else None for i in range(N)])
    host = cost["unit"] + cost["mil"] + cost["sil"]
    per_commit = {"A2": ([0, 1, 2], host), "A3q": ([0, 1, 2, 3], host + cost["qemu"]),
                  "A3b": ([0, 1, 2, 4], host + cost["board"]), "AT": ([0, 1, 2, 3], host + cost["qemu"])}
    res = {}
    for cname, (idx, run_s) in per_commit.items():
        for tname, delay in TRIGGER.items():
            esc, lat, comp, board_only = [], [], [], []
            for bl in backlogs:
                latencies, compute, escapes, bo = [], 0.0, 0, 0
                pending = []
                for i in range(N):
                    compute += run_s
                    d = bl[i]
                    if d is None:
                        continue
                    if det[d, idx].any():
                        latencies.append(delay + run_s / 3600.0)
                        compute += run_s  # re-run after the fix
                    elif cname == "AT" and det[d, 4]:
                        pending.append(i)
                    elif rel[d]:
                        escapes += 1
                if cname == "AT":
                    compute += cost["board"]
                    sprint_end = N * DT_COMMIT
                    for i in pending:
                        bo += 1
                        extra = math.ceil(math.log2(N))
                        compute += extra * cost["board"]
                        latencies.append(sprint_end + delay - (i + 1) * DT_COMMIT
                                         + (1 + extra) * cost["board"] / 3600.0)
                esc.append(escapes)
                lat.append(np.mean(latencies) if latencies else np.nan)
                comp.append(compute)
                board_only.append(bo)
            res[f"{cname}|{tname}"] = dict(escapes=esc, latency_h=lat, compute_s=comp, board_only=board_only)
    return res


def boot_ci(x, rng, B=2000):
    x = np.asarray([v for v in x if not np.isnan(v)], float)
    if len(x) == 0:
        return [float("nan")] * 3
    meds = [np.median(rng.choice(x, len(x))) for _ in range(B)]
    return [float(np.median(x)), float(np.percentile(meds, 2.5)), float(np.percentile(meds, 97.5))]


def cliffs(a, b):
    a, b = np.asarray(a, float), np.asarray(b, float)
    m = ~(np.isnan(a) | np.isnan(b))
    a, b = a[m], b[m]
    return float((np.sum(a[:, None] > b[None, :]) - np.sum(a[:, None] < b[None, :])) / (len(a) * len(b)))


def main():
    ids, det, rel, cost = load(*sys.argv[1:4])
    res = simulate(det, rel, cost)
    rng = np.random.default_rng(SEED + 1)
    rep = dict(n=len(ids), n_field_relevant=int(rel.sum()), board_only_defects=int((det[:, 4] & ~det[:, :4].any(1)).sum()),
               cost_s=cost, params=dict(N=N, DT_COMMIT_h=DT_COMMIT, P_DEFECT=P_DEFECT, R=R, SEED=SEED),
               summary={k: {m: boot_ci(v[m], rng) for m in v} for k, v in res.items()},
               cliffs_delta={"AT vs A3b compute (auto)": cliffs(res["AT|auto"]["compute_s"], res["A3b|auto"]["compute_s"]),
                             "AT vs A3b latency (auto)": cliffs(res["AT|auto"]["latency_h"], res["A3b|auto"]["latency_h"]),
                             "AT vs A3b escapes (auto)": cliffs(res["AT|auto"]["escapes"], res["A3b|auto"]["escapes"]),
                             "AT vs A3q escapes (auto)": cliffs(res["AT|auto"]["escapes"], res["A3q|auto"]["escapes"])})
    out = sys.argv[2].replace(".jsonl", "_tiered.json")
    json.dump(rep, open(out, "w"), indent=1)
    print(json.dumps({k: rep[k] for k in ("n", "board_only_defects", "cost_s", "cliffs_delta")}, indent=1))


if __name__ == "__main__":
    main()
