"""E5b analysis — normative decision rules, frozen with protocol/ADDENDUM-E5b.md BEFORE any E5b run.

R1 (optimisation level, -O0 and -Os, same ELF on QEMU and st-iotnode): over the INIT/LUD mutants detected by
   any arm at that level, zero mutants detected by the board and missed by QEMU (5 passes). Supported iff 0.
R2 (host tools vs optimisation): exploratory; report Valgrind and MemorySanitizer counterexamples (mutants a
   target detects and the tool misses) and median wall time per level.
R3 (timing noise, st-iotnode -O2, and nRF52840 calibration): per subject, spread = (max - min) / min of the
   10 baseline step maxima. Supported iff spread <= 0.05 for every subject on each board.
R4 (second board, nRF52840-DK, -O2):
   H1n  control mutants of subject 3: nRF pass-0 verdict equals E5's QEMU pass-0 verdict; Wilson 95 % lower
        bound >= 0.95.
   H2n  INIT/LUD mutants of all subjects: zero detected by the nRF board and missed by E5's QEMU arm.
   H4n  DIV ladder: in every subject the nRF board flags at least one level that QEMU does not flag.
        ALU ladder and the comparison with the st-iotnode flags: exploratory.
Usage: python analyze_e5b.py   (writes results/e5b/e5b_analysis.json)
"""
import json
import math
import pathlib
import statistics

E5 = pathlib.Path(__file__).resolve().parent
RB = E5 / "results" / "e5b"
SUBJECTS = ("soc", "fuel", "bess")


def wilson(k, n, z=1.959964):
    if n == 0:
        return [None, None]
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return [c - h, c + h]


def load(path):
    if not path.exists():
        return []
    return [json.loads(l) for l in path.read_text().splitlines() if l.strip()]


def by_id(recs):
    out = {}
    for r in recs:
        out.setdefault(r["id"], {})[r["arm"]] = r
    return out


def det(rec):
    if rec is None or not rec.get("valid"):
        return None
    return bool(rec.get("detected"))


def level(subject, mid):
    spec = json.loads((E5 / "protocol" / f"e5_mutants_{subject}.json").read_text())
    return {m["id"]: m.get("level") for m in spec["mutants"]}.get(mid)


