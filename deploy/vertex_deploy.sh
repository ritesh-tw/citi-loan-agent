#!/bin/bash
# Deploy to Vertex AI Agent Engine with tracing enabled.
#
# Prerequisites:
#   - gcloud CLI installed and authenticated
#   - Vertex AI API enabled in GCP project
#   - Cloud Resource Manager API enabled
#   - A GCS staging bucket created
#
# Usage:
#   GOOGLE_CLOUD_PROJECT=my-project STAGING_BUCKET=gs://my-bucket bash deploy/vertex_deploy.sh

set -euo pipefail

PROJECT_ID="${GOOGLE_CLOUD_PROJECT:?Set GOOGLE_CLOUD_PROJECT}"
LOCATION="${GOOGLE_CLOUD_LOCATION:-us-central1}"
STAGING_BUCKET="${STAGING_BUCKET:?Set STAGING_BUCKET (e.g., gs://my-agent-staging)}"
DISPLAY_NAME="${DISPLAY_NAME:-Loan Application Agent}"

echo "=== Deploying to Vertex AI Agent Engine ==="
echo "Project:  $PROJECT_ID"
echo "Region:   $LOCATION"
echo "Bucket:   $STAGING_BUCKET"
echo "Display:  $DISPLAY_NAME"
echo ""

adk deploy agent_engine \
    --project="$PROJECT_ID" \
    --region="$LOCATION" \
    --staging_bucket="$STAGING_BUCKET" \
    --display_name="$DISPLAY_NAME" \
    --trace_to_cloud \
    loan_application_agent

echo ""
echo "=== Deployment Complete ==="
echo ""
echo "View in GCP Console:"
echo "  https://console.cloud.google.com/vertex-ai/agent-builder/agent-engines?project=$PROJECT_ID"
echo ""
echo "Monitoring Dashboard:"
echo "  GCP Console → Vertex AI → Agent Engine → $DISPLAY_NAME → Monitoring"
echo ""
echo "Trace Explorer:"
echo "  https://console.cloud.google.com/traces?project=$PROJECT_ID"
