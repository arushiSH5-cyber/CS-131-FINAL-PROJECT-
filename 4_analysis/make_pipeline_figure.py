#!/usr/bin/env python3
"""
Build figures/fig7_why_streaming.png — the Phase 1 + Phase 2 visual.

The rest of Phase 4 charts the *answer*. This one charts the *method*: why a
273.5 GB dataset has to be streamed, and what happens to the tools that refuse
to. Every value below is a measurement copied from a committed log, with its
source cited — nothing here is estimated except the two clearly-labelled
extrapolations.

    python3 make_pipeline_figure.py     # -> figures/fig7_why_streaming.png
"""
from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

HERE = Path(__file__).resolve().parent
FIG = HERE / "figures"

AI = "#D9463E"
GEN = "#3F6D9E"
GOLD = "#E8A03C"
INK = "#22262B"
MUTE = "#5A6270"
GRID = "#DCE0E5"

plt.rcParams.update({
    "figure.dpi": 200, "savefig.dpi": 200, "savefig.bbox": "tight",
    "font.family": "DejaVu Sans", "font.size": 10,
    "axes.edgecolor": INK, "axes.labelcolor": INK,
    "axes.titlesize": 12, "axes.titleweight": "bold",
    "axes.spines.top": False, "axes.spines.right": False,
    "text.color": INK, "xtick.color": INK, "ytick.color": INK,
    "grid.color": GRID, "grid.linewidth": .7,
})

# ---- Panel A: wall-clock, 1 core vs 10 cores  (1_profile/profiling.txt) ----
# Only passes where BOTH core counts are known. The row-count pass was never
# run in parallel, so it is not shown rather than guessed.
# label, single-stream minutes, 10-core minutes, single-core was projected?
PASSES = [
    ("Byte count\nzcat | wc -c", 38.48, 13.44, False),
    ("Event-type table\njq .type | sort | uniq -c", 315.47, 30.08, True),
]

# ---- Panel B: RAM needed to LOAD it   (2_breaking/breaking.txt) ------------
# label, gigabytes, colour
LOADS = [
    ("streaming\nany size", 0.05, GEN),
    ("pandas\n1 hour", 14.36, AI),
    ("pandas\n1 day", 270.0, AI),
    ("pandas\nfull 23 days", 3900.0, AI),
]
LAPTOP, BOX = 16.0, 130.0        # typical laptop RAM; the DGX box (121 GiB)

fig, (a, b) = plt.subplots(1, 2, figsize=(13.5, 5.6),
                           gridspec_kw={"width_ratios": [1, 1.05]})

# ============================== panel A ====================================
y = np.arange(len(PASSES))
a.barh(y + .19, [p[1] for p in PASSES], .36, color="#B9BEC6",
       label="1 core (single stream)")
a.barh(y - .19, [p[2] for p in PASSES], .36, color=GEN,
       label="10 cores (xargs -P 10)")

for i, (lab, one, ten, projected) in enumerate(PASSES):
    a.text(one + 7, i + .19, f"{one:.0f} min{' *' if projected else ''}",
           va="center", fontsize=10, color=MUTE, fontweight="bold")
    a.text(ten + 7, i - .19, f"{ten:.0f} min", va="center", fontsize=10,
           color=GEN, fontweight="bold")
    a.text(max(one, ten) + 48, i, f"{one / ten:.1f}× faster", va="center",
           fontsize=12, fontweight="bold", color=INK)

a.set_yticks(y)
a.set_yticklabels([p[0] for p in PASSES], fontsize=10)
a.invert_yaxis()
a.set_xlim(0, 400)
a.set_ylim(1.75, -0.75)
a.set_xlabel("wall-clock over all 552 files (minutes)")
a.set_title("PROFILING — same answer, less waiting", loc="left")
a.grid(axis="x")
a.set_axisbelow(True)
a.legend(frameon=False, loc="upper right", fontsize=10)
a.text(0, -.20, "* projected from the 315 CPU-minutes actually burned.   "
                "Both core counts returned byte-identical counts —\n"
                "   parallelism changed the wait, never the answer. "
                "This is the Phase 3 cluster result in miniature.",
       transform=a.transAxes, fontsize=9, color=MUTE, va="top", linespacing=1.5)

# ============================== panel B ====================================
x = np.arange(len(LOADS))
b.bar(x, [l[1] for l in LOADS], .56, color=[l[2] for l in LOADS])
b.set_yscale("log")
b.set_ylim(.02, 26000)

for i, (lab, v, c) in enumerate(LOADS):
    txt = f"{v * 1000:.0f} MB" if v < 1 else (f"{v:.1f} GB" if v < 1000 else f"{v / 1000:.1f} TB")
    b.text(i, v * 1.6, txt, ha="center", fontsize=12.5, fontweight="bold", color=c)

for lvl, lab, style in ((LAPTOP, "laptop  16 GB", ":"),
                        (BOX, "our box  121 GiB", "--")):
    b.axhline(lvl, color=INK, ls=style, lw=1.3)
    b.text(-.45, lvl * 1.3, lab, ha="left", fontsize=9, color=INK,
           fontweight="bold")

b.set_xticks(x)
b.set_xticklabels([l[0] for l in LOADS], fontsize=10)
b.set_ylabel("RAM needed to LOAD the data (GB, log scale)")
b.set_title("BREAKING — why load-into-memory cannot work here", loc="left")
b.grid(axis="y")
b.set_axisbelow(True)
b.text(0, -.20, "Measured: 1.0 GB of JSON → 14.4 GB resident (14.3×). The 1-day and "
                "23-day bars extrapolate that\nsame ratio. pandas dies inside "
                "data.read() — before parsing a single row.",
       transform=b.transAxes, fontsize=9, color=MUTE, va="top", linespacing=1.5)

fig.suptitle("273.5 GB does not fit in memory — so never put it there",
             fontsize=15, fontweight="bold", y=1.005)
fig.tight_layout(rect=[0, .05, 1, 1])
fig.savefig(FIG / "fig7_why_streaming.png")
plt.close(fig)
print(f"wrote {FIG / 'fig7_why_streaming.png'}")
