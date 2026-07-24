# Phase 2 — How to reproduce each breaking point and screenshot it

Two failures to capture: **Excel's row cap** and **pandas running out of
memory**. Both are 100% reproducible with the steps below. Save the images
into `2_breaking/screenshots/` with the exact filenames referenced in
`breaking.txt`.

---

## A. Excel row cap → `screenshots/excel_rowcap.png`

Excel hard-caps a sheet at **1,048,576 rows** (Excel 2007+). We open a CSV
with ~1.6 million real GitHub events and let it fail.

**1. Get the CSV onto your laptop.** The file is on the DGX at
`/home/ishigaki-cs6/final_project/data/excel_rowcap.csv` (148 MB, 1,612,732
rows — git-ignored, never commit it). Two easy ways:

- **JupyterLab** (see `HOW_TO_JUPYTER.md`): in the file browser open
  `final_project/data/`, right-click `excel_rowcap.csv` → **Download**.
- **scp** from your laptop (absolute path, works for either of us):
  ```
  scp <your-username>@<dgx-hostname>:/home/ishigaki-cs6/final_project/data/excel_rowcap.csv .
  ```

**2. Open it in Excel** (File → Open, or double-click).

**3. What you will see — this is the screenshot:** Excel loads for a while,
then shows the alert:

> **File not loaded completely.**
> This data set is too large for the Excel grid. If you save this workbook,
> you'll lose data that wasn't loaded. …

Click OK, then press **Ctrl+End** (Mac: **Fn+Ctrl+→**) — the cursor lands on
the very last row, **1,048,576**, mid-day: everything after it was silently
thrown away.

**4. Frame the screenshot** so it shows BOTH:
- the "File not loaded completely" dialog (or re-trigger it by re-opening), and
- the bottom row number **1048576** visible in the row header / Name Box after
  Ctrl+End.

If the dialog closed before you could capture it, just reopen the file — it
appears every time.

*(Excel for Mac shows the same warning; LibreOffice shows "The data could not
be loaded completely because the maximum number of rows per sheet was
exceeded" — also acceptable, but the assignment says Excel, so prefer Excel.)*

**5. Record in `breaking.txt`:** rows in the CSV (from `wc -l`), what Excel
kept (1,048,576 incl. header), what % of the data was silently dropped.
(Already filled in — just confirm what you see matches.)

---

## B. pandas out-of-memory → `screenshots/pandas_oom.png`

This box has 121 GiB unified memory, so to make the failure *reproducible and
safe* we cap the Python process at **8 GB** (a typical laptop) with `ulimit`,
then ask pandas to load ONE day of GH Archive (18.9 GB of JSON). pandas tries
to pull all of it into RAM and dies with `MemoryError`.

**1. Open two terminals on the DGX** (two JupyterLab terminal tabs work).

**2. Terminal 2 (the memory monitor)** — start this FIRST:
```bash
watch -n 1 'free -h; echo; ps -o pid,rss,vsz,etime,cmd -C python | head -5'
```
You'll watch the python process RSS climb toward the cap and vanish.

**3. Terminal 1 (the crash):**
```bash
cd ~/final_project
( ulimit -v 8000000    # cap THIS subshell at ~8 GB virtual memory
  .venv/bin/python -c 'import pandas as pd
df = pd.read_json("data/day.json", lines=True)
print(df.shape)' )
```

**4. What you will see — this is the screenshot:** after ~1–2 minutes the
traceback ends in:

```
MemoryError
```

(Under a `ulimit -v` cap the allocation fails *inside* Python, so you get a
clean `MemoryError` traceback — the kernel OOM-killer `Killed` message only
appears if you run uncapped on a machine that truly runs out.) Screenshot
**Terminal 1 showing the `ulimit` command + the MemoryError traceback**,
ideally with Terminal 2's memory readout visible next to it.

**5. The companion number** (already captured in `pandas_break.log`):
uncapped, pandas needs **multiple GB of RAM just for ONE HOUR** of data
(`/usr/bin/time -v` → "Maximum resident set size"). Scale that to the full
23-day dataset and pandas would need **far more RAM than the 121 GB this DGX
has** — the failure isn't the laptop's fault; load-into-memory fundamentally
doesn't scale. That extrapolation goes on the poster next to the screenshot.

**6. Record in `breaking.txt`:** the cap (8 GB), file size attempted
(`ls -lh data/day.json`), outcome (MemoryError), wall-clock before death.

---

## C. Bonus screenshot (optional, strong on the poster)

While `1_profile/run_profiling.sh` or the Spark job (`spark_agg.py`) is
running, screenshot `htop`:
20 cores lit up by Spark vs. one lonely core for `zcat | jq` — visually
explains WHY distributed wins.
