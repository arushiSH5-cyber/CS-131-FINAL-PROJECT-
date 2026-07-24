#!/usr/bin/env bash
# CS131 Phase 1 — run EVERY profiling command with `time`, sequentially,
# logging the exact command and its real output. This log is the source of
# truth pasted into 1_profile/profiling.txt.
#
# Sequential on purpose: timings must not contaminate each other.
set -uo pipefail
cd "$HOME/final_project/data"
LOG="$HOME/final_project/1_profile/profiling_run.log"
: > "$LOG"

note() { echo -e "$*" | tee -a "$LOG"; }

run() {
  # $1 = the exact command string (shown and executed verbatim)
  note "\$ time $1"
  { time eval "$1"; } >> "$LOG" 2>&1
  note ""
}

note "=== CS131 Phase 1 profiling run ==="
note "host: $(hostname)  date: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
note "dataset: GH Archive, 1 day per quarter 2021-Q1..2026-Q3 (the 15th), 24 hourly files/day"
note "file inventory:"
run "ls *.json.gz | wc -l"

note "================================================================"
note "0. PROVE THE SIZE FLOOR (> 5 GB and > 50 million rows)"
note "================================================================"
run "du -ch *.json.gz | tail -1"
run "zcat *.json.gz | wc -c"
run "zcat *.json.gz | wc -l"

note "================================================================"
note "1. PEEK AT THE SCHEMA (head / tail / jq)"
note "================================================================"
run "zcat 2024-01-15-15.json.gz | head -1 | jq ."
run "zcat 2024-01-15-15.json.gz | head -1 | jq 'keys'"
run "zcat 2024-01-15-15.json.gz | tail -1 | jq -c '{id,type,actor:.actor.login,repo:.repo.name,created_at}'"

note "================================================================"
note "2. TOP CATEGORIES / CARDINALITY (sort | uniq -c | sort -nr)"
note "================================================================"
run "zcat *.json.gz | jq -r '.type' | sort | uniq -c | sort -nr"
run "zcat *.json.gz | jq -r '.actor.login' | LC_ALL=C sort -u | wc -l"
run "zcat *.json.gz | jq -r '.repo.name'  | LC_ALL=C sort -u | wc -l"

note "================================================================"
note "3. NUMERIC AGGREGATE (awk sum / average)"
note "================================================================"
run "zcat *.json.gz | jq -r 'select(.type==\"PushEvent\") | .payload.size' | awk '{s+=\$1; n++} END{printf \"sum=%d avg=%.3f n=%d\\n\", s, s/n, n}'"

note "================================================================"
note "4. FILTERING COUNTS (grep -c)"
note "================================================================"
run "zcat *.json.gz | grep -c -iE '\"name\":\"[^\"]*(llm|gpt|pytorch|tensorflow|langchain|diffus|transformer|huggingface|openai|neural|deep-learning|machine-learning|agentic|rag-)'"
run "zcat *.json.gz | grep -c '\"type\":\"PullRequestEvent\"'"

note "=== profiling run complete: $(date -u +%Y-%m-%dT%H:%M:%SZ) ==="
