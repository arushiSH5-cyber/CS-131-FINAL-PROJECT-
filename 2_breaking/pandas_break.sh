#!/usr/bin/env bash
# CS131 Phase 2B — force the reproducible pandas failure, capture evidence.
#
# Experiment 1: measure pandas' real memory appetite on ONE HOUR (~1 GB raw)
#               with /usr/bin/time -v  -> extrapolate to the full dataset.
# Experiment 2: pandas on ONE DAY (day.json, ~multi-GB) under an 8 GB
#               virtual-memory cap -> MemoryError / crash. THIS is the
#               screenshot moment.
set -uo pipefail
cd "$HOME/final_project"
PY=".venv/bin/python"
LOG="$HOME/final_project/2_breaking/pandas_break.log"
: > "$LOG"

echo "===== Experiment 1: pandas memory appetite, ONE HOUR (uncapped) =====" | tee -a "$LOG"
echo "\$ /usr/bin/time -v $PY -c 'import pandas as pd; df = pd.read_json(\"data/2024-01-15-15.json.gz\", lines=True); print(df.shape)'" | tee -a "$LOG"
/usr/bin/time -v $PY -c 'import pandas as pd; df = pd.read_json("data/2024-01-15-15.json.gz", lines=True); print(df.shape)' 2>&1 | grep -E "shape|\(|Maximum resident|Elapsed|Exit" | tee -a "$LOG"

echo | tee -a "$LOG"
echo "===== Experiment 2: pandas on ONE DAY under 8 GB cap  ->  OOM =====" | tee -a "$LOG"
echo "\$ ( ulimit -v 8000000; python -c 'import pandas as pd; df = pd.read_json(\"data/day.json\", lines=True); print(df.shape)' )" | tee -a "$LOG"
OUT=$(mktemp)
( ulimit -v 8000000
  $PY -c 'import pandas as pd; df = pd.read_json("data/day.json", lines=True); print(df.shape)' ) > "$OUT" 2>&1
STATUS=$?
tail -15 "$OUT" | tee -a "$LOG"
echo "exit code: $STATUS" | tee -a "$LOG"
rm -f "$OUT"
echo | tee -a "$LOG"
echo "done" | tee -a "$LOG"
