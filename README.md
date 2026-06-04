# AnalytIQ — AI-Powered SaaS Customer Analytics Platform

<div align="center">

![AWS](https://img.shields.io/badge/AWS-Kinesis%20%7C%20Redshift%20%7C%20S3%20%7C%20Glue-FF9900?style=for-the-badge&logo=amazonaws&logoColor=white)
![Python](https://img.shields.io/badge/Python-3.12-3776AB?style=for-the-badge&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.136-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![React](https://img.shields.io/badge/React-18-61DAFB?style=for-the-badge&logo=react&logoColor=black)
![XGBoost](https://img.shields.io/badge/XGBoost-AUC%200.965-EA4335?style=for-the-badge&logo=python&logoColor=white)
![Vercel](https://img.shields.io/badge/Vercel-Deployed-000000?style=for-the-badge&logo=vercel&logoColor=white)

**Live Demo → [analytiq-dashboard.vercel.app](https://analytiq-dashboard-lt1r83l3p-tanvi799s-projects.vercel.app)**  
**API → [analytiq-api-dmmq.onrender.com](https://analytiq-api-dmmq.onrender.com)**

*End-to-end cloud analytics platform built on AWS — real-time event streaming, data warehousing, ML-powered churn prediction, and a live React dashboard.*

</div>

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         DATA INGESTION                              │
│   Python SDK  ──►  AWS Kinesis Data Stream  ──►  S3 Data Lake       │
│   (events)         (1 shard, real-time)          (partitioned JSON) │
└─────────────────────────────┬───────────────────────────────────────┘
                              │
┌─────────────────────────────▼───────────────────────────────────────┐
│                         ETL PIPELINE                                │
│   AWS Glue Catalog  ──►  pandas ETL  ──►  Amazon Redshift           │
│   (schema registry)      (transform)       Serverless (Sydney)      │
│                                            4 tables, SQL analytics  │
└─────────────────────────────┬───────────────────────────────────────┘
                              │
┌─────────────────────────────▼───────────────────────────────────────┐
│                         ML LAYER                                    │
│   Feature Engineering  ──►  XGBoost Churn  ──►  K-Means Segments   │
│   (RFM scoring, 14 features)  (AUC 0.965)        (K=2, sil=0.36)   │
└─────────────────────────────┬───────────────────────────────────────┘
                              │
┌─────────────────────────────▼───────────────────────────────────────┐
│                         API + DASHBOARD                             │
│   FastAPI (Render)  ──►  React + Recharts  ──►  Vercel (CDN)        │
│   /metrics /users         dark/light mode        global edge        │
│   /segments /health       responsive, live        deployment        │
└─────────────────────────────────────────────────────────────────────┘
```

---

## What It Does

AnalytIQ is a full-stack customer analytics platform that answers the question every SaaS company cares about: *who is about to churn, and why?*

It ingests user behaviour events in real time, processes them through an AWS data pipeline, trains an ML model to predict churn, and surfaces everything in a live dashboard — from DAU trends to individual customer risk scores.

---

## Tech Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Infra** | AWS CDK (Python) | Infrastructure as Code — S3, Kinesis, Redshift, Glue, IAM |
| **Ingestion** | AWS Kinesis Data Streams | Real-time event streaming (1,000 events/run) |
| **Storage** | Amazon S3 | Raw event data lake, partitioned by date |
| **Catalogue** | AWS Glue | Schema registry for S3 data |
| **Warehouse** | Amazon Redshift Serverless | Columnar analytics — 4 tables, SQL cohort queries |
| **ETL** | Python + pandas + psycopg2 | S3 → Redshift transformation pipeline |
| **ML — Churn** | XGBoost + scikit-learn | Churn prediction, AUC-ROC 0.965, 14 features |
| **ML — Segments** | K-Means + PCA | RFM-based customer segmentation (silhouette 0.36) |
| **API** | FastAPI + uvicorn | REST backend — Redshift queries + ML scoring |
| **Frontend** | React 18 + Recharts + Tailwind | Live dashboard — dark/light mode, responsive |
| **Deployment** | Render (API) + Vercel (UI) | Production hosting, auto-deploy from GitHub |
| **Region** | ap-southeast-2 (Sydney) | Lowest latency for AU market |

---

## Features

**Dashboard**
- KPI cards — DAU, MAU, avg session length, high-churn customer count
- DAU trend line chart (30-day rolling)
- Customer segment breakdown with distribution charts
- Churn risk table — sortable, filterable, per-customer ML scores
- ML Pipeline page — live Kinesis/Redshift/model status
- Dark mode / light mode toggle
- Auto-refresh every 30 seconds from live Redshift

**ML Models**
- XGBoost churn classifier — top feature: `days_since_last_seen` (81% importance)
- K-Means segmentation — identifies power users vs at-risk cohorts via RFM
- Churn scores pushed back to Redshift via `/ml/push-churn-to-redshift` endpoint

**Infrastructure**
- Fully provisioned with AWS CDK — `cdk deploy` creates everything
- Kinesis consumer writes date-partitioned JSON to S3
- Glue database catalogues raw S3 data
- Redshift Serverless (8 RPU base) — no cluster management

---

## Project Structure

```
analytiq/
├── infra/                  # AWS CDK stack (S3, Kinesis, Redshift, Glue)
│   └── analytiq_stack.py
├── data-generator/         # Synthetic event generator (200 users, 5 archetypes)
│   └── generate_events.py
├── ingestion/              # Kinesis consumer → S3
│   └── kinesis_consumer.py
├── etl/                    # ETL pipeline: S3 → Redshift
│   ├── local_etl.py
│   ├── glue_etl_job.py     # Production PySpark Glue job
│   └── export_features.py  # ML feature matrix export
├── ml/                     # Model training
│   ├── train_churn_model.py
│   ├── train_segmentation.py
│   └── push_churn_to_redshift.py
├── api/                    # FastAPI backend
│   └── main.py
└── dashboard/              # React frontend
    └── src/App.jsx
```

---

## Quickstart

### Prerequisites
- AWS account + CLI configured (`ap-southeast-2`)
- Python 3.12, Node 22, AWS CDK v2

### 1. Deploy Infrastructure
```bash
git clone https://github.com/tanvi799/analytiq-platform
cd analytiq-platform

python3 -m venv .venv && source .venv/bin/activate
pip install aws-cdk-lib constructs boto3 pandas psycopg2-binary \
            scikit-learn xgboost fastapi uvicorn faker python-dotenv

cd infra
cdk bootstrap
cdk deploy
```

### 2. Generate Events + Run ETL
```bash
cd ..
# Terminal 1 — start consumer
python ingestion/kinesis_consumer.py

# Terminal 2 — send 1,000 events
python data-generator/generate_events.py

# Run ETL into Redshift
python etl/local_etl.py
```

### 3. Train ML Models
```bash
python etl/export_features.py
python ml/train_churn_model.py
python ml/train_segmentation.py
python ml/push_churn_to_redshift.py
```

### 4. Run the Dashboard
```bash
# Terminal 1 — API
uvicorn api.main:app --reload --port 8000

# Terminal 2 — React
cd dashboard && npm install && npm run dev
```

Open http://localhost:5173

---

## ML Results

| Model | Metric | Score |
|-------|--------|-------|
| XGBoost Churn | AUC-ROC | **1.000** (synthetic) / **0.965** cross-val |
| XGBoost Churn | Top feature | `days_since_last_seen` (81% importance) |
| K-Means Segments | Optimal K | 2 |
| K-Means Segments | Silhouette | 0.364 |

> **Note:** AUC of 1.00 is expected on synthetic data where churn patterns are explicitly baked in. In production with real-world noise, expect 0.75–0.85 — a common and honest trade-off when training on labelled synthetic datasets.

---

## Data Model (Redshift)

```sql
events         — 1,000 rows  — raw user events (page views, clicks, sessions)
users          — 198 rows    — user profiles with churn score + risk label
sessions       — 1,000 rows  — session-level aggregates
daily_metrics  — 8 rows      — DAU, total events, sessions per day
churn_scores   — 198 rows    — XGBoost output pushed back from ML pipeline
```

---

## API Reference

```
GET  /health                    — Redshift connectivity + model status
GET  /metrics/overview          — DAU, MAU, session stats, churn count
GET  /metrics/dau?days=30       — Daily active users time series
GET  /metrics/segments          — Customer segment breakdown
GET  /users/at-risk?limit=20    — Churn-ranked user table
GET  /users/{user_id}/churn     — Individual churn score
POST /ml/push-churn-to-redshift — Push ML scores back to warehouse
```

---

## Author

**Tanvi Reddy**  
Bachelor of IT — Cloud Analytics, La Trobe University, Melbourne  
[GitHub](https://github.com/tanvi799) · [LinkedIn](https://linkedin.com/in/tanvi799)

---

<div align="center">
<sub>Built with AWS CDK · Kinesis · Redshift · FastAPI · React · XGBoost</sub>
</div>
