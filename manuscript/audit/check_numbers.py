"""Recompute every number in manuscript/main.tex from the raw results under testbed/.

Read-only: nothing under testbed/ is written. Run from anywhere:
    python manuscript/audit/check_numbers.py
Prints one line per check: label | recomputed value.
"""
import importlib
import json
import math
import sys
from pathlib import Path
from statistics import median

ROOT = Path(__file__).resolve().parents[2]
TB = ROOT / "testbed"
OUT = []


def say(label, value):
    OUT.append((label, value))
    print(f"{label} | {value}")


def jl(p):
    return [json.loads(l) for l in open(p, encoding="utf-8") if l.strip()]


def js(p):
    return json.load(open(p, encoding="utf-8"))


def wilson(k, n, z=1.959963984540054):
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return round(100 * (c - h), 2), round(100 * min(1.0, c + h), 2)


def mcnemar_exact(gained, lost):
    n = gained + lost
    if n == 0:
        return 1.0
    k = min(gained, lost)
    p = sum(math.comb(n, i) for i in range(k + 1)) / 2 ** n
    return min(1.0, 2 * p)


def fisher_two_sided(a, b, c, d):
    """2x2 table [[a,b],[c,d]], two-sided exact p (sum of tables as or less probable)."""
    r1, r2, c1, n = a + b, c + d, a + c, a + b + c + d

    def pr(x):
        return math.comb(r1, x) * math.comb(r2, c1 - x) / math.comb(n, c1)

    p0 = pr(a)
    lo, hi = max(0, c1 - r2), min(r1, c1)
    return sum(pr(x) for x in range(lo, hi + 1) if pr(x) <= p0 * (1 + 1e-9))


