"""Exploratory, post hoc (virtual review r1, VR-K-03): split E1 detection by test suite x execution level.

Factor A of E1 changes the test suite and the execution level together (UNIT = hand-written unit tests on
host C; MIL/SIL/PIL = requirement vectors on model / host C / target, plus back-to-back checks). This script
re-reads the frozen E1 records unchanged and reports, for the field-relevant mutants, which suite caught each
mutant at which level, so the gain of a stage can be separated from the gain of the suite.

Inputs: testbed/{soc,fuel}/results/e1_qemu.jsonl (unit, mil, sil, field), e1_pil_iotnode.jsonl (board PIL).
Output: testbed/e1_decompose.json. No run, no new data: a re-analysis of existing records.
"""
import json
import pathlib

ROOT = pathlib.Path(__file__).parent


def req_fail(fails):
    """Requirement-test failures only (drop back-to-back and timing entries)."""
    return [f for f in fails if not f.startswith("B2B") and "timing" not in f]


def b2b_fail(fails):
    return [f for f in fails if f.startswith("B2B")]


out = {}
for s in ("soc", "fuel"):
    recs = [json.loads(l) for l in open(ROOT / s / "results" / "e1_qemu.jsonl")]
    board = {}
    for l in open(ROOT / s / "results" / "e1_pil_iotnode.jsonl"):
        r = json.loads(l)
        board[r["id"]] = r
    live = [r for r in recs if not r.get("stillborn")]
    rel = [r for r in live if r["field"]["fail"]]
    arms = {}
    for r in rel:
        bf = board[r["id"]]["eval"]["fails"] if r["id"] in board else []
        arms[r["id"]] = {
            "level": r["level"],
            "unit_suite@host": not r["unit"]["passed"],
            "req@model (MIL)": bool(req_fail(r["mil"]["fails"])),
            "req@host (SIL)": bool(req_fail(r["sil"]["fails"])),
            "b2b host-vs-model": bool(b2b_fail(r["sil"]["fails"])),
            "req@board (PIL)": bool(req_fail(bf)),
        }
    keys = list(next(iter(arms.values())).keys())[1:]
    tab = {}
    for lev in ("all", "model", "code"):
        sub = [a for a in arms.values() if lev == "all" or a["level"] == lev]
        tab[lev] = {"n": len(sub), **{k: sum(a[k] for a in sub) for k in keys}}
    # what the unit suite misses that a requirement test catches, at the same level (host C)
    tab["unit_missed_req_host_caught"] = sum(
        1 for a in arms.values() if not a["unit_suite@host"] and a["req@host (SIL)"])
    tab["req_host_missed"] = sum(1 for a in arms.values() if not a["req@host (SIL)"])
    out[s] = tab
    print(s, json.dumps(tab, indent=1))

(ROOT / "e1_decompose.json").write_text(json.dumps(out, indent=1))
