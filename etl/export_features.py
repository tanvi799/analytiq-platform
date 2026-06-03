"""
AnalytIQ — Week 3: Feature Matrix Exporter
Pulls the ML feature matrix from Redshift and saves to S3.
This CSV feeds the churn prediction model in Week 5.
Run: python etl/export_features.py
"""

import boto3
import pandas as pd
import psycopg2
from datetime import datetime, timezone

REGION   = "ap-southeast-2"
ACCOUNT  = boto3.client("sts", region_name=REGION).get_caller_identity()["Account"]
PROCESSED_BUCKET = f"analytiq-processed-{ACCOUNT}"

REDSHIFT_HOST = f"analytiq-wg.{ACCOUNT}.{REGION}.redshift-serverless.amazonaws.com"
REDSHIFT_PORT = 5439
REDSHIFT_DB   = "analytiq"
REDSHIFT_USER = "analytiq_admin"
REDSHIFT_PASS = "ChangeMe123!"

s3 = boto3.client("s3", region_name=REGION)

FEATURE_QUERY = """
SELECT
    u.user_id,
    u.segment,
    u.plan,
    u.country,
    u.total_events,
    u.total_sessions,
    u.unique_pages,
    DATEDIFF('day', u.last_seen_at,  GETDATE()) AS days_since_last_seen,
    DATEDIFF('day', u.first_seen_at, GETDATE()) AS account_age_days,
    ROUND(u.total_events::FLOAT / NULLIF(
        DATEDIFF('day', u.first_seen_at, GETDATE()), 0), 2
    ) AS events_per_day,
    ROUND(u.total_sessions::FLOAT / NULLIF(
        DATEDIFF('day', u.first_seen_at, GETDATE()), 0), 2
    ) AS sessions_per_day,
    CASE
        WHEN DATEDIFF('day', u.last_seen_at, GETDATE()) > 3
         AND u.segment IN ('dormant', 'at_risk') THEN 1
        ELSE 0
    END AS churned
FROM users u
ORDER BY churned DESC, days_since_last_seen DESC;
"""

RFM_QUERY = """
WITH rfm_raw AS (
    SELECT
        user_id,
        DATEDIFF('day', last_seen_at, GETDATE()) AS recency_days,
        total_sessions                            AS frequency,
        total_events                              AS monetary
    FROM users
),
rfm_scored AS (
    SELECT
        user_id, recency_days, frequency, monetary,
        6 - NTILE(5) OVER (ORDER BY recency_days ASC) AS r_score,
        NTILE(5) OVER (ORDER BY frequency ASC)         AS f_score,
        NTILE(5) OVER (ORDER BY monetary ASC)          AS m_score
    FROM rfm_raw
)
SELECT
    user_id,
    r_score, f_score, m_score,
    ROUND((r_score + f_score + m_score) / 3.0, 2) AS rfm_score,
    CASE
        WHEN (r_score + f_score + m_score) >= 12 THEN 'champion'
        WHEN (r_score + f_score + m_score) >= 9  THEN 'loyal'
        WHEN (r_score + f_score + m_score) >= 6  THEN 'at_risk'
        ELSE 'dormant'
    END AS rfm_label
FROM rfm_scored;
"""


def query_redshift(sql: str) -> pd.DataFrame:
    conn = psycopg2.connect(
        host=REDSHIFT_HOST, port=REDSHIFT_PORT,
        dbname=REDSHIFT_DB, user=REDSHIFT_USER, password=REDSHIFT_PASS,
        connect_timeout=15,
    )
    df = pd.read_sql(sql, conn)
    conn.close()
    return df


def upload_to_s3(df: pd.DataFrame, filename: str) -> str:
    key = f"ml-features/{filename}"
    csv_bytes = df.to_csv(index=False).encode("utf-8")
    s3.put_object(Bucket=PROCESSED_BUCKET, Key=key,
                  Body=csv_bytes, ContentType="text/csv")
    return f"s3://{PROCESSED_BUCKET}/{key}"


def main():
    print("=== AnalytIQ Feature Matrix Export ===\n")

    # ── Feature matrix ────────────────────────────────────────────────────────
    print("Querying feature matrix from Redshift...")
    features_df = query_redshift(FEATURE_QUERY)
    print(f"  {len(features_df)} users, {features_df['churned'].sum()} churned")

    path = upload_to_s3(features_df, "features.csv")
    print(f"  ✓ Saved to {path}")

    # ── RFM scores ────────────────────────────────────────────────────────────
    print("\nQuerying RFM scores...")
    rfm_df = query_redshift(RFM_QUERY)

    # Merge RFM into features
    combined_df = features_df.merge(rfm_df, on="user_id", how="left")
    path2 = upload_to_s3(combined_df, "features_with_rfm.csv")
    print(f"  ✓ Saved to {path2}")

    # Also save locally for quick ML prototyping
    combined_df.to_csv("ml/features_with_rfm.csv", index=False)
    print(f"  ✓ Also saved locally to ml/features_with_rfm.csv")

    # ── Quick stats ───────────────────────────────────────────────────────────
    print("\n── Feature Matrix Summary ──────────────────────")
    print(f"  Total users:     {len(combined_df)}")
    print(f"  Churned (label=1): {combined_df['churned'].sum()} "
          f"({combined_df['churned'].mean()*100:.1f}%)")
    print(f"  Active  (label=0): {(combined_df['churned']==0).sum()}")
    print(f"\n  Segment breakdown:")
    print(combined_df.groupby("segment")["churned"]
          .agg(["count","sum","mean"])
          .rename(columns={"count":"users","sum":"churned","mean":"churn_rate"})
          .round(2).to_string())
    print(f"\n  RFM label breakdown:")
    print(combined_df["rfm_label"].value_counts().to_string())
    print("\n✅ Feature matrix ready for ML (Week 5)!")


if __name__ == "__main__":
    main()
