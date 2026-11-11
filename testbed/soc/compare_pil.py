"""Compare real-target PIL verdicts with the QEMU development run, and recompute the E1 configurations
with the real PIL column (A3_real). Field relevance: the field verdict recorded with the real run when
present, else the QEMU one. Usage: python compare_pil.py <subject_dir> <board>
"""
import json
import math
import sys
from pathlib import Path


def wilson(k, n, z=1.96):
    if n == 0:
        return (0.0, 0.0)
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (round(c - h, 3), round(c + h, 3))


def mcnemar_exact(b, c):
    n = b + c
    if n == 0:
        return 1.0
    k = min(b, c)
    p = sum(math.comb(n, i) for i in range(k + 1)) / 2 ** n
    return min(1.0, 2 * p)


def main():
    root, board = Path(sys.argv[1]), sys.argv[2]
    q = {(r := json.loads(l))["id"]: r for l in (root / "results" / "e1_qemu.jsonl").read_text().splitlines()}
    real = {(r := json.loads(l))["id"]: r for l in (root / "results" / f"e1_pil_{board}.jsonl").read_text().splitlines()}
    live = [i for i, r in q.items() if not r.get("stillborn")]
    missing = [i for i in live if i not in real]
    invalid = [i for i in live if i in real and not real[i].get("eval", {}).get("valid")]
    both = [i for i in live if i in real and real[i]["eval"].get("valid")]

    def det(i, s):
        return not q[i][s]["passed"]

    def det_real(i):
        return not real[i]["eval"]["passed"]

    def field_fail(i):
        f = real[i]["eval"].get("field") or q[i].get("field", {})
        return bool(f.get("fail"))

    agree = sum(det(i, "pil") == det_real(i) for i in both)
    disagree = [dict(id=i, qemu_fail=det(i, "pil"), real_fail=det_real(i),
                     qemu_fails=q[i]["pil"]["fails"][:3], real_fails=real[i]["eval"]["fails"][:3]) for i in both
                if det(i, "pil") != det_real(i)]
    field_disagree = [i for i in both if bool(q[i].get("field", {}).get("fail")) != field_fail(i)]

    fr = [i for i in both if field_fail(i)]
    cfg = {
        "A0": lambda i: det(i, "unit"),
        "A1": lambda i: det(i, "unit") or det(i, "mil"),
        "A2": lambda i: det(i, "unit") or det(i, "mil") or det(i, "sil"),
        "A3_qemu": lambda i: det(i, "unit") or det(i, "mil") or det(i, "sil") or det(i, "pil"),
        "A3_real": lambda i: det(i, "unit") or det(i, "mil") or det(i, "sil") or det_real(i),
    }
    rates = {}
    for k, f in cfg.items():
        n = sum(f(i) for i in fr)
        rates[k] = dict(detected=n, of=len(fr), rate=round(n / len(fr), 3) if fr else None, wilson95=wilson(n, len(fr)))
    b = sum(cfg["A3_real"](i) and not cfg["A2"](i) for i in fr)
    c = sum(cfg["A2"](i) and not cfg["A3_real"](i) for i in fr)
    pil_only_real = [i for i in both if det_real(i) and not any(det(i, s) for s in ("unit", "mil", "sil"))]
    timing_only_real = [i for i in pil_only_real if all("timing" in x for x in real[i]["eval"]["fails"])]
    cyc = [real[i]["eval"]["max_cycles"] for i in both]
    out = dict(board=board, live=len(live), compared=len(both), missing=missing, invalid=invalid,
               pil_verdict_agreement=f"{agree}/{len(both)}", disagreements=disagree,
               field_verdict_disagreements=field_disagree, field_relevant=len(fr), configs=rates,
               mcnemar_A2_to_A3real=dict(gained=b, lost=c, p=mcnemar_exact(b, c)),
               pil_only_real=pil_only_real, timing_only_real=timing_only_real,
               max_cycles_range=[min(cyc), max(cyc)] if cyc else None)
    p = root / "results" / f"e1_pil_{board}_vs_qemu.json"
    p.write_text(json.dumps(out, indent=1))
    print(json.dumps({k: v for k, v in out.items() if k != "disagreements"}, indent=1))
    for d in disagree:
        print(json.dumps(d))


if __name__ == "__main__":
    main()
