"""Mutant generation for subject 2 (same operator classes as testbed/soc/mutate.py; fixed before any run,
applied exhaustively to every site).

Model level (applied to the spec, so they reach both the model and the generated code):
  MP   parameter x0.5 and x2 for k_cal, AFR, rho, dt_max, trim_lim, rate_max          (12)
  MS   sign flip of the signed terms s_trim, s_int                                     (2)
  MK   threshold shift (the lookup/breakpoint analogue here): thr_dfco +-2.0 %,
       rpm_dfco +-400 rpm                                                               (4)
  MSAT feature removed: rate saturation, trim clamp, DFCO                              (3)
  MDT  integrator time-scale mismatch dt_scale x10 and x0.1                            (2)
Code level (applied to the generated baseline fuel.c only):
  AOR, ROR, SDL, FPP, TW exactly as in subject 1 (TW finds no 'int' token in this code: 0 mutants).
Usage: python mutate.py <baseline_spec.json> <baseline fuel.c> <out manifest.json>
"""
import copy
import json
import re
import sys

FUNCS = ("fuel_init", "fuel_rate_of", "fuel_step")
HOT = ("fuel_rate_of", "fuel_step")


def model_mutants(spec):
    out = []

    def add(mid, op, desc, fn):
        s = copy.deepcopy(spec)
        fn(s)
        s["version"] = mid
        out.append(dict(id=mid, level="model", op=op, desc=desc, spec=s))

    for p in ("k_cal", "AFR", "rho", "dt_max", "trim_lim", "rate_max"):
        for f in (0.5, 2.0):
            add(f"MP-{p}-x{f}", "MP", f"{p} x{f}", lambda s, p=p, f=f: s["params"].__setitem__(p, s["params"][p] * f))
    for e in ("s_trim", "s_int"):
        add(f"MS-{e}", "MS", f"sign flip {e}", lambda s, e=e: s["eq"].__setitem__(e, -s["eq"][e]))
    for p, d in (("thr_dfco", 2.0), ("thr_dfco", -2.0), ("rpm_dfco", 400.0), ("rpm_dfco", -400.0)):
        add(f"MK-{p}-{'+' if d > 0 else '-'}", "MK", f"{p} {d:+g}",
            lambda s, p=p, d=d: s["params"].__setitem__(p, s["params"][p] + d))
    for flag in ("sat", "trim_clamp", "dfco"):
        add(f"MSAT-{flag}", "MSAT", f"{flag} removed", lambda s, flag=flag: s["eq"].__setitem__(flag, False))
    for f in (10.0, 0.1):
        add(f"MDT-x{f}", "MDT", f"dt_scale x{f}", lambda s, f=f: s["eq"].__setitem__("dt_scale", s["eq"]["dt_scale"] * f))
    return out


def _func_spans(lines):
    owner, cur, depth = {}, None, 0
    for i, ln in enumerate(lines):
        if cur is None:
            for f in FUNCS:
                if re.match(rf"^(float|void)\s+{f}\(", ln):
                    cur, depth = f, 0
        if cur is not None:
            depth += ln.count("{") - ln.count("}")
            owner[i] = cur
            if depth == 0 and "}" in ln:
                cur = None
    return owner


def code_mutants(c_text):
    lines = c_text.split("\n")
    owner = _func_spans(lines)
    out = []

    def add(op, i, new_line, desc):
        new = lines[:i] + [new_line] + lines[i + 1:]
        mid = f"{op}-{len([m for m in out if m['op'] == op]) + 1:03d}"
        out.append(dict(id=mid, level="code", op=op, desc=f"L{i + 1} {owner[i]}: {desc}",
                        line=i + 1, before=lines[i].strip(), after=new_line.strip(), c_text="\n".join(new)))

    for i, ln in enumerate(lines):
        if i not in owner or ln.strip().startswith(("//", "/*", "*")):
            continue
        for m in re.finditer(r" ([+\-*/]) ", ln):
            rep = {"+": "-", "-": "+", "*": "/", "/": "*"}[m.group(1)]
            add("AOR", i, ln[:m.start(1)] + rep + ln[m.end(1):], f"'{m.group(1)}' -> '{rep}'")
        for m in re.finditer(r" (<=|>=|<|>) ", ln):
            op = m.group(1)
            shift = {"<": "<=", "<=": "<", ">": ">=", ">=": ">"}[op]
            neg = {"<": ">=", "<=": ">", ">": "<=", ">=": "<"}[op]
            for rep, kind in ((shift, "boundary"), (neg, "negation")):
                add("ROR", i, ln[:m.start(1)] + rep + ln[m.end(1):], f"'{op}' -> '{rep}' ({kind})")
        if re.match(r"^\s+(f->\w+|trim|rate|dtc)\s*=\s*[^=].*;\s*$", ln):
            add("SDL", i, re.match(r"^(\s*)", ln).group(1) + ";", f"delete '{ln.strip()}'")
        for fn, dn in (("expf(", "exp("), ("fabsf(", "fabs(")):
            if fn in ln:
                add("FPP", i, ln.replace(fn, dn, 1), f"{fn[:-1]} -> {dn[:-1]}")
        if owner[i] in HOT:
            for m in re.finditer(r"\b(\d+\.\d+)f\b", ln):
                add("FPP", i, ln[:m.start()] + m.group(1) + ln[m.end():], f"literal {m.group(0)} -> {m.group(1)}")
        for m in re.finditer(r"\bint\b", ln):
            add("TW", i, ln[:m.start()] + "unsigned" + ln[m.end():], "'int' -> 'unsigned'")
    return out


if __name__ == "__main__":
    spec = json.load(open(sys.argv[1]))
    c_text = open(sys.argv[2]).read()
    mm, cm = model_mutants(spec), code_mutants(c_text)
    manifest = {"model": mm, "code": cm,
                "counts": {"model": len(mm), "code": len(cm),
                           "by_op": {op: sum(1 for m in mm + cm if m["op"] == op)
                                     for op in ("MP", "MS", "MK", "MSAT", "MDT", "AOR", "ROR", "SDL", "FPP", "TW")}}}
    json.dump(manifest, open(sys.argv[3], "w"), indent=1)
    print(json.dumps(manifest["counts"], indent=1))
    for m in cm:
        print(m["id"], m["desc"], "|", m["before"], "=>", m["after"])
