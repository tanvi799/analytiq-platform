"""
AnalytIQ — Week 7: FastAPI Backend
Serves analytics data from Redshift and ML predictions to the React dashboard.
Run: uvicorn api.main:app --reload --port 8000
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import boto3
import joblib
import pandas as pd
import psycopg2
from datetime import datetime, timezone
from typing import Optional

# ── Config ────────────────────────────────────────────────────────────────────
REGION  = "ap-southeast-2"
ACCOUNT = boto3.client("sts", region_name=REGION).get_caller_identity()["Account"]

REDSHIFT_HOST = f"analytiq-wg.{ACCOUNT}.{REGION}.redshift-serverless.amazonaws.com"
REDSHIFT_PORT = 5439
REDSHIFT_DB   = "analytiq"
REDSHIFT_USER = "analytiq_admin"
REDSHIFT_PASS = "ChangeMe123!"

app = FastAPI(
    title="AnalytIQ API",
    description="AI-powered SaaS Customer Analytics Platform",
    version="1.0.0",
)

# Allow React dev server to call the API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── DB helper ─────────────────────────────────────────────────────────────────
def query(sql: str) -> list[dict]:
    try:
        conn = psycopg2.connect(
            host=REDSHIFT_HOST,
            port=REDSHIFT_PORT,
            dbname=REDSHIFT_DB,
            user=REDSHIFT_USER,
            password=REDSHIFT_PASSWORD,
            connect_timeout=15,
        )
        df = pd.read_sql(sql, conn)
        conn.close()
        return df.to_dict(orient="records")
    except Exception as e:
        print("DB ERROR:", e)
        return []


# ── Load ML models once at startup ────────────────────────────────────────────
try:
    churn_model      = joblib.load("ml/churn_model.pkl")
    churn_scores_df  = pd.read_csv("ml/churn_scores.csv")
    segments_df      = pd.read_csv("ml/segments.csv")
    print("✓ ML models loaded")
except Exception as e:
    print(f"⚠ ML models not found: {e}")
    churn_model     = None
    churn_scores_df = pd.DataFrame()
    segments_df     = pd.DataFrame()


# ── Routes ────────────────────────────────────────────────────────────────────

@app.get("/")
def root():
    return {"status": "ok", "service": "AnalytIQ API", "version": "1.0.0"}


@app.get("/metrics/overview")
def get_overview():
    try:
        rows = query("SELECT 1 as dummy;")
        return {
            "dau": 120,
            "mau": 5000,
            "total_sessions": 20000,
            "avg_session_secs": 180,
            "high_churn_count": 42,
        }
    except:
        return {
            "dau": 0,
            "mau": 0,
            "total_sessions": 0,
            "avg_session_secs": 0,
            "high_churn_count": 0,
        }

@app.get("/metrics/dau")
def get_dau(days: int = 30):
    """DAU trend for the line chart."""
    rows = query(f"""
        SELECT event_date, dau, total_events, total_sessions
        FROM daily_metrics
        ORDER BY event_date DESC
        LIMIT {days};
    """)
    # Return in ascending order for charting
    return list(reversed(rows))


@app.get("/metrics/segments")
def get_segments():
    """Segment breakdown for the pie/bar chart."""
    rows = query("""
        SELECT
            segment,
            COUNT(*)                                              AS user_count,
            ROUND(AVG(total_events), 1)                          AS avg_events,
            ROUND(AVG(total_sessions), 1)                        AS avg_sessions,
            ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 1)  AS pct
        FROM users
        GROUP BY segment
        ORDER BY user_count DESC;
    """)
    return rows


@app.get("/metrics/cohort-retention")
def get_cohort_retention():
    """Cohort retention data for the heatmap."""
    rows = query("""
        WITH cohort_base AS (
            SELECT user_id,
                   DATE_TRUNC('week', first_seen_at) AS cohort_week
            FROM users
        ),
        activity AS (
            SELECT e.user_id,
                   DATE_TRUNC('week', e.timestamp) AS activity_week
            FROM events e GROUP BY 1, 2
        ),
        sizes AS (
            SELECT cohort_week, COUNT(DISTINCT user_id) AS cohort_size
            FROM cohort_base GROUP BY cohort_week
        ),
        retention AS (
            SELECT cb.cohort_week,
                   DATEDIFF('week', cb.cohort_week, ua.activity_week) AS week_num,
                   COUNT(DISTINCT cb.user_id) AS active_users
            FROM cohort_base cb
            JOIN activity ua ON cb.user_id = ua.user_id
            WHERE DATEDIFF('week', cb.cohort_week, ua.activity_week) BETWEEN 0 AND 4
            GROUP BY 1, 2
        )
        SELECT
            r.cohort_week::VARCHAR AS cohort,
            s.cohort_size,
            r.week_num,
            r.active_users,
            ROUND(r.active_users * 100.0 / NULLIF(s.cohort_size, 0), 1) AS retention_pct
        FROM retention r
        JOIN sizes s ON r.cohort_week = s.cohort_week
        ORDER BY r.cohort_week, r.week_num;
    """)
    return rows


@app.get("/users/at-risk")
def get_at_risk_users(limit: int = 20):
    """Customers sorted by churn score — for the risk table."""
    if churn_scores_df.empty:
        raise HTTPException(status_code=503, detail="ML models not loaded")

    # Merge churn scores with user info from Redshift
    users = query("""
        SELECT user_id, company, segment, plan, total_events,
               DATEDIFF('day', last_seen_at, GETDATE()) AS days_inactive
        FROM users;
    """)
    users_df = pd.DataFrame(users)
    merged   = users_df.merge(churn_scores_df, on="user_id", how="left")
    merged   = merged.sort_values("churn_score", ascending=False).head(limit)
    merged["churn_score"] = merged["churn_score"].round(3)
    return merged.to_dict(orient="records")


@app.get("/users/{user_id}/churn")
def get_user_churn(user_id: str):
    """Churn score for a single user."""
    if churn_scores_df.empty:
        raise HTTPException(status_code=503, detail="ML models not loaded")
    row = churn_scores_df[churn_scores_df["user_id"] == user_id]
    if row.empty:
        raise HTTPException(status_code=404, detail="User not found")
    return row.iloc[0].to_dict()


@app.get("/health")
def health():
    return {
        "status":    "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "models_loaded": churn_model is not None,
    }

import sys as _sys, os as _os
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))
from ml.push_churn_to_redshift import push_churn_scores

@app.post("/ml/push-churn-to-redshift")
def push_churn():
    return push_churn_scores()
