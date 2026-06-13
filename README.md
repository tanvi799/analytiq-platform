# AnalytIQ — Real-Time Customer Analytics & Churn Prediction

A full-stack analytics platform demonstrating an end-to-end AWS data pipeline
(Kinesis → Glue → Redshift), ML-based churn scoring (XGBoost) and customer
segmentation (K-Means/GMM), and a React dashboard for visualizing the results.

---

## Live Demo

- **Dashboard**: [[your deployed URL](https://analytiq-dashboard-alpha.vercel.app)]
- **API**: [https://analytiq-api-dmmq.onrender.com] (may take ~30-60s to wake from cold start — the
  dashboard automatically falls back to sample data while waiting, see
  "Demo Mode" below)

---

## Architecture

```
Event ingestion (Kinesis) → ETL (AWS Glue) → Warehouse (Redshift)
    → Segmentation (K-Means/GMM) + Churn scoring (XGBoost)
    → FastAPI backend → React dashboard
```

---

## Key Findings

### Churn model (XGBoost)
AUC of 0.965 reported during training is on **synthetic, pre-labelled data**
where churn outcomes were generated alongside the features — this score
reflects the model recovering its own generation rules, not a real
predictive result. On real-world data, a churn classifier with this feature
set would realistically score **AUC 0.75-0.85**. The value of this component
is the pipeline itself (feature engineering, training, serving, scoring at
inference time), not the headline metric.

### Customer segmentation (K-Means)
The clustering pipeline tests K=3-5 with log-transformed, scaled RFM features
and compares K-Means against a Gaussian Mixture Model using both silhouette
score and Davies-Bouldin index. On the current synthetic dataset, the
**optimal K is 2**, not the 5 segments shown on the dashboard.

This is not a bug — it's what the data shows. `total_sessions` and
`total_events` are perfectly correlated in the generated data (effectively
one feature, not two), and `days_since_last_seen` (recency) dominates the
remaining variance. The result is that unsupervised clustering finds a
single dominant split: **active vs. inactive users**. The 5 segments
(`power_user`, `regular`, `at_risk`, `new_user`, `dormant`) shown on the
dashboard are **business-defined cohorts** based on churn-score thresholds
and recency rules, not K-Means cluster assignments. K-Means independently
validates that recency is the dominant signal — which is itself a useful
finding, separate from the rule-based segmentation used for the UI.

To recover 5 distinct unsupervised clusters, the synthetic data generator
would need to encode segment-specific feature distributions (e.g. give
`power_user` higher `unique_pages` relative to `total_events`, decouple
`total_sessions` from `total_events`). That's a data-generation change, not
a modeling change, and is left as a known improvement.

---

## Not Implemented (Deliberate Scope Decisions)

This is a portfolio/demo project, and the following are intentionally out of
scope rather than oversights:

- **Authentication & authorization** — the API has no auth layer (no API
  keys, OAuth, or session management). All endpoints are publicly readable.
  In a production deployment this would sit behind an API gateway with
  key-based auth or OAuth2, plus per-tenant data isolation.
- **Rate limiting** — no request throttling is implemented. Production would
  add this at the API gateway / load balancer layer (e.g. AWS API Gateway
  usage plans, or `slowapi`/`fastapi-limiter` at the app layer).
- **Multi-tenancy / data isolation** — all data is global; there's no
  per-customer scoping.
- **Write-path validation & idempotency** — the `/ml/push-churn-to-redshift`
  endpoint performs a delete+insert upsert without request validation,
  idempotency keys, or audit logging.

These are the first things added before any real user data touches this
system.

---

## Testing

Basic unit tests cover the ML pipeline and core API endpoints — see
`tests/`. Run with:

```bash
pytest tests/ -v
```

Coverage is intentionally focused (not exhaustive) on:
- Feature engineering correctness (RFM score calculation)
- Churn model inference shape/output bounds
- Segmentation pipeline (scaling, clustering, label assignment)
- API endpoint contracts (`/health`, `/metrics/overview`, `/users/at-risk`)

---

## Demo Mode (Frontend Resilience)

The dashboard's API is hosted on Render's free tier, which sleeps after
inactivity and can take 30-60 seconds to cold-start. To avoid a blank/broken
demo on first load, every API call has a 4-second timeout; on timeout or
failure, the dashboard falls back to bundled static sample data and displays
a "Demo mode" banner. It automatically switches back to live data once the
API responds (polling every 30s).

---

## Cost Estimate

### Current (demo workload, free tier)
At demo traffic levels (a handful of users, low event volume), this runs at
**under $2/month** — primarily S3 storage and minimal Redshift Serverless
compute (which scales to near-zero when idle). Render's free tier covers the
API host.

### At 100,000 daily active users (estimated)
Scaling this architecture to a real workload of ~100k DAU (assuming ~10
events/user/day = ~1M events/day) would look roughly like:

| Component | Estimated monthly cost | Notes |
|---|---|---|
| Kinesis Data Streams | ~$25-40 | 2-3 shards to handle ~1M events/day with headroom for spikes |
| AWS Glue ETL | ~$50-100 | Scheduled jobs (hourly/daily), DPU-hours depend on job frequency |
| Redshift Serverless | ~$300-600 | Largest cost driver; scales with query concurrency and data volume (base RPU-hours + storage) |
| S3 (raw events + processed) | ~$10-20 | ~30-60GB/month at this volume, standard storage class |
| ML inference (XGBoost scoring) | ~$20-50 | Batch scoring on a schedule (e.g. EC2/Fargate spot or Lambda for batch jobs) rather than real-time |
| API hosting (FastAPI) | ~$25-100 | Moving off Render free tier to a small dedicated instance or container service with autoscaling |
| **Total (rough)** | **~$450-900/month** | |

The dominant cost is **Redshift**, and the biggest lever for reducing it is
query patterns: pre-aggregating dashboard metrics (materialized views /
scheduled rollups) rather than querying raw event tables on every dashboard
load. At this scale, a cheaper alternative worth evaluating is replacing
Redshift with a combination of S3 + Athena (pay-per-query) for ad-hoc
analysis, with a smaller RDS/Postgres instance serving the pre-aggregated
metrics the dashboard actually reads.

This estimate is directional, not a quote — actual cost depends heavily on
query patterns, retention policy, and how much aggregation happens
upstream vs. at query time.

---

## Tech Stack

- **Frontend**: React, Recharts, Tailwind CSS, Vite
- **Backend**: FastAPI
- **Data pipeline**: AWS Kinesis, Glue, Redshift Serverless, S3
- **ML**: scikit-learn (K-Means, GMM), XGBoost
- **Hosting**: Vercel (frontend), Render (API)
