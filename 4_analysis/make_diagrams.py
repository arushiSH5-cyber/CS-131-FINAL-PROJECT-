#!/usr/bin/env python3
"""
Build the two poster diagrams:

  figures/fig9_pipeline.png       method diagram — raw GH Archive to the answer,
                                  every box labelled with the real measured number
  figures/fig10_findings_grid.png all four findings as one 2x2 image

Both read from the committed Phase 3 output and results.json, so every figure
on the poster is derived from our own measurements — nothing is illustrative.

    python3 analysis.py && python3 make_diagrams.py
"""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.lines import Line2D
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

import analysis

HERE = Path(__file__).resolve().parent
FIG = HERE / "figures"
OUT = HERE.parent / "3_scaling" / "out"

AI = "#D9463E"
GEN = "#3F6D9E"
GOLD = "#C9812A"
INK = "#1B2733"
MUTE = "#5A6270"
FLAG = "#B9BEC6"
SOFT = "#EEF2F7"

plt.rcParams.update({
    "figure.dpi": 200, "savefig.dpi": 200, "savefig.bbox": "tight",
    "font.family": "DejaVu Sans",
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

RAW_BYTES = 273_494_892_306              # 1_profile: zcat *.json.gz | wc -c
CSV_BYTES = sum((OUT / f).stat().st_size
                for f in ("monthly.csv", "monthly_growth.csv"))


# ====================== fig 9 — the method diagram ========================
def pipeline_diagram() -> None:
    fig, ax = plt.subplots(figsize=(16, 6.6))
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 40)
    ax.axis("off")

    stages = [
        ("GH ARCHIVE", "#5A6270", [
            "552 hourly .json.gz",
            "1 full day per quarter,",
            "21Q1 – 26Q3 (the 15th)",
            "",
            "34.8 GiB compressed",
            "273.5 GB raw JSON",
        ], "public HTTP\nno account needed"),
        ("GCS BUCKET", GEN, [
            "gcloud storage cp -n",
            "→ gs://…/gharchive/",
            "",
            "552 objects, every",
            "size diffed against",
            "local: ALL_552_MATCH",
        ], "uploaded once,\nread many"),
        ("PYSPARK / DATAPROC", GEN, [
            "explicit StructType schema",
            "(never infer over 273 GB)",
            "repo.name rlike AI kwords",
            "groupBy + countDistinct ×2",
            "join + lag() window + cache()",
            "85,339,283 rows · 118 dropped",
        ], "1 / 2 / 4 workers\n43m37s → 10m21s\nbyte-identical out"),
        ("AGGREGATED CSV", GOLD, [
            "monthly.csv — 692 rows",
            "month × class × type,",
            "events, actors, repos,",
            "share_of_class",
            "monthly_growth.csv — 46",
            "lag-based growth %",
        ], f"{CSV_BYTES/1024:.0f} KB\nthe Phase 4 handoff"),
        ("QUALITY GATE", AI, [
            "volume check:",
            "day < 50% of median",
            "event-mix check:",
            "interaction < 60% of med.",
            "",
            "23 sampled days → 20 usable",
        ], "21Q4, 26Q2, 26Q3\nrejected"),
        ("THE ANSWER", AI, [
            f"AI/ML {h['ai_volume_growth_x']}× vs gen {h['general_volume_growth_x']}×",
            f"({h['ai_cagr_pct']}%/yr vs {h['general_cagr_pct']}%/yr)",
            f"peak {h['ai_share_peak_pct']}% in {h['ai_share_peak_quarter']}",
            f"{h['structural_lift_x']}× structural lift",
            f"starred {h['star_intensity_mean_x']}× more,",
            "every usable quarter",
        ], "attention boom\nbefore code boom"),
    ]

    bw, gap = 14.9, 2.0
    y0, bh = 11.0, 19.0
    for i, (title, colour, lines, note) in enumerate(stages):
        x = 0.8 + i * (bw + gap)
        ax.add_patch(FancyBboxPatch(
            (x, y0), bw, bh, boxstyle="round,pad=0.35,rounding_size=0.8",
            facecolor="white", edgecolor=colour, linewidth=2.1, zorder=2))
        ax.add_patch(FancyBboxPatch(
            (x, y0 + bh - 3.1), bw, 3.1,
            boxstyle="round,pad=0.35,rounding_size=0.8",
            facecolor=colour, edgecolor=colour, linewidth=2.1, zorder=3))
        ax.text(x + bw / 2, y0 + bh - 1.55, title, ha="center", va="center",
                fontsize=10.8, fontweight="bold", color="white", zorder=4)
        for j, ln in enumerate(lines):
            ax.text(x + .7, y0 + bh - 5.1 - j * 2.15, ln, ha="left", va="center",
                    fontsize=8.3, color=INK if j < 4 else MUTE, zorder=4)
        ax.text(x + bw / 2, y0 - 1.6, note, ha="center", va="top",
                fontsize=8.6, color=colour, fontweight="bold",
                linespacing=1.35, zorder=4)

        if i < len(stages) - 1:
            ax.add_patch(FancyArrowPatch(
                (x + bw + .3, y0 + bh / 2), (x + bw + gap - .3, y0 + bh / 2),
                arrowstyle="-|>", mutation_scale=17, linewidth=2,
                color=MUTE, zorder=1))

    # reduction band across the top
    ax.add_patch(FancyBboxPatch(
        (0.8, 33.0), 98.4, 6.0, boxstyle="round,pad=0.3,rounding_size=0.8",
        facecolor=SOFT, edgecolor="none", zorder=1))
    ax.text(2.2, 36.0,
            f"{RAW_BYTES/1e9:.1f} GB of raw JSON   →   {CSV_BYTES/1024:.0f} KB of CSV",
            fontsize=15, fontweight="bold", color=INK, va="center")
    ax.text(51, 36.0,
            f"a {RAW_BYTES/CSV_BYTES/1e6:.1f} million-fold reduction — "
            "the point of the engineering — shrink the data, keep the answer",
            fontsize=11, color=MUTE, va="center", style="italic")

    ax.text(50, 2.0,
            "Phase 1 profiled it at the command line · Phase 2 proved Excel and pandas "
            "cannot hold it · Phase 3 ground it down with Spark · Phase 4 answers the question",
            ha="center", fontsize=10, color=MUTE, style="italic")

    fig.savefig(FIG / "fig9_pipeline.png")
    plt.close(fig)


# =================== fig 10 — all four findings, 2x2 ======================
def findings_grid() -> None:
    fig, axes = plt.subplots(2, 2, figsize=(14.5, 9.4))
    fig.subplots_adjust(hspace=.42, wspace=.24, top=.90, bottom=.07,
                        left=.06, right=.97)

    # (a) indexed volume ---------------------------------------------------
    a = axes[0, 0]
    x = np.arange(len(ok))
    for col, colour, lab in (("ai_ml", AI, "AI/ML repos"),
                             ("general", GEN, "General repos")):
        idx = 100 * ok[col] / ok[col].iloc[0]
        a.plot(x, idx, color=colour, lw=2.3, marker="o", ms=4, label=lab)
        a.annotate(f"{idx.iloc[-1]:.0f}", xy=(x[-1], idx.iloc[-1]),
                   xytext=(6, 0), textcoords="offset points", fontsize=10,
                   color=colour, fontweight="bold", va="center")
    a.axhline(100, color=INK, lw=.9, ls=":")
    a.set_title(f"① Growth — AI/ML {h['ai_volume_growth_x']}× vs general "
                f"{h['general_volume_growth_x']}×",
                fontsize=12.5, fontweight="bold", loc="left")
    a.set_ylabel("volume, indexed to 21Q1 = 100")
    a.legend(frameon=False, fontsize=9.5)

    # (b) share over time --------------------------------------------------
    b = axes[0, 1]
    xs = np.arange(len(series))
    us = series["usable"].values
    y = series["ai_share_pct"].values
    b.plot(xs[us], y[us], color=AI, lw=2.3, zorder=3)
    b.scatter(xs[us], y[us], color=AI, s=30, zorder=4)
    b.scatter(xs[~us], y[~us], facecolors="white", edgecolors=FLAG, s=30,
              linewidths=1.4, zorder=4)
    for i, u in enumerate(us):
        if not u:
            b.axvspan(i - .5, i + .5, color=FLAG, alpha=.35, lw=0, zorder=0)
    pk = int(series["ai_share_pct"].idxmax())
    b.annotate("GPT-4 + AutoGPT\nMar 2023", xy=(pk, y[pk]),
               xytext=(pk + 1.3, y[pk] - .07), fontsize=9.5,
               fontweight="bold", color=AI,
               arrowprops=dict(arrowstyle="->", color=AI, lw=1.2))
    b.axhline(h["post_gpt4_mean_share_pct"], color=GEN, ls="--", lw=1.3)
    b.text(.3, h["post_gpt4_mean_share_pct"] + .09,
           f"post-GPT-4 mean {h['post_gpt4_mean_share_pct']:.2f}%  "
           f"({h['structural_lift_x']}× lift)", fontsize=9, color=GEN,
           fontweight="bold")
    b.set_ylim(0, 2.65)
    b.set_title(f"② Spike + partial retreat — peak {h['ai_share_peak_pct']}% "
                f"in {h['ai_share_peak_quarter']}",
                fontsize=12.5, fontweight="bold", loc="left")
    b.set_ylabel("AI/ML share of all events (%)")

    # (c) star intensity ---------------------------------------------------
    c = axes[1, 0]
    xc = np.arange(len(ok))
    c.bar(xc, ok["star_intensity"], .62, color=AI, alpha=.88)
    c.axhline(1, color=INK, lw=1.2)
    c.axhline(ok["star_intensity"].mean(), color=GEN, ls="--", lw=1.3)
    c.text(.2, 1.14, "parity", fontsize=9, color=INK)
    c.text(len(ok) - .6, ok["star_intensity"].mean() + .18,
           f"mean {h['star_intensity_mean_x']}×", fontsize=9.5, color=GEN,
           fontweight="bold", ha="right")
    c.set_title(f"③ Attention — starred {h['star_intensity_mean_x']}× more, in "
                f"all {h['usable_quarters']} usable quarters",
                fontsize=12.5, fontweight="bold", loc="left")
    c.set_ylabel("AI star-rate ÷ general star-rate")

    # (d) quality gate -----------------------------------------------------
    d = axes[1, 1]
    bad = ~series["usable"].values
    d.bar(xs, series["mix_ratio"], .62,
          color=np.where(bad, FLAG, GEN),
          edgecolor=np.where(bad, AI, "none"), linewidth=1.4)
    d.axhline(analysis.MIX_FLOOR, color=AI, ls="--", lw=1.4)
    d.text(.3, analysis.MIX_FLOOR + .05,
           f"reject < {analysis.MIX_FLOOR:.2f}", fontsize=9.5, color=AI,
           fontweight="bold", ha="left")
    d.axhline(1, color=INK, lw=.9, ls=":")
    for i in np.where(series["volume_ratio"].values < analysis.VOL_FLOOR)[0]:
        d.annotate(f"{series['quarter'].iloc[i]}\nfails volume check",
                   xy=(i, series["mix_ratio"].iloc[i]),
                   xytext=(i + .8, 1.22), fontsize=8.5, color=AI,
                   fontweight="bold",
                   arrowprops=dict(arrowstyle="->", color=AI, lw=1.1))
    for i in np.where(bad & (series["mix_ratio"].values < analysis.MIX_FLOOR))[0]:
        d.text(i, series["mix_ratio"].iloc[i] + .04,
               series["quarter"].iloc[i], ha="center", fontsize=8.5,
               color=AI, fontweight="bold")
    d.set_title("④ Quality gate — 3 of 23 sampled days rejected",
                fontsize=12.5, fontweight="bold", loc="left")
    d.set_ylabel("interaction-event share ÷ median")

    for ax_, lbls in ((a, ok["quarter"]), (b, series["quarter"]),
                      (c, ok["quarter"]), (d, series["quarter"])):
        ax_.set_xticks(np.arange(len(lbls)))
        ax_.set_xticklabels(lbls, rotation=45, ha="right", fontsize=7.8)
        ax_.grid(axis="y")
        ax_.set_axisbelow(True)

    fig.suptitle("Four findings from 85,339,283 GitHub events — "
                 "AI/ML repositories vs general software repositories, 2021–2026",
                 fontsize=15, fontweight="bold", y=.965)
    fig.text(.5, .925,
             "The AI boom shows up on GitHub as an attention boom first, "
             "and a code boom second.",
             ha="center", fontsize=12, style="italic", color=MUTE)
    fig.savefig(FIG / "fig10_findings_grid.png")
    plt.close(fig)


if __name__ == "__main__":
    pipeline_diagram()
    findings_grid()
    print(f"wrote {FIG/'fig9_pipeline.png'}")
    print(f"wrote {FIG/'fig10_findings_grid.png'}")
    print(f"raw {RAW_BYTES:,} B  ->  csv {CSV_BYTES:,} B  "
          f"= {RAW_BYTES/CSV_BYTES:,.0f}x reduction")
