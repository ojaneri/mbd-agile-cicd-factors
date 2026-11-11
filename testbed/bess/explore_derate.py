"""Exploration (provenance): is the derating exercised on train / field data with the baseline spec?"""
import json
import numpy as np
import common, ref

spec = common.load_spec(common.ROOT / "spec" / "baseline.json")
for name, segs in (("train-R5", common.load_segments(common.TRAIN_MONTHS, ["5"])),
                   ("field-R5", common.load_segments(common.FIELD_MONTHS, [common.FIELD_RACK]))):
    n = lat = latref = mis = 0
    for s in segs.values():
        rst = np.zeros(len(s["I"])); rst[0] = 1
        T, D = ref.run(spec, dict(rst=rst, I=s["I"], TREF=s["TREF"]))
        Dr = ref.derate_from_temp(spec, rst, s["TCELL"])
        n += len(D); lat += int(np.sum(D < 1)); latref += int(np.sum(Dr < 1)); mis += int(np.sum(np.abs(D - Dr) > 1e-9))
    print(name, "rows", n, "derated rows est", lat, "ref", latref, "mismatch frac", mis / n)
