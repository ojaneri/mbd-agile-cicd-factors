"""Print the median [CI] table of the tiered replay. Usage: python tiersum.py <..._tiered.json>"""
import json
import sys

r = json.load(open(sys.argv[1]))
for k, v in r["summary"].items():
    print(k.ljust(16), " ".join(f"{m}={v[m][0]:.4g}[{v[m][1]:.4g},{v[m][2]:.4g}]" for m in v))