# ------------------------------------------------------------------ E1 (S1, S2), board PIL
STAGES = ("unit", "mil", "sil")
e1 = {}
for s in ("soc", "fuel"):
    q = {r["id"]: r for r in jl(TB / s / "results" / "e1_qemu.jsonl")}
    b = {r["id"]: r for r in jl(TB / s / "results" / "e1_pil_iotnode.jsonl")}
    live = [i for i, r in q.items() if not r.get("stillborn")]
    say(f"E1 {s}: live mutants", len(live))
    say(f"E1 {s}: board records valid", sum(1 for i in live if b[i]["eval"]["valid"]))
    det = {i: [not q[i][st]["passed"] for st in STAGES] + [not b[i]["eval"]["passed"]] for i in live}
    rel = {i: b[i]["eval"]["field"]["fail"] for i in live}
    relq = {i: q[i]["field"]["fail"] for i in live}
    say(f"E1 {s}: field-relevant (board field) / (qemu field)", (sum(rel.values()), sum(relq.values())))
    fr = [i for i in live if rel[i]]
    lv = {f"A{k}": [i for i in fr if any(det[i][:k + 1])] for k in range(4)}
    for k in range(4):
        n = len(lv[f"A{k}"])
        say(f"E1 {s}: A{k} detected / {len(fr)}; Wilson %", (n, round(100 * n / len(fr), 1), wilson(n, len(fr))))
    for k in range(3):
        g = len(set(lv[f"A{k+1}"]) - set(lv[f"A{k}"]))
        l_ = len(set(lv[f"A{k}"]) - set(lv[f"A{k+1}"]))
        say(f"E1 {s}: McNemar A{k}->A{k+1} gained/lost/p", (g, l_, mcnemar_exact(g, l_)))
    # SIL alone, and audit: field-relevant code mutants fail a requirement (non-B2B) test at SIL
    sil_alone = sum(1 for i in fr if det[i][2])
    say(f"E1 {s}: SIL alone detects field-relevant", f"{sil_alone}/{len(fr)}")
    mil_alone = sum(1 for i in fr if det[i][1])
    say(f"E1 {s}: MIL alone detects field-relevant", f"{mil_alone}/{len(fr)}")
    fr_code = [i for i in fr if q[i]["level"] == "code"]
    req = sum(1 for i in fr_code if any(not f.startswith("B2B") for f in q[i]["sil"]["fails"]))
    say(f"E1 {s}: field-relevant code mutants failing a requirement test at SIL", f"{req}/{len(fr_code)}")
    first_sil = [i for i in fr if not det[i][0] and not det[i][1] and det[i][2]]
    say(f"E1 {s}: first detected at SIL (count, levels)", (len(first_sil), sorted({q[i]['level'] for i in first_sil})))
    first_mil = [i for i in fr if not det[i][0] and det[i][1]]
    say(f"E1 {s}: first detected at MIL (count, levels)", (len(first_mil), sorted({q[i]['level'] for i in first_mil})))
    nfr = [i for i in live if not rel[i]]
    flagged = [i for i in nfr if any(det[i])]
    say(f"E1 {s}: non-field-relevant n / flagged by any stage (board PIL) / unflagged", (len(nfr), len(flagged), len(nfr) - len(flagged)))
    flagged_q = [i for i in nfr if any(det[i][:3]) or not q[i]["pil"]["passed"]]
    say(f"E1 {s}: non-field-relevant flagged (QEMU PIL) / unflagged", (len(flagged_q), len(nfr) - len(flagged_q)))
    tim = [i for i in live if det[i][3] and not any(det[i][:3]) and not rel[i]
           and all("cycles" in f.lower() or "timing" in f.lower() for f in b[i]["eval"]["fails"])]
    say(f"E1 {s}: timing-only on board (PIL-only, fails are timing)", (len(tim), sorted(tim)))
    pil_only = [i for i in live if det[i][3] and not any(det[i][:3])]
    say(f"E1 {s}: PIL-only on board", sorted(pil_only))
    agree = sum(1 for i in live if (not q[i]["pil"]["passed"]) == (not b[i]["eval"]["passed"]))
    dis = [i for i in live if (not q[i]["pil"]["passed"]) != (not b[i]["eval"]["passed"])]
    say(f"E1 {s}: QEMU vs board PIL agreement; disagreements", (agree, len(live), dis))
    e1[s] = dict(q=q, b=b, live=live, dis=dis)
    # mutant-run medians, for comparison with the calibration medians used in Table I
    for st in STAGES:
        say(f"E1 {s}: median {st} wall_s over mutant runs", round(median(q[i][st]["wall_s"] for i in live), 3))
    brd = [(b[i].get("build_s") or 0) + (b[i]["run"].get("seconds_flash") or 0) + (b[i]["run"].get("seconds_run") or 0) for i in live]
    say(f"E1 {s}: median board PIL wall (build+flash+run) over mutant runs", round(median(brd), 2))
    cal = js(TB / s / "protocol" / "calibration.json")
    for st in STAGES:
        say(f"E1 {s}: calibration median {st} cost_s", round(median(cal["cost_s"][st]), 3))
    bc = js(TB / s / "protocol" / "calibration_iotnode.json")
    good = [x for x in bc["reps"] if x.get("ok")]
    say(f"E1 {s}: calibration board PIL cost (median build+flash+run)",
        round(median((x.get("build_s") or 0) + (x.get("seconds_flash") or 0) + (x.get("seconds_run") or 0) for x in good), 2))
    say(f"E1 {s}: board baseline max cycles / budget", (bc.get("baseline_max_cycles"), bc.get("cycle_budget")))

# platform agreement pooled; initialisation deletions (assignments inside *_init)
pool_agree = sum(len(e1[s]["live"]) - len(e1[s]["dis"]) for s in e1)
pool_n = sum(len(e1[s]["live"]) for s in e1)
say("E1 pooled: agreement, Wilson %", (pool_agree, pool_n, wilson(pool_agree, pool_n)))
init_ids = {}
for s in e1:
    m = js(TB / s / "protocol" / "mutants.json")
    init_ids[s] = [x["id"] for x in m["code"] if x["op"] == "SDL" and "_init:" in x["desc"]]
n_init = sum(len(v) for v in init_ids.values())
dis_init = sum(1 for s in e1 for i in e1[s]["dis"] if i in init_ids[s])
say("E1 pooled: init deletions (ids)", init_ids)
say("E1 pooled: disagreements among init / others", (f"{dis_init}/{n_init}", f"{pool_n - pool_agree - dis_init}/{pool_n - n_init}"))
say("E1 pooled: Fisher exact p (two-sided) 3/6 vs 0/199",
    fisher_two_sided(dis_init, n_init - dis_init, pool_n - pool_agree - dis_init, pool_n - n_init - (pool_n - pool_agree - dis_init)))
say("E1 total mutants S1+S2; field-relevant", (130 + 75, 68 + 34))

bess_an = js(TB / "bess" / "results" / "e1_qemu_analysis.json")
say("E1 bess: live mutants (analysis)", bess_an["n_live"])
bid = js(TB / "bess" / "spec" / "identification.json")
say("S3 field RMSE model / naive", (round(bid["field_rmse_degC"], 3), round(bid["naive_tref_rmse_field_degC"], 3)))

