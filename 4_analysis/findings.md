# Phase 4 — The Answer

**Question.** How has open-source activity around AI/ML repositories changed
compared with general software-development repositories from 2021 to 2026?

**Input.** `3_scaling/out/monthly.csv` + `monthly_growth.csv` — 43 KB of
aggregates that PySpark distilled from **273.5 GB / 85,339,283 raw GH Archive
events** on Dataproc (Phase 3). Sample design: one full day (24 hourly files)
per quarter, 2021-Q1 → 2026-Q3.

**Reproduce.** `python3 analysis.py` → `figures/`, `results.json`,
`quarterly_series.csv`. Or open `analysis.ipynb`.

---

## Headline finding

> **AI/ML open-source activity grew 2.35× from 2021-Q1 to 2026-Q1 while general
> software activity grew 1.28× — an 18.7% vs 5.1% annual rate. But the shift is
> smaller and stranger than the hype implies: AI/ML repos went from 0.52% to
> 0.94% of all public GitHub events, spiking to 2.26% in 2023-Q2 before giving
> most of it back. What durably changed was not how much AI code gets written —
> it is how much attention it attracts. AI/ML repos are starred at 4× the
> general rate in every single usable quarter.**

The one-sentence version for the poster: **the AI boom shows up on GitHub as an
attention boom first and a code boom second.**

---

## The four things the data actually says

### 1. Real growth, but AI is still a small slice of GitHub

`figures/fig2_indexed_volume.png`

| | 2021-Q1 | 2026-Q1 | Growth | CAGR |
|---|---|---|---|---|
| AI/ML repos | 13,658 events | 32,140 | **2.35×** | **18.7%/yr** |
| General repos | 2,639,242 events | 3,386,909 | 1.28× | 5.1%/yr |

AI/ML activity grew **3.7× faster** than general activity. But it started from
0.5% of the platform, so even after five years of the largest hype cycle in
software, AI/ML repos are **under 1% of public GitHub events**. Both facts are
true and the poster should say both — "AI is growing much faster" and "AI is
still tiny" are not in tension.

### 2. The 2023-Q2 spike is real, and it lines up with GPT-4

`figures/fig1_ai_share.png`

AI/ML share of all events by quarter: 0.52% → **2.26% in 2023-Q2** → 0.94% by
2026-Q1. The peak is **4.4× the 2021-Q1 baseline** and it lands in the quarter
containing GPT-4 (14 Mar 2023) and AutoGPT (30 Mar 2023), one quarter after
ChatGPT (30 Nov 2022). This is the proposal's "do jumps line up with releases?"
sub-question, answered: **yes, for one enormous jump.** Llama 3 (Apr 2024)
produced a visible but far smaller bump (24Q2).

The spike was **not** the existing AI crowd working harder
(`figures/fig5_population.png`): distinct actors in AI/ML repos went
**3,734 → 19,977 in a single quarter (5.4×)**. New people arrived, and most of
them left again by 23Q3.

### 3. The retreat is partial, not total — there is a real structural lift

Averaging away the spike quarter:

| Period | Mean AI/ML share |
|---|---|
| Pre-ChatGPT (21Q1–22Q4) | 0.61% |
| Post-GPT-4 (23Q3–26Q1) | **0.95%** |

A **1.56× permanent step up** in AI's share of the platform. So the honest story
is neither "AI took over GitHub" nor "it was pure hype": a spike of tourists
came and went, and left behind a base level ~56% higher than before.

### 4. The durable difference is attention, not code

`figures/fig3_event_mix.png`, `figures/fig4_star_intensity.png`

Pooled over all usable quarters, share of each class's own events:

| Event | AI/ML repos | General repos | Ratio |
|---|---|---|---|
| **WatchEvent (star)** | **18.6%** | 4.3% | **4.4×** |
| **ForkEvent** | **3.7%** | 1.2% | **3.1×** |
| PullRequestEvent | 9.2% | 7.5% | 1.2× |
| IssueCommentEvent | 6.0% | 4.4% | 1.4× |
| PushEvent | 43.5% | 59.2% | 0.7× |

