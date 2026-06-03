-- ============================================================
-- AnalytIQ — Week 3 Analytics SQL
-- Run each section in Redshift Query Editor v2
-- ============================================================


-- ── 1. DAU trend (last 8 days) ────────────────────────────────────────────────
SELECT
    event_date,
    dau,
    total_events,
    total_sessions,
    ROUND(total_events::FLOAT / NULLIF(dau, 0), 1) AS events_per_user
FROM daily_metrics
ORDER BY event_date;


-- ── 2. Cohort retention ───────────────────────────────────────────────────────
-- Shows what % of users from each signup cohort are still active
-- This is the most impressive SQL query for your portfolio
WITH cohort_base AS (
    SELECT
        user_id,
        DATE_TRUNC('week', first_seen_at)  AS cohort_week,
        first_seen_at
    FROM users
),
user_activity AS (
    SELECT
        e.user_id,
        DATE_TRUNC('week', e.timestamp)    AS activity_week
    FROM events e
    GROUP BY 1, 2
),
cohort_sizes AS (
    SELECT cohort_week, COUNT(DISTINCT user_id) AS cohort_size
    FROM cohort_base
    GROUP BY cohort_week
),
retention AS (
    SELECT
        cb.cohort_week,
        DATEDIFF('week', cb.cohort_week, ua.activity_week) AS weeks_since_signup,
        COUNT(DISTINCT cb.user_id) AS active_users
    FROM cohort_base cb
    JOIN user_activity ua ON cb.user_id = ua.user_id
    WHERE DATEDIFF('week', cb.cohort_week, ua.activity_week) BETWEEN 0 AND 4
    GROUP BY 1, 2
)
SELECT
    r.cohort_week,
    cs.cohort_size,
    r.weeks_since_signup,
    r.active_users,
    ROUND(r.active_users::FLOAT / NULLIF(cs.cohort_size, 0) * 100, 1) AS retention_pct
FROM retention r
JOIN cohort_sizes cs ON r.cohort_week = cs.cohort_week
ORDER BY r.cohort_week, r.weeks_since_signup;


-- ── 3. RFM Scoring ────────────────────────────────────────────────────────────
-- Recency, Frequency, Monetary — classic customer analytics scoring
-- R = days since last seen (lower = better)
-- F = total sessions (higher = better)
-- M = total events as proxy for "value" (higher = better)
WITH rfm_raw AS (
    SELECT
        user_id,
        company,
        segment,
        plan,
        DATEDIFF('day', last_seen_at, GETDATE())  AS recency_days,
        total_sessions                             AS frequency,
        total_events                               AS monetary
    FROM users
),
rfm_scored AS (
    SELECT
        user_id,
        company,
        segment,
        plan,
        recency_days,
        frequency,
        monetary,
        -- Score 1-5 using NTILE (5=best)
        6 - NTILE(5) OVER (ORDER BY recency_days ASC)  AS r_score,  -- lower recency = higher score
        NTILE(5) OVER (ORDER BY frequency ASC)          AS f_score,
        NTILE(5) OVER (ORDER BY monetary ASC)           AS m_score
    FROM rfm_raw
)
SELECT
    user_id,
    company,
    segment,
    plan,
    recency_days,
    frequency,
    monetary,
    r_score,
    f_score,
    m_score,
    ROUND((r_score + f_score + m_score) / 3.0, 2)  AS rfm_score,
    CASE
        WHEN (r_score + f_score + m_score) >= 12 THEN 'champion'
        WHEN (r_score + f_score + m_score) >= 9  THEN 'loyal'
        WHEN (r_score + f_score + m_score) >= 6  THEN 'at_risk'
        ELSE                                           'dormant'
    END AS rfm_label
FROM rfm_scored
ORDER BY rfm_score DESC;


-- ── 4. Feature matrix for ML (churn prediction) ───────────────────────────────
-- This CSV gets exported and fed into your scikit-learn model in Week 5
-- Label: churned = 1 if last seen > 3 days ago AND segment is at_risk/dormant
SELECT
    u.user_id,
    u.segment,
    u.plan,
    u.country,
    u.total_events,
    u.total_sessions,
    u.unique_pages,
    DATEDIFF('day', u.last_seen_at,  GETDATE())  AS days_since_last_seen,
    DATEDIFF('day', u.first_seen_at, GETDATE())  AS account_age_days,
    ROUND(u.total_events::FLOAT / NULLIF(
        DATEDIFF('day', u.first_seen_at, GETDATE()), 0), 2
    )                                             AS events_per_day,
    ROUND(u.total_sessions::FLOAT / NULLIF(
        DATEDIFF('day', u.first_seen_at, GETDATE()), 0), 2
    )                                             AS sessions_per_day,
    -- Churn label: 1 = churned, 0 = active
    CASE
        WHEN DATEDIFF('day', u.last_seen_at, GETDATE()) > 3
         AND u.segment IN ('dormant', 'at_risk') THEN 1
        ELSE 0
    END AS churned
FROM users u
ORDER BY churned DESC, days_since_last_seen DESC;


-- ── 5. Segment summary (for dashboard pie chart) ──────────────────────────────
SELECT
    segment,
    COUNT(*)                                             AS user_count,
    ROUND(AVG(total_events), 1)                         AS avg_events,
    ROUND(AVG(total_sessions), 1)                       AS avg_sessions,
    ROUND(AVG(DATEDIFF('day', last_seen_at, GETDATE())), 1) AS avg_days_inactive,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 1) AS pct_of_total
FROM users
GROUP BY segment
ORDER BY user_count DESC;
