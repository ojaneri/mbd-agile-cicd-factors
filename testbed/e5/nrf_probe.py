"""Probe the nRF52840 serial stream once (flash the smoke baseline, capture, print a summary). No result file."""
import importlib.util
import json
import pathlib

E5 = pathlib.Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("pil_iotlab", E5.parent / "soc" / "pil_iotlab.py")
iot = importlib.util.module_from_spec(spec)
spec.loader.exec_module(iot)
iot.ARCHI = "nrf52840dk"
s = json.loads((E5 / "results" / "e5b" / "session_nrf52840.json").read_text())
elf = pathlib.Path.home() / "cicd-work/e5b/nrf/host/smoke_baseline/e5_nrf52840.elf"
print("flash", iot.flash(s["exp"], s["node"], elf)[0])
out = pathlib.Path("/tmp/nrf_probe.txt")
rep = iot.capture(s["exp"], s["node"], out, run_timeout=150)
txt = out.read_text(errors="replace")
print(json.dumps({k: rep.get(k) for k in ("ok", "seconds_run", "bytes", "attempts", "error")}))
print("head:", txt[:300].replace("\n", " | "))
print("S lines:", [l for l in txt.splitlines() if l.startswith("@S")][:4])
