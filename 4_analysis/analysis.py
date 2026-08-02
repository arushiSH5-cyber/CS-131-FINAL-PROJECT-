#!/usr/bin/env python3
"""
CS 131 Final Project — Phase 4: answer the question.

Reads the Phase 3 aggregated CSVs (3_scaling/out/) and produces every number
and figure used in findings.md and on the poster. 273.5 GB of raw GH Archive
JSON came into Spark; 43 KB of CSV came out; this script turns that into the
answer.

    python3 analysis.py            # writes figures/ + results.json

The question:
    How has open-source activity around AI/ML repositories changed compared
    with general software-development repositories from 2021 to 2026?
"""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.lines import Line2D
from matplotlib.patches import Patch

HERE = Path(__file__).resolve().parent
OUT_DIR = HERE.parent / "3_scaling" / "out"
FIG_DIR = HERE / "figures"

# ---------------------------------------------------------------- style ----
AI = "#D9463E"       # AI/ML repos
GEN = "#3F6D9E"      # general repos
FLAG = "#B9BEC6"     # excluded / flagged samples
INK = "#22262B"
GRID = "#DCE0E5"

plt.rcParams.update({
    "figure.dpi": 200,
    "savefig.dpi": 200,
    "savefig.bbox": "tight",
    "font.family": "DejaVu Sans",
    "font.size": 10,
    "axes.edgecolor": INK,
    "axes.labelcolor": INK,
    "axes.titlesize": 13,
    "axes.titleweight": "bold",
    "axes.spines.top": False,
    "axes.spines.right": False,
    "text.color": INK,
    "xtick.color": INK,
    "ytick.color": INK,
    "grid.color": GRID,
    "grid.linewidth": 0.7,
})

# Real AI-tool releases, mapped to the sampled quarter they land in. Used to
# test the proposal's claim that jumps line up with tool releases.
RELEASES = {
    "2022-10": "Stable Diffusion\n+ Whisper (Aug/Sep '22)",
    "2023-01": "ChatGPT\n(30 Nov '22)",
    "2023-04": "GPT-4 (14 Mar '23)\nAutoGPT (30 Mar '23)",
    "2024-04": "Llama 3 (18 Apr '24)",
}

# Event types that require a *human* to act on someone else's work. Their
# collapse is the fingerprint of an upstream archive problem (§ flag_samples).
INTERACTION = [
    "PullRequestEvent", "WatchEvent", "IssueCommentEvent",
    "IssuesEvent", "PullRequestReviewEvent",
]

# Detection thresholds. Both are set with >1.6x margin to the nearest clean
# quarter, so no borderline judgement call is being hidden here.
VOL_FLOOR = 0.50     # sampled day is < 50% of the median day => missing hours
MIX_FLOOR = 0.60     # interaction mix < 60% of median => degraded event stream


# ------------------------------------------------------------------ load ---
def load() -> tuple[pd.DataFrame, pd.DataFrame]:
    monthly = pd.read_csv(OUT_DIR / "monthly.csv")
    growth = pd.read_csv(OUT_DIR / "monthly_growth.csv")
    return monthly, growth


def quarter_label(month: str) -> str:
    """'2023-04' -> '23Q2'. The sample is one day per quarter, not a month."""
    y, m = month.split("-")
    return f"{y[2:]}Q{(int(m) - 1) // 3 + 1}"


# ------------------------------------------------------- data quality ------
def flag_samples(monthly: pd.DataFrame) -> pd.DataFrame:
    """Score every sampled day and mark the ones that are not usable.

    We sample one full day per quarter, so each row of the answer rests on a
    single day of GH Archive. If that day is short some hours, or the archive
    dropped whole event types that day, the point is an artifact -- and it
    would otherwise read as a real collapse in developer activity. Two
    independent checks catch two different failure modes:

      volume  -- total events vs the median sampled day. Catches a day where
                 hourly files are missing: every event type shrinks together.
      mix     -- share of human-interaction events vs the median. Catches a
                 day where the archive kept writing pushes but lost PRs,
                 stars and comments: the total looks fine, the shape does not.
    """
    per_day = (monthly.groupby("month")["class_events"].sum()
               .rename("total").to_frame())
    per_day["total"] = monthly.groupby(["month", "repo_class"])["class_events"] \
        .first().groupby("month").sum()
    inter = (monthly[monthly["type"].isin(INTERACTION)]
             .groupby("month")["events"].sum())
    per_day["interaction_share"] = inter / per_day["total"]

    per_day["volume_ratio"] = per_day["total"] / per_day["total"].median()
    per_day["mix_ratio"] = (per_day["interaction_share"]
                            / per_day["interaction_share"].median())

    per_day["short_day"] = per_day["volume_ratio"] < VOL_FLOOR
    per_day["degraded_stream"] = per_day["mix_ratio"] < MIX_FLOOR
    per_day["usable"] = ~(per_day["short_day"] | per_day["degraded_stream"])
    per_day["reason"] = np.where(
        per_day["short_day"], "missing hours in sampled day",
        np.where(per_day["degraded_stream"],
                 "upstream archive dropped interaction events", ""))
    return per_day.reset_index()


