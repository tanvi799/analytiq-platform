"""
AnalytIQ — Kinesis Consumer
Reads events from the Kinesis stream and writes them as JSON files to S3.
Run this alongside generate_events.py to watch events land in your data lake.
"""

import json
import time
import uuid
import boto3
from datetime import datetime

STREAM_NAME = "analytiq-events"
REGION      = "ap-southeast-2"
BUCKET      = None  # auto-detected from S3 if None

kinesis = boto3.client("kinesis", region_name=REGION)
s3      = boto3.client("s3",       region_name=REGION)


def get_bucket_name() -> str:
    """Find the raw events bucket by prefix."""
    sts = boto3.client("sts", region_name=REGION)
    account = sts.get_caller_identity()["Account"]
    return f"analytiq-raw-events-{account}"


def get_shard_iterator(stream_name: str) -> str:
    """Get a shard iterator starting from the latest position."""
    shards = kinesis.list_shards(StreamName=stream_name)["Shards"]
    shard_id = shards[0]["ShardId"]   # single shard in dev

    resp = kinesis.get_shard_iterator(
        StreamName=stream_name,
        ShardId=shard_id,
        ShardIteratorType="LATEST",
    )
    return resp["ShardIterator"]


def write_to_s3(events: list[dict], bucket: str) -> str:
    """
    Write a batch of events to S3 as a partitioned JSON file.
    Path: raw/year=YYYY/month=MM/day=DD/<uuid>.json
    Partitioning by date makes Glue crawling much faster.
    """
    now = datetime.utcnow()
    key = (
        f"raw/year={now.year}/month={now.month:02d}"
        f"/day={now.day:02d}/{uuid.uuid4()}.json"
    )
    body = "\n".join(json.dumps(e) for e in events)   # newline-delimited JSON

    s3.put_object(
        Bucket=bucket,
        Key=key,
        Body=body.encode("utf-8"),
        ContentType="application/json",
    )
    return key


def consume(bucket: str):
    """Poll Kinesis and write batches of events to S3."""
    print(f"Consuming from stream '{STREAM_NAME}' → s3://{bucket}/raw/")
    print("Ctrl+C to stop.\n")

    iterator = get_shard_iterator(STREAM_NAME)
    total = 0

    while True:
        response = kinesis.get_records(ShardIterator=iterator, Limit=100)
        records  = response["Records"]
        iterator = response["NextShardIterator"]

        if records:
            events = [json.loads(r["Data"]) for r in records]
            key = write_to_s3(events, bucket)
            total += len(events)
            print(f"  ✓ {len(events):3d} events → s3://{bucket}/{key}  (total: {total})")
        else:
            print("  … waiting for events", end="\r")

        time.sleep(1)   # poll every second


if __name__ == "__main__":
    bucket = BUCKET or get_bucket_name()
    consume(bucket)
