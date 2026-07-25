"""
CS 131 Final Project — Phase 3 PySpark job (GH Archive).

Reads GH Archive gzip-NDJSON events directly from GCS, classifies each event's
repo as AI/ML vs general, and aggregates monthly activity by class and event
type. Same job is run on 1 / 2 / 4 workers for the scaling experiment — only
the cluster size changes, this file does not.

Outputs (small CSVs, the Phase 4 handoff):
  <out_root>/monthly         month, repo_class, type, events, actors, repos,
                             class_events, share_of_class   (join demo)
  <out_root>/monthly_growth  month, repo_class, class_events, prev_events,
                             mom_growth_pct                 (window demo)

Submit:
  gcloud dataproc jobs submit pyspark spark_job.py \
    --cluster cs131-cluster --region us-central1 \
    -- 'gs://yixuliu-cs131-project/gharchive/*.json.gz' \
       gs://yixuliu-cs131-project/out
"""
import sys
from pyspark.sql import SparkSession, Window, functions as F
from pyspark.sql.types import StructType, StructField, StringType

# Explicit schema (do NOT let Spark infer over GBs of JSON).
SCHEMA = StructType([
    StructField("type", StringType()),
    StructField("created_at", StringType()),
    StructField("repo", StructType([
        StructField("id", StringType()),
        StructField("name", StringType()),
    ])),
    StructField("actor", StructType([
        StructField("login", StringType()),
    ])),
])

# Case-insensitive markers that flag an AI/ML repo by name.
# EXACTLY the Phase 1 AIRE keyword list (DATASET.md Day-1 agreement) so the
# result cross-checks against 1_profile's grep -c pre-filter. Difference to
# keep in mind: this matches repo.name ONLY, while the Phase 1 grep matched
# any  "name":"..."  string on the raw line (incl. nested payload repos), so
# grep's 787,912 is a slight overcount by construction.
AI_PAT = r"(?i)(llm|gpt|pytorch|tensorflow|langchain|diffus|transformer|" \
         r"huggingface|openai|neural|deep-learning|machine-learning|" \
         r"agentic|rag-)"


def main(in_path: str, out_root: str) -> None:
    spark = (SparkSession.builder
             .appName("cs131-gharchive-monthly")
             .getOrCreate())

    df = spark.read.schema(SCHEMA).json(in_path)

    enriched = (df
        .withColumn("month", F.substring("created_at", 1, 7))          # YYYY-MM
        .withColumn("repo_class",
                    F.when(F.col("repo.name").rlike(AI_PAT), "ai_ml")
                     .otherwise("general")))

    enriched.cache()  # reused by every aggregation + the sanity counts below

    # Corrupt/incomplete lines parse to all-null rows (PERMISSIVE mode); they
    # would silently vanish from the joined CSV and poison the lag window
    # (NULL sorts first). Aggregate over clean rows only; both counts are
    # printed at the end so any dropped rows are visible in the driver log.
    clean = enriched.filter(F.col("month").isNotNull()
                            & F.col("repo.name").isNotNull())

    # Monthly event volume by repo class and event type (groupBy demo).
    monthly = (clean
        .groupBy("month", "repo_class", "type")
        .agg(F.count("*").alias("events"),
             F.countDistinct("actor.login").alias("actors"),
             F.countDistinct("repo.id").alias("repos")))

    # JOIN demo: each event type's share of its class's monthly volume.
    class_totals = (clean
        .groupBy("month", "repo_class")
        .agg(F.count("*").alias("class_events")))
    monthly_with_share = (monthly
        .join(class_totals, ["month", "repo_class"])
        .withColumn("share_of_class",
                    F.round(F.col("events") / F.col("class_events"), 6))
        .orderBy("month", "repo_class", "type"))
    monthly_with_share.coalesce(1).write.mode("overwrite") \
        .option("header", True).csv(out_root + "/monthly")

    # WINDOW demo: month-over-month growth of each class's total volume.
    w = Window.partitionBy("repo_class").orderBy("month")
    growth = (class_totals
        .withColumn("prev_events", F.lag("class_events").over(w))
        .withColumn("mom_growth_pct",
                    F.round(100.0 * (F.col("class_events") - F.col("prev_events"))
                            / F.col("prev_events"), 2))
        .orderBy("repo_class", "month"))
    growth.coalesce(1).write.mode("overwrite") \
        .option("header", True).csv(out_root + "/monthly_growth")

    # Sanity prints for the driver log — cross-checked against Phase 1:
    # parsed total should equal 85,339,283 (Spark JSON-object count, wc -l + 1).
    print(f"TOTAL_ROWS_PARSED={enriched.count()}")
    print(f"CLEAN_ROWS={clean.count()}")
    clean.groupBy("repo_class").count().orderBy("repo_class").show()
    (clean.groupBy("type").count().orderBy(F.desc("count")).show(20, False))

    spark.stop()


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit("usage: spark_job.py <in_glob> <out_root>   (both gs:// on Dataproc)")
    main(sys.argv[1], sys.argv[2])
