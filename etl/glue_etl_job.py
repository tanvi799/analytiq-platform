"""
AnalytIQ — AWS Glue ETL Job (Week 2)
Reads raw JSON events from S3, cleans/transforms them,
and loads into Redshift Serverless.

Deploy this script to AWS Glue via the console or CLI.
"""

import sys
from awsglue.transforms import *
from awsglue.utils import getResolvedOptions
from awsglue.context import GlueContext
from awsglue.job import Job
from pyspark.context import SparkContext
from pyspark.sql import functions as F
from pyspark.sql.types import *
from pyspark.sql.window import Window

# ── Job init ──────────────────────────────────────────────────────────────────
args = getResolvedOptions(sys.argv, ["JOB_NAME", "RAW_BUCKET", "REDSHIFT_URL",
                                      "REDSHIFT_USER", "REDSHIFT_PASSWORD",
                                      "REDSHIFT_DB", "TEMP_BUCKET"])

sc          = SparkContext()
glueContext = GlueContext(sc)
spark       = glueContext.spark_session
job         = Job(glueContext)
job.init(args["JOB_NAME"], args)

RAW_PATH   = f"s3://{args['RAW_BUCKET']}/raw/"
TEMP_PATH  = f"s3://{args['TEMP_BUCKET']}/glue-temp/"
REDSHIFT_URL = args["REDSHIFT_URL"]   # jdbc:redshift://...

print(f"Reading raw events from {RAW_PATH}")

# ── 1. Read raw JSON from S3 ──────────────────────────────────────────────────
raw_df = spark.read.option("recursiveFileLookup", "true").json(RAW_PATH)

print(f"Raw record count: {raw_df.count()}")
raw_df.printSchema()

# ── 2. Flatten nested properties column ───────────────────────────────────────
flat_df = raw_df.select(
    F.col("event_id"),
    F.col("event_type"),
    F.col("user_id"),
    F.col("company"),
    F.col("segment"),
    F.col("plan"),
    F.col("country"),
    F.col("page"),
    F.col("session_id"),
    F.to_timestamp(F.col("timestamp")).alias("event_ts"),
    F.col("properties.duration_ms").cast(IntegerType()).alias("duration_ms"),
    F.col("properties.referrer").alias("referrer"),
    F.col("properties.device").alias("device"),
    F.current_timestamp().alias("ingested_at"),
)

# ── 3. Clean and validate ─────────────────────────────────────────────────────
clean_df = (
    flat_df
    # Drop rows missing critical fields
    .filter(F.col("event_id").isNotNull())
    .filter(F.col("user_id").isNotNull())
    .filter(F.col("event_ts").isNotNull())
    # Deduplicate by event_id (in case consumer ran twice)
    .dropDuplicates(["event_id"])
    # Normalise strings
    .withColumn("event_type", F.lower(F.trim(F.col("event_type"))))
    .withColumn("country",    F.upper(F.trim(F.col("country"))))
    .withColumn("device",     F.lower(F.trim(F.col("device"))))
    # Cap duration outliers at 5 minutes (300,000ms)
    .withColumn("duration_ms", F.when(
        F.col("duration_ms") > 300_000, 300_000
    ).otherwise(F.col("duration_ms")))
    # Add date partition columns for Redshift sort efficiency
    .withColumn("event_date",  F.to_date(F.col("event_ts")))
    .withColumn("event_hour",  F.hour(F.col("event_ts")))
)

print(f"Clean record count: {clean_df.count()}")

# ── 4. Build sessions table ───────────────────────────────────────────────────
# Group events by session_id to calculate session-level metrics
sessions_df = (
    clean_df
    .groupBy("session_id", "user_id", "device")
    .agg(
        F.min("event_ts").alias("started_at"),
        F.max("event_ts").alias("ended_at"),
        F.count("event_id").alias("event_count"),
        F.countDistinct("page").alias("pages_visited"),
        F.sum("duration_ms").alias("total_duration_ms"),
    )
    .withColumn(
        "duration_secs",
        (F.unix_timestamp("ended_at") - F.unix_timestamp("started_at")).cast(IntegerType())
    )
    .drop("total_duration_ms")
)

print(f"Sessions count: {sessions_df.count()}")

# ── 5. Build users summary table ──────────────────────────────────────────────
users_df = (
    clean_df
    .groupBy("user_id", "company", "segment", "plan", "country")
    .agg(
        F.min("event_ts").alias("first_seen_at"),
        F.max("event_ts").alias("last_seen_at"),
        F.count("event_id").alias("total_events"),
        F.countDistinct("session_id").alias("total_sessions"),
        F.countDistinct("page").alias("unique_pages"),
    )
)

print(f"Users count: {users_df.count()}")

# ── 6. Build daily metrics table ──────────────────────────────────────────────
daily_df = (
    clean_df
    .groupBy("event_date")
    .agg(
        F.countDistinct("user_id").alias("dau"),
        F.count("event_id").alias("total_events"),
        F.countDistinct("session_id").alias("total_sessions"),
        F.avg("duration_ms").alias("avg_duration_ms"),
    )
    .withColumn("avg_duration_ms", F.round(F.col("avg_duration_ms"), 0).cast(IntegerType()))
    .orderBy("event_date")
)

# ── 7. Write to Redshift ───────────────────────────────────────────────────────
def write_to_redshift(df, table: str, mode: str = "append"):
    """Write a Spark DataFrame to a Redshift table."""
    print(f"Writing {df.count()} rows to Redshift table: {table}")
    (
        df.write
        .format("jdbc")
        .option("url",          REDSHIFT_URL)
        .option("dbtable",      table)
        .option("user",         args["REDSHIFT_USER"])
        .option("password",     args["REDSHIFT_PASSWORD"])
        .option("driver",       "com.amazon.redshift.jdbc42.Driver")
        .option("tempdir",      TEMP_PATH)
        .mode(mode)
        .save()
    )
    print(f"  ✓ {table} written successfully")

write_to_redshift(clean_df,    "events",        mode="append")
write_to_redshift(sessions_df, "sessions",      mode="append")
write_to_redshift(users_df,    "users",         mode="append")
write_to_redshift(daily_df,    "daily_metrics", mode="append")

job.commit()
print("✅ Glue ETL job complete!")
