# CS 131 Final Project — Big-Data Analysis of GitHub Activity

**Course:** CS 131 · **Format:** Pairs · **Duration:** ~4 weeks
**Members:** Yixu Liu (017406857) · Arushi Nirmal
**Repo:** https://github.com/kgr-17/CS131_final_project
**Presentation:** August 3 (poster on laptop screen)

---

Question

> **How has open-source activity around AI/ML repositories changed compared with
> general software-development repositories from 2021 to 2026?**

The "so what": AI tooling exploded over this window (large language models,
copilots, agent frameworks). We want to measure — not guess — whether public
GitHub activity actually shifted toward AI/ML repos, and by how much, using the
full public event stream rather than a sample.

Secondary questions we can answer from the same data:
- Which GitHub event types (push, PR, issue, fork, star/watch) dominate large projects?
- Which repos/orgs show the fastest growth in public activity?
- Did AI-repo activity jump after specific tool releases?

Dataset

**GH Archive** (https://www.gharchive.org/) — an hourly archive of the public
GitHub event timeline. Each hour is one gzip-compressed newline-delimited JSON
file (`https://data.gharchive.org/YYYY-MM-DD-H.json.gz`), one JSON object per
event (`PushEvent`, `PullRequestEvent`, `IssuesEvent`, `ForkEvent`,
`WatchEvent`, …), each carrying `type`, `actor`, `repo`, `payload`, `created_at`.

**Size floor (hard requirement):** raw data must be **> 5 GB** and **> 50 million
rows**. One recent day is millions of events; we pull enough days/months across
2021–2026 to comfortably clear both thresholds. Exact measured sizes are
recorded in Phase 1 (`1_profile/profiling.txt`).

**Backup dataset (Option B):** GDELT 2.0 global news/events — see
[`0_proposal/OPTION_B_gdelt.md`](0_proposal/OPTION_B_gdelt.md). Same four-phase
structure; used only if GH Archive is rejected in proposal feedback.

## The two-tool comparison (the point of the project)

1. **In-memory tools** (Excel, pandas) — load everything into RAM. We document
   them *breaking* on data this size (Phase 2).
2. **Streaming / distributed tools** (CLI pipelines, PySpark on Dataproc) — never
   hold the whole dataset in memory. We show them succeeding and *scaling*
   (Phases 1 & 3).

---

## Repository layout

```
CS131_final_project/       ← repo root
├── README.md              ← this file
├── RULES.md               ← collaboration + workflow rules (READ FIRST)
├── TEAMWORK.md            ← division of work: who owns which phase
├── 0_proposal/            ← one-page proposal PDF submitted to Canvas
├── 1_profile/             ← Phase 1: CLI profiling (no loading into memory)
│   └── profiling.txt        exact commands + timed results
├── 2_breaking/            ← Phase 2: Excel + pandas breaking point
│   ├── breaking.txt         experiment notes + numbers
│   └── screenshots/         Excel row-cap / pandas OOM screenshots
├── 3_scaling/             ← Phase 3: PySpark on Dataproc (done)
│   ├── scaling.txt          1 vs 2 vs 4 worker runtimes + full writeup
│   ├── spark_job.py         the PySpark job (same file for every cluster size)
│   ├── run_scaling.sh       submit + timing harness
│   ├── logs/                per-run driver logs, job timings, cluster snapshots
│   └── out/                 aggregated CSVs — 273.5 GB in, 43 KB out (Phase 4 input)
└── 4_analysis/            ← Phase 4: answer + visualizations + poster (done)
    ├── findings.md          the answer, four findings, data-quality gate, limits
    ├── analysis.ipynb       executed notebook — the whole argument, outputs kept
    ├── analysis.py          quality gate + series + headline numbers + figures
    ├── figures/             the ten charts
    └── poster.pdf           final poster (links back to this repo)
```

Milestones

| Week | Milestone | Status |
|------|-----------|--------|
| 1 | Proposal approved + Phase 1 CLI profiling | ☑ done — 552 files, 273.5 GB, 85.3 M events profiled (`1_profile/profiling.txt`) |
| 2 | Phase 2 — Excel fails, pandas chokes, benchmark table | ☑ done — Excel drops 35% silently; pandas 14× RAM amplification → MemoryError (`2_breaking/breaking.txt`) |
| 3 | Phase 3 — PySpark on Dataproc + 1/2/4-worker scaling | ☑ done — 43m37s → 17m28s → 10m21s, byte-identical outputs (`3_scaling/scaling.txt`) |
| 4 | Phase 4 — answer the question, visualize, poster | ☑ done — AI/ML grew 2.35× vs general 1.28×; starred 4× more, every quarter (`4_analysis/findings.md`) |

The answer

> **AI/ML activity grew 2.35× from 2021-Q1 to 2026-Q1 while general software grew
> 1.28× — 18.7%/yr vs 5.1%/yr. But AI/ML went only from 0.52% to 0.94% of all
> public GitHub events, spiking to 2.26% in 2023-Q2 (the GPT-4 / AutoGPT quarter)
> before giving most of it back. What durably changed is not how much AI code gets
> written — it is how much attention it attracts: AI/ML repos are starred at 4× the
> general rate in every single usable quarter.**
>
> *The AI boom shows up on GitHub as an attention boom first and a code boom second.*

Three of the 23 sampled days are rejected before any finding is computed — 2021-Q4
is missing hourly files, and 2026-Q2/Q3 lost interaction events upstream. The
`−68.65%` in `3_scaling/out/monthly_growth.csv` is that artifact, not a real
collapse. Full write-up: [`4_analysis/findings.md`](4_analysis/findings.md).

Tools

CLI: `zcat`/`gunzip`, `wc`, `jq`, `grep -c`, `cut`, `awk`, `sort`, `uniq -c`,
`time` · Python: `pandas` (to break it) · **PySpark** on **GCP Dataproc**,
data read directly from a **GCS** bucket via `gs://…`.

---

Reproducing

Each phase directory documents its own exact commands. Start with
[`RULES.md`](RULES.md) for the workflow and [`TEAMWORK.md`](TEAMWORK.md) for who
owns each phase, then work the phases in order 1 → 4. See
[`0_proposal/proposal.md`](0_proposal/proposal.md) for the one-page proposal that
was submitted to Canvas.
