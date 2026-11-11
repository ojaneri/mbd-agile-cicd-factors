"""E1 analysis, written before any mutant result exists (pre-registered).

Definitions
- stillborn: generated code does not compile (excluded from all rates, counted).
- field-relevant: the deployed (target) build fails the field oracle on held-out real cycles.
- detected by stage S: stage S reports any failure (requirement, back-to-back, timing, build, crash).
- Factor A configurations (cumulative): A0 = UNIT, A1 = UNIT+MIL, A2 = UNIT+MIL+SIL, A3 = A2+PIL.
- escape(config) = field-relevant and not detected by any stage of the config.
Reported
- per config: detection rate over field-relevant mutants, Wilson 95 % CI, escape count;
- successive configs compared with an exact McNemar test (two-sided binomial on discordant pairs);
- per operator class: detection by first detecting stage;
- stage-unique detections (detected only by that stage among the four);
- non-field-relevant mutants: how many any stage still flags (requirements stricter than the field
  oracle) and how many nothing flags (equivalent or benign);
- cost per config = sum of the median baseline stage wall times (calibration.json); for PIL the cost
  is only meaningful on a real target.
Usage: python analyze_e1.py results/e1_<target>.jsonl
"""
import json
import math
import sys
from statistics import median

import common

STAGES = ("unit", "mil", "sil", "pil")
CONFIGS = {"A0": STAGES[:1], "A1": STAGES[:2], "A2": STAGES[:3], "A3": STAGES[:4]}


def wilson(k, n, z=1.959964):
    if n == 0:
        return (float("nan"), float("nan"))
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (c - h, c + h)


def mcnemar_exact(b, c):
    n = b + c
    if n == 0:
        return 1.0
    k = min(b, c)
    p = sum(math.comb(n, i) for i in range(k + 1)) / 2 ** n
    return min(1.0, 2 * p)


def main(path):
    recs = [json.loads(l) for l in open(path) if l.strip()]
    cal = json.loads((common.ROOT / "protocol" / "calibration.json").read_text())
    live = [r for r in recs if not r.get("stillborn")]
    det = {r["id"]: {s: not r[s]["passed"] for s in STAGES} for r in live}
    rel = [r for r in live if r["field"]["fail"]]
    nonrel = [r for r in live if not r["field"]["fail"]]
    rep = {"n_total": len(recs), "n_stillborn": len(recs) - len(live), "n_live": len(live),
           "n_field_relevant": len(rel), "configs": {}, "mcnemar": {}, "by_op": {}, "unique": {}}
    cost = {s: median(cal["cost_s"][s]) for s in STAGES}
    for c, ss in CONFIGS.items():
        k = sum(1 for r in rel if any(det[r["id"]][s] for s in ss))
        lo, hi = wilson(k, len(rel))
        rep["configs"][c] = dict(stages=list(ss), detected=k, n=len(rel), rate=k / len(rel) if rel else None,
                                 ci95=[lo, hi], escapes=len(rel) - k, cost_s=sum(cost[s] for s in ss))
    names = list(CONFIGS)
    for a, b in zip(names, names[1:]):
        da = [any(det[r["id"]][s] for s in CONFIGS[a]) for r in rel]
        db = [any(det[r["id"]][s] for s in CONFIGS[b]) for r in rel]
        only_b = sum(1 for x, y in zip(da, db) if y and not x)
        only_a = sum(1 for x, y in zip(da, db) if x and not y)
        rep["mcnemar"][f"{a}->{b}"] = dict(gained=only_b, lost=only_a, p_exact=mcnemar_exact(only_a, only_b))
    for r in rel:
        first = next((s for s in STAGES if det[r["id"]][s]), "escaped")
        rep["by_op"].setdefault(r["op"], {}).setdefault(first, 0)
        rep["by_op"][r["op"]][first] += 1
    for s in STAGES:
        rep["unique"][s] = sorted(r["id"] for r in rel if det[r["id"]][s] and sum(det[r["id"]].values()) == 1)
    rep["non_field_relevant"] = dict(n=len(nonrel),
                                     flagged=sum(1 for r in nonrel if any(det[r["id"]].values())),
                                     unflagged=sorted(r["id"] for r in nonrel if not any(det[r["id"]].values())))
    rep["escaped_all"] = sorted(r["id"] for r in rel if not any(det[r["id"]].values()))
    # Timing-only: flagged by PIL timing and by nothing else (the field oracle is functional, so these
    # are performance regressions that only a target stage can see; reported apart, not as escapes).
    rep["timing_only"] = sorted(
        r["id"] for r in live
        if det[r["id"]]["pil"] and not any(det[r["id"]][s] for s in STAGES[:3])
        and all("timing" in f for f in r["pil"]["fails"]))
    rep["stillborn_ids"] = sorted(r["id"] for r in recs if r.get("stillborn"))
    out = path.replace(".jsonl", "_analysis.json")
    json.dump(rep, open(out, "w"), indent=1)
    print(json.dumps(rep, indent=1))


if __name__ == "__main__":
    main(sys.argv[1])
