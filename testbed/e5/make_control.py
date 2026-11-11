"""Build the H1 control set for a subject from its E1 campaign (frozen rule, see protocol/README.md):
every live E1 mutant except deletions of assignments inside *_init and except mutants whose C text equals
an E5 mutant's. Usage (WSL): python make_control.py <subject> <subject_dir> <work_dir> <src_basename>
Writes protocol/e5_control_<subject>.json"""
import hashlib
import json
import pathlib
import re
import sys

E5 = pathlib.Path(__file__).resolve().parent
subject, sdir, work, src = sys.argv[1], pathlib.Path(sys.argv[2]), pathlib.Path(sys.argv[3]), sys.argv[4]
e1 = [json.loads(l) for l in (sdir / "results" / "e1_qemu.jsonl").read_text().splitlines() if l.strip()]
e5 = json.loads((E5 / "protocol" / f"e5_mutants_{subject}.json").read_text())
e5_sha = {m["sha256"] for m in e5["mutants"]}
keep, dropped = [], []
for r in e1:
    if r.get("stillborn"):
        continue
    if r["level"] == "code" and re.search(r"\w+_init: delete '", r.get("desc", "")):
        dropped.append((r["id"], "init deletion"))
        continue
    cp = work / "build" / "mut" / r["id"] / f"{src}.c"
    if not cp.exists():
        dropped.append((r["id"], "no C text"))
        continue
    if hashlib.sha256(cp.read_text().encode()).hexdigest() in e5_sha:
        dropped.append((r["id"], "same as an E5 mutant"))
        continue
    keep.append(dict(id=r["id"], op=r["op"], level=r["level"], desc=r.get("desc")))
(E5 / "protocol" / f"e5_control_{subject}.json").write_text(
    json.dumps(dict(subject=subject, mutants=keep, dropped=dropped), indent=1))
print(subject, "control", len(keep), "dropped", len(dropped))
