"""E2 — integration cadence and trigger (Agile + CI axes), trace-driven replay. Written before any E2 run.

Evidence used (measured, not assumed):
- per-mutant detection by each stage and field relevance: E1 results on the chosen PIL target;
- stage costs (seconds per pipeline run): median baseline wall times for UNIT/MIL/SIL (calibration.json);
  PIL cost = build + flash + run on the real target (calibration_<board>.json), never QEMU.
Model (fixed here, before any run):
- backlog of N = 10 increments, one commit every DT_COMMIT = 2 h of development time;
- each increment carries a defect with probability P_DEFECT = 0.3, drawn uniformly from live mutants;
  defects are assumed not to mask each other (stated limitation);
- factor B (cadence): batch b in {1, 5, 10} commits per pipeline run (per increment / sprint / big-bang);
- factor C (trigger): automated (start when the batch closes) or manual gate with delay D in
  {1 h, 8 h, 24 h} (sensitivity sweep, not a point estimate);
- factor A (stages): A0..A3 as in E1;
- a failing run is followed by bisection over the batch: ceil(log2 b) extra runs of the same config
  (the strategy evaluated by Beheshtian et al., IEEE TSE 2022), then the culprit is fixed;
- escapes: field-relevant defects not detected by the config reach the release.
Metrics per backlog: mean feedback latency of detected defects [h], localisation runs, escapes,
pipeline compute [s], mean lead time commit -> passing release candidate [h].
Replications: R = 2000 backlogs from a fixed seed, identical across configurations (paired).
Reported: median and bootstrap 95 % CI per configuration; Cliff's delta for planned contrasts
(b=1 vs b=10 at A3 automated; automated vs manual 8 h at b=1, A3).
Usage: python e2.py <e1_results.jsonl> <board_calibration.json> [out.json]
"""
import itertools
import json
import math
import sys
from statistics import median

import numpy as np

import common

N, DT_COMMIT, P_DEFECT, R, SEED = 10, 2.0, 0.3, 2000, 20261111
BATCH = (1, 5, 10)
TRIGGER = {"auto": 0.0, "manual_1h": 1.0, "manual_8h": 8.0, "manual_24h": 24.0}
STAGES = ("unit", "mil", "sil", "pil")
CONFIGS = {"A0": STAGES[:1], "A1": STAGES[:2], "A2": STAGES[:3], "A3": STAGES[:4]}


def load(e1_path, board_cal):
    recs = [json.loads(l) for l in open(e1_path) if l.strip()]
    live = [r for r in recs if not r.get("stillborn")]
    cal = json.loads((common.ROOT / "protocol" / "calibration.json").read_text())
    bc = json.loads(open(board_cal).read())
    cost = {s: median(cal["cost_s"][s]) for s in ("unit", "mil", "sil")}
    good = [x for x in bc["reps"] if x.get("ok")]
    cost["pil"] = median((x.get("build_s") or 0) + (x.get("seconds_flash") or 0) + (x.get("seconds_run") or 0)
                         for x in good)
    # PIL column and field oracle come from the real target when its E1 re-run exists (never QEMU).
    real_path = common.ROOT / "results" / f"e1_pil_{bc['board']}.jsonl"
    real = {}
    if real_path.exists():
        for l in real_path.read_text().splitlines():
            x = json.loads(l)
            if x.get("eval", {}).get("valid"):
                real[x["id"]] = x["eval"]
    live = [r for r in live if r["id"] in real] if real else live
    det = np.array([[not r[s]["passed"] for s in STAGES[:3]] +
                    [not real[r["id"]]["passed"] if real else not r["pil"]["passed"]] for r in live], dtype=bool)
    rel = np.array([real[r["id"]]["field"]["fail"] if real else r["field"]["fail"] for r in live], dtype=bool)
    return det, rel, cost, [r["id"] for r in live]


