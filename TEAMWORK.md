# Teamwork — Division of Work

How the two of us split this project. The goal of this split is that each partner
**owns a complete, end-to-end slice** of the pipeline — code *and* commands *and*
writeup — so we can work in parallel, our commit histories each stand on their
own, and we meet in the middle at one clean data handoff. Read alongside
[`RULES.md`](RULES.md) (the grading-critical workflow rules) and the
[`README.md`](README.md) phase map.

**Members:** Yixu Liu · Arushi Nirmal
**Presentation:** August 3 (joint)

---

## Two ownership tracks

We divided the four phases into two tracks that run down opposite ends of the
same pipeline and join at the aggregated-data handoff.

- **Arushi — Data Characterization & Storytelling.**
  Owns the *front* of the pipeline (what is this data, at the command line) and
  the *end* of it (what does the data actually say, and how we present it). This
  is the through-line the poster audience sees: from "here's the raw event
  stream" to "here's the answer and the charts that prove it."

- **Yixu — Scaling & Cloud Infrastructure.**
  Owns the *engine room*: demonstrating where in-memory tools give out, then
  standing up the distributed pipeline (GCS + Dataproc + PySpark) that processes
  the full dataset, plus the shared repo/environment plumbing both tracks run on.

Both tracks involve real coding and real timed command runs — that's a hard
requirement (`RULES.md` §2, §4), and the split is built to satisfy it for each
partner independently.

---

## Working in parallel — neither track blocks the other

The split is designed so **both partners can start in Week 1 and each work all
the way to a complete draft without waiting on the other.** Neither of us is ever
idle waiting for the other to finish.

- **Separate toolchains, shared inputs.** The two tracks run on completely
  different tools (CLI + Excel + notebook vs. memory limits + Spark + cloud).
  They share only the *raw data* — which either of us downloads independently
  with `download_gharchive.sh` — and one keyword definition. There is no
  day-to-day dependency between them.
- **The keyword list is a Day-1 agreement, not a wait.** We fix the AI/ML repo
  keyword set together in the first week (a 10-minute conversation), and from
  then on both tracks use it independently.
- **The one natural chain is decoupled.** Phase 4's charts would normally wait on
  Phase 3's aggregated output — so we break that: Arushi builds and styles the
  charts against a **small sample aggregation first** (her own Phase 1 output or
  the existing sample notebook), and the full Spark CSVs are a **drop-in swap at
  the end** that only refreshes the numbers. The chart code is finished long
  before Spark is; nobody blocks.

Result: two independent streams that run start-to-finish in parallel and
integrate late into one poster. Parallel — but still one team: shared infra, one
agreed method, a joint poster, and a joint presentation.

---

## Ownership by phase

| Phase | Directory | Lead | Also contributes |
|-------|-----------|------|------------------|
| 0 Proposal | `0_proposal/` | Both | — |
| 1 Profile | `1_profile/` | **Arushi** | Yixu (keyword list, review) |
| 2 Breaking — Excel | `2_breaking/` | **Arushi** | — |
| 2 Breaking — pandas / memory | `2_breaking/` | **Yixu** | — |
| 3 Scaling | `3_scaling/` | **Yixu** | Arushi (pairs on a run; records runtimes) |
| 4 Analysis + Poster | `4_analysis/` | **Arushi** | Yixu (supplies aggregated data; co-interprets) |

---

## Detailed responsibilities

### Arushi — Data Characterization & Storytelling

**Phase 1 — Profiling (`1_profile/profiling.txt`).**
Own the command-line characterization end to end. The exact commands are laid
out in `profiling.txt`; the work is to run each one **with `time` in front**,
paste the real timed output, and prove the size floor with genuine `du -h` /
`wc -l` numbers.

- Pull data with the helper: `./download_gharchive.sh 2024-01-15 2024-01-22`
  (see [`DATASET.md`](DATASET.md) for the acquisition pipeline).
- Run and record: size floor (`> 5 GB` and `> 50 M` rows), schema peek (`jq`),
  event-type distribution (`sort | uniq -c`), actor/repo cardinality, one
  numeric aggregate (`awk`), and the AI-keyword pre-filter (`grep -c`).
- Write the "Profiling" poster-section notes at the bottom of the file:
  wall-clock vs. data size, and why streaming works where load-into-memory
  wouldn't.

**Phase 2 — Excel breaking point (`2_breaking/`).**
Demonstrate and document the in-memory spreadsheet failure.

- Flatten one chunk of events to CSV, open it in Excel, and capture the row-cap
  behavior (1,048,576-row limit → truncates / refuses).
- Record the numbers and save `screenshots/excel_rowcap.png`; fill the Excel
  section of `breaking.txt`.

**Phase 4 — Analysis + Poster (`4_analysis/`).**
Own the answer and how it's told.

