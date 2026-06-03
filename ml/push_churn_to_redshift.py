"""
AnalytIQ — Push churn scores to Redshift
Run: python ml/push_churn_to_redshift.py
"""
import csv, json, logging
from datetime import datetime, timezone
import psycopg2
from psycopg2.extras import execute_values

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)

REDSHIFT_HOST     = "analytiq-wg.477170636779.ap-southeast-2.redshift-serverless.amazonaws.com"
REDSHIFT_PORT     = 5439
REDSHIFT_DB       = "analytiq"
REDSHIFT_USER     = "analytiq_admin"
REDSHIFT_PASSWORD = "ChangeMe123!"
CHURN_CSV_PATH    = "ml/churn_scores.csv"

DDL = """
CREATE TABLE IF NOT EXISTS public.churn_scores (
    user_id       VARCHAR(64)  NOT NULL PRIMARY KEY,
    churn_score   FLOAT        NOT NULL,
    churn_risk    VARCHAR(16)  NOT NULL,
    scored_at     TIMESTAMP    NOT NULL,
    model_version VARCHAR(32)  DEFAULT 'xgboost-v1'
);
"""

def push_churn_scores(csv_path=CHURN_CSV_PATH):
    rows = []
    with open(csv_path, newline="") as f:
        for r in csv.DictReader(f):
            score = float(r["churn_score"])
            risk  = r.get("churn_risk") or ("high" if score>=0.7 else "medium" if score>=0.4 else "low")
            rows.append((r["user_id"], score, risk, datetime.now(timezone.utc), "xgboost-v1"))
    log.info(f"Read {len(rows)} rows from {csv_path}")

    conn = psycopg2.connect(
        host=REDSHIFT_HOST, port=REDSHIFT_PORT,
        dbname=REDSHIFT_DB, user=REDSHIFT_USER, password=REDSHIFT_PASSWORD,
        connect_timeout=15,
    )
    conn.autocommit = True
    cur = conn.cursor()

    cur.execute(DDL)
    cur.execute("DELETE FROM public.churn_scores;")
    execute_values(cur,
        "INSERT INTO public.churn_scores (user_id, churn_score, churn_risk, scored_at, model_version) VALUES %s",
        rows, page_size=200,
    )

    cur.close()
    conn.close()

    result = {
        "status":      "success",
        "rows_pushed": len(rows),
        "pushed_at":   datetime.now(timezone.utc).isoformat(),
        "high_risk":   sum(1 for r in rows if r[2]=="high"),
        "medium_risk": sum(1 for r in rows if r[2]=="medium"),
        "low_risk":    sum(1 for r in rows if r[2]=="low"),
    }
    log.info(f"Pushed {len(rows)} churn scores to Redshift")
    return result

if __name__ == "__main__":
    print(json.dumps(push_churn_scores(), indent=2, default=str))
