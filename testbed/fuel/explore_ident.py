import pandas as pd, numpy as np
D="/mnt/d/artigos/genai-mbd-exp/data/"
r=pd.read_csv(D+"refueling_history.csv").set_index("Segment_id")["Refueling"]
d=pd.read_csv(D+"dataset.csv", usecols=["timestamp","RPM","THROTTLE_POS","MAF","SHORT_FUEL_TRIM_1","LONG_FUEL_TRIM_1","segment_id","segment_file"], parse_dates=["timestamp"])
d=d[d.segment_id.between(8,22)].sort_values(["segment_id","timestamp"]).copy()
print("throttle at rpm<900 quantiles", d[d.RPM<900].THROTTLE_POS.quantile([.05,.5,.95]).round(2).tolist())
print("throttle at rpm>1500 quantiles", d[d.RPM>1500].THROTTLE_POS.quantile([.01,.05,.1,.5]).round(2).tolist())
d["dt"]=d.groupby("segment_id").timestamp.diff().dt.total_seconds().fillna(0).clip(upper=5.0)
st=d.SHORT_FUEL_TRIM_1.fillna(0); lt=d.LONG_FUEL_TRIM_1.fillna(0)
base=d.MAF*60/(14.7*0.745)*(1+(st+lt)/100)   # ml/min, k=1
for name,cut in [("noDFCO",np.zeros(len(d),bool))]+[(f"DFCO thr<={t} rpm>{rp}",(d.THROTTLE_POS<=t)&(d.RPM>rp)) for t in (21.0,22.0,23.0,24.0) for rp in (1300,1600,2000)]:
    rate=np.where(cut,0,base); vol=(rate*d.dt/60).groupby(d.segment_id).sum()/1000  # litres
    tr=[s for s in range(8,18)]; te=list(range(18,23))
    k=float((vol[tr]*r[tr]).sum()/(vol[tr]**2).sum())
    etr=(k*vol[tr]-r[tr])/r[tr]*100; ete=(k*vol[te]-r[te])/r[te]*100
    print(f"{name:25s} cut%={cut.mean()*100:5.2f} k={k:.4f} train rel err mean|.|={etr.abs().mean():.2f}% max={etr.abs().max():.2f}%  held-out " + " ".join(f"{s}:{e:+.2f}" for s,e in ete.items()))
