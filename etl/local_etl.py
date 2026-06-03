"""
AnalytIQ — Local ETL (pandas version)
Reads raw JSON from S3, transforms, loads into Redshift via INSERT.
"""

import json
import boto3
import pandas as pd
import psycopg2
from io import StringIO
from datetime import datetime, timezone

REGION   = "ap-southeast-2"
ACCOUNT  = boto3.client("sts", region_name=REGION).get_caller_identity()["Account"]
RAW_BUCKET = f"analytiq-raw-events-{ACCOUNT}"

REDSHIFT_HOST = f"analytiq-wg.{ACCOUNT}.{REGION}.redshift-serverless.amazonaws.com"
REDSHIFT_PORT = 5439
REDSHIFT_DB   = "analytiq"
REDSHIFT_USER = "analytiq_admin"
REDSHIFT_PASS = "ChangeMe123!"

s3 = boto3.client("s3", region_name=REGION)


def read_raw_events() -> pd.DataFrame:
    print(f"Reading raw events from s3://{RAW_BUCKET}/raw/")
    paginator = s3.get_paginator("list_objects_v2")
    pages = paginator.paginate(Bucket=RAW_BUCKET, Prefix="raw/")
    records = []
    file_count = 0
    for page in pages:
        for obj in page.get("Contents", []):
            body = s3.get_object(Bucket=RAW_BUCKET, Key=obj["Key"])["Body"].read()
            for line in body.decode("utf-8").strip().split("\n"):
                if line:
                    records.append(json.loads(line))
            file_count += 1
    print(f"  Read {len(records)} events from {file_count} files")
    return pd.DataFrame(records)


def transform(df: pd.DataFrame) -> dict:
    props = pd.json_normalize(df["properties"])
    df = pd.concat([df.drop(columns=["properties"]), props], axis=1)
    df["event_ts"] = pd.to_datetime(df["timestamp"], utc=True, errors="coerce")
    df = df.dropna(subset=["event_id", "user_id", "event_ts"])
    df = df.drop_duplicates(subset=["event_id"])
    df["event_type"] = df["event_type"].str.lower().str.strip()
    df["country"]    = df["country"].str.upper().str.strip()
    df["device"]     = df["device"].str.lower().str.strip()
    df["duration_ms"] = df["duration_ms"].clip(upper=300_000)
    df["ingested_at"] = datetime.now(timezone.utc)

    events_df = df[[
        "event_id","event_type","user_id","company","segment",
        "plan","country","page","session_id","event_ts",
        "duration_ms","referrer","device","ingested_at"
    ]].rename(columns={"event_ts":"timestamp"})

    sessions_df = (
        df.groupby(["session_id","user_id","device"])
        .agg(started_at=("event_ts","min"), ended_at=("event_ts","max"),
             event_count=("event_id","count"), pages_visited=("page","nunique"))
        .reset_index()
    )
    sessions_df["duration_secs"] = (
        (sessions_df["ended_at"] - sessions_df["started_at"])
        .dt.total_seconds().astype(int)
    )

    users_df = (
        df.groupby(["user_id","company","segment","plan","country"])
        .agg(first_seen_at=("event_ts","min"), last_seen_at=("event_ts","max"),
             total_events=("event_id","count"), total_sessions=("session_id","nunique"),
             unique_pages=("page","nunique"))
        .reset_index()
    )

    daily_df = (
        df.assign(event_date=df["event_ts"].dt.date)
        .groupby("event_date")
        .agg(dau=("user_id","nunique"), total_events=("event_id","count"),
             total_sessions=("session_id","nunique"), avg_duration_ms=("duration_ms","mean"))
        .reset_index()
    )
    daily_df["avg_duration_ms"] = daily_df["avg_duration_ms"].round(0).astype(int)

    print(f"  Events:  {len(events_df)}")
    print(f"  Sessions:{len(sessions_df)}")
    print(f"  Users:   {len(users_df)}")
    print(f"  Daily:   {len(daily_df)} days")

    return {"events": events_df, "sessions": sessions_df,
            "users": users_df, "daily_metrics": daily_df}


def df_to_sql_values(df: pd.DataFrame) -> str:
    """Convert DataFrame rows to SQL VALUES string."""
    rows = []
    for _, row in df.iterrows():
        vals = []
        for v in row:
            if pd.isna(v) or v is None:
                vals.append("NULL")
            elif isinstance(v, (int, float)):
                vals.append(str(v))
            else:
                escaped = str(v).replace("'", "''")
                vals.append(f"'{escaped}'")
        rows.append(f"({','.join(vals)})")
    return ",\n".join(rows)


def load_to_redshift(tables: dict):
    print(f"\nConnecting to Redshift...")
    conn = psycopg2.connect(
        host=REDSHIFT_HOST, port=REDSHIFT_PORT,
        dbname=REDSHIFT_DB, user=REDSHIFT_USER, password=REDSHIFT_PASS,
        connect_timeout=15,
    )
    conn.autocommit = True
    cur = conn.cursor()

    # Fix datetime columns
    for table_name, df in tables.items():
        for col in df.select_dtypes(include=["datetimetz","datetime64[ns, UTC]","datetime64[ns]"]).columns:
            df[col] = df[col].dt.strftime("%Y-%m-%d %H:%M:%S")

        print(f"  Loading {len(df)} rows → {table_name}...")

        # Insert in batches of 100
        batch_size = 100
        cols = ", ".join(df.columns)
        for i in range(0, len(df), batch_size):
            batch = df.iloc[i:i+batch_size]
            values = df_to_sql_values(batch)
            sql = f"INSERT INTO {table_name} ({cols}) VALUES {values};"
            cur.execute(sql)

        print(f"    ✓ {table_name} loaded")

    cur.close()
    conn.close()
    print("\n✅ ETL complete — data is in Redshift!")


def main():
    print("=== AnalytIQ Local ETL ===\n")
    raw_df = read_raw_events()
    if raw_df.empty:
        print("No events found. Run the data generator first.")
        return
    print("\nTransforming...")
    tables = transform(raw_df)
    print("\nLoading to Redshift...")
    load_to_redshift(tables)


if __name__ == "__main__":
    main()