def simulate(det, rel, cost, rng_seed):
    rng = np.random.default_rng(rng_seed)
    backlogs = []
    for _ in range(R):
        has = rng.random(N) < P_DEFECT
        which = rng.integers(0, len(det), N)
        backlogs.append([int(which[i]) if has[i] else None for i in range(N)])
    results = {}
    for (cname, ss), b, (tname, delay) in itertools.product(CONFIGS.items(), BATCH, TRIGGER.items()):
        idx = [STAGES.index(s) for s in ss]
        run_s = sum(cost[s] for s in ss)
        run_h = run_s / 3600.0
        lat, loc, esc, comp, lead = [], [], [], [], []
        for bl in backlogs:
            latencies, runs, escapes, leads = [], 0, 0, []
            for start in range(0, N, b):
                batch = list(range(start, min(start + b, N)))
                close_t = (batch[-1] + 1) * DT_COMMIT
                done_t = close_t + delay + run_h
                runs += 1
                caught = [i for i in batch if bl[i] is not None and det[bl[i], idx].any()]
                for i in batch:
                    if bl[i] is not None and not det[bl[i], idx].any() and rel[bl[i]]:
                        escapes += 1
                if caught:
                    extra = math.ceil(math.log2(len(batch))) if len(batch) > 1 else 0
                    runs += extra * len(caught)
                    for i in caught:
                        latencies.append(done_t - (i + 1) * DT_COMMIT)
                    # after fixes the batch is re-run once to obtain a passing release candidate
                    runs += 1
                    rc_t = done_t + extra * len(caught) * run_h + delay + run_h
                else:
                    rc_t = done_t
                leads += [rc_t - (i + 1) * DT_COMMIT for i in batch]
            lat.append(np.mean(latencies) if latencies else np.nan)
            loc.append(runs - math.ceil(N / b))
            esc.append(escapes)
            comp.append(runs * run_s)
            lead.append(np.mean(leads))
        results[f"{cname}|b{b}|{tname}"] = dict(latency_h=lat, extra_runs=loc, escapes=esc,
                                                compute_s=comp, lead_h=lead)
    return results


def boot_ci(x, rng, B=2000):
    x = np.asarray([v for v in x if not np.isnan(v)])
    if len(x) == 0:
        return [float("nan")] * 3
    meds = [np.median(rng.choice(x, len(x))) for _ in range(B)]
    return [float(np.median(x)), float(np.percentile(meds, 2.5)), float(np.percentile(meds, 97.5))]


def cliffs_delta(a, b):
    a, b = np.asarray(a, float), np.asarray(b, float)
    m = ~(np.isnan(a) | np.isnan(b))
    a, b = a[m], b[m]
    gt = np.sum(a[:, None] > b[None, :])
    lt = np.sum(a[:, None] < b[None, :])
    return float((gt - lt) / (len(a) * len(b))) if len(a) and len(b) else float("nan")


def main(e1_path, board_cal, out=None):
    det, rel, cost, ids = load(e1_path, board_cal)
    res = simulate(det, rel, cost, SEED)
    rng = np.random.default_rng(SEED + 1)
    summary = {k: {m: boot_ci(v[m], rng) for m in v} for k, v in res.items()}
    contrasts = {
        "A3 auto: b1 vs b10 latency_h": cliffs_delta(res["A3|b1|auto"]["latency_h"], res["A3|b10|auto"]["latency_h"]),
        "A3 auto: b1 vs b10 compute_s": cliffs_delta(res["A3|b1|auto"]["compute_s"], res["A3|b10|auto"]["compute_s"]),
        "A3 b1: auto vs manual_8h lead_h": cliffs_delta(res["A3|b1|auto"]["lead_h"], res["A3|b1|manual_8h"]["lead_h"]),
        "b1 auto: A2 vs A3 escapes": cliffs_delta(res["A2|b1|auto"]["escapes"], res["A3|b1|auto"]["escapes"]),
    }
    rep = dict(params=dict(N=N, DT_COMMIT_h=DT_COMMIT, P_DEFECT=P_DEFECT, R=R, SEED=SEED),
               stage_cost_s=cost, n_live=len(ids), n_field_relevant=int(rel.sum()),
               summary=summary, cliffs_delta=contrasts)
    out = out or e1_path.replace(".jsonl", "_e2.json")
    json.dump(rep, open(out, "w"), indent=1)
    print(json.dumps(dict(stage_cost_s=cost, contrasts=contrasts), indent=1))


if __name__ == "__main__":
    main(*sys.argv[1:])
