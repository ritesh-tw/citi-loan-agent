#!/bin/bash
# Deploy/Update Vertex AI Agent Engine with full tracing & telemetry.
#
# This script ALWAYS:
#   - Uses .env.gcp (not .env) so Agent Engine gets production env vars
#   - Enables --trace_to_cloud (Cloud Trace integration)
#   - Enables --otel_to_cloud (OpenTelemetry telemetry collection)
#   - Updates the EXISTING engine (via --agent_engine_id) instead of creating new ones
#
# Prerequisites:
#   - gcloud CLI installed and authenticated
#   - adk CLI installed (pip install google-adk)
#   - Vertex AI API enabled in GCP project
#
# Usage:
#   bash deploy/vertex_deploy.sh           # Update existing engine (default)
#   bash deploy/vertex_deploy.sh --create  # Create a brand-new engine (rare)

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
AGENT_DIR="$PROJECT_ROOT/loan_application_agent"
ENV_GCP="$AGENT_DIR/.env.gcp"

# ── Load config from .env.gcp ──────────────────────────────────────────────
if [[ ! -f "$ENV_GCP" ]]; then
  echo "ERROR: $ENV_GCP not found"
  exit 1
fi

# Source values we need for CLI flags (without exporting to shell)
PROJECT_ID=$(grep -E '^GOOGLE_CLOUD_PROJECT=' "$ENV_GCP" | cut -d= -f2)
LOCATION=$(grep -E '^GOOGLE_CLOUD_LOCATION=' "$ENV_GCP" | cut -d= -f2)
AGENT_ENGINE_ID=$(grep -E '^AGENT_ENGINE_ID=' "$ENV_GCP" | cut -d= -f2)

PROJECT_ID="${PROJECT_ID:-cs-host-d29276312550417ca85da7}"
LOCATION="${LOCATION:-us-central1}"

echo "=== Vertex AI Agent Engine Deployment ==="
echo "Project:         $PROJECT_ID"
echo "Region:          $LOCATION"
echo "Agent Engine ID: ${AGENT_ENGINE_ID:-<new>}"
echo "Env file:        $ENV_GCP"
echo "Trace to Cloud:  enabled"
echo "OTel to Cloud:   enabled"
echo ""

# ── Build deploy command ────────────────────────────────────────────────────
DEPLOY_CMD=(
  adk deploy agent_engine
  --project="$PROJECT_ID"
  --region="$LOCATION"
  --trace_to_cloud                          # Enable Cloud Trace
  --otel_to_cloud                           # Enable OpenTelemetry telemetry collection
  --env_file="$ENV_GCP"                     # Use GCP env vars (not local .env)
  --display_name="loan_application_agent"
  --description="Citibank UK Loan Application Agent - 4-stage workflow with identity verification, loan exploration, and pre-qualification"
)

# Update existing engine unless --create is passed
if [[ "${1:-}" == "--create" ]]; then
  echo "MODE: Creating NEW Agent Engine"
  echo ""
else
  if [[ -z "$AGENT_ENGINE_ID" ]]; then
    echo "ERROR: AGENT_ENGINE_ID not set in $ENV_GCP. Use --create for a new engine."
    exit 1
  fi
  echo "MODE: Updating existing Agent Engine"
  echo ""
  DEPLOY_CMD+=(--agent_engine_id="$AGENT_ENGINE_ID")
fi

# ── Deploy ──────────────────────────────────────────────────────────────────
"${DEPLOY_CMD[@]}" loan_application_agent

echo ""
echo "=== Deployment Complete ==="
echo ""
echo "View in GCP Console:"
echo "  https://console.cloud.google.com/vertex-ai/agents/agent-engines?project=$PROJECT_ID"
echo ""
echo "Traces:"
echo "  https://console.cloud.google.com/vertex-ai/agents/agent-engines/locations/$LOCATION/agent-engines/${AGENT_ENGINE_ID}/traces?project=$PROJECT_ID"
