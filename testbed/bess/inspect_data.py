"""Exploration of the BESS temperature dataset (provenance only; not a pipeline stage)."""
import hashlib
import sys

import numpy as np
import pandas as pd

P = "/mnt/d/artigos/genai-mbd-exp/data_besstemp/dataset.csv"
print("sha256", hashlib.sha256(open(P, "rb").read()).hexdigest())
d = pd.read_csv(P); d["timestamp"] = pd.to_datetime(d["timestamp"], format="ISO8601")
print(d.shape, d.dtypes.to_dict())
print(d.describe().T)
d["month"] = d.segment_file.str[:6]
d["rack"] = d.segment_file.str.extract(r"_R(\d+)$")[0]
print(d.groupby("month").agg(rows=("CURRENT", "size"), segs=("segment_id", "nunique"),
                             tc_mean=("TCELL", "mean"), tc_max=("TCELL", "max"), tr_max=("TREF", "max"),
                             i_absmax=("CURRENT", lambda x: x.abs().max())))
print(d.groupby("rack").size())
seg = d.groupby("segment_file").agg(n=("CURRENT", "size"))
print("segment length quantiles", seg.n.quantile([0, .1, .5, .9, 1]).to_dict())
dt = d.groupby("segment_file").timestamp.diff().dt.total_seconds().dropna()
print("dt values", dt.value_counts().head(8).to_dict())
print("TCELL-TREF quantiles", (d.TCELL - d.TREF).quantile([0, .01, .5, .99, 1]).to_dict())
print("TCELL quantiles", d.TCELL.quantile([.5, .9, .99, .999, 1]).to_dict())
print("TCELL unique step", np.unique(np.round(np.diff(np.sort(d.TCELL.unique())), 4))[:10])
print("NaN", d.isna().sum().to_dict())
