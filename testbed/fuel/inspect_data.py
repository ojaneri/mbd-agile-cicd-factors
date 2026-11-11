import hashlib, pandas as pd, numpy as np
D="/mnt/d/artigos/genai-mbd-exp/data/"
for f in ("dataset.csv","refueling_history.csv"):
    print(f, hashlib.sha256(open(D+f,"rb").read()).hexdigest())
r=pd.read_csv(D+"refueling_history.csv"); print(r[["Lp","Segment_id","Trapez_l","Refueling","Total_km"]].to_string())
d=pd.read_csv(D+"dataset.csv", usecols=["timestamp","RPM","SPEED","THROTTLE_POS","MAF","SHORT_FUEL_TRIM_1","LONG_FUEL_TRIM_1","segment_id","segment_file"], parse_dates=["timestamp"])
print(len(d)); print(d.isna().mean().round(3).to_string())
d=d.sort_values(["segment_id","timestamp"])
for sid,g in d.groupby("segment_id"):
    dt=g.timestamp.diff().dt.total_seconds().iloc[1:]
    print(sid, len(g), g.segment_file.nunique(), "dt med %.3f p95 %.3f max %.0f  n>5s %d"%(dt.median(), dt.quantile(.95), dt.max(), (dt>5).sum()),
          "MAF nan %.3f STFT nan %.3f LTFT nan %.3f"%(g.MAF.isna().mean(), g.SHORT_FUEL_TRIM_1.isna().mean(), g.LONG_FUEL_TRIM_1.isna().mean()))