# ------------------------------------------------------------------ E2 replay
def load_e2_module(subject):
    sys.path.insert(0, str(TB / subject))
    for mod in ("common", "e2"):
        sys.modules.pop(mod, None)
    try:
        return importlib.import_module("e2")
    finally:
        sys.path.pop(0)


e2 = {}
for s in ("soc", "fuel"):
    d = js(TB / s / "results" / "e1_qemu_e2.json")
    e2[s] = d
    say(f"E2 {s}: params", d["params"])
    say(f"E2 {s}: stage_cost_s", {k: round(v, 3) for k, v in d["stage_cost_s"].items()})
    for k in ("A2|b1|auto", "A2|b10|auto", "A3|b1|auto", "A3|b5|auto", "A3|b10|auto", "A0|b1|auto", "A0|b10|auto"):
        v = d["summary"][k]
        say(f"E2 {s}: {k} latency s / h, compute s, escapes (medians)",
            (round(v["latency_h"][0] * 3600, 1), round(v["latency_h"][0], 2), round(v["compute_s"][0], 1), v["escapes"][0]))
    r = d["summary"]["A3|b1|auto"]["compute_s"][0] / d["summary"]["A2|b1|auto"]["compute_s"][0]
    say(f"E2 {s}: compute ratio A3 b1 / A2 b1", round(r, 2))
    say(f"E2 {s}: Cliff's delta", d["cliffs_delta"])
    gate = [round(d["summary"][f"A3|b1|{t}"]["latency_h"][0] - d["summary"]["A3|b1|auto"]["latency_h"][0], 3)
            for t in ("manual_1h", "manual_8h", "manual_24h")]
    say(f"E2 {s}: gate adds to A3 b1 latency (h)", gate)
    # re-simulate in memory (no file written) to check per-replay escapes, not only medians
    try:
        mod = load_e2_module(s)
        det, rel, cost, ids = mod.load(str(TB / s / "results" / "e1_qemu.jsonl"),
                                       str(TB / s / "protocol" / "calibration_iotnode.json"))
        res = mod.simulate(det, rel, cost, mod.SEED)
        same = abs(median(res["A3|b1|auto"]["compute_s"]) - d["summary"]["A3|b1|auto"]["compute_s"][0]) < 1e-6
        say(f"E2 {s}: resimulation reproduces A3|b1|auto compute median", same)
        for c in ("A0", "A1", "A2", "A3"):
            for bsz in (1, 5, 10):
                esc = res[f"{c}|b{bsz}|auto"]["escapes"]
                say(f"E2 {s}: {c}|b{bsz}|auto escapes: replays with >=1 escape / max / median",
                    (sum(1 for x in esc if x > 0), max(esc), median(esc)))
    except Exception as ex:  # noqa: BLE001
        say(f"E2 {s}: resimulation failed", repr(ex))

# ------------------------------------------------------------------ E5
recs = {s: jl(TB / "e5" / "results" / f"e5_{s}.jsonl") for s in ("soc", "fuel", "bess")}
allr = [r for s in recs for r in recs[s]]
say("E5: records, valid", (len(allr), sum(1 for r in allr if r["valid"])))
an = js(TB / "e5" / "results" / "e5_analysis.json")
U = set()
fam = {}
seen = {}
for r in allr:
    if r["family"] in ("INIT", "LUD"):
        fam[r["id"]] = r["family"]
        seen[r["id"]] = r["seen"] in (True, "True")
        if r["detected"] in (True, "True"):
            U.add(r["id"])
say("E5: INIT/LUD mutants, observable, observable unseen",
    (len(fam), len(U), sum(1 for i in U if not seen[i])))
say("E5: INIT / LUD counts", (sum(1 for v in fam.values() if v == "INIT"), sum(1 for v in fam.values() if v == "LUD")))
for arm in ("host_sil", "host_poison", "host_valgrind", "host_msan", "qemu", "board"):
    rs = [r for r in allr if r["arm"] == arm and r["id"] in U]
    k = sum(1 for r in rs if r["detected"] in (True, "True"))
    ku = sum(1 for r in rs if r["detected"] in (True, "True") and not seen[r["id"]])
    w = median(float(r["wall_s"]) for r in allr if r["arm"] == arm and r["family"] in ("INIT", "LUD"))
    say(f"E5 {arm}: caught/26, Wilson %, unseen, median wall (INIT/LUD records)", (k, wilson(k, len(U)), ku, round(w, 3)))
    if arm == "host_poison":
        for f in ("INIT", "LUD"):
            say(f"E5 host_poison {f}", f"{sum(1 for r in rs if r['detected'] in (True, 'True') and fam[r['id']] == f)}/{sum(1 for i in U if fam[i] == f)}")
    if arm in ("qemu", "board"):
        say(f"E5 {arm}: detected at pass 0", sum(1 for r in rs if r["detect_p0"] in (True, "True")))
