# Project Rules & Workflow

Read this before touching anything. These rules exist so we hit every graded
requirement and so the commit history proves **both partners** did real work.

## 1. Where work lives

- Everything goes under `~/final_project/` in the **kgr-17/CS131_final_project**
  repo. This is the submission repo (one repo per pair — we use this one).
  NOTE: the assignment text lists paths as `~/cs131/project/...`; confirm with the
  instructor that a dedicated repo is accepted, or mirror into `cs131/project/`.
- Never copy multi-GB raw data into the repo or the home dir. Raw data stays in
  `/tmp`, a scratch disk, or a **GCS bucket**. Only *commands, code, results, and
  screenshots* get committed.
- Add a `.gitignore` (already provided) so `*.json`, `*.gz`, `*.csv`, `*.parquet`
  never get committed by accident.

## 2. Grading-critical rules (do not skip)

- **Size floor is hard:** raw data must be **> 5 GB AND > 50 million rows**.
  Prove it in `1_profile/profiling.txt` with real `du -h` / `wc -l` output.
- **`time` in front of every profiling command** so cost is measured, not guessed.
- **Both members must commit meaningful work** to `project/` — coding *and*
  running commands, not just pushing a text file. See §4.
- Each phase has a **named poster section**: "Profiling", "Breaking", "Scaling",
  plus the final analysis. The poster must link back to this GitHub repo.
- **Delete the Dataproc cluster** at the end of each work session
  (`gcloud dataproc clusters delete …`). Prefer ephemeral clusters +
  `gcloud dataproc jobs submit pyspark`.

## 3. Phase order & Definition of Done

| Phase | Directory | Done when… |
|-------|-----------|-----------|
| 0 Proposal | `0_proposal/` | One-page PDF (≤ half page text) approved on Canvas |
| 1 Profile | `1_profile/` | `profiling.txt` has every exact command + timed output; size floor proven |
| 2 Breaking | `2_breaking/` | Excel failure screenshot + pandas OOM/time screenshot + benchmark table in `breaking.txt` |
| 3 Scaling | `3_scaling/` | PySpark job runs on Dataproc from `gs://…`; 1/2/4-worker runtimes in `scaling.txt` |
| 4 Analysis | `4_analysis/` | Question answered with viz; `poster.pdf` assembled with all 3 sections + repo link |

Do not start a phase's writeup before the prior phase's Definition of Done is met.

## 4. Git workflow (makes the commit history "meaningful")

- **Commit small and often**, with a real message describing what was run.
  Good: `Phase1: add uniq -c cardinality command + timed result (42s)`.
  Bad: `update`, `push txt`.
- **Both partners push under their own GitHub identity.** Split the work so each
  person owns some phases/commands. If you pair on one machine, use
  co-authored commits so both names appear:

  ```
  git commit -m "Phase1: event-type counts via jq | sort | uniq -c

  Co-authored-by: Partner Name <partner-email>"
  ```
- Branch per phase is optional; if used, open a PR and merge to `main`. Keep
  `main` always working.
- Never force-push shared history.

## 5. Cost & safety (GCP)

- Read raw data from GCS with `gs://…`; do **not** download it to the cluster or
  home dir.
- Smallest cluster that works. Scaling experiment = same job on 1 → 2 → 4
  workers; record runtime each time, then **delete the cluster**.
- Check for running clusters at end of day: `gcloud dataproc clusters list`.

## 6. Deliverable checklist (final)

- [ ] `0_proposal/proposal.pdf` submitted to Canvas, feedback received
- [ ] `1_profile/profiling.txt` — timed CLI commands, size floor proven
- [ ] `2_breaking/breaking.txt` + `2_breaking/screenshots/` — Excel + pandas
- [ ] `3_scaling/scaling.txt` + `*.py` — Dataproc job + 1/2/4-worker times
- [ ] `4_analysis/poster.pdf` — narrative, analysis, 3 phase sections, repo link
- [ ] Commit history shows both members coding + running commands
- [ ] All Dataproc clusters deleted
