"""Compact view of results/e5b/e5b_analysis.json (run analyze_e5b.py first)."""
import json
import pathlib

a = json.loads((pathlib.Path(__file__).parent / "results" / "e5b" / "e5b_analysis.json").read_text())
print("R1", json.dumps(a["R1"], indent=0))
print("R2", json.dumps(a["R2"], indent=0))
print("R3", json.dumps(a["R3"], indent=0))
r = a["R4"]
print("H1n", {k: v for k, v in r["H1n"].items()})
print("H2n", r["H2n"])
print("H4n supported", r["H4n"]["supported"])
for k, v in r["H4n"]["ladders"].items():
    print(" ", k, "nrf", v["nrf_flags"], "qemu", v["qemu_flags"], "iotnode", v["iotnode_flags"], list(v["st_max"].values()))
