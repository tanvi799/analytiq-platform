-- AnalytIQ — Redshift Schema
-- Run this in the Redshift Query Editor after deploying the CDK stack
-- Redshift Serverless console → Query Editor v2 → select analytiq-wg

-- ── Raw events (loaded from S3 via COPY) ─────────────────────────────────────
CREATE TABLE IF NOT EXISTS events (
    event_id        VARCHAR(36)     NOT NULL,
    event_type      VARCHAR(50)     NOT NULL,
    user_id         VARCHAR(36)     NOT NULL,
    company         VARCHAR(200),
    segment         VARCHAR(50),
    plan            VARCHAR(20),
    country         VARCHAR(5),
    page            VARCHAR(200),
    session_id      VARCHAR(36),
    timestamp       TIMESTAMP       NOT NULL,
    duration_ms     INTEGER,
    referrer        VARCHAR(100),
    device          VARCHAR(20),
    ingested_at     TIMESTAMP       DEFAULT GETDATE()
)
DISTKEY(user_id)
SORTKEY(timestamp);

-- ── Users (one row per user, updated via upsert) ──────────────────────────────
CREATE TABLE IF NOT EXISTS users (
    user_id         VARCHAR(36)     NOT NULL PRIMARY KEY,
    company         VARCHAR(200),
    email           VARCHAR(200),
    segment         VARCHAR(50),
    plan            VARCHAR(20),
    country         VARCHAR(5),
    signed_up_at    TIMESTAMP,
    last_seen_at    TIMESTAMP,
    total_events    INTEGER         DEFAULT 0,
    churn_score     FLOAT           DEFAULT 0.0,    -- updated by ML model
    churn_risk      VARCHAR(10)     DEFAULT 'low',  -- high / medium / low
    updated_at      TIMESTAMP       DEFAULT GETDATE()
)
DISTKEY(user_id)
SORTKEY(signed_up_at);

-- ── Sessions (aggregated from events) ────────────────────────────────────────
CREATE TABLE IF NOT EXISTS sessions (
    session_id      VARCHAR(36)     NOT NULL PRIMARY KEY,
    user_id         VARCHAR(36)     NOT NULL,
    started_at      TIMESTAMP,
    ended_at        TIMESTAMP,
    duration_secs   INTEGER,
    event_count     INTEGER,
    pages_visited   INTEGER,
    device          VARCHAR(20)
)
DISTKEY(user_id)
SORTKEY(started_at);

-- ── Daily metrics (pre-aggregated for fast dashboard queries) ─────────────────
CREATE TABLE IF NOT EXISTS daily_metrics (
    metric_date     DATE            NOT NULL,
    dau             INTEGER,
    new_users       INTEGER,
    churned_users   INTEGER,
    total_sessions  INTEGER,
    avg_session_s   FLOAT,
    top_page        VARCHAR(200),
    PRIMARY KEY (metric_date)
)
SORTKEY(metric_date);

-- ── Useful views ──────────────────────────────────────────────────────────────

-- DAU for the last 30 days
CREATE OR REPLACE VIEW v_dau_30d AS
SELECT
    TRUNC(timestamp)    AS event_date,
    COUNT(DISTINCT user_id) AS dau
FROM events
WHERE timestamp >= GETDATE() - INTERVAL '30 days'
GROUP BY 1
ORDER BY 1;

-- Cohort retention — % of users still active each week after signup
CREATE OR REPLACE VIEW v_cohort_retention AS
WITH cohorts AS (
    SELECT
        user_id,
        DATE_TRUNC('month', signed_up_at) AS cohort_month
    FROM users
),
activity AS (
    SELECT
        e.user_id,
        DATEDIFF('week', c.cohort_month, e.timestamp) AS weeks_since_signup
    FROM events e
    JOIN cohorts c USING (user_id)
    WHERE weeks_since_signup BETWEEN 0 AND 8
)
SELECT
    c.cohort_month,
    a.weeks_since_signup,
    COUNT(DISTINCT a.user_id)                               AS active_users,
    COUNT(DISTINCT c2.user_id)                              AS cohort_size,
    ROUND(COUNT(DISTINCT a.user_id)::FLOAT
          / NULLIF(COUNT(DISTINCT c2.user_id), 0) * 100, 1) AS retention_pct
FROM activity a
JOIN cohorts c  USING (user_id)
JOIN cohorts c2 ON c.cohort_month = c2.cohort_month
GROUP BY 1, 2
ORDER BY 1, 2;

-- Customers at risk (high churn score)
CREATE OR REPLACE VIEW v_at_risk_customers AS
SELECT
    user_id,
    company,
    email,
    segment,
    plan,
    churn_score,
    churn_risk,
    last_seen_at,
    DATEDIFF('day', last_seen_at, GETDATE()) AS days_inactive
FROM users
WHERE churn_score > 0.5
ORDER BY churn_score DESC
LIMIT 100;

-- Segment summary
CREATE OR REPLACE VIEW v_segment_summary AS
SELECT
    segment,
    COUNT(*)                    AS user_count,
    ROUND(AVG(churn_score), 3) AS avg_churn_score,
    COUNT(*) * 100.0 / SUM(COUNT(*)) OVER () AS pct_of_total
FROM users
GROUP BY segment
ORDER BY user_count DESC;
