"""
CS 131 Final Project — Phase 3 PySpark job (GH Archive).

Reads GH Archive gzip-NDJSON events directly from GCS, classifies each event's
repo as AI/ML vs general, and aggregates monthly activity by class and event
type. Same job is run on 1 / 2 / 4 workers for the scaling experiment — only
--num-workers changes, this file does not.

Submit:
  gcloud dataproc jobs submit pyspark spark_job.py \
    --cluster cs131-cluster --region us-west1 \
    -- gs://<BUCKET>/gharchive/'*.json.gz' gs://<BUCKET>/out/monthly
"""
import sys
from pyspark.sql import SparkSession, functions as F
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
AI_PAT = r"(?i)(llm|gpt|pytorch|tensorflow|langchain|diffus|transformer|" \
         r"stable-?diffusion|huggingface|openai|deep-?learning|neural|" \
         r"machine-?learning|/ml-|-ml/|agentic|rag-)"


def main(in_path: str, out_path: str) -> None:
    spark = (SparkSession.builder
             .appName("cs131-gharchive-monthly")
             .getOrCreate())

    df = spark.read.schema(SCHEMA).json(in_path)

    enriched = (df
        .withColumn("month", F.substring("created_at", 1, 7))          # YYYY-MM
        .withColumn("is_ai",
                    F.col("repo.name").rlike(AI_PAT).cast("int"))
        .withColumn("repo_class",
                    F.when(F.col("is_ai") == 1, "ai_ml").otherwise("general")))

    enriched.cache()  # reused by both aggregations below

    # Monthly event volume by repo class and event type.
    monthly = (enriched
        .groupBy("month", "repo_class", "type")
        .agg(F.count("*").alias("events"),
             F.countDistinct("actor.login").alias("actors"),
             F.countDistinct("repo.id").alias("repos"))
        .orderBy("month", "repo_class", "type"))

    monthly.coalesce(1).write.mode("overwrite").option("header", True).csv(out_path)

    # Quick sanity print in the driver logs.
    (enriched.groupBy("repo_class").count().show())

    spark.stop()


if __name__ == "__main__":
    in_path = sys.argv[1] if len(sys.argv) > 1 else "gs://<BUCKET>/gharchive/*.json.gz"
    out_path = sys.argv[2] if len(sys.argv) > 2 else "gs://<BUCKET>/out/monthly"
    main(in_path, out_path)