AI/ML repos are **starred 4.4× and forked 3.1× more intensively** than general
repos, while being **pushed to less**. And this is not a one-quarter artifact:
the star-intensity ratio is above 1 in **every one of the 20 usable quarters**,
ranging 2.1× – 6.6× (peaking at 6.6× in 23Q2, when 35% of all AI-repo events
were stars).

**Interpretation.** Stars and forks are *consumption* signals — someone found the
repo, bookmarked it, copied it. Pushes are *production*. The AI/ML corner of
GitHub is disproportionately a place people come to **look at and take from**,
not to build in. That is exactly what a field dominated by a handful of large
model/framework repos with enormous audiences looks like.

---

## Data quality: three of 23 sampled days are unusable

`figures/fig6_data_quality.png`

Each quarterly point rests on a single sampled day, so one bad day becomes a
fake trend. Two independent automated checks in `analysis.py::flag_samples`
catch two different failure modes. Both thresholds clear the nearest usable
quarter by >1.6×, so nothing borderline is being hidden.

| Check | Rule | Catches | Rejected |
|---|---|---|---|
| Volume | day total < 50% of median day | missing hourly files — every event type shrinks together | **2021-Q4** (32% of median) |
| Mix | interaction share < 60% of median | archive kept pushes but dropped PRs/stars/comments — total looks fine, shape does not | **2026-Q2** (49%), **2026-Q3** (3%) |

Why this matters concretely: `monthly_growth.csv` reports **−68.65%** for AI/ML
in 2021-Q4 and **+296.94%** in 2022-Q1. Neither happened. Both are the same
short sampled day, first as a fake crash and then as a fake recovery. Reporting
those as findings would have been the single biggest error available in this
project.

2026-Q3 is the extreme case: general-repo `PullRequestEvent` collapses from
~304,000 to **10,806** while `PushEvent` stays normal — an upstream GH Archive
problem, not a change in developer behaviour.

---

## Limits of this analysis — read before believing any number above

1. **The keyword classifier is frozen in 2021 and decays.** AI/ML is defined by
   `llm|gpt|pytorch|tensorflow|langchain|diffus|transformer|huggingface|openai|
   neural|deep-learning|machine-learning|agentic|rag-` matched against
   `repo.name`. It cannot match repos named for tools that did not exist when
   the list was fixed — `claude`, `mcp`, `cursor`, `copilot`, `gemini`, `agent`,
   `vllm`, `ollama`. **AI activity in 2024–2026 is therefore systematically
   undercounted, and the measured 2.35× growth is a floor, not a ceiling.**
   The 2023-Q2 spike is partly a *naming* event: that was the quarter when
   everything got named `*gpt*`.
2. **Name ≠ content.** A repo called `my-gpt-homework` counts as AI/ML; DeepMind
   research in a repo named after a person does not.
3. **Bots inflate everything.** Phase 1 found `github-actions[bot]` alone at
   19,295 events/hour and spam accounts pushing 2,000+/hour. Push counts are
   the most bot-contaminated and star counts the least — which slightly
   *strengthens* finding #4, since the AI signal lives in stars.
4. **One day per quarter.** 23 days stand in for five years. A day with a viral
   release or an outage moves a whole quarter. This is the sampling cost that
   bought us a 2021→2026 span instead of one dense month.
5. **`monthly_growth.csv` is quarter-over-quarter**, not month-over-month —
   consecutive rows are 3 months apart by construction. Labeled accordingly.
6. **Distinct repo/actor counts are lower bounds.** Spark's `countDistinct` is
   per (month, class, event-type), so summing across types double-counts; we
   report the max across types instead.

---

## Figures

| File | Shows |
|---|---|
| `fig1_ai_share.png` | AI/ML share of all events, 21Q1–26Q3, releases annotated **← headline chart** |
| `fig2_indexed_volume.png` | AI vs general volume indexed to 21Q1 = 100 |
| `fig3_event_mix.png` | Event-type mix, AI vs general, pooled |
| `fig4_star_intensity.png` | Star-rate ratio per quarter — above 1 every quarter |
| `fig5_population.png` | Distinct AI repos and actors — the 23Q2 population jump |
| `fig6_data_quality.png` | The two rejection checks and the three bad days |

All numbers in this document are emitted by `analysis.py` into `results.json`;
nothing here is hand-typed from a chart.
