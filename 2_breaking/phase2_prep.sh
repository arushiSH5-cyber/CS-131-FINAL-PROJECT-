#!/usr/bin/env bash
# CS131 Phase 2 prep:
#  (1) day.json   — one full day (2024-01-15) uncompressed NDJSON, the file
#                   pandas will choke on (multi-GB).
#  (2) excel_rowcap.csv — 8 hours of events flattened to CSV, > 2M rows,
#                   comfortably past Excel's 1,048,576-row cap.
set -uo pipefail
cd "$HOME/final_project/data"
LOG="$HOME/final_project/2_breaking/phase2_prep.log"
: > "$LOG"

echo "== build day.json (24 hourly files, uncompressed) ==" | tee -a "$LOG"
{ time zcat 2024-01-15-{0..23}.json.gz > day.json ; } 2>&1 | tee -a "$LOG"
ls -la day.json | tee -a "$LOG"
{ time wc -l day.json ; } 2>&1 | tee -a "$LOG"

echo "== build excel_rowcap.csv (8 hours flattened, id,type,actor,repo,created_at) ==" | tee -a "$LOG"
echo 'id,type,actor,repo,created_at' > excel_rowcap.csv
{ time zcat 2024-01-15-{0..7}.json.gz \
    | jq -r '[.id,.type,.actor.login,.repo.name,.created_at] | @csv' \
    >> excel_rowcap.csv ; } 2>&1 | tee -a "$LOG"
ls -la excel_rowcap.csv | tee -a "$LOG"
wc -l excel_rowcap.csv | tee -a "$LOG"
echo "done" | tee -a "$LOG"
