"""Shared constants and data access for subject 1 (SoC observer, LG HG2 data).

Data: processed 1 s LG HG2 cycles produced by genai-mbd-exp/code/convert_lghg2.py from
Mendeley Data doi 10.17632/cp3473x7xv.3 (CC BY 4.0). SOC reference = 1 + Ah/3.0 (lab charge counting).
Current sign in the data: negative = discharge.
"""
import hashlib
import json
import pathlib

import numpy as np
import pandas as pd

ROOT = pathlib.Path(__file__).resolve().parent
DATA = pathlib.Path("/mnt/d/artigos/genai-mbd-exp/data_lghg2/dataset.csv")
DATA_SHA256 = "2fd898df640fd93d410ea4774708a7ee81f8ac8392e72d90315a7db910e5228b"

# Fixed split (pre-registered): identification cycles vs held-out field oracle cycles, 25 degC only.
# 25degC_HWFET is excluded: only 601 rows of rest at full charge.
TRAIN = ["25degC_UDDS", "25degC_LA92", "25degC_US06",
         "25degC_Mixed1", "25degC_Mixed2", "25degC_Mixed3", "25degC_Mixed4"]
FIELD = ["25degC_Mixed5", "25degC_Mixed6", "25degC_Mixed7", "25degC_Mixed8"]

Q_AH = 3.0          # nominal capacity used by the SOC reference itself
DT = 1.0            # sample time of the processed data [s]
N_KNOTS = 11        # OCV table breakpoints, equally spaced in SoC


def check_data():
    h = hashlib.sha256(DATA.read_bytes()).hexdigest()
    if h != DATA_SHA256:
        raise SystemExit(f"dataset hash mismatch: {h}")
    return h


def load_cycles(names):
    d = pd.read_csv(DATA, usecols=["timestamp", "CURRENT", "VOLTAGE", "SOC", "segment_file"],
                    parse_dates=["timestamp"])
    out = {}
    for n in names:
        c = d[d.segment_file == n].sort_values("timestamp")
        t = (c.timestamp - c.timestamp.iloc[0]).dt.total_seconds().to_numpy()
        gaps = int(np.sum(np.diff(t) != 1.0))
        out[n] = dict(I=c.CURRENT.to_numpy(float), V=c.VOLTAGE.to_numpy(float),
                      SOC=c.SOC.to_numpy(float), gaps=gaps)
    return out


def load_spec(path):
    return json.loads(pathlib.Path(path).read_text())
