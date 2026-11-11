"""Shared constants and data access for subject 3 (BESS rack thermal virtual sensor with derating).

Data: Qu, J., "Dataset for: A Multi-Agent AI Framework for Explainable Battery System Maintenance",
Zenodo, doi 10.5281/zenodo.20094787, CC BY 4.0 (licence 'cc-by-4.0', access 'open', checked against the
Zenodo records API on 2026-11-11). Converted by genai-mbd-exp/code/convert_bess.py in 'temp' mode:
5 s grid, racks 1/5/9, TCELL = rack temperature sensor 109 (middle), TREF = mean of the other 7 rack
sensors (1, 28, 55, 82, 136, 163, 190), CURRENT [A] (charge > 0). Local dataset.csv: 2,264,252 rows,
1,332 segments (segment_file = <month>_Operation<k>_R<rack>), sha256 pinned below (equals the hash
pinned by genai-mbd-exp/code/prep_bess_temp.sh). dt = 5 s on every row; no NaN. TCELL is quantised to 1 degC.
Identification: months 2024-10 .. 2025-01, all three racks. Field (held-out): months 2025-02 .. 2025-05,
rack 5 only (to keep the field replay ~390k rows).
"""
import hashlib
import json
import pathlib

import numpy as np
import pandas as pd

ROOT = pathlib.Path(__file__).resolve().parent
DATA = pathlib.Path("/mnt/d/artigos/genai-mbd-exp/data_besstemp/dataset.csv")
DATA_SHA256 = "7249bace12866f6f460e5553a229c9e18f061d15ca87e680cd709b613573b38e"
TRAIN_MONTHS = ("202410", "202411", "202412", "202501")
FIELD_MONTHS = ("202502", "202503", "202504", "202505")
FIELD_RACK = "5"


def check_data():
    got = hashlib.sha256(DATA.read_bytes()).hexdigest()
    if got != DATA_SHA256:
        raise SystemExit(f"hash mismatch {DATA}: {got}")


def load_segments(months, racks=None):
    """Per segment_file (in file order): dict(I, TREF, TCELL, month, rack) as float arrays."""
    d = pd.read_csv(DATA, usecols=["CURRENT", "TREF", "TCELL", "segment_file"])
    d["month"] = d.segment_file.str[:6]
    d["rack"] = d.segment_file.str.extract(r"_R(\d+)$")[0]
    d = d[d.month.isin(months)]
    if racks is not None:
        d = d[d.rack.isin(racks)]
    out = {}
    for sf, g in d.groupby("segment_file", sort=False):
        out[sf] = dict(I=g.CURRENT.to_numpy(float), TREF=g.TREF.to_numpy(float), TCELL=g.TCELL.to_numpy(float),
                       month=g.month.iloc[0], rack=g.rack.iloc[0])
    return out


def load_spec(path):
    return json.loads(pathlib.Path(path).read_text())
