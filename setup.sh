#!/bin/bash
# AnalytIQ — Week 1 Setup Script
# Run this once to scaffold the full project

set -e

echo "🚀 Setting up AnalytIQ project..."

# Create folder structure
mkdir -p analytiq/{infra,ingestion,etl,ml,api,dashboard,data-generator,docs}

cd analytiq

# Python virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install Python dependencies
pip install \
  aws-cdk-lib \
  constructs \
  boto3 \
  fastapi \
  uvicorn \
  faker \
  python-dotenv \
  pandas \
  scikit-learn \
  xgboost \
  mlflow \
  psycopg2-binary

# Node (required for CDK CLI)
npm install -g aws-cdk

echo ""
echo "✅ Done! Next steps:"
echo "   1. Run: aws configure   (enter your AWS keys)"
echo "   2. Run: cd infra && cdk bootstrap"
echo "   3. Run: cdk deploy"