def main():
    out = {"R1": {}, "R2": {}, "R3": {}, "R4": {}}
    for v in ("O0", "Os"):
        ids = {}
        for s in SUBJECTS:
            ids.update(by_id(load(RB / f"e5b_{s}_{v}.jsonl")))
        initlud = {m: a for m, a in ids.items() if a and next(iter(a.values())).get("family") in ("INIT", "LUD")}
        U = [m for m, a in initlud.items() if any(det(r) for r in a.values())]
        both = [m for m in U if det(initlud[m].get("qemu")) is not None and det(initlud[m].get("board")) is not None]
        board_only = sorted(m for m in both if det(initlud[m]["board"]) and not det(initlud[m]["qemu"]))
        qemu_only = sorted(m for m in both if det(initlud[m]["qemu"]) and not det(initlud[m]["board"]))
        out["R1"][v] = dict(n_mutants=len(initlud), observable=len(U), compared=len(both),
                            board_only=board_only, qemu_only=qemu_only,
                            detected={a: sum(bool(det(initlud[m].get(a))) for m in U)
                                      for a in ("host_sil", "host_poison", "host_valgrind", "host_msan", "qemu", "board")},
                            supported=bool(both) and not board_only)
        r2 = {}
        for tool in ("host_valgrind", "host_msan"):
            ce = sorted(m for m in U if (det(initlud[m].get("qemu")) or det(initlud[m].get("board")))
                        and det(initlud[m].get(tool)) is False)
            walls = [initlud[m][tool]["wall_s"] for m in initlud if tool in initlud[m] and initlud[m][tool].get("valid")]
            r2[tool] = dict(counterexamples=ce, median_wall_s=statistics.median(walls) if walls else None)
        qw = [initlud[m]["qemu"]["wall_s"] for m in initlud if "qemu" in initlud[m]]
        r2["qemu_median_wall_s"] = statistics.median(qw) if qw else None
        out["R2"][v] = r2

    for board, pat in (("iotnode", "noise_{s}_iotnode.json"), ("nrf52840", "calibration_{s}_nrf.json")):
        res = {}
        for s in SUBJECTS:
            p = RB / pat.format(s=s)
            if not p.exists():
                continue
            c = json.loads(p.read_text())
            st = [x for x in c.get("board_st_max_reps", []) if x is not None]
            dw = [x for x in c.get("board_dw_max_reps", []) if x is not None]
            res[s] = dict(n=len(st), clean=c.get("clean", {}).get("board"), st_min=min(st, default=None),
                          st_max=max(st, default=None), dw_min=min(dw, default=None), dw_max=max(dw, default=None),
                          spread=(max(st) - min(st)) / min(st) if st else None)
        res["supported"] = bool(res) and all(v["spread"] is not None and v["spread"] <= 0.05 and v["n"] == 10
                                             for k, v in res.items() if k != "supported")
        out["R3"][board] = res

    e5 = {}
    for s in SUBJECTS:
        e5.update(by_id(load(E5 / "results" / f"e5_{s}.jsonl")))
    nrf = {}
    for s in SUBJECTS:
        nrf.update(by_id(load(RB / f"e5b_{s}_nrf.jsonl")))
    ctl = [m for m, a in nrf.items() if a.get("board", {}).get("family") == "CONTROL"
           and det(a.get("board")) is not None and det(e5.get(m, {}).get("qemu")) is not None]
    agree = [m for m in ctl if bool(nrf[m]["board"]["detect_p0"]) == bool(e5[m]["qemu"]["detect_p0"])]
    lb = wilson(len(agree), len(ctl))
    out["R4"]["H1n"] = dict(n=len(ctl), agree=len(agree), wilson95=lb, disagreements=sorted(set(ctl) - set(agree)),
                            supported=bool(ctl) and lb[0] is not None and lb[0] >= 0.95)
    il = [m for m, a in nrf.items() if a.get("board", {}).get("family") in ("INIT", "LUD")
          and det(a.get("board")) is not None and det(e5.get(m, {}).get("qemu")) is not None]
    nrf_only = sorted(m for m in il if det(nrf[m]["board"]) and not det(e5[m]["qemu"]))
    q_only = sorted(m for m in il if det(e5[m]["qemu"]) and not det(nrf[m]["board"]))
    vs_iot = sorted(m for m in il if det(e5[m].get("board")) is not None and det(nrf[m]["board"]) != det(e5[m]["board"]))
    out["R4"]["H2n"] = dict(n=len(il), nrf_detected=sum(bool(det(nrf[m]["board"])) for m in il),
                            nrf_only=nrf_only, qemu_only=q_only, differs_from_iotnode=vs_iot,
                            supported=bool(il) and not nrf_only)
    lad = {}
    h4 = []
    for s in SUBJECTS:
        for fam in ("ALU", "DIV"):
            ms = [m for m, a in nrf.items() if a.get("board", {}).get("family") == fam and a["board"].get("subject") == s]
            if not ms:
                continue
            fn = sorted(level(s, m) for m in ms if det(nrf[m]["board"]))
            fq = sorted(level(s, m) for m in ms if det(e5.get(m, {}).get("qemu")))
            fb = sorted(level(s, m) for m in ms if det(e5.get(m, {}).get("board")))
            lad[f"{s}:{fam}"] = dict(nrf_flags=fn, qemu_flags=fq, iotnode_flags=fb,
                                     st_max={m: nrf[m]["board"].get("st_max") for m in sorted(ms, key=lambda x: level(s, x) or 0)})
            if fam == "DIV":
                h4.append(bool(set(fn) - set(fq)))
    out["R4"]["H4n"] = dict(ladders=lad, supported=bool(h4) and all(h4) and len(h4) == len(SUBJECTS))
    (RB / "e5b_analysis.json").write_text(json.dumps(out, indent=1))
    print(json.dumps(out, indent=1)[:5000])


if __name__ == "__main__":
    main()
