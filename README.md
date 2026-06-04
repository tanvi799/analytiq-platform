<div align="center">

<img src="https://img.shields.io/badge/AWS-CDK-FF9900?style=for-the-badge&logo=amazonaws&logoColor=white"/>
<img src="https://img.shields.io/badge/Python-3.12-3776AB?style=for-the-badge&logo=python&logoColor=white"/>
<img src="https://img.shields.io/badge/React-18-61DAFB?style=for-the-badge&logo=react&logoColor=black"/>
<img src="https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white"/>
<img src="https://img.shields.io/badge/XGBoost-AUC_0.965-EA4335?style=for-the-badge"/>
<img src="https://img.shields.io/badge/Vercel-Live-000000?style=for-the-badge&logo=vercel&logoColor=white"/>

<br/>
<br/>

# AnalytIQ — AI-Powered SaaS Customer Analytics Platform

### End-to-end cloud analytics platform — real-time event streaming, AWS data warehouse, ML churn prediction, and a live React dashboard

<br/>

**[ Live Dashboard]((https://analytiq-dashboard-alpha.vercel.app))** &nbsp;·&nbsp; **[ Live API](https://analytiq-api-dmmq.onrender.com/health)** &nbsp;·&nbsp; **[ GitHub](https://github.com/tanvi799/analytiq-platform)**

<br/>

> Built as part of a two-project AWS portfolio alongside an [AWS Fraud Detection & Operations Monitor](https://aws-fraud-operations-monitor.vercel.app) — demonstrating both security ops and customer intelligence use cases on AWS.

</div>

---

## What It Does

AnalytIQ answers the question every SaaS company cares about: **who is about to churn, and why?**

It ingests user behaviour events in real time via AWS Kinesis, processes them through an ETL pipeline into Amazon Redshift, trains an XGBoost model to predict churn probability per customer, and surfaces everything in a production-grade React dashboard — from rolling DAU trends to individual customer risk scores ranked by ML confidence.

---

## Architecture

```
┌──────────────────────────────────────────────────────────────────────┐
│                          DATA INGESTION                              │
│                                                                      │
│   Python SDK  ──►  AWS Kinesis Data Stream  ──►  Amazon S3           │
│   (events)         (real-time, 1 shard)          (date-partitioned)  │
└──────────────────────────────┬───────────────────────────────────────┘
                               │
┌──────────────────────────────▼───────────────────────────────────────┐
│                          ETL PIPELINE                                │
│                                                                      │
│   AWS Glue Catalog  ──►  pandas ETL  ──►  Amazon Redshift Serverless │
│   (schema registry)      (clean + load)    (4 tables, Sydney)        │
└──────────────────────────────┬───────────────────────────────────────┘
                               │
┌──────────────────────────────▼───────────────────────────────────────┐
│                          ML LAYER                                    │
│                                                                      │
│   RFM Feature Matrix  ──►  XGBoost Churn  ──►  K-Means Segmentation │
│   (14 features)             (AUC 0.965)         (RFM clustering)     │
└──────────────────────────────┬───────────────────────────────────────┘
                               │
┌──────────────────────────────▼───────────────────────────────────────┐
│                          API + DASHBOARD                             │
│                                                                      │
│   FastAPI (Render)  ──►  React 18 + Recharts  ──►  Vercel (CDN)      │
│   REST + ML scoring       dark/light mode          global edge       │
└──────────────────────────────────────────────────────────────────────┘
```

---

## Tech Stack

| Layer | Technology | Detail |
|-------|-----------|--------|
| **Infrastructure** | AWS CDK (Python) | IaC — S3, Kinesis, Redshift Serverless, Glue, IAM |
| **Ingestion** | AWS Kinesis Data Streams | Real-time event streaming, 1,000 events/run |
| **Storage** | Amazon S3 | Raw event data lake, date-partitioned JSON |
| **Catalogue** | AWS Glue | Schema registry for S3 raw data |
| **Warehouse** | Amazon Redshift Serverless | Columnar analytics, 4 tables, SQL cohort queries |
| **ETL** | Python · pandas · psycopg2 | S3 → clean → Redshift transformation pipeline |
| **ML — Churn** | XGBoost · scikit-learn | Churn prediction, AUC-ROC 0.965, 14 features |
| **ML — Segments** | K-Means · PCA | RFM-based customer segmentation, silhouette 0.36 |
| **API** | FastAPI · uvicorn | REST backend — Redshift queries + ML scoring |
| **Frontend** | React 18 · Recharts · Tailwind | Live dashboard, dark/light mode, responsive |
| **Deployment** | Render (API) · Vercel (UI) | Auto-deploy from GitHub, global CDN |
| **Region** | ap-southeast-2 · Sydney | Lowest latency for AU market |

---

## Dashboard Features

- **KPI cards** — DAU, MAU, avg session length, high-churn customer count with animated counters
- **DAU area chart** — 30-day rolling trend with live data badge
- **Segment donut chart** — 5 customer archetypes (power users, regular, at-risk, new, dormant)
- **Churn risk table** — sortable by score or days inactive, filterable by risk level, searchable by company name
- **Score distribution chart** — XGBoost output bucketed across 5 risk bands
- **ML Pipeline page** — live Kinesis / Redshift / model status with push-to-Redshift button
- **API Health page** — per-service status with latency and raw JSON response viewer
- **Dark mode / light mode** — full theme toggle with Inter font throughout
- **Resizable sidebar** — drag to resize between 180–320px, collapse to icon-only
- **Mobile responsive** — slide-in drawer on mobile, bottom tab navigation, adaptive layouts
- **Auto-refresh** — live data every 30 seconds with manual refresh button

---

## ML Results

| Model | Metric | Result |
|-------|--------|--------|
| XGBoost Churn | AUC-ROC (test set) | **1.000** (synthetic data) |
| XGBoost Churn | AUC-ROC (5-fold CV) | **0.965 ± 0.07** |
| XGBoost Churn | Top feature | `days_since_last_seen` (81% importance) |
| XGBoost Churn | #2 feature | `segment_enc` (16% importance) |
| K-Means Segments | Optimal K | **2** |
| K-Means Segments | Silhouette score | **0.364** |

> **Note on AUC 1.00:** Expected on synthetic data where churn patterns are deliberately baked in (dormant/at-risk users labelled churned). Cross-validation mean of 0.965 is the honest production estimate. In real-world SaaS data, expect 0.75–0.85 — a well-known trade-off when training on labelled synthetic datasets.

---

## Data Model (Redshift Serverless)

```sql
events         — 1,000 rows  — page views, clicks, feature usage, logins
users          — 198 rows    — profiles, segment labels, churn score + risk
sessions       — 1,000 rows  — session-level aggregates, device, duration
daily_metrics  — 8 rows      — DAU, total events, sessions per day
churn_scores   — 198 rows    — XGBoost output pushed back to warehouse
```

---

## API Reference

```
GET  /health                     Redshift connectivity + model load status
GET  /metrics/overview           DAU, MAU, session stats, churn risk count
GET  /metrics/dau?days=30        Daily active users time series
GET  /metrics/segments           Customer segment breakdown with percentages
GET  /users/at-risk?limit=20     Churn-ranked customer table with ML scores
GET  /users/{user_id}/churn      Individual user churn probability
POST /ml/push-churn-to-redshift  Upsert ML scores back to Redshift warehouse
```

---

## Project Structure

```
analytiq-platform/
├── infra/
│   ├── analytiq_stack.py        AWS CDK stack (S3, Kinesis, Redshift, Glue, IAM)
│   ├── app.py                   CDK app entrypoint
│   └── redshift_schema.sql      Warehouse schema + cohort views
├── data-generator/
│   └── generate_events.py       Synthetic event generator — 200 users, 5 archetypes
├── ingestion/
│   └── kinesis_consumer.py      Reads stream → writes partitioned JSON to S3
├── etl/
│   ├── local_etl.py             pandas ETL: S3 → 4 Redshift tables
│   ├── glue_etl_job.py          Production PySpark Glue job
│   └── export_features.py       ML feature matrix + RFM export
├── ml/
│   ├── train_churn_model.py     XGBoost churn classifier + evaluation plots
│   ├── train_segmentation.py    K-Means segmentation + PCA visualisation
│   └── push_churn_to_redshift.py  Upsert churn scores to warehouse
├── api/
│   └── main.py                  FastAPI backend — 7 endpoints
└── dashboard/
    └── src/App.jsx              React dashboard — 975 lines, 6 pages
```

---

## Quickstart

### Prerequisites
- AWS account + CLI configured (`ap-southeast-2`)
- Python 3.12, Node 22, AWS CDK v2

### 1 — Deploy AWS infrastructure
```bash
git clone https://github.com/tanvi799/analytiq-platform
cd analytiq-platform

python3 -m venv .venv && source .venv/bin/activate
pip install aws-cdk-lib constructs boto3 pandas psycopg2-binary \
            scikit-learn xgboost fastapi uvicorn faker python-dotenv

cd infra && cdk bootstrap && cdk deploy
```

### 2 — Stream events + run ETL
```bash
cd ..
# Terminal 1 — Kinesis consumer
python ingestion/kinesis_consumer.py

# Terminal 2 — fire 1,000 events
python data-generator/generate_events.py

# Load into Redshift
python etl/local_etl.py
```

### 3 — Train ML models
```bash
python etl/export_features.py        # RFM feature matrix → S3
python ml/train_churn_model.py       # XGBoost churn predictor
python ml/train_segmentation.py      # K-Means segmentation
python ml/push_churn_to_redshift.py  # Push scores back to warehouse
```

### 4 — Run the dashboard
```bash
# Terminal 1 — API
uvicorn api.main:app --reload --port 8000

# Terminal 2 — React
cd dashboard && npm install && npm run dev
```
Open **http://localhost:5173**

---

## Cost (AWS Free Tier)

| Service | Free Tier | Monthly Estimate |
|---------|-----------|-----------------|
| Amazon S3 | 5 GB | ~$0 |
| AWS Kinesis | 1 shard × 24h retention | ~$1 |
| Amazon Redshift Serverless | 300 RPU-hour trial | ~$0 (trial) |
| AWS Glue | 1M objects free | ~$0 |
| **Total** | | **< $2/month** |

---

## Author

**Tanvi Reddy**
Bachelor of IT — Cloud Analytics, La Trobe University, Melbourne

[![GitHub](https://img.shields.io/badge/GitHub-tanvi799-181717?style=flat-square&logo=github)](https://github.com/tanvi799)
---

<div align="center">
<sub>Built with AWS · Python · React · deployed on Vercel + Render</sub>
</div>
