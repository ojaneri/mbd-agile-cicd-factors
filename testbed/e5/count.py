"""Count E5 records per subject, arm and validity. Usage: python count.py"""
import collections
import json
import pathlib

E5 = pathlib.Path(__file__).resolve().parent
for p in sorted((E5 / "results").glob("e5_*.jsonl")):
    c = collections.Counter()
    for line in p.read_text().splitlines():
        if line.strip():
            r = json.loads(line)
            c[(r["family"], r["arm"], r.get("valid"))] += 1
    print(p.name, dict(sorted(c.items())))
