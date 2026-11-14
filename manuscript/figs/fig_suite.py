"""Fig. suite: E1 field-relevant mutants caught by each test suite, split by mutant class (exploratory).

Reads testbed/e1_decompose.json (written by testbed/e1_decompose.py from the frozen E1 records; no new run).
Writes manuscript/figs/fig_suite.pdf. Bars: share caught, with the count "k/n" above each bar.
Run: wsl -- /root/venvs/cicd/bin/python /mnt/d/artigos/CICD/manuscript/figs/fig_suite.py
"""
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[2]
D = json.loads((ROOT / "testbed" / "e1_decompose.json").read_text())
SUBJ = [("soc", "S1"), ("fuel", "S2")]
ARMS = [("unit_suite@host", "Unit\n(host C)"), ("req@model (MIL)", "Req.\n(MIL)"),
        ("req@host (SIL)", "Req.\n(SIL)"), ("b2b host-vs-model", "B2B\nSIL/MIL")]
CLS = [("model", "model-level", "0.25", None), ("code", "code-level", "white", "////")]

plt.rcParams.update({"font.family": "serif", "font.size": 7, "axes.linewidth": 0.6,
                     "pdf.fonttype": 42, "hatch.linewidth": 0.5})
fig, axes = plt.subplots(1, 2, figsize=(3.5, 1.55), sharey=True)
w = 0.38
for ax, (s, lab) in zip(axes, SUBJ):
    for j, (cls, cname, col, hatch) in enumerate(CLS):
        n = D[s][cls]["n"]
        for i, (key, _) in enumerate(ARMS):
            k = D[s][cls][key]
            x = i + (j - 0.5) * w
            ax.bar(x, 100 * k / n, w, color=col, edgecolor="0.1", lw=0.5, hatch=hatch,
                   label=f"{cname}" if i == 0 else None)
            ax.text(x, 100 * k / n + 2, f"{k}/{n}", ha="center", va="bottom", fontsize=4.6, rotation=90)
    ax.set_xticks(range(len(ARMS)))
    ax.set_xticklabels([a[1] for a in ARMS], fontsize=6)
    ax.set_ylim(0, 128)
    ax.set_yticks([0, 50, 100])
    ax.tick_params(length=2, pad=1.5)
    ax.text(0.02, 0.97, lab, transform=ax.transAxes, fontsize=7, va="top", fontweight="bold")
    for sp in ("top", "right"):
        ax.spines[sp].set_visible(False)
axes[0].set_ylabel("caught (%)")
h, l = axes[0].get_legend_handles_labels()
fig.legend(h, l, ncol=2, fontsize=6, frameon=False, loc="upper center", bbox_to_anchor=(0.55, 1.08),
           handlelength=1.6, columnspacing=1.2)
fig.tight_layout(pad=0.2, w_pad=0.5)
out = Path(__file__).with_name("fig_suite.pdf")
fig.savefig(out, bbox_inches="tight")
print("wrote", out)
