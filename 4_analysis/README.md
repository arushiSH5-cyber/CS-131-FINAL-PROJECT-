# Phase 4 — Answer the Question + Poster

The "so what" that justifies all the engineering.

> **How has open-source activity around AI/ML repositories changed compared with
> general software-development repositories from 2021 to 2026?**

## The answer

**AI/ML open-source activity grew 2.35× from 2021-Q1 to 2026-Q1 while general
software activity grew 1.28× — 18.7%/yr vs 5.1%/yr. But AI/ML went only from
0.52% to 0.94% of all public GitHub events, spiking to 2.26% in 2023-Q2 (the
GPT-4 / AutoGPT quarter) before giving most of it back. What durably changed is
not how much AI code gets written — it is how much attention it attracts: AI/ML
repos are starred at 4× the general rate in every single usable quarter.**

> The AI boom shows up on GitHub as an attention boom first and a code boom second.

Full write-up with all four findings and the limits: **[`findings.md`](findings.md)**

## What's here

| File | What it is |
|---|---|
| [`findings.md`](findings.md) | The write-up — headline, four findings, data-quality section, limits |
| [`analysis.ipynb`](analysis.ipynb) | Executed notebook walking the whole argument, outputs committed |
| [`analysis.py`](analysis.py) | All the logic: quality gate, series, headline numbers, six figures |
| [`make_poster.py`](make_poster.py) | Builds `poster.pdf` from `results.json` + `figures/` |
| [`poster.pdf`](poster.pdf) | The poster (16:9, presented Aug 3) — also `poster.png` |
| `results.json` | Every headline number, emitted by `analysis.py` |
| `quarterly_series.csv` | The 23-quarter series with quality flags |
| `figures/` | The six charts |

The notebook **imports** `analysis.py` rather than restating it, and the poster
reads `results.json`. So the notebook, the write-up and the poster cannot drift
apart — there is one source of truth for every number.

## Reproduce

```bash
pip install pandas matplotlib          # see ../requirements.txt
python3 analysis.py                    # -> figures/, results.json, quarterly_series.csv
python3 make_poster.py                 # -> poster.pdf, poster.png
```

Input is the Phase 3 handoff, already committed: `../3_scaling/out/monthly.csv`
(692 rows) and `monthly_growth.csv` (46 rows) — **273.5 GB of raw GH Archive
JSON in, 43 KB of CSV out**. No cluster, no raw data and no network needed.

## One thing worth knowing before reading any number

Each quarterly point rests on **one sampled day**, so a single bad day becomes a
fake trend. `analysis.py::flag_samples` rejects **3 of the 23 sampled days**
before any finding is computed:

| Quarter | Check that caught it | What actually happened |
|---|---|---|
| 2021-Q4 | volume — 32% of a median day | hourly files missing from the sample |
| 2026-Q2 | event mix — 49% of median | upstream archive dropped interaction events |
| 2026-Q3 | event mix — 3% of median | same, worse: general PRs 304,163 → 10,806 |

The `−68.65%` and `+296.94%` sitting in `monthly_growth.csv` are the 2021-Q4
artifact — one short day, first as a fake crash and then as a fake recovery.
Reporting those as findings would have been the biggest available error in this
project. See `figures/fig6_data_quality.png`.

## Charts

1. `fig1_ai_share.png` — AI/ML share of all events, 21Q1–26Q3, releases annotated **← headline**
2. `fig2_indexed_volume.png` — AI vs general volume indexed to 21Q1 = 100
3. `fig3_event_mix.png` — event-type mix, AI vs general, pooled
4. `fig4_star_intensity.png` — star-rate ratio per quarter, above 1 every quarter
5. `fig5_population.png` — distinct AI repos and actors, the 23Q2 population jump
6. `fig6_data_quality.png` — the two rejection checks and the three bad days

## Poster contents (per RULES.md §2)

- Motivating narrative (why measure this instead of assuming it)
- Final analysis results + visualizations
- The three required sections: **Profiling**, **Breaking**, **Scaling**
- A link back to https://github.com/kgr-17/CS131_final_project
