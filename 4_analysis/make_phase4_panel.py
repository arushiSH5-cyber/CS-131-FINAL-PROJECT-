#!/usr/bin/env python3
"""
Build figures/fig8_phase4_column.png — one portrait image for the Phase 4
column of the joint poster.

The six standalone figures are landscape and do not fit a narrow poster
column. This stacks the two charts that actually carry the answer, under a
strip of the three headline numbers, at roughly 4:5 so it drops into the
Canva column as a single image.

    python3 analysis.py && python3 make_phase4_panel.py
"""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.lines import Line2D

import analysis

HERE = Path(__file__).resolve().parent
FIG = HERE / "figures"

AI = "#D9463E"
GEN = "#3F6D9E"
GOLD = "#C9812A"
INK = "#1B2733"
MUTE = "#5A6270"
FLAG = "#B9BEC6"

plt.rcParams.update({
    "figure.dpi": 200, "savefig.dpi": 200, "savefig.bbox": "tight",
    "font.family": "DejaVu Sans", "font.size": 10,
    "axes.edgecolor": INK, "axes.labelcolor": INK,
    "axes.spines.top": False, "axes.spines.right": False,
    "text.color": INK, "xtick.color": INK, "ytick.color": INK,
    "grid.color": "#DCE0E5", "grid.linewidth": .7,
})

h = json.loads((HERE / "results.json").read_text())
monthly, _ = analysis.load()
quality = analysis.flag_samples(monthly)
series = analysis.build_series(monthly, quality)
ok = series[series["usable"]].reset_index(drop=True)

fig = plt.figure(figsize=(7.6, 9.6))
gs = fig.add_gridspec(3, 1, height_ratios=[.42, 1.15, 1.0], hspace=.42,
                      left=.13, right=.97, top=.965, bottom=.055)

# ---------------------------- headline strip ------------------------------
strip = fig.add_subplot(gs[0])
strip.axis("off")
strip.set_xlim(0, 3)
strip.set_ylim(0, 1)
for i, (big, label, colour) in enumerate([
    (f"{h['ai_volume_growth_x']}×", "AI/ML growth\n21Q1 → 26Q1", AI),
    (f"{h['general_volume_growth_x']}×", "general growth\nsame window", "#8FA6BE"),
    (f"{h['star_intensity_mean_x']}×", "more likely to\nbe STARRED", GOLD),
]):
    strip.text(i + .5, .62, big, fontsize=34, fontweight="bold", color=colour,
               ha="center", va="center")
    strip.text(i + .5, .28, label, fontsize=10.5, color=MUTE, ha="center",
               va="center", linespacing=1.4)
strip.text(1.5, -.02, "The AI boom shows up on GitHub as an attention boom\n"
                      "first, and a code boom second.",
           fontsize=12, fontweight="bold", style="italic", color=INK,
           ha="center", va="top", linespacing=1.4)

# ------------------------- panel A: share over time -----------------------
a = fig.add_subplot(gs[1])
x = np.arange(len(series))
usable = series["usable"].values
y = series["ai_share_pct"].values

a.plot(x[usable], y[usable], color=AI, lw=2.4, zorder=3)
a.scatter(x[usable], y[usable], color=AI, s=34, zorder=4)
a.scatter(x[~usable], y[~usable], facecolors="white", edgecolors=FLAG, s=34,
          zorder=4, linewidths=1.5)
for i, okk in enumerate(usable):
    if not okk:
        a.axvspan(i - .5, i + .5, color=FLAG, alpha=.35, zorder=0, lw=0)

pk = int(series["ai_share_pct"].idxmax())
a.annotate("GPT-4  14 Mar '23\nAutoGPT  30 Mar '23",
           xy=(pk, y[pk]), xytext=(pk + 1.2, y[pk] + .05),
           fontsize=9.5, fontweight="bold", color=AI, ha="left",
           arrowprops=dict(arrowstyle="->", color=AI, lw=1.2))
ci = list(series["month"]).index("2023-01")
a.annotate("ChatGPT\n30 Nov '22", xy=(ci, y[ci]), xytext=(ci - 4.6, 1.62),
           fontsize=9.5, color=INK,
           arrowprops=dict(arrowstyle="->", color=INK, lw=1))

a.axhline(h["pre_chatgpt_mean_share_pct"], color=GEN, ls=":", lw=1.3)
a.axhline(h["post_gpt4_mean_share_pct"], color=GEN, ls="--", lw=1.3)
a.text(.3, .17, f"pre-ChatGPT mean {h['pre_chatgpt_mean_share_pct']:.2f}%",
       fontsize=8.5, color=GEN)
a.text(.3, 1.07,
       f"post-GPT-4 mean {h['post_gpt4_mean_share_pct']:.2f}%  "
       f"({h['structural_lift_x']}× lift)",
       fontsize=8.5, color=GEN, fontweight="bold")

a.set_xticks(x[::2])
a.set_xticklabels(series["quarter"][::2], rotation=45, ha="right", fontsize=8.5)
a.set_ylim(0, 2.65)
a.set_ylabel("AI/ML share of all\npublic GitHub events (%)", fontsize=10)
a.set_title("AI/ML captured a lasting — but smaller-than-the-hype — share",
            fontsize=11.5, fontweight="bold", loc="left")
a.grid(axis="y")
a.set_axisbelow(True)
a.legend(handles=[
    Line2D([], [], color=AI, marker="o", lw=2.2, label="usable sample"),
    Line2D([], [], color=FLAG, marker="o", mfc="white", ls="none",
           label="rejected — bad archive day"),
], loc="upper left", frameon=False, fontsize=8.5)

# --------------------------- panel B: event mix ---------------------------
b = fig.add_subplot(gs[2])
d = monthly[monthly["month"].isin(set(ok["month"]))]
mix = (d.groupby(["repo_class", "type"])["events"].sum()
       / d.groupby("repo_class")["events"].sum()).unstack(0) * 100
mix = mix.loc[["PushEvent", "WatchEvent", "CreateEvent", "PullRequestEvent",
               "IssueCommentEvent", "ForkEvent"]][::-1]

yy = np.arange(len(mix))
b.barh(yy + .19, mix["ai_ml"], .36, color=AI, label="AI/ML repos")
b.barh(yy - .19, mix["general"], .36, color=GEN, label="General repos")
for i, t in enumerate(mix.index):
    av, gv = mix.loc[t, "ai_ml"], mix.loc[t, "general"]
    b.text(av + .8, i + .19, f"{av:.1f}%", va="center", fontsize=9, color=AI)
    b.text(gv + .8, i - .19, f"{gv:.1f}%", va="center", fontsize=9, color=GEN)
    if av / gv >= 2:
        b.text(max(av, gv) + 8.5, i, f"{av / gv:.1f}× more",
               va="center", fontsize=10, fontweight="bold", color=AI)

b.set_yticks(yy)
b.set_yticklabels([t.replace("Event", "") for t in mix.index], fontsize=9.5)
b.set_xlim(0, 74)
b.set_xlabel("share of that class's own events (%)", fontsize=9.5)
b.set_title("Starred and forked far more — pushed to less",
            fontsize=11.5, fontweight="bold", loc="left")
b.grid(axis="x")
b.set_axisbelow(True)
b.legend(frameon=False, loc="lower right", fontsize=9.5)

fig.savefig(FIG / "fig8_phase4_column.png")
plt.close(fig)
print(f"wrote {FIG / 'fig8_phase4_column.png'}")