- Read the small aggregated CSVs produced by Phase 3 and build the charts
  (monthly AI-vs-general volume; growth rate; event-type mix over time) in the
  analysis notebook.
- Write the headline finding and tie any visible jumps to real AI-tool release
  dates.
- Lay out `poster.pdf`: motivating narrative + results + the three required
  sections (Profiling, Breaking, Scaling) + the repo link.

### Yixu — Scaling & Cloud Infrastructure

**Phase 2 — pandas / memory breaking point (`2_breaking/`).**
Force a reproducible in-memory failure and benchmark it.

- Use the `ulimit -v` (or memory-capped Docker) recipe in `breaking.txt` to make
  `pandas` OOM on a multi-GB file on the 121 GB box; capture peak memory and the
  crash; save `screenshots/pandas_oom.png`.
- Fill the two-way benchmark table (pandas OOM vs. CLI stream vs. PySpark).

**Phase 3 — Scaling on Dataproc (`3_scaling/`).**
Own the distributed pipeline end to end.

- Install `gcloud`/`gsutil` (user-space, no sudo — see [`SETUP.md`](SETUP.md)),
  create the GCS bucket, and upload the raw files once (`gsutil -m cp`).
- Own `spark_job.py`: explicit schema, AI-vs-general classification, monthly
  `groupBy` aggregation, `cache()` on the reused DataFrame.
- Run the **scaling experiment**: same job on 1 → 2 → 4 workers, record each
  wall-clock and speedup in `scaling.txt`, then **delete the cluster** every
  session (`RULES.md` §5).

**Shared infrastructure.**
Repo scaffold, `.venv`/`requirements.txt`, the `download_gharchive.sh` helper,
`.gitignore` discipline (no raw data in the repo), and the GCS data that Phase 3
reads.

---

## Shared by both

- **Proposal** (`0_proposal/`) — jointly written; submitted to Canvas.
- **Poster** — Arushi leads layout; both write their own phase sections and
  co-write the narrative and the final answer.
- **Presentation** (Aug 3) — both present; each leads the phases they owned.
- **Repo hygiene** — commit small and often with real messages; keep `main`
  working; never commit raw data.
- **Weekly sync** — quick check that the current phase's Definition of Done
  (`RULES.md` §3) is met before the next phase starts.

---

## Handoffs

The two tracks are independent except at two clean seams, and **neither seam
forces either partner to wait**:

1. **Keyword list → both (Day-1 agreement).** The AI/ML repo keyword set lives in
   one place ([`DATASET.md`](DATASET.md) / `spark_job.py`) so Arushi's Phase 1
   `grep` pre-filter and Yixu's Phase 3 Spark classifier use the *same*
   definition. We agree on it together in Week 1, then work independently.
2. **Aggregated CSVs → charts (late drop-in, not a block).** Phase 4's charts are
   built and styled against a small **sample** aggregation first — from Arushi's
   own Phase 1 output or the existing sample notebook — so the charting work
   starts immediately and never waits on Spark. When Phase 3's full aggregated
   CSVs land, they're a **drop-in swap** that refreshes the numbers; the chart
   code is already done. No one sits idle waiting for the other.

---

## Commit ownership (grading-critical)

`RULES.md` §4 requires the commit history to show **both** partners doing real
work — coding *and* running commands, not just pushing text.

- Each partner pushes under their **own** GitHub identity for the phases they
  own. Arushi's profiling runs, Excel demo, and analysis notebook are her
  commits; Yixu's memory experiment, Spark job, and scaling runs are his.
- When we pair on one machine (e.g. an early Phase 3 run together), use a
  **co-authored commit** so both names appear:

  ```
  git commit -m "Phase3: 2-worker scaling run, 4m12s wall-clock

  Co-authored-by: Arushi Nirmal <arushi-email>"
  ```

---

## Timeline

Four weeks, ending at the Aug 3 presentation. The two columns are **independent
streams** — read each one top-to-bottom on its own. Neither week in one column
depends on the same week in the other.

| Week | Arushi (independent stream) | Yixu (independent stream) |
|------|-----------------------------|---------------------------|
| 1 | **Phase 1** CLI profiling; agree keyword list | Repo/env/GCP groundwork; start raw-data download |
| 2 | **Excel** row-cap demo + screenshot | **pandas** OOM experiment + benchmark table |
| 3 | Build **Phase 4** charts on sample data; draft poster layout | **Phase 3** GCS + Spark + 1/2/4-worker scaling |
| 4 | Swap in final aggregated CSVs; finalize answer + poster | Deliver final CSVs; write own phase sections; co-interpret |

*Optional:* Arushi can pair on one of Yixu's Week-3 Dataproc runs to see it live
and co-author that commit — helpful, but not required for either stream to
finish.
