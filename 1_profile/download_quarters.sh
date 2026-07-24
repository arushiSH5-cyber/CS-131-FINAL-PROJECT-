#!/usr/bin/env bash
# Parallel GH Archive downloader for the CS131 dataset:
# 1 day per quarter, 2021-2026 (the 15th of Jan/Apr/Jul/Oct), 24 hours each.
# 8 parallel wget streams. Files land in ~/final_project/data/ (git-ignored).
set -uo pipefail

DEST="$HOME/final_project/data"
mkdir -p "$DEST"
cd "$DEST"

DAYS=""
for y in 2021 2022 2023 2024 2025; do
  DAYS+="$y-01-15 $y-04-15 $y-07-15 $y-10-15 "
done
DAYS+="2026-01-15 2026-04-15 2026-07-15"

# Build the list of missing files
LIST=$(mktemp)
for d in $DAYS; do
  for h in $(seq 0 23); do
    f="${d}-${h}.json.gz"
    [[ -s "$f" ]] || echo "$f" >> "$LIST"
  done
done

total=$(wc -l < "$LIST")
echo "need $total files -> $DEST"

# 8 parallel streams; -c resumes partial files; failures logged, not fatal
xargs -a "$LIST" -P 8 -I{} bash -c \
  'wget -q -c "https://data.gharchive.org/{}" || echo "FAILED {}" >> download_failures.log'

rm -f "$LIST"
echo "=== download pass complete ==="
[[ -f download_failures.log ]] && { echo "failures:"; cat download_failures.log; }
echo "files present: $(ls *.json.gz 2>/dev/null | wc -l)"
du -sh "$DEST"
