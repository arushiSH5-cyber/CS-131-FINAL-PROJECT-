#!/usr/bin/env bash
# CS131 Phase 1 profiling — part 2 (fast): the characterization commands over
# the FULL 552-file dataset, parallelized across 10 of the 20 cores (shared
# machine etiquette: run under nice -n 19 + ionice -c3 so others preempt us).
# Still pure streaming — constant memory per core, nothing loaded into RAM.
# Every command is prefixed with `time`. Sequential between commands so the
# timings stay clean.
set -uo pipefail
cd "$HOME/final_project/data"
LOG="$HOME/final_project/1_profile/profiling_run2.log"
: > "$LOG"

note() { echo -e "$*" | tee -a "$LOG"; }
run() {
  note "\$ time $1"
  { time eval "$1"; } >> "$LOG" 2>&1
  note ""
}

T=$(mktemp -d /tmp/prof_XXXX)
trap 'rm -rf "$T"' EXIT

# Day-1 agreed AI/ML keyword list (see DATASET.md) + PR-event literal,
# exported so the parallel sub-shells inherit them.
export AIRE='"name":"[^"]*(llm|gpt|pytorch|tensorflow|langchain|diffus|transformer|huggingface|openai|neural|deep-learning|machine-learning|agentic|rag-)'
export PRRE='"type":"PullRequestEvent"'

note "=== CS131 Phase 1 profiling run, part 2 (parallel, 10 of 20 cores, nice 19) ==="
note "host: $(hostname)  date: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
note ""

note "================================================================"
note "0a. ROW COUNT — single stream, exact template command (> 50 M floor)"
note "================================================================"
run "zcat *.json.gz | wc -l"

note "================================================================"
note "0b. UNCOMPRESSED SIZE — parallel (per-file zcat|wc -c, summed)"
note "================================================================"
run "ls *.json.gz | xargs -P 10 -n 28 sh -c 'zcat \"\$@\" | wc -c' sh | awk '{s+=\$1} END{print s}'"

note "================================================================"
note "1. PEEK AT THE SCHEMA (head / tail / jq)"
note "================================================================"
run "zcat 2024-01-15-15.json.gz | head -1 | jq ."
run "zcat 2024-01-15-15.json.gz | head -1 | jq 'keys'"
run "zcat 2024-01-15-15.json.gz | tail -1 | jq -c '{id,type,actor:.actor.login,repo:.repo.name,created_at}'"

note "================================================================"
note "2. TOP CATEGORIES / CARDINALITY — parallel over all 552 files"
note "================================================================"
note "# Event-type distribution (per-file jq|sort|uniq -c, merged with awk):"
run "ls *.json.gz | xargs -P 10 -n 28 sh -c 'zcat \"\$@\" | jq -r \".type\" | sort | uniq -c' sh | awk '{c[\$2]+=\$1} END{for(t in c) printf \"%9d %s\\n\", c[t], t}' | sort -nr"

note "# Distinct actors (per-batch sorted-unique files, then one merge):"
run "ls *.json.gz | xargs -P 10 -n 28 sh -c 'zcat \"\$@\" | jq -r \".actor.login\" | LC_ALL=C sort -u > $T/actors_\$\$.txt' sh && LC_ALL=C sort -mu $T/actors_*.txt | wc -l"

note "# Distinct repos (same technique):"
run "ls *.json.gz | xargs -P 10 -n 28 sh -c 'zcat \"\$@\" | jq -r \".repo.name\" | LC_ALL=C sort -u > $T/repos_\$\$.txt' sh && LC_ALL=C sort -mu $T/repos_*.txt | wc -l"

note "================================================================"
note "3. NUMERIC AGGREGATE (awk) — commits per PushEvent, parallel"
note "================================================================"
run "ls *.json.gz | xargs -P 10 -n 28 sh -c 'zcat \"\$@\" | jq -r \"select(.type==\\\"PushEvent\\\") | .payload.size\" | awk \"{s+=\\\$1; n++} END{print s, n}\"' sh | awk '{S+=\$1; N+=\$2} END{printf \"sum=%d avg=%.3f n=%d\\n\", S, S/N, N}'"

note "================================================================"
note "4. FILTERING COUNTS (grep -c) — parallel, per-batch counts summed"
note "================================================================"
note "# Events mentioning an AI/ML repo keyword (pre-filter; list in DATASET.md):"
run "ls *.json.gz | xargs -P 10 -n 28 sh -c 'zcat \"\$@\" | grep -c -iE \"\$AIRE\"' sh | awk '{s+=\$1} END{print s}'"

note "# PullRequestEvents only:"
run "ls *.json.gz | xargs -P 10 -n 28 sh -c 'zcat \"\$@\" | grep -c \"\$PRRE\"' sh | awk '{s+=\$1} END{print s}'"

note "=== part 2 complete: $(date -u +%Y-%m-%dT%H:%M:%SZ) ==="
