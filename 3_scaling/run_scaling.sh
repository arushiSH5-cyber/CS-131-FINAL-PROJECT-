#!/usr/bin/env bash
# CS131 Phase 3 — submit spark_job.py to a Dataproc cluster and record timings.
# Usage: ./run_scaling.sh <cluster-name> <tag>       e.g. ./run_scaling.sh cs131-w1 w1
# Writes logs/<tag>_submit.log (driver output + `time`), logs/<tag>_job.json
# (service-side status history) and logs/<tag>_cluster.json (hardware snapshot).
set -euo pipefail
CLUSTER=$1; TAG=$2
REGION=us-central1
BUCKET=gs://yixuliu-cs131-project
JOB=$(cd "$(dirname "$0")" && pwd)/spark_job.py
LOGS=$(cd "$(dirname "$0")" && pwd)/logs
mkdir -p "$LOGS"

# Hardware provenance: prove every run used identical machines/disks/image.
gcloud dataproc clusters describe "$CLUSTER" --region $REGION --format=json \
  > "$LOGS/${TAG}_cluster.json"

# The timed run. Wall-clock here includes gcloud submit/poll overhead; the
# service-side RUNNING->DONE time (primary metric) is extracted afterwards.
# Identical memory properties on EVERY run (fairness): the image defaults
# overcommit a single-node cluster (2x6773m executors + 4g driver + master
# daemons > 16 GB physical -> the kernel killed the driver, exit 143). These
# sizes fit the single node AND preserve the default 2-executors-per-node
# packing on multi-worker clusters, so per-node parallelism is unchanged.
PROPS='spark.driver.memory=1536m,spark.executor.memory=4096m,spark.executor.memoryOverhead=512m'

{ time gcloud dataproc jobs submit pyspark "$JOB" \
    --cluster "$CLUSTER" --region $REGION \
    --properties "$PROPS" \
    -- "$BUCKET/gharchive/*.json.gz" "$BUCKET/out/$TAG" ; } \
  > "$LOGS/${TAG}_submit.log" 2>&1

JOB_ID=$(grep -oE 'jobId: [a-z0-9]+' "$LOGS/${TAG}_submit.log" | head -1 | awk '{print $2}')
gcloud dataproc jobs describe "$JOB_ID" --region $REGION --format=json \
  > "$LOGS/${TAG}_job.json"

python3 - "$LOGS/${TAG}_job.json" <<'EOF'
import json, sys
from datetime import datetime
d = json.load(open(sys.argv[1]))
hist = d["statusHistory"] + [d["status"]]
ts = {h["state"]: h["stateStartTime"] for h in hist}
p = lambda s: datetime.fromisoformat(ts[s].replace("Z", "+00:00"))
print(f"jobId={d['reference']['jobId']}")
for s in ("PENDING", "SETUP_DONE", "RUNNING", "DONE"):
    if s in ts: print(f"  {s:10s} {ts[s]}")
if "RUNNING" in ts and "DONE" in ts:
    print(f"SERVICE_ELAPSED_RUNNING_TO_DONE={(p('DONE')-p('RUNNING')).total_seconds():.0f}s")
EOF
