"""
AnalytIQ — FastAPI Backend
"""
import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import joblib
import pandas as pd
import psycopg2
from datetime import datetime, timezone

REDSHIFT_HOST = os.getenv("REDSHIFT_HOST", "analytiq-wg.477170636779.ap-southeast-2.redshift-serverless.amazonaws.com")
REDSHIFT_PORT = int(os.getenv("REDSHIFT_PORT", "5439"))
REDSHIFT_DB   = os.getenv("REDSHIFT_DB",   "analytiq")
REDSHIFT_USER = os.getenv("REDSHIFT_USER", "analytiq_admin")
REDSHIFT_PASS = os.getenv("REDSHIFT_PASS", "ChangeMe123!")

app = FastAPI(title="AnalytIQ API", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

def query(sql):
    try:
        conn = psycopg2.connect(host=REDSHIFT_HOST, port=REDSHIFT_PORT, dbname=REDSHIFT_DB, user=REDSHIFT_USER, password=REDSHIFT_PASS, connect_timeout=15)
        df = pd.read_sql(sql, conn)
        conn.close()
        return df.to_dict(orient="records")
    except Exception as e:
        print(f"DB error: {e}")
        return []

try:
    churn_model     = joblib.load("ml/churn_model.pkl")
    churn_scores_df = pd.read_csv("ml/churn_scores.csv")
    segments_df     = pd.read_csv("ml/segments.csv")
    print("ML models loaded")
except Exception as e:
    print(f"ML not found: {e}")
    churn_model     = None
    churn_scores_df = pd.DataFrame()
    segments_df     = pd.DataFrame()

@app.get("/")
def root():
    return {"status": "ok", "service": "AnalytIQ API", "version": "1.0.0"}

@app.get("/health")
def health():
    return {"status": "healthy", "timestamp": datetime.now(timezone.utc).isoformat(), "models_loaded": churn_model is not None}

@app.get("/metrics/overview")
def get_overview():
    rows  = query("SELECT MAX(dau) AS peak_dau, SUM(total_sessions) AS total_sessions, ROUND(AVG(avg_duration_ms)/1000.0,1) AS avg_session_secs FROM daily_metrics;")
    users = query("SELECT COUNT(*) AS total FROM users;")
    return {
        "dau":              rows[0].get("peak_dau", 0)         if rows else 0,
        "mau":              users[0].get("total", 0)            if users else 0,
        "total_sessions":   rows[0].get("total_sessions", 0)   if rows else 0,
        "avg_session_secs": rows[0].get("avg_session_secs", 0) if rows else 0,
        "high_churn_count": int((churn_scores_df["churn_risk"] == "high").sum()) if not churn_scores_df.empty else 0,
    }

@app.get("/metrics/dau")
def get_dau(days: int = 30):
    rows = query(f"SELECT CAST(event_date AS VARCHAR) AS event_date, dau, total_events, total_sessions FROM daily_metrics ORDER BY event_date DESC LIMIT {days};")
    return list(reversed(rows))

@app.get("/metrics/segments")
def get_segments():
    return query("SELECT segment, COUNT(*) AS user_count, ROUND(AVG(total_events),1) AS avg_events, ROUND(AVG(total_sessions),1) AS avg_sessions, ROUND(COUNT(*)*100.0/SUM(COUNT(*)) OVER(),1) AS pct FROM users WHERE segment IS NOT NULL GROUP BY segment ORDER BY user_count DESC;")

@app.get("/users/at-risk")
def get_at_risk_users(limit: int = 20):
    users = query("SELECT user_id, company, segment, plan, total_events, DATEDIFF('day', last_seen_at, GETDATE()) AS days_inactive FROM users;")
    if not users:
        return []
    users_df = pd.DataFrame(users)
    if churn_scores_df.empty:
        return users_df.head(limit).to_dict(orient="records")
    merged = users_df.merge(churn_scores_df, on="user_id", how="left")
    merged = merged.sort_values("churn_score", ascending=False).head(limit)
    merged["churn_score"] = merged["churn_score"].fillna(0).round(3)
    merged["churn_risk"]  = merged["churn_risk"].fillna("low")
    return merged.to_dict(orient="records")

@app.get("/users/{user_id}/churn")
def get_user_churn(user_id: str):
    if churn_scores_df.empty:
        raise HTTPException(status_code=503, detail="ML models not loaded")
    row = churn_scores_df[churn_scores_df["user_id"] == user_id]
    if row.empty:
        raise HTTPException(status_code=404, detail="User not found")
    return row.iloc[0].to_dict()

@app.post("/ml/push-churn-to-redshift")
def push_churn():
    try:
        import sys
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from ml.push_churn_to_redshift import push_churn_scores
        return push_churn_scores()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
