#!/usr/bin/env bash
# CS131 Phase 1 profiling — part 3.
# Waits for part 2 (run_profiling_fast.sh -> profiling_run2.log) to finish so
# timings never overlap, then runs the remaining commands sequentially:
#   A. clean re-run of the trivial inventory commands (part-1 log is tainted)
#   B. the exact single-stream `zcat *.json.gz | wc -c` size-floor proof
#      (part 1's attempt was SIGTERMed -> partial count, unusable)
#   C. rubric extras on ONE hourly file: cut -d',' and column -t
# (A full-dataset single-stream jq pass was considered and dropped: hours of
#  runtime, and B vs part 2's 0b already gives the 1-core-vs-10-core number.)
# Launched via setsid so an SSH/network drop cannot kill it.
# Whole script runs under nice -n 19 / ionice -c3 (shared box etiquette).
set -uo pipefail
cd "$HOME/final_project/data"
LOG="$HOME/final_project/1_profile/profiling_run3.log"
LOG2="$HOME/final_project/1_profile/profiling_run2.log"
FAST="$HOME/final_project/1_profile/run_profiling_fast.sh"
: > "$LOG"

note() { echo -e "$*" | tee -a "$LOG"; }
run() {
  note "# $(uptime | sed 's/.*load/load/')"
  note "\$ time $1"
  { time eval "$1"; } >> "$LOG" 2>&1
  note ""
}

note "=== CS131 Phase 1 profiling run, part 3 (single-stream redos + extras; nice 19) ==="
note "host: $(hostname)  started: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
note "waiting for part 2 to complete before touching the data (clean timings)..."

RELAUNCHED=0
while ! grep -q 'part 2 complete' "$LOG2" 2>/dev/null; do
  if pgrep -f 'run_profiling_fast\.sh' >/dev/null 2>&1; then
    sleep 60
  elif [ "$RELAUNCHED" -eq 0 ]; then
    note "part 2 process gone without completion marker -> relaunching it ($(date -u +%Y-%m-%dT%H:%M:%SZ))"
    cp "$LOG2" "$LOG2.partial.$(date +%s)" 2>/dev/null || true
    RELAUNCHED=1
    bash "$FAST"   # synchronous; rewrites profiling_run2.log from scratch
  else
    note "WARNING: part 2 died twice without completing; proceeding with part 3 anyway."
    break
  fi
done
note "part 2 finished; starting part 3 at $(date -u +%Y-%m-%dT%H:%M:%SZ)"
note ""

note "================================================================"
note "A. INVENTORY (clean re-run; part-1 log was contaminated)"
note "================================================================"
run "ls *.json.gz | wc -l"
run "du -ch *.json.gz | tail -1"

note "================================================================"
note "B. UNCOMPRESSED SIZE — exact template command, single stream"
note "================================================================"
run "zcat *.json.gz | wc -c"

note "================================================================"
note "C. RUBRIC EXTRAS on one hourly file: cut -d',' -f and column -t"
note "================================================================"
note "# First 3 events as CSV (schema peek, csv-tool friendly):"
run "zcat 2024-01-15-15.json.gz | head -3 | jq -r '[.created_at,.type,.actor.login,.repo.name] | @csv'"
note "# Event-type counts in that hour via cut on the CSV field:"
run "zcat 2024-01-15-15.json.gz | jq -r '[.created_at,.type,.repo.name] | @csv' | cut -d',' -f2 | sort | uniq -c | sort -nr | head -15"
note "# Same table aligned with column -t:"
run "zcat 2024-01-15-15.json.gz | jq -r '.type' | sort | uniq -c | sort -nr | column -t"

note "=== part 3 complete: $(date -u +%Y-%m-%dT%H:%M:%SZ) ==="
