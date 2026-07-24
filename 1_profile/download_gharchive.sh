#!/usr/bin/env bash
# Download GH Archive raw hourly files over public HTTP (no Google needed).
# Files land in ~/final_project/data/ (git-ignored). Each hour ~130 MB, 24/day.
#
# Usage:
#   ./download_gharchive.sh 2024-01-15                 # one full day (24 files)
#   ./download_gharchive.sh 2024-01-15 2024-01-22      # inclusive date range
#   HOURS="0 6 12 18" ./download_gharchive.sh 2024-01-15   # only some hours/day
#
# Data source: https://data.gharchive.org/YYYY-MM-DD-H.json.gz  (H = 0..23)
set -euo pipefail

START="${1:?usage: $0 START_DATE [END_DATE]}"
END="${2:-$START}"
HOURS="${HOURS:-$(seq 0 23)}"
DEST="$HOME/final_project/data"
mkdir -p "$DEST"
cd "$DEST"

# iterate dates from START to END inclusive (GNU date)
d="$START"
while :; do
  for h in $HOURS; do
    f="${d}-${h}.json.gz"
    if [[ -s "$f" ]]; then
      echo "skip  $f (already have it)"
    else
      echo "get   $f"
      # -c resume, -q quiet; skip missing hours without aborting the whole run
      wget -q -c "https://data.gharchive.org/${f}" || echo "  !! missing/failed: $f"
    fi
  done
  [[ "$d" == "$END" ]] && break
  d="$(date -I -d "$d + 1 day")"
done

echo
echo "downloaded into: $DEST"
du -ch "$DEST"/*.json.gz | tail -1
echo "files: $(ls "$DEST"/*.json.gz 2>/dev/null | wc -l)"
