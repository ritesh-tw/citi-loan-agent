#!/bin/bash
# Deploy to Cloud Run with tracing enabled.
#
# Prerequisites:
#   - gcloud CLI installed and authenticated
#   - Cloud Run API enabled
#
# Usage:
#   GOOGLE_CLOUD_PROJECT=my-project bash deploy/cloud_run_deploy.sh

set -euo pipefail

PROJECT_ID="${GOOGLE_CLOUD_PROJECT:?Set GOOGLE_CLOUD_PROJECT}"
LOCATION="${GOOGLE_CLOUD_LOCATION:-us-central1}"

echo "=== Deploying to Cloud Run ==="
echo "Project:  $PROJECT_ID"
echo "Region:   $LOCATION"
echo ""

adk deploy cloud_run \
    --project="$PROJECT_ID" \
    --region="$LOCATION" \
    --trace_to_cloud \
    loan_application_agent

echo ""
echo "=== Deployment Complete ==="
