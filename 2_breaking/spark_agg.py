#!/usr/bin/env python3
"""CS131 Phase 2C — the SAME aggregation (events per type) in PySpark,
run locally on all 20 cores, over (a) one day and (b) the whole dataset.

Streaming/distributed: Spark reads the gzipped files partition-by-partition;
it never holds the whole dataset in memory.

Usage: spark_agg_local.py <glob> [label]
  e.g.  spark_agg_local.py 'data/2024-01-15-*.json.gz'  one-day
        spark_agg_local.py 'data/*.json.gz'             full-dataset
"""
import sys, time
from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql.types import StructType, StructField, StringType

glob = sys.argv[1]
label = sys.argv[2] if len(sys.argv) > 2 else glob

# Explicit minimal schema: parse ONLY the field we aggregate on — this is a
# column-pruning trick pandas cannot do on raw JSON.
schema = StructType([StructField("type", StringType(), True)])

spark = (SparkSession.builder
         .appName(f"cs131-agg-{label}")
         .master("local[*]")
         .config("spark.driver.memory", "16g")
         .getOrCreate())
spark.sparkContext.setLogLevel("WARN")

t0 = time.time()
df = spark.read.schema(schema).json(glob)
counts = df.groupBy("type").count().orderBy(F.desc("count")).collect()
wall = time.time() - t0

print(f"\n=== events per type — {label} ===")
total = 0
for row in counts:
    print(f"{row['count']:>12,}  {row['type']}")
    total += row["count"]
print(f"{total:>12,}  TOTAL")
print(f"wall-clock: {wall:.1f}s  (Spark local[*], 20 cores)")
spark.stop()
