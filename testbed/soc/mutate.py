"""Mutant generation for subject 1 (operators fixed before any run; applied exhaustively to every site).

Model level (applied to the spec, so they reach both the model and the generated code):
  MP   parameter x0.5 and x2 for R0, R1, tau, Q, L, L_rest                       (12)
  MS   sign flip of each signed term s_id, s_cc, s_r0, s_v1, s_corr               (5)
  MK   OCV knot shift +-0.05 V, every knot                                          (22)
  MSAT saturation removed                                                           (1)
  MDT  integrator sample-time mismatch dt_int x10 and x0.1                         (2)
  MRST rest logic: rest_ms x0.5, x2; rest_i x0.1, x10                              (4)
Code level (applied to the generated baseline soc_obs.c only; the model is untouched):
  AOR  arithmetic operator swap at each binary site:  + <-> -,  * <-> /
  ROR  relational operator at each site: boundary shift (< <-> <=, > <-> >=) and negation
  SDL  deletion of each assignment statement to a state or local variable
  FPP  float-to-double promotion: expf->exp, fabsf->fabs, and each 'f'-suffixed literal in the
       hot path (soc_obs_ocv, soc_obs_step) made a double literal
  TW   integer type change: each 'int' token -> 'unsigned'
Usage: python mutate.py <baseline_spec.json> <baseline soc_obs.c> <out manifest.json>
"""
import copy
import json
import re
import sys

FUNCS = ("soc_obs_ocv", "soc_obs_ocv_inv", "soc_obs_init", "soc_obs_step")
HOT = ("soc_obs_ocv", "soc_obs_step")


def model_mutants(spec):
    out = []

    def add(mid, op, desc, fn):
        s = copy.deepcopy(spec)
        fn(s)
        s["version"] = mid
        out.append(dict(id=mid, level="model", op=op, desc=desc, spec=s))

    for p in ("R0", "R1", "tau", "Q", "L", "L_rest"):
        for f in (0.5, 2.0):
            add(f"MP-{p}-x{f}", "MP", f"{p} x{f}", lambda s, p=p, f=f: s["params"].__setitem__(p, s["params"][p] * f))
    for e in ("s_id", "s_cc", "s_r0", "s_v1", "s_corr"):
        add(f"MS-{e}", "MS", f"sign flip {e}", lambda s, e=e: s["eq"].__setitem__(e, -s["eq"][e]))
    for j in range(len(spec["params"]["knots"])):
        for d in (0.05, -0.05):
            add(f"MK-{j}-{'+' if d > 0 else '-'}", "MK", f"knot {j} {d:+.2f} V",
                lambda s, j=j, d=d: s["params"]["knots"].__setitem__(j, s["params"]["knots"][j] + d))
    add("MSAT", "MSAT", "saturation removed", lambda s: s["eq"].__setitem__("sat", False))
    for f in (10.0, 0.1):
        add(f"MDT-x{f}", "MDT", f"dt_int x{f}", lambda s, f=f: s["eq"].__setitem__("dt_int", s["eq"]["dt_int"] * f))
    for p, f in (("rest_ms", 0.5), ("rest_ms", 2.0), ("rest_i", 0.1), ("rest_i", 10.0)):
        add(f"MRST-{p}-x{f}", "MRST", f"{p} x{f}", lambda s, p=p, f=f: s["params"].__setitem__(p, s["params"][p] * f))
    return out


def _func_spans(lines):
    """Map line index -> function name for lines inside the bodies of FUNCS."""
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
        # AOR: binary operators written with surrounding spaces by the generator
        for m in re.finditer(r" ([+\-*/]) ", ln):
            rep = {"+": "-", "-": "+", "*": "/", "/": "*"}[m.group(1)]
            add("AOR", i, ln[:m.start(1)] + rep + ln[m.end(1):], f"'{m.group(1)}' -> '{rep}'")
        # ROR: relational operators in conditions
        for m in re.finditer(r" (<=|>=|<|>) ", ln):
            op = m.group(1)
            shift = {"<": "<=", "<=": "<", ">": ">=", ">=": ">"}[op]
            neg = {"<": ">=", "<=": ">", ">": "<=", ">=": "<"}[op]
            for rep, kind in ((shift, "boundary"), (neg, "negation")):
                add("ROR", i, ln[:m.start(1)] + rep + ln[m.end(1):], f"'{op}' -> '{rep}' ({kind})")
        # SDL: assignment statements to existing variables (not declarations, not returns)
        if re.match(r"^\s+(o->\w+|idx|lo|hi)\s*=\s*[^=].*;\s*$", ln):
            add("SDL", i, re.match(r"^(\s*)", ln).group(1) + ";", f"delete '{ln.strip()}'")
        # FPP: double promotion
        for fn, dn in (("expf(", "exp("), ("fabsf(", "fabs(")):
            if fn in ln:
                add("FPP", i, ln.replace(fn, dn, 1), f"{fn[:-1]} -> {dn[:-1]}")
        if owner[i] in HOT:
            for m in re.finditer(r"\b(\d+\.\d+)f\b", ln):
                add("FPP", i, ln[:m.start()] + m.group(1) + ln[m.end():], f"literal {m.group(0)} -> {m.group(1)}")
        # TW: integer type change
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
                                     for op in sorted({m["op"] for m in mm + cm})}}}
    json.dump(manifest, open(sys.argv[3], "w"), indent=1)
    print(json.dumps(manifest["counts"], indent=1))
    for m in cm:
        print(m["id"], m["desc"], "|", m["before"], "=>", m["after"])
