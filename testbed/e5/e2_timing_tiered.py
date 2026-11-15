"""E5c: tiered placement replayed on the timing-ladder class (exploratory re-analysis of E5/E5b records).

Protocol: protocol/E5c-timing-tiered.md (committed before this script ran).
Usage: python e2_timing_tiered.py            (from testbed/e5; writes results/e5c_timing_tiered.json)
"""
import json
import math
import pathlib
import re
import statistics

import numpy as np

E5 = pathlib.Path(__file__).resolve().parent
TB = E5.parent
SUBJECTS = ("soc", "fuel", "bess")
N, DT_COMMIT, P_DEFECT, R, SEED = 10, 2.0, 0.3, 2000, 20261111


def load(subject, reference):
    recs = [json.loads(l) for l in open(E5 / "results" / f"e5_{subject}.jsonl") if l.strip()]
    lad = {}
    for r in recs:
        if r.get("family") in ("ALU", "DIV") and r.get("valid"):
            lad.setdefault(r["id"], {})[r["arm"]] = r
    for i, arms in lad.items():
        assert "host_sil" in arms and not arms["host_sil"]["detected"], f"host_sil flags ladder {i}"
    h4 = json.loads((E5 / "results" / "e5_analysis.json").read_text())["H4"]
    h4n = json.loads((E5 / "results" / "e5b" / "e5b_analysis.json").read_text())["R4"]["H4n"]["ladders"]
    mut = json.loads((E5 / "protocol" / f"e5_mutants_{subject}.json").read_text())
    level_of = {}
    for m in mut["mutants"]:
        if m.get("family") in ("ALU", "DIV"):
            level_of[m["id"]] = float(re.match(r"\+([0-9.]+) x baseline", m["desc"]).group(1))
    ids = sorted(lad)
    q, b = [], []
    for i in ids:
        fam = lad[i]["qemu"]["family"]
        key = f"{subject}:{fam}"
        lv = level_of[i]
        q.append(lv in h4[key]["qemu_flags"])
        b.append(lv in (h4[key]["board_flags"] if reference == "iotnode" else h4n[key]["nrf_flags"]))
    cal = json.loads((TB / subject / "protocol" / "calibration.json").read_text())
    med = lambda v: statistics.median(v) if isinstance(v, list) else float(v)
    cost = {s: med(cal["cost_s"][s]) for s in ("unit", "mil", "sil")}
    cost["qemu"] = statistics.median(lad[i]["qemu"]["wall_s"] for i in ids)
    cost["board"] = statistics.median(lad[i]["board"]["wall_s"] for i in ids)
    return ids, np.array(q, bool), np.array(b, bool), cost


def simulate(q, b, cost):
    rng = np.random.default_rng(SEED)
    backlogs = []
    for _ in range(R):
        has = rng.random(N) < P_DEFECT
        which = rng.integers(0, len(q), N)
        backlogs.append([int(which[i]) if has[i] else None for i in range(N)])
    host = cost["unit"] + cost["mil"] + cost["sil"]
    per_commit = {"A2": host, "A3q": host + cost["qemu"], "A3b": host + cost["board"], "AT": host + cost["qemu"]}
    res = {}
    for cname, run_s in per_commit.items():
        esc, fa, lat, comp = [], [], [], []
        for bl in backlogs:
            latencies, compute, escapes, alarms, pending = [], 0.0, 0, 0, []
            for i in range(N):
                compute += run_s
                d = bl[i]
                if d is None:
                    continue
                qemu_on = cname in ("A3q", "AT")
                if cname == "A3b" and b[d]:
                    latencies.append(run_s / 3600.0)
                    compute += run_s
                elif qemu_on and q[d] and b[d]:
                    latencies.append(run_s / 3600.0)
                    compute += run_s
                elif qemu_on and q[d] and not b[d]:
                    alarms += 1
                    compute += cost["qemu"]
                elif cname == "AT" and b[d]:
                    pending.append(i)
                elif b[d]:
                    escapes += 1
            if cname == "AT":
                compute += cost["board"]
                for i in pending:
                    extra = math.ceil(math.log2(N))
                    compute += extra * cost["board"]
                    latencies.append(N * DT_COMMIT - (i + 1) * DT_COMMIT + (1 + extra) * cost["board"] / 3600.0)
            esc.append(escapes)
            fa.append(alarms)
            lat.append(np.mean(latencies) if latencies else np.nan)
            comp.append(compute)
        res[cname] = dict(escapes=esc, false_alarms=fa, latency_h=lat, compute_s=comp)
    return res


def boot_ci(x, rng, B=2000):
    x = np.asarray([v for v in x if not np.isnan(v)], float)
    if len(x) == 0:
        return [float("nan")] * 3
    meds = [np.median(rng.choice(x, len(x))) for _ in range(B)]
    return [float(np.median(x)), float(np.percentile(meds, 2.5)), float(np.percentile(meds, 97.5))]


def summarise(res, rng):
    out = {}
    for k, v in res.items():
        out[k] = {m: boot_ci(v[m], rng) for m in v}
        out[k]["mean_escapes"] = float(np.mean(v["escapes"]))
        out[k]["share_sprints_with_escape"] = float(np.mean(np.asarray(v["escapes"]) > 0))
        out[k]["mean_false_alarms"] = float(np.mean(v["false_alarms"]))
    return out


def main():
    rep = {"protocol": "protocol/E5c-timing-tiered.md", "label": "exploratory",
           "params": dict(N=N, DT_COMMIT_h=DT_COMMIT, P_DEFECT=P_DEFECT, R=R, SEED=SEED)}
    for ref in ("iotnode", "nrf"):
        rep[ref] = {}
        for s in SUBJECTS:
            ids, q, b, cost = load(s, ref)
            res = simulate(q, b, cost)
            rng = np.random.default_rng(SEED + 1)
            rep[ref][s] = dict(n=len(ids), reference_flagged=int(b.sum()), qemu_flagged=int(q.sum()),
                               both=int((q & b).sum()), board_only=int((b & ~q).sum()),
                               qemu_only=int((q & ~b).sum()), cost_s=cost, summary=summarise(res, rng))
    out = E5 / "results" / "e5c_timing_tiered.json"
    out.write_text(json.dumps(rep, indent=1))
    for ref in ("iotnode", "nrf"):
        for s in SUBJECTS:
            r = rep[ref][s]
            print(ref, s, {k: r[k] for k in ("n", "reference_flagged", "qemu_flagged", "board_only", "qemu_only")})
            for c, m in r["summary"].items():
                print("   ", c, "esc/sprint %.2f, sprints with escape %.2f, false alarms %.2f, compute %.1f s, latency %.2f h"
                      % (m["mean_escapes"], m["share_sprints_with_escape"], m["mean_false_alarms"],
                         m["compute_s"][0], m["latency_h"][0]))
    print("wrote", out)


if __name__ == "__main__":
    main()
