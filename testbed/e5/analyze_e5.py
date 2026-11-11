"""E5 pre-registered analysis (frozen with the protocol). Usage: python analyze_e5.py [subjects...]
Reads results/e5_<subject>.jsonl and protocol/calibration_<subject>.json; writes results/e5_analysis.json.

Sets
  F  = INIT + LUD mutants of all subjects;  F_unseen = F without the E1-seen INIT mutants of subjects 1-2.
  U  = members of F detected by at least one arm (observable); equivalent ones are reported, not dropped.
Arm detection = the arm's `detected` flag (oracle failure, tool error, or output differing between runs
of the same arm: poison patterns, paint passes, captures). Target arms are also reported per pass type.
Hypotheses and decision rules
  H1  subject 3 control mutants: the pass-0 verdict on QEMU equals the board's; supported iff the Wilson 95 %
      lower bound of the agreement rate >= 0.95.
  H2  for U: every mutant detected on the board is detected on QEMU (same ELF, 5 passes).
      Supported iff 0 counterexamples (primary on F_unseen, also reported on F).
  H3  for U: every mutant detected by any target arm is detected by host_valgrind, and the median wall time
      of host_valgrind per mutant is below that of qemu. Supported iff 0 counterexamples and cost holds.
      host_msan reported the same way (secondary). host_poison: predicted to detect INIT, not LUD (exploratory).
  H4  per subject and ladder: the set of levels flagged on QEMU equals the set flagged on the board.
      Predicted: ALU equal (both flag exactly f > 1); DIV different (board flags f > 1, QEMU none).
Arms whose baseline was not clean in calibration are excluded and reported.
"""
import json
import math
import pathlib
import statistics
import sys

E5 = pathlib.Path(__file__).resolve().parent
ARMS = ("host_sil", "host_poison", "host_valgrind", "host_msan", "qemu", "board")


def wilson(k, n, z=1.96):
    if n == 0:
        return (None, None)
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (round(c - h, 4), round(c + h, 4))


def load(subject):
    p = E5 / "results" / f"e5_{subject}.jsonl"
    recs = {}
    if p.exists():
        for line in p.read_text().splitlines():
            if line.strip():
                r = json.loads(line)
                if r.get("valid"):
                    recs[(r["id"], r["arm"])] = r  # last valid record wins
    return recs


