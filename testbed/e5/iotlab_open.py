"""Open a FIT IoT-LAB reservation on ONE st-iotnode for E5 and record it in results/iotlab_session.json.
Usage (WSL): python iotlab_open.py <minutes> <firmware.elf>      (stop it with: python iotlab_open.py stop)"""
import importlib.util
import json
import pathlib
import sys

E5 = pathlib.Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("pil_iotlab", E5.parent / "soc" / "pil_iotlab.py")
iot = importlib.util.module_from_spec(spec)
spec.loader.exec_module(iot)
SESSION = E5 / "results" / "iotlab_session.json"

if sys.argv[1] == "stop":
    s = json.loads(SESSION.read_text())
    print(iot.stop(s["exp"]))
    sys.exit(0)
minutes, elf = int(sys.argv[1]), sys.argv[2]
nodes = iot.alive_nodes()
if not nodes:
    raise SystemExit("no alive st-iotnode at " + iot.SITE)
node = nodes[0]
exp = iot.submit(elf, node, minutes, name="cicd-e5")
SESSION.write_text(json.dumps(dict(exp=exp, node=node, site=iot.SITE, archi=iot.ARCHI, minutes=minutes), indent=1))
print(json.dumps(dict(exp=exp, node=node, alive=nodes[:10])))
