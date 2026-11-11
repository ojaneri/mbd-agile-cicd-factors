"""Open (or stop) one FIT IoT-LAB reservation for E5b on ONE node of the given board, recorded in
results/e5b/session_<board>.json.  Usage (WSL): python e5b_open.py <iotnode|nrf52840> <minutes> <elf> | stop <board>"""
import importlib.util
import json
import pathlib
import sys

E5 = pathlib.Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("pil_iotlab", E5.parent / "soc" / "pil_iotlab.py")
iot = importlib.util.module_from_spec(spec)
spec.loader.exec_module(iot)
ARCHI = {"iotnode": "st-iotnode", "nrf52840": "nrf52840dk"}

if sys.argv[1] == "stop":
    s = json.loads((E5 / "results" / "e5b" / f"session_{sys.argv[2]}.json").read_text())
    iot.ARCHI = s["archi"]
    print(iot.stop(s["exp"]))
    sys.exit(0)
board, minutes, elf = sys.argv[1], int(sys.argv[2]), sys.argv[3]
iot.ARCHI = ARCHI[board]
nodes = iot.alive_nodes()
if not nodes:
    raise SystemExit(f"no alive {iot.ARCHI} at {iot.SITE}")
node = nodes[0]
exp = iot.submit(elf, node, minutes, name=f"cicd-e5b-{board}")
path = E5 / "results" / "e5b" / f"session_{board}.json"
path.parent.mkdir(parents=True, exist_ok=True)
path.write_text(json.dumps(dict(exp=exp, node=node, site=iot.SITE, archi=iot.ARCHI, minutes=minutes), indent=1))
print(json.dumps(dict(exp=exp, node=node, alive=nodes[:10])))