say("E5: analysis median wall (arms)", {a: round(v["median_wall_s"], 3) for a, v in an["arms"].items()})
ctl_q = {r["id"]: r for r in recs["bess"] if r["family"] == "CONTROL" and r["arm"] == "qemu"}
ctl_b = {r["id"]: r for r in recs["bess"] if r["family"] == "CONTROL" and r["arm"] == "board"}
agree = sum(1 for i in ctl_q if (ctl_q[i]["detect_p0"] in (True, "True")) == (ctl_b[i]["detect_p0"] in (True, "True")))
say("E5 H1: control agree (pass 0) / n, Wilson %", (agree, len(ctl_q), wilson(agree, len(ctl_q))))
board_only = [i for i in ctl_q if ctl_b[i]["detected"] in (True, "True") and ctl_q[i]["detected"] not in (True, "True")]
say("E5 control: caught by board but not QEMU", board_only)
cnt = [r for r in allr if r["family"] in ("INIT", "LUD")]
cex = [i for i in U if any(r["arm"] == "board" and r["id"] == i and r["detected"] in (True, "True") for r in cnt)
       and not any(r["arm"] == "qemu" and r["id"] == i and r["detected"] in (True, "True") for r in cnt)]
say("E5 H2: board-caught, QEMU-missed", cex)
vg_miss = [i for i in U if not any(r["arm"] == "host_valgrind" and r["id"] == i and r["detected"] in (True, "True") for r in cnt)]
say("E5 H3: Valgrind misses", vg_miss)
say("E5: board median / MSan median", round(an["arms"]["board"]["median_wall_s"] / an["arms"]["host_msan"]["median_wall_s"], 1))

# H4 ratios and flags from st_max and each platform's budget
for s in ("soc", "fuel", "bess"):
    cal = js(TB / "e5" / "protocol" / f"calibration_{s}.json")
    qb, bb = cal["qemu_budget"], cal["board_budget"]
    say(f"E5 {s}: baselines board/qemu, budgets", (cal["board_baseline_st_max"], cal["qemu_baseline_st_max"], bb, qb))
    muts = {m["id"]: m for m in js(TB / "e5" / "protocol" / f"e5_mutants_{s}.json")["mutants"]}
    for lad in ("ALU", "DIV"):
        h = an["H4"][f"{s}:{lad}"]
        rows = []
        qf, bf = [], []
        for mid, v in sorted(h["st_max"].items()):
            lvl = float(muts[mid]["level"])
            rows.append((lvl, int(muts[mid]["n"]), round(v["board"] / bb, 2), round(v["qemu"] / qb, 2),
                         v["board"] - cal["board_baseline_st_max"], v["qemu"] - cal["qemu_baseline_st_max"]))
            if v["board"] > bb:
                bf.append(lvl)
            if v["qemu"] > qb:
                qf.append(lvl)
        say(f"E5 {s} {lad}: (level, n, board/budget, qemu/budget, +cycles, +ticks)", rows)
        say(f"E5 {s} {lad}: flags board / qemu (recomputed)", (bf, qf))
say("S1 baseline CPI 107/68", round(107 / 68, 2))

t = js(TB / "e5" / "results" / "e5_bess_tiered.json")
say("Tiered: costs", {k: round(v, 3) for k, v in t["cost_s"].items()})
for k in ("A2|auto", "A3q|auto", "AT|auto", "A3b|auto"):
    v = t["summary"][k]
    say(f"Tiered {k}: compute s, latency s, escapes", (round(v["compute_s"][0], 4), round(v["latency_h"][0] * 3600, 2), v["escapes"][0]))
say("Tiered: AT / A3b compute", round(t["summary"]["AT|auto"]["compute_s"][0] / t["summary"]["A3b|auto"]["compute_s"][0], 3))
say("Tiered: board_only_defects, n, Cliff", (t["board_only_defects"], t["n"], t["cliffs_delta"]))
say("SIL/MIL cost ratio S1 (calibration)", round(e2["soc"]["stage_cost_s"]["sil"] / e2["soc"]["stage_cost_s"]["mil"], 3))
