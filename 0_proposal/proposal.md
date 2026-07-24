# Proposal — CS 131 Final Project

**Title:** From Code to Copilots: Measuring the Rise of AI/ML Open-Source Activity on GitHub (2021–2026)

**Members:** Yixu Liu · Arushi Nirmal

Open-source development shifted hard toward AI/ML over the last five years, but
"everyone knows AI is booming" is an assumption, not a measurement. **Motivation:**
we want to quantify that shift from the raw public record instead of anecdotes.
**Goals:** using the full GitHub public event stream, we will compare activity in
AI/ML repositories against general software repositories from 2021 to 2026 —
measuring event volume, growth rates, and dominant event types (pushes, pull
requests, issues, stars, forks) — and pinpoint whether jumps line up with major
AI-tool releases. **Technical tools:** we characterize the data with command-line
streaming (`zcat`, `jq`, `awk`, `grep -c`, `sort | uniq -c`, `wc -l`, all timed),
demonstrate the breaking point of in-memory tools (Excel's row cap and pandas
running out of RAM), then process the full dataset with **PySpark on GCP
Dataproc**, reading directly from a **GCS** bucket and running a 1/2/4-worker
scaling experiment.

**Dataset:** *GH Archive* (gharchive.org) — an hourly archive of every public
GitHub event as gzip-compressed newline-delimited JSON. We pull enough days
across 2021–2026 to exceed **5 GB / 50 million events**.

<!-- Keep the submitted PDF to at most HALF a page. Export this to proposal.pdf. -->
