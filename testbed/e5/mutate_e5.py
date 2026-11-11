"""E5 mutant generator (frozen before any E5 run). Runs on one subject's baseline C file.

Families (exhaustive, mechanical):
  INIT  delete each assignment `p->field = ...;` inside the subject's *_init function
        (subjects 1-2: these repeat E1 SDL mutants and are flagged seen=True; subject 3: unseen).
  LUD   local uninitialised declaration: for each local declaration with an initialiser
        `float x = expr;` (also int/uint32_t/double) anywhere in the file, drop the initialiser.
        New in E5 for every subject (seen=False).
  ALU / DIV  graded timing regressions at the top of the step function: E5_LOAD_ALU(n) / E5_LOAD_DIV(n)
        with n = round(f * B) and round(f * B / 14), f in LEVELS, B = baseline max SysTick cycles per
        step on the real board (E5 calibration). Generated only after the board calibration exists.
Usage: python mutate_e5.py <subject> <baseline_c> <step_function> [board_baseline_cycles]
Writes protocol/e5_mutants_<subject>.json
"""
import hashlib
import json
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent
LEVELS = (0.25, 0.5, 0.9, 1.1, 1.5, 3.0)
DIV_CYCLES = 14
DECL = re.compile(r"^(\s*)(float|double|int|uint32_t)\s+(\w+)\s*=\s*(.+);\s*$")
BARE = re.compile(r"^(\s+)(float|double|int|uint32_t)\s+(\w+);\s*$")
ASSIGN = re.compile(r"^(\s*)\w+->\w+\s*=.*;\s*$")


def func_span(lines, pattern):
    """(start, end) line indices of the first function whose header matches pattern (brace matching)."""
    for i, ln in enumerate(lines):
        if re.match(pattern, ln):
            depth, j = 0, i
            while j < len(lines):
                depth += lines[j].count("{") - lines[j].count("}")
                if depth == 0 and "{" in "".join(lines[i:j + 1]):
                    return i, j
                j += 1
    raise ValueError(pattern)


def generate(subject, c_text, step_fn, board_b=None, seen_init=False):
    lines = c_text.split("\n")
    muts = []

    def add(fam, idx, new_lines, desc, seen):
        mid = f"E5-{subject.upper()}-{fam}-{sum(m['family'] == fam for m in muts) + 1:02d}"
        text = "\n".join(new_lines)
        muts.append(dict(id=mid, family=fam, line=idx + 1, desc=desc, seen=seen,
                         sha256=hashlib.sha256(text.encode()).hexdigest(), c=text))

    a, b = func_span(lines, r"^void \w+_init\(")
    for i in range(a + 1, b):
        if ASSIGN.match(lines[i]):
            nl = list(lines)
            nl[i] = re.match(r"^(\s*)", lines[i]).group(1) + ";"
            add("INIT", i, nl, f"L{i + 1} delete '{lines[i].strip()}'", seen_init)
    for i, ln in enumerate(lines):
        m = DECL.match(ln)
        if m and not ln.strip().startswith("for"):
            nl = list(lines)
            nl[i] = f"{m.group(1)}{m.group(2)} {m.group(3)};"
            add("LUD", i, nl, f"L{i + 1} '{ln.strip()}' -> '{m.group(2)} {m.group(3)};'", False)
        # declared without initialiser and assigned later (subject 3's style): delete the first assignment
        m2 = BARE.match(ln)
        if m2:
            var = m2.group(3)
            for j in range(i + 1, len(lines)):
                if re.match(rf"^\s*{var}\s*=[^=].*;\s*$", lines[j]):
                    nl = list(lines)
                    nl[j] = re.match(r"^(\s*)", lines[j]).group(1) + ";"
                    add("LUD", j, nl, f"L{j + 1} first assignment of '{var}' deleted: '{lines[j].strip()}'", False)
                    break
                if lines[j].startswith("}"):
                    break
    if board_b:
        s, _ = func_span(lines, rf"^\w[\w\s\*]*\b{step_fn}\(")
        brace = s if "{" in lines[s] else s + 1
        for fam, per in (("ALU", 1), ("DIV", DIV_CYCLES)):
            for f in LEVELS:
                n = max(1, round(f * board_b / per))
                nl = list(lines)
                nl.insert(brace + 1, f"    E5_LOAD_{fam}({n});")
                nl.insert(0, '#include "e5_load.h"')
                add(fam, brace, nl, f"+{f:g} x baseline cycles ({fam} n={n}, B={board_b})", False)
                muts[-1]["level"] = f
                muts[-1]["n"] = n
    return muts


def main():
    subject, cpath, step_fn = sys.argv[1], pathlib.Path(sys.argv[2]), sys.argv[3]
    board_b = int(sys.argv[4]) if len(sys.argv) > 4 else None
    muts = generate(subject, cpath.read_text(), step_fn, board_b, seen_init=subject in ("soc", "fuel"))
    # Mutants whose C text was already exercised (e.g. a development smoke test) are marked seen.
    import os
    # E5_SEEN_E1=<E1 mutants.json>:<id>,<id>  marks E5 mutants that delete the same line as those E1 SDL mutants.
    spec_seen = os.environ.get("E5_SEEN_E1")
    if spec_seen:
        path, ids = spec_seen.rsplit(":", 1)
        e1 = json.loads(pathlib.Path(path).read_text())
        e1m = [m for k in ("model", "code") for m in e1.get(k, [])] if isinstance(e1, dict) else e1
        for m1 in e1m:
            if m1["id"] in ids.split(","):
                ln = int(re.match(r"L(\d+)", m1["desc"]).group(1))
                for m in muts:
                    if m["line"] == ln and m["family"] in ("INIT", "LUD"):
                        m["seen"] = True
                        m["seen_reason"] = f"same line as E1 {m1['id']} ({m1['desc']}), run in a smoke test"
    out = HERE / "protocol" / f"e5_mutants_{subject}.json"
    out.write_text(json.dumps(dict(subject=subject, baseline_sha256=hashlib.sha256(cpath.read_bytes()).hexdigest(),
                                   board_baseline_cycles=board_b, mutants=muts), indent=1))
    fams = {}
    for m in muts:
        fams[m["family"]] = fams.get(m["family"], 0) + 1
    print(subject, fams)
    for m in muts:
        print(" ", m["id"], m["desc"])


if __name__ == "__main__":
    main()
