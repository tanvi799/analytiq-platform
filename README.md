# AnalytIQ — AI SaaS Customer Analytics Platform

> A cloud-native customer analytics platform built on AWS — featuring real-time event ingestion, a Redshift data warehouse, ML-powered churn prediction, and a live React dashboard.

![Stack](https://img.shields.io/badge/AWS-CDK-orange?logo=amazon-aws)
![Python](https://img.shields.io/badge/Python-3.11-blue?logo=python)
![React](https://img.shields.io/badge/Frontend-React-61DAFB?logo=react)
![ML](https://img.shields.io/badge/ML-scikit--learn-F7931E?logo=scikitlearn)

---

## Architecture

```
Tracking SDK / Data Generator
          │
          ▼
  AWS Kinesis Data Stream
          │
          ▼
   Kinesis Consumer ──► S3 (raw data lake)
                              │
                              ▼
                       AWS Glue ETL
                              │
                              ▼
                    Amazon Redshift Serverless
                              │
                    ┌─────────┴──────────┐
                    ▼                    ▼
              ML Models            FastAPI Backend
         (churn, segments)               │
                    │                    ▼
                    └──────► React Dashboard
```

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Ingestion | AWS Kinesis Data Streams, Python SDK |
| Storage | Amazon S3 (data lake), Amazon Redshift Serverless |
| ETL | AWS Glue (PySpark) |
| ML | scikit-learn, XGBoost, MLflow |
| API | FastAPI, Docker, AWS ECS |
| Frontend | React, Recharts, Tailwind CSS |
| Infrastructure | AWS CDK (Python), GitHub Actions CI/CD |

---

## Week 1 Setup — Get Running in 30 Minutes

### Prerequisites
- AWS account (free tier)
- Python 3.11+
- Node.js 18+ (for CDK CLI)
- VS Code

### Step 1 — Clone and install

```bash
git clone https://github.com/YOUR_USERNAME/analytiq.git
cd analytiq
bash setup.sh
source .venv/bin/activate
```

### Step 2 — Configure AWS credentials

```bash
aws configure
# Enter your:
#   AWS Access Key ID
#   AWS Secret Access Key
#   Default region: ap-southeast-2   (Sydney)
#   Default output format: json
```

To get your keys: AWS Console → IAM → Users → your user → Security credentials → Create access key

### Step 3 — Deploy the infrastructure

```bash
cd infra
cdk bootstrap aws://YOUR_ACCOUNT_ID/ap-southeast-2
cdk deploy
```

This provisions: S3 buckets, Kinesis stream, Redshift Serverless, Glue database, and IAM roles. Takes ~5 minutes.

After deploy, you'll see outputs like:
```
AnalytIQStack.RawBucket = analytiq-raw-events-123456789
AnalytIQStack.KinesisStream = analytiq-events
AnalytIQStack.RedshiftWorkgroup = analytiq-wg
```

### Step 4 — Set up Redshift schema

1. Open AWS Console → Amazon Redshift → Query Editor v2
2. Connect to workgroup: `analytiq-wg`, database: `analytiq`
3. Paste and run `infra/redshift_schema.sql`

### Step 5 — Generate events and watch them land in S3

Open two terminal tabs:

**Tab 1 — Start the consumer:**
```bash
python ingestion/kinesis_consumer.py
```

**Tab 2 — Fire events:**
```bash
python data-generator/generate_events.py
```

You should see events appearing in real time in Tab 1, and files appearing in your S3 bucket under `raw/year=.../month=.../day=.../`.

---

## Project Structure

```
analytiq/
├── infra/
│   ├── app.py                  # CDK app entrypoint
│   ├── analytiq_stack.py       # AWS infrastructure (S3, Kinesis, Redshift)
│   ├── cdk.json
│   └── redshift_schema.sql     # Data warehouse schema + views
├── ingestion/
│   └── kinesis_consumer.py     # Reads stream → writes to S3
├── data-generator/
│   └── generate_events.py      # Synthetic event generator
├── etl/                        # Glue ETL jobs (Week 3)
├── ml/                         # Churn + segmentation models (Week 5–6)
├── api/                        # FastAPI backend (Week 7)
├── dashboard/                  # React frontend (Week 7)
├── docs/                       # Architecture diagrams, data model
├── setup.sh
└── README.md
```

---

## Build Roadmap

| Week | Focus | Status |
|------|-------|--------|
| 1 | AWS infra + event ingestion | ✅ Done |
| 2 | Kinesis consumer + S3 landing | ✅ Done |
| 3 | Glue ETL + Redshift loading | ⏳ Next |
| 4 | Cohort SQL + feature matrix | ⏳ |
| 5 | Churn prediction model | ⏳ |
| 6 | Segmentation + anomaly detection | ⏳ |
| 7 | FastAPI + React dashboard | ⏳ |
| 8 | Polish, demo, docs | ⏳ |

---

## Cost Estimate (AWS Free Tier)

| Service | Free Tier | Estimated Monthly |
|---------|-----------|-------------------|
| S3 | 5 GB | ~$0 |
| Kinesis | 1 shard × 24h | ~$1 |
| Redshift Serverless | 300 RPU-hours/month trial | ~$0 (trial) |
| Glue | 1M objects free | ~$0 |
| **Total** | | **< $2/month** |

---

## Demo

🎥 [Watch the 2-minute dashboard walkthrough](#) ← add Loom link in Week 8

🌐 [Live dashboard](#) ← add deployed URL in Week 8

---

## Author

Built by **[Your Name]** — Bachelor of IT (Cloud Analytics), La Trobe University Melbourne  
Part of a two-project AWS portfolio alongside an [AWS Fraud Detection & Operations Monitor](#).