# ---------------------------------------------------------- core series ----
def build_series(monthly: pd.DataFrame, quality: pd.DataFrame) -> pd.DataFrame:
    wide = (monthly.groupby(["month", "repo_class"])["class_events"].first()
            .unstack().rename_axis(columns=None).reset_index())
    wide["total"] = wide["ai_ml"] + wide["general"]
    wide["ai_share_pct"] = 100 * wide["ai_ml"] / wide["total"]

    stars = (monthly[monthly["type"] == "WatchEvent"]
             .pivot(index="month", columns="repo_class", values="share_of_class")
             .rename(columns={"ai_ml": "ai_star_share",
                              "general": "gen_star_share"}).reset_index())
    wide = wide.merge(stars, on="month")
    wide["star_intensity"] = wide["ai_star_share"] / wide["gen_star_share"]

    # countDistinct is per (month, class, type); a repo active in several event
    # types is counted once per type, so summing over-counts. The max over
    # types is a strict LOWER bound on distinct repos -- honest, and enough to
    # show the population change.
    pop = (monthly.groupby(["month", "repo_class"])[["repos", "actors"]].max()
           .unstack())
    pop.columns = [f"{a}_{b}" for a, b in pop.columns]
    wide = wide.merge(pop.reset_index(), on="month")

    wide = wide.merge(quality[["month", "usable", "volume_ratio",
                               "mix_ratio", "reason"]], on="month")
    wide["quarter"] = wide["month"].map(quarter_label)
    return wide.sort_values("month").reset_index(drop=True)


def headline(series: pd.DataFrame) -> dict:
    ok = series[series["usable"]]
    first, last = ok.iloc[0], ok.iloc[-1]
    peak = ok.loc[ok["ai_share_pct"].idxmax()]
    base = ok[ok["month"] < "2023-01"]["ai_share_pct"].mean()
    post = ok[ok["month"] >= "2023-07"]["ai_share_pct"].mean()
    years = (int(last["month"][:4]) - int(first["month"][:4])
             + (int(last["month"][5:7]) - int(first["month"][5:7])) / 12)
    return {
        "window": f"{first['quarter']}–{last['quarter']}",
        "usable_quarters": int(len(ok)),
        "excluded_quarters": series.loc[~series["usable"], "quarter"].tolist(),
        "ai_share_first_pct": round(float(first["ai_share_pct"]), 3),
        "ai_share_last_pct": round(float(last["ai_share_pct"]), 3),
        "ai_share_peak_pct": round(float(peak["ai_share_pct"]), 3),
        "ai_share_peak_quarter": peak["quarter"],
        "peak_vs_start_x": round(float(peak["ai_share_pct"] / first["ai_share_pct"]), 2),
        "pre_chatgpt_mean_share_pct": round(float(base), 3),
        "post_gpt4_mean_share_pct": round(float(post), 3),
        "structural_lift_x": round(float(post / base), 2),
        "ai_volume_growth_x": round(float(last["ai_ml"] / first["ai_ml"]), 2),
        "general_volume_growth_x": round(float(last["general"] / first["general"]), 2),
        "ai_cagr_pct": round(float(100 * ((last["ai_ml"] / first["ai_ml"]) ** (1 / years) - 1)), 1),
        "general_cagr_pct": round(float(100 * ((last["general"] / first["general"]) ** (1 / years) - 1)), 1),
        "peak_ai_repos": int(peak["repos_ai_ml"]),
        "peak_ai_actors": int(peak["actors_ai_ml"]),
        "prior_quarter_ai_actors": int(ok.iloc[ok.index.get_loc(peak.name) - 1]["actors_ai_ml"]),
        "star_intensity_mean_x": round(float(ok["star_intensity"].mean()), 2),
        "star_intensity_min_x": round(float(ok["star_intensity"].min()), 2),
        "star_intensity_peak_x": round(float(ok["star_intensity"].max()), 2),
        "ai_star_share_peak_pct": round(float(100 * ok["ai_star_share"].max()), 1),
    }


