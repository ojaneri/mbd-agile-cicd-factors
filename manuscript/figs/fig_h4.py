"""Fig. H4: timing ladders, step maximum relative to each platform's own budget (2x its baseline).

Reads testbed/e5/results/e5_analysis.json (H4 st_max per ladder level) and
testbed/e5/protocol/calibration_<subject>.json (budgets). Writes manuscript/figs/fig_h4.pdf.
Board values are SysTick cycles; QEMU values are SysTick ticks under -icount (an instruction proxy).
Run: wsl -- /root/venvs/cicd/bin/python /mnt/d/artigos/CICD/manuscript/figs/fig_h4.py
"""
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[2]
E5 = ROOT / "testbed" / "e5"
H4 = json.loads((E5 / "results" / "e5_analysis.json").read_text())["H4"]
SUBJ = [("soc", "S1", "o"), ("fuel", "S2", "s"), ("bess", "S3", "^")]

plt.rcParams.update({"font.family": "serif", "font.size": 7, "axes.linewidth": 0.6,
                     "pdf.fonttype": 42, "lines.linewidth": 0.9, "lines.markersize": 3})
fig, axes = plt.subplots(1, 2, figsize=(3.5, 1.65), sharey=True)
for ax, fam, title in zip(axes, ("ALU", "DIV"), ("ALU: 1-cycle instr.", "DIV: 14-cycle instr.")):
    for s, lab, mk in SUBJ:
        cal = json.loads((E5 / "protocol" / f"calibration_{s}.json").read_text())
        h = H4[f"{s}:{fam}"]
        lv = h["levels"]
        # analyze_e5.py writes st_max in ladder order (sorted by level), the same order as "levels".
        st = list(h["st_max"].values())
        assert len(st) == len(lv)
        b = [x["board"] / cal["board_budget"] for x in st]
        q = [x["qemu"] / cal["qemu_budget"] for x in st]
        ax.plot(lv, b, "-", marker=mk, color="0.1", label=f"{lab} board")
        ax.plot(lv, q, "--", marker=mk, color="0.55", mfc="white", label=f"{lab} QEMU")
    ax.axhline(1.0, color="0.3", lw=0.6, ls=":")
    ax.set_xscale("log")
    ax.set_xticks([0.25, 0.5, 0.9, 1.5, 3.0])
    ax.set_xticklabels(["0.25", "0.5", "0.9", "1.5", "3"])
    ax.minorticks_off()
    ax.text(0.04, 0.96, title, transform=ax.transAxes, fontsize=6.5, va="top")
    ax.set_xlabel("added load / board baseline cycles", fontsize=6.5)
axes[0].set_ylabel("step max / own budget")
axes[0].text(0.26, 1.04, "budget", fontsize=6, color="0.3")
h, l = axes[0].get_legend_handles_labels()
fig.legend(h, l, ncol=3, fontsize=5.8, frameon=False, loc="upper center", bbox_to_anchor=(0.55, 1.17),
           handlelength=2.2, columnspacing=0.8)
fig.tight_layout(pad=0.2, w_pad=0.6)
out = Path(__file__).with_name("fig_h4.pdf")
fig.savefig(out, bbox_inches="tight")
print("wrote", out)
