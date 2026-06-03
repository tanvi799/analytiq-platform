#!/bin/bash
# AnalytIQ — Deploy Glue ETL Job to AWS
# Run from the project root: bash etl/deploy_glue_job.sh

set -e

# ── Config (auto-detect account) ─────────────────────────────────────────────
REGION="ap-southeast-2"
ACCOUNT=$(aws sts get-caller-identity --query Account --output text)
RAW_BUCKET="analytiq-raw-events-${ACCOUNT}"
PROCESSED_BUCKET="analytiq-processed-${ACCOUNT}"
JOB_NAME="analytiq-etl"
SCRIPT_S3_PATH="s3://${PROCESSED_BUCKET}/glue-scripts/glue_etl_job.py"

echo "Deploying Glue ETL job for account ${ACCOUNT}..."

# ── 1. Upload ETL script to S3 ────────────────────────────────────────────────
echo "Uploading ETL script to S3..."
aws s3 cp etl/glue_etl_job.py "${SCRIPT_S3_PATH}" --region "${REGION}"
echo "  ✓ Script uploaded to ${SCRIPT_S3_PATH}"

# ── 2. Get the Glue IAM role ARN ─────────────────────────────────────────────
GLUE_ROLE_ARN=$(aws iam list-roles \
  --query "Roles[?contains(RoleName, 'GlueRole')].Arn" \
  --output text)

echo "  ✓ Glue role: ${GLUE_ROLE_ARN}"

# ── 3. Create or update the Glue job ─────────────────────────────────────────
# Check if job already exists
JOB_EXISTS=$(aws glue get-job --job-name "${JOB_NAME}" --region "${REGION}" \
  2>/dev/null && echo "yes" || echo "no")

GLUE_JOB_ARGS=$(cat <<EOF
{
  "--JOB_NAME":           "${JOB_NAME}",
  "--RAW_BUCKET":         "${RAW_BUCKET}",
  "--TEMP_BUCKET":        "${PROCESSED_BUCKET}",
  "--REDSHIFT_URL":       "jdbc:redshift://analytiq-wg.${ACCOUNT}.${REGION}.redshift-serverless.amazonaws.com:5439/analytiq",
  "--REDSHIFT_USER":      "analytiq_admin",
  "--REDSHIFT_PASSWORD":  "ChangeMe123!",
  "--REDSHIFT_DB":        "analytiq",
  "--enable-metrics":     "true",
  "--enable-spark-ui":    "true"
}
EOF
)

if [ "$JOB_EXISTS" = "yes" ]; then
  echo "Updating existing Glue job..."
  aws glue update-job \
    --job-name "${JOB_NAME}" \
    --job-update "{
      \"Role\": \"${GLUE_ROLE_ARN}\",
      \"Command\": {
        \"Name\": \"glueetl\",
        \"ScriptLocation\": \"${SCRIPT_S3_PATH}\",
        \"PythonVersion\": \"3\"
      },
      \"DefaultArguments\": ${GLUE_JOB_ARGS},
      \"GlueVersion\": \"4.0\",
      \"NumberOfWorkers\": 2,
      \"WorkerType\": \"G.1X\",
      \"Timeout\": 60
    }" \
    --region "${REGION}"
else
  echo "Creating new Glue job..."
  aws glue create-job \
    --name "${JOB_NAME}" \
    --role "${GLUE_ROLE_ARN}" \
    --command "{
      \"Name\": \"glueetl\",
      \"ScriptLocation\": \"${SCRIPT_S3_PATH}\",
      \"PythonVersion\": \"3\"
    }" \
    --default-arguments "${GLUE_JOB_ARGS}" \
    --glue-version "4.0" \
    --number-of-workers 2 \
    --worker-type "G.1X" \
    --timeout 60 \
    --region "${REGION}"
fi

echo ""
echo "✅ Glue job '${JOB_NAME}' deployed!"
echo ""
echo "To run it now:"
echo "  aws glue start-job-run --job-name ${JOB_NAME} --region ${REGION}"
echo ""
echo "To check status:"
echo "  aws glue get-job-runs --job-name ${JOB_NAME} --region ${REGION} --query 'JobRuns[0].JobRunState'"
