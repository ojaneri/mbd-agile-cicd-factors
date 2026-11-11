"""E5b smoke test (baseline only, no mutant, no board): builds the nRF52840 ELF and runs the -O0/-Os
baseline under QEMU to check that the stream is complete and the oracles pass.
Usage (WSL): python e5b_smoke.py <subject> <O0|Os|nrf>"""
import json
import sys

subject, variant = sys.argv[1], sys.argv[2]
sys.argv = [sys.argv[0], subject, variant, "smoke"]
import e5b  # noqa: E402

R = e5b.R
tests, refs, names = R.tests_and_refs()
vdir = R.prepare("smoke_baseline", (R.BASE / f"{R.S['src']}.c").read_text(), "host")
ok, err = R.build_fw(vdir, 5)
elf = vdir / f"e5_{e5b.BOARD}.elf"
print("build", ok, err[-200:] if not ok else "", elf.stat().st_size if elf.exists() else None)
if ok and e5b.BOARD == "iotnode":
    rep = R.target_arm("qemu", vdir, tests, refs, names, 5, 1, None)
    print(json.dumps({k: rep.get(k) for k in ("valid", "detected", "st_max", "wall_s")}))
