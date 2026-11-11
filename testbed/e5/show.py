"""Print a compact view of an E5 results file. Usage: python show.py <results.jsonl>"""
import json
import sys

KEYS = ("valid", "detected", "detect_oracle", "detect_tool", "differential", "detect_p0", "detect_paint",
        "differential_paint", "differential_any", "st_max", "dw_max")
for line in open(sys.argv[1]):
    r = json.loads(line)
    print(r["id"], r["arm"], round(r.get("wall_s", 0), 1), {k: r[k] for k in KEYS if k in r})