# --------------------------------------------------------------- figures ---
def _quarter_axis(ax, series: pd.DataFrame) -> None:
    ax.set_xticks(range(len(series)))
    ax.set_xticklabels(series["quarter"], rotation=45, ha="right", fontsize=8)
    for i, ok in enumerate(series["usable"]):
        if not ok:
            ax.axvspan(i - .5, i + .5, color=FLAG, alpha=.35, zorder=0, lw=0)
    ax.grid(axis="y", zorder=0)
    ax.set_axisbelow(True)


def fig_ai_share(series: pd.DataFrame, h: dict) -> None:
    fig, ax = plt.subplots(figsize=(9, 4.6))
    x = np.arange(len(series))
    ok = series["usable"].values
    y = series["ai_share_pct"].values

    ax.plot(x[ok], y[ok], color=AI, lw=2.4, zorder=3)
    ax.scatter(x[ok], y[ok], color=AI, s=42, zorder=4)
    ax.scatter(x[~ok], y[~ok], facecolors="white", edgecolors=FLAG,
               s=42, zorder=4, linewidths=1.6)

    pk = int(series["ai_share_pct"].idxmax())
    ax.annotate(RELEASES["2023-04"], xy=(pk, y[pk]), xytext=(pk + 1.4, y[pk] + .12),
                fontsize=8.5, ha="left", color=AI, fontweight="bold",
                arrowprops=dict(arrowstyle="->", color=AI, lw=1.2))
    ax.annotate(RELEASES["2023-01"],
                xy=(list(series["month"]).index("2023-01"), y[list(series["month"]).index("2023-01")]),
                xytext=(list(series["month"]).index("2023-01") - 3.2, 1.75),
                fontsize=8.5, ha="left", color=INK,
                arrowprops=dict(arrowstyle="->", color=INK, lw=1))

    base = h["pre_chatgpt_mean_share_pct"]
    post = h["post_gpt4_mean_share_pct"]
    ax.axhline(base, color=GEN, ls=":", lw=1.4)
    ax.axhline(post, color=GEN, ls="--", lw=1.4)
    ax.text(len(series) - .4, base, f"  pre-ChatGPT mean {base:.2f}%",
            va="center", fontsize=8, color=GEN)
    ax.text(len(series) - .4, post, f"  post-GPT-4 mean {post:.2f}%",
            va="center", fontsize=8, color=GEN, fontweight="bold")

    _quarter_axis(ax, series)
    ax.set_ylabel("AI/ML share of all public GitHub events (%)")
    ax.set_title("AI/ML repositories captured a lasting, but smaller-than-the-hype, "
                 "share of GitHub")
    ax.set_ylim(0, 2.7)
    ax.legend(handles=[
        Line2D([], [], color=AI, marker="o", lw=2.4, label="AI/ML share (usable samples)"),
        Line2D([], [], color=FLAG, marker="o", mfc="white", ls="none",
               label="excluded — bad sample (see fig. 6)"),
    ], loc="upper left", frameon=False, fontsize=8.5)
    fig.savefig(FIG_DIR / "fig1_ai_share.png")
    plt.close(fig)


def fig_indexed_volume(series: pd.DataFrame, h: dict) -> None:
    ok = series[series["usable"]].reset_index(drop=True)
    fig, ax = plt.subplots(figsize=(9, 4.6))
    x = np.arange(len(ok))
    for col, colour, label in ((("ai_ml"), AI, "AI/ML repos"),
                               (("general"), GEN, "General repos")):
        idx = 100 * ok[col] / ok[col].iloc[0]
        ax.plot(x, idx, color=colour, lw=2.4, marker="o", ms=4.5, label=label)
        ax.annotate(f"{idx.iloc[-1]:.0f}", xy=(x[-1], idx.iloc[-1]),
                    xytext=(6, 0), textcoords="offset points",
                    color=colour, fontweight="bold", va="center", fontsize=9.5)

    ax.axhline(100, color=INK, lw=.9, ls=":")
    ax.set_xticks(x)
    ax.set_xticklabels(ok["quarter"], rotation=45, ha="right", fontsize=8)
    ax.grid(axis="y")
    ax.set_axisbelow(True)
    ax.set_ylabel(f"Event volume, indexed to {ok['quarter'].iloc[0]} = 100")
    ax.set_title(f"AI/ML activity grew {h['ai_volume_growth_x']}x while general "
                 f"activity grew {h['general_volume_growth_x']}x")
    ax.legend(frameon=False)
    fig.savefig(FIG_DIR / "fig2_indexed_volume.png")
    plt.close(fig)