def main(subjects):
    out = dict(subjects=subjects, excluded_arms={}, sets={}, arms={}, H1=None, H2={}, H3={}, H4={})
    allrec = {}
    for s in subjects:
        cal = json.loads((E5 / "protocol" / f"calibration_{s}.json").read_text())
        out["excluded_arms"][s] = cal.get("excluded_arms", [])
        allrec.update(load(s))
    ids = {}
    for (mid, arm), r in allrec.items():
        ids.setdefault(mid, dict(family=r["family"], seen=r.get("seen", False), subject=r["subject"], arms={}))
        ids[mid]["arms"][arm] = r
    F = [m for m, v in ids.items() if v["family"] in ("INIT", "LUD")]
    Fu = [m for m in F if not ids[m]["seen"]]

    def det(m, arm):
        r = ids[m]["arms"].get(arm)
        return None if r is None else bool(r["detected"])

    U = [m for m in F if any(det(m, a) for a in ARMS)]
    Uu = [m for m in U if m in Fu]
    out["sets"] = dict(F=len(F), F_unseen=len(Fu), U=len(U), U_unseen=len(Uu),
                       equivalent_or_unobserved=sorted(set(F) - set(U)),
                       missing_arms={m: [a for a in ARMS if a not in ids[m]["arms"]] for m in F
                                     if any(a not in ids[m]["arms"] for a in ARMS)})
    for arm in ARMS:
        row = {}
        for label, S in (("U", U), ("U_unseen", Uu)):
            ran = [m for m in S if det(m, arm) is not None]
            k = sum(det(m, arm) for m in ran)
            row[label] = dict(detected=k, of=len(ran), wilson95=wilson(k, len(ran)))
        walls = [ids[m]["arms"][arm]["wall_s"] for m in F if arm in ids[m]["arms"]]
        row["median_wall_s"] = statistics.median(walls) if walls else None
        if arm in ("qemu", "board"):
            for sub in ("detect_p0", "detect_paint", "differential_paint", "differential_any"):
                ran = [m for m in U if arm in ids[m]["arms"]]
                row[sub] = sum(bool(ids[m]["arms"][arm].get(sub)) for m in ran)
        if arm == "host_poison":
            row["by_family"] = {fam: dict(detected=sum(bool(det(m, arm)) for m in U if ids[m]["family"] == fam),
                                          of=sum(1 for m in U if ids[m]["family"] == fam and det(m, arm) is not None))
                                for fam in ("INIT", "LUD")}
        out["arms"][arm] = row

    for label, S in (("F_unseen", Uu), ("F", U)):
        both = [m for m in S if det(m, "board") is not None and det(m, "qemu") is not None]
        ce = [m for m in both if det(m, "board") and not det(m, "qemu")]
        rev = [m for m in both if det(m, "qemu") and not det(m, "board")]
        out["H2"][label] = dict(n=len(both), counterexamples=ce, qemu_only=rev, supported=len(both) > 0 and not ce)
    for tool in ("host_valgrind", "host_msan"):
        res = {}
        for label, S in (("F_unseen", Uu), ("F", U)):
            both = [m for m in S if det(m, tool) is not None and (det(m, "qemu") is not None or det(m, "board") is not None)]
            ce = [m for m in both if (det(m, "qemu") or det(m, "board")) and not det(m, tool)]
            res[label] = dict(n=len(both), counterexamples=ce)
        wt, wq = out["arms"][tool]["median_wall_s"], out["arms"]["qemu"]["median_wall_s"]
        res["cost"] = dict(median_wall_s=wt, qemu_median_wall_s=wq, cheaper=(wt is not None and wq is not None and wt < wq))
        res["supported"] = (res["F_unseen"]["n"] > 0 and not res["F_unseen"]["counterexamples"] and res["cost"]["cheaper"])
        out["H3"][tool] = res

    ctl = [m for m, v in ids.items() if v["family"] == "CONTROL"
           and "qemu" in v["arms"] and "board" in v["arms"]]
    agree = [m for m in ctl if bool(ids[m]["arms"]["qemu"]["detect_p0"]) == bool(ids[m]["arms"]["board"]["detect_p0"])]
    lb = wilson(len(agree), len(ctl))
    out["H1"] = dict(n=len(ctl), agree=len(agree), rate=(len(agree) / len(ctl)) if ctl else None, wilson95=lb,
                     disagreements=sorted(set(ctl) - set(agree)), supported=bool(ctl) and lb[0] is not None and lb[0] >= 0.95)

    for s in subjects:
        for fam in ("ALU", "DIV"):
            spec = json.loads((E5 / "protocol" / f"e5_mutants_{s}.json").read_text())
            lvl = {m["id"]: m.get("level") for m in spec["mutants"]}
            lad = sorted((m for m, v in ids.items() if v["subject"] == s and v["family"] == fam),
                         key=lambda m: lvl.get(m) or 0)
            if not lad:
                continue
            fq = sorted(lvl[m] for m in lad if det(m, "qemu"))
            fb = sorted(lvl[m] for m in lad if det(m, "board"))
            ran = [m for m in lad if det(m, "qemu") is not None and det(m, "board") is not None]
            out["H4"][f"{s}:{fam}"] = dict(levels=sorted(lvl[m] for m in lad), ran=len(ran), qemu_flags=fq,
                                           board_flags=fb, equal=fq == fb,
                                           st_max={m: {a: ids[m]["arms"][a].get("st_max") for a in ("qemu", "board")
                                                       if a in ids[m]["arms"]} for m in lad})
    p = E5 / "results" / "e5_analysis.json"
    p.write_text(json.dumps(out, indent=1))
    print(json.dumps({k: out[k] for k in ("sets", "H1", "H2", "H3")}, indent=1)[:6000])
    for k, v in out["H4"].items():
        print(k, "qemu", v["qemu_flags"], "board", v["board_flags"], "equal", v["equal"])


if __name__ == "__main__":
    main(sys.argv[1:] or ["soc", "fuel", "bess"])
