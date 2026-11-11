"""Shared constants and data access for subject 2 (fuel-flow virtual sensor, Opel Corsa 2012).

Data: Kaggle pedro2025/obd2-panel-opel-2012, CC BY 4.0 (checked against the Kaggle API 2026-11-11).
Local copy used by genai-mbd-exp: 789,373 rows in dataset.csv (not 998k: that count is the latest
Kaggle upload; this file's hash equals the one pinned in genai-mbd-exp/code/DESKTOP.md).
Oracle: refuelling litres per tank (refueling_history.csv, Segment_id = tank).
Sampling: median dt ~1.15-1.23 s; gaps > 5 s occur only between trips (engine off) -> dt clamped.
"""
import hashlib
import json
import pathlib

import numpy as np
import pandas as pd

ROOT = pathlib.Path(__file__).resolve().parent
DATA = pathlib.Path("/mnt/d/artigos/genai-mbd-exp/data/dataset.csv")
REFUEL = pathlib.Path("/mnt/d/artigos/genai-mbd-exp/data/refueling_history.csv")
DATA_SHA256 = "27e6b070324dcf5b5600b73710be7763c4dada2e221b91e39128605132eee8b3"
REFUEL_SHA256 = "e0f70623872d730d6ac01cd7adb729a3ec72e43638df991658f3801fc835c70c"

TRAIN = list(range(8, 18))   # identification tanks (fixed, as in genai-mbd-exp)
FIELD = list(range(18, 23))  # held-out field-oracle tanks
COLS = ["RPM", "THROTTLE_POS", "MAF", "SHORT_FUEL_TRIM_1", "LONG_FUEL_TRIM_1"]


def check_data():
    for p, h in ((DATA, DATA_SHA256), (REFUEL, REFUEL_SHA256)):
        got = hashlib.sha256(p.read_bytes()).hexdigest()
        if got != h:
            raise SystemExit(f"hash mismatch {p}: {got}")


def refuel_litres():
    return pd.read_csv(REFUEL).set_index("Segment_id")["Refueling"].astype(float)


def load_tanks(ids):
    """Per tank: dt [s] (raw, unclamped; first row 0), MAF [g/s], RPM, THR [%], STFT, LTFT [%].
    NaN (<0.7 % of LTFT, <0.1 % of others in tanks 8-22) are replaced by 0 (documented)."""
    d = pd.read_csv(DATA, usecols=["timestamp", "segment_id"] + COLS, parse_dates=["timestamp"])
    d = d[d.segment_id.isin(ids)].sort_values(["segment_id", "timestamp"])
    out = {}
    for sid, g in d.groupby("segment_id"):
        dt = g.timestamp.diff().dt.total_seconds().fillna(0.0).to_numpy(float)
        f = lambda c: g[c].fillna(0.0).to_numpy(float)
        out[int(sid)] = dict(dt=dt, MAF=f("MAF"), RPM=f("RPM"), THR=f("THROTTLE_POS"),
                             STFT=f("SHORT_FUEL_TRIM_1"), LTFT=f("LONG_FUEL_TRIM_1"))
    return out


def load_spec(path):
    return json.loads(pathlib.Path(path).read_text())