def fig_event_mix(monthly: pd.DataFrame, series: pd.DataFrame) -> None:
    usable = set(series.loc[series["usable"], "month"])
    d = monthly[monthly["month"].isin(usable)]
    mix = (d.groupby(["repo_class", "type"])["events"].sum()
           / d.groupby("repo_class")["events"].sum())
    mix = (mix.unstack(0) * 100).fillna(0)
    mix = mix.loc[mix.max(axis=1).sort_values().index].tail(9)

    fig, ax = plt.subplots(figsize=(9, 5))
    y = np.arange(len(mix))
    ax.barh(y + .19, mix["ai_ml"], .36, color=AI, label="AI/ML repos")
    ax.barh(y - .19, mix["general"], .36, color=GEN, label="General repos")
    for i, t in enumerate(mix.index):
        a, g = mix.loc[t, "ai_ml"], mix.loc[t, "general"]
        ax.text(a + .5, i + .19, f"{a:.1f}%", va="center", fontsize=8, color=AI)
        ax.text(g + .5, i - .19, f"{g:.1f}%", va="center", fontsize=8, color=GEN)
        if a / g >= 2 or g / a >= 2:
            ax.text(max(a, g) + 5.5, i, f"{a / g:.1f}x", va="center",
                    fontsize=9, fontweight="bold",
                    color=AI if a > g else GEN)

    ax.set_yticks(y)
    ax.set_yticklabels([t.replace("Event", "") for t in mix.index], fontsize=9)
    ax.set_xlabel("Share of that class's total events (%), pooled over usable quarters")
    ax.set_title("AI/ML repos are starred and forked far more; general repos are "
                 "pushed to more")
    ax.set_xlim(0, 78)
    ax.grid(axis="x")
    ax.set_axisbelow(True)
    ax.legend(frameon=False, loc="lower right")
    fig.savefig(FIG_DIR / "fig3_event_mix.png")
    plt.close(fig)


def fig_star_intensity(series: pd.DataFrame, h: dict) -> None:
    ok = series[series["usable"]].reset_index(drop=True)
    fig, ax = plt.subplots(figsize=(9, 4.2))
    x = np.arange(len(ok))
    ax.bar(x, ok["star_intensity"], .62, color=AI, alpha=.85)
    ax.axhline(1, color=INK, lw=1.2)
    ax.axhline(ok["star_intensity"].mean(), color=GEN, ls="--", lw=1.4)
    ax.text(len(ok) - .4, ok["star_intensity"].mean(),
            f"  mean {h['star_intensity_mean_x']}x", va="center",
            fontsize=8.5, color=GEN, fontweight="bold")
    ax.text(-.4, 1.12, "parity — an AI repo would be starred like any other",
            fontsize=8, color=INK)
    ax.set_xticks(x)
    ax.set_xticklabels(ok["quarter"], rotation=45, ha="right", fontsize=8)
    ax.set_ylabel("AI star-rate ÷ general star-rate")
    ax.set_title("Every single usable quarter: AI/ML repos are starred at "
                 "several times the general rate")
    ax.grid(axis="y")
    ax.set_axisbelow(True)
    fig.savefig(FIG_DIR / "fig4_star_intensity.png")
    plt.close(fig)


def fig_population(series: pd.DataFrame) -> None:
    ok = series[series["usable"]].reset_index(drop=True)
    fig, ax = plt.subplots(figsize=(9, 4.2))
    x = np.arange(len(ok))
    ax.bar(x - .19, ok["repos_ai_ml"], .36, color=AI, label="distinct AI/ML repos")
    ax.bar(x + .19, ok["actors_ai_ml"], .36, color="#E8A03C",
           label="distinct actors in AI/ML repos")

    pk = int(ok["actors_ai_ml"].idxmax())
    jump = ok["actors_ai_ml"].iloc[pk] / ok["actors_ai_ml"].iloc[pk - 1]
    ax.annotate(f"population, not just volume:\nactors {jump:.1f}x in one quarter",
                xy=(pk + .19, ok["actors_ai_ml"].iloc[pk]),
                xytext=(pk + 1.6, ok["actors_ai_ml"].iloc[pk] * .95),
                fontsize=8.5, fontweight="bold", color=INK,
                arrowprops=dict(arrowstyle="->", color=INK, lw=1.1))

    ax.set_xticks(x)
    ax.set_xticklabels(ok["quarter"], rotation=45, ha="right", fontsize=8)
    ax.set_ylim(0, ok["actors_ai_ml"].max() * 1.15)
    ax.set_ylabel("distinct count in the sampled day (lower bound)")
    ax.set_title("The 2023 jump was new people and new repos, not the same crowd "
                 "committing harder")
    ax.grid(axis="y")
    ax.set_axisbelow(True)
    ax.legend(frameon=False, loc="upper left")
    fig.savefig(FIG_DIR / "fig5_population.png")
    plt.close(fig)


def fig_data_quality(series: pd.DataFrame) -> None:
    fig, axes = plt.subplots(2, 1, figsize=(9, 6.2), sharex=True)
    x = np.arange(len(series))

    for ax, col, floor, title, ylab in (
        (axes[0], "volume_ratio", VOL_FLOOR,
         "Check 1 — sampled-day volume vs the median sampled day",
         "total events ÷ median"),
        (axes[1], "mix_ratio", MIX_FLOOR,
         "Check 2 — human-interaction share (PR, star, issue, review) vs median",
         "interaction share ÷ median"),
    ):
        bad = series[col] < floor
        ax.bar(x, series[col], .62,
               color=np.where(bad, FLAG, GEN), edgecolor=np.where(bad, AI, "none"),
               linewidth=1.4)
        ax.axhline(floor, color=AI, ls="--", lw=1.4)
        ax.text(len(series) - .4, floor, f"  reject < {floor:.2f}",
                va="center", fontsize=8, color=AI, fontweight="bold")
        ax.axhline(1, color=INK, lw=.9, ls=":")
        ax.set_title(title, fontsize=11)
        ax.set_ylabel(ylab, fontsize=9)
        ax.grid(axis="y")
        ax.set_axisbelow(True)
        for i in np.where(bad)[0]:
            ax.text(i, series[col].iloc[i] + .04, series["quarter"].iloc[i],
                    ha="center", fontsize=8, color=AI, fontweight="bold")

    axes[0].legend(handles=[
        Patch(facecolor=GEN, label="usable"),
        Patch(facecolor=FLAG, edgecolor=AI, label="rejected"),
    ], loc="upper left", frameon=False, fontsize=9, ncol=2)
    axes[1].set_xticks(x)
    axes[1].set_xticklabels(series["quarter"], rotation=45, ha="right", fontsize=8)
    fig.suptitle("Three of 23 sampled days are unusable — and they fail for two "
                 "different reasons", fontweight="bold", fontsize=13, y=.99)
    fig.tight_layout(rect=[0, 0, 1, .95])
    fig.savefig(FIG_DIR / "fig6_data_quality.png")
    plt.close(fig)


# ------------------------------------------------------------------ main ---
def main() -> None:
    FIG_DIR.mkdir(exist_ok=True)
    monthly, growth = load()
    quality = flag_samples(monthly)
    series = build_series(monthly, quality)
    h = headline(series)

    fig_ai_share(series, h)
    fig_indexed_volume(series, h)
    fig_event_mix(monthly, series)
    fig_star_intensity(series, h)
    fig_population(series)
    fig_data_quality(series)

    series.to_csv(HERE / "quarterly_series.csv", index=False)
    (HERE / "results.json").write_text(json.dumps(h, indent=2) + "\n")

    print(json.dumps(h, indent=2))
    print(f"\nfigures -> {FIG_DIR}")
    print("rejected samples:")
    for _, r in series[~series["usable"]].iterrows():
        print(f"  {r['quarter']} ({r['month']}): {r['reason']}")


if __name__ == "__main__":
    main()
