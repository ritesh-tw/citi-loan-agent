# Citi Loan Application Agent — Project Guide

## Project Overview
Multi-agent loan application system built with Google ADK, deployed on GCP (Vertex AI Agent Engine + Cloud Run).

## Architecture
```
Frontend (Next.js, Cloud Run) → Backend (FastAPI, Cloud Run) → Agent Engine (Vertex AI)
                                                                      ↕
                                                               Cloud SQL (PostgreSQL)
                                                               Trustwise LLM Gateway
```

## Key Files
- `loan_application_agent/` — Agent code (ADK agents, tools, prompts)
- `loan_application_agent/.env` — Local dev environment
- `loan_application_agent/.env.gcp` — GCP production environment (single source of truth for all GCP config)
- `loan_application_agent/.agent_engine_config.json` — Agent Engine metadata
- `server/` — FastAPI backend (proxies to Agent Engine)
- `frontend/` — Next.js UI
- `deploy/` — All deployment scripts and configs

## GCP Configuration
- **Project:** `cs-host-d29276312550417ca85da7`
- **Region:** `us-central1`
- **Agent Engine ID:** `5798796837099929600` (NEVER create new engines — always update this one)
- **Artifact Registry:** `us-central1-docker.pkg.dev/cs-host-d29276312550417ca85da7/genesis/`
- **VPC Connector:** `genesis-connector` (required for Cloud SQL access)
- **Cloud SQL Private IP:** `10.21.0.3:5432`

---

## Deployment Instructions

### CRITICAL RULES
1. **ALWAYS update the existing Agent Engine** (`5798796837099929600`) — NEVER create new ones
2. **ALWAYS use `.env.gcp`** for GCP deployments — NEVER use `.env` (which has local DB URL)
3. **ALWAYS enable telemetry** — use `--trace_to_cloud` and `--otel_to_cloud` flags
4. **All env vars for GCP** live in `loan_application_agent/.env.gcp` — update there first, then deploy

---

### Deploy: Vertex AI Agent Engine
Updates the agent code running inside Vertex AI Agent Engine.

**When to run:** After changing any files in `loan_application_agent/` (agents, tools, prompts, model config).

```bash
bash deploy/vertex_deploy.sh
```

**What it does:**
- Reads config from `loan_application_agent/.env.gcp`
- Updates existing engine `5798796837099929600` (via `--agent_engine_id`)
- Enables `--trace_to_cloud` and `--otel_to_cloud`
- Passes all `.env.gcp` vars as runtime env vars to Agent Engine

**Manual equivalent:**
```bash
adk deploy agent_engine \
  --project=cs-host-d29276312550417ca85da7 \
  --region=us-central1 \
  --agent_engine_id=5798796837099929600 \
  --trace_to_cloud \
  --otel_to_cloud \
  --env_file=loan_application_agent/.env.gcp \
  --display_name="loan_application_agent" \
  loan_application_agent
```

---

### Deploy: Backend (Cloud Run)
Updates the FastAPI server that proxies requests to Agent Engine.

**When to run:** After changing files in `server/`, `Dockerfile`, `requirements.txt`, or env vars in `.env.gcp`.

**Step 1 — Build & push Docker image:**
```bash
gcloud builds submit \
  --config=deploy/cloudbuild-backend.yaml \
  --project=cs-host-d29276312550417ca85da7
```

**Step 2 — Deploy to Cloud Run with all env vars from .env.gcp:**
```bash
gcloud run deploy loan-agent-backend \
  --image=us-central1-docker.pkg.dev/cs-host-d29276312550417ca85da7/genesis/loan-agent-backend:latest \
  --region=us-central1 \
  --project=cs-host-d29276312550417ca85da7 \
  --vpc-connector=genesis-connector \
  --vpc-egress=private-ranges-only \
  --set-env-vars="$(grep -v '^#' loan_application_agent/.env.gcp | grep -v '^$' | tr '\n' ',' | sed 's/,$//')"
```

**Update a single env var without rebuilding:**
```bash
gcloud run services update loan-agent-backend \
  --region=us-central1 \
  --project=cs-host-d29276312550417ca85da7 \
  --update-env-vars="KEY=VALUE"
```

---

### Deploy: Frontend (Cloud Run)
Updates the Next.js UI.

**When to run:** After changing files in `frontend/`.

**Build & push:**
```bash
gcloud builds submit \
  --config=deploy/cloudbuild-frontend.yaml \
  --project=cs-host-d29276312550417ca85da7
```

**Deploy:**
```bash
gcloud run deploy loan-agent-frontend \
  --image=us-central1-docker.pkg.dev/cs-host-d29276312550417ca85da7/genesis/loan-agent-frontend:latest \
  --region=us-central1 \
  --project=cs-host-d29276312550417ca85da7 \
  --set-env-vars="NEXT_PUBLIC_API_URL=https://loan-agent-backend-632353252476.us-central1.run.app,NEXT_PUBLIC_BEARER_TOKEN=citi-poc-demo-token,NEXT_PUBLIC_ADMIN_PASSWORD=Trustwise@citibank"
```

**Note:** `NEXT_PUBLIC_*` vars are baked at build time. Changing them requires a rebuild, not just a redeploy.

---

### Deploy All (Full Stack)
When deploying everything (e.g., after major changes):

1. **Agent Engine first** (agent logic): `bash deploy/vertex_deploy.sh`
2. **Backend second** (proxy server): Build + deploy Cloud Run backend
3. **Frontend last** (UI): Build + deploy Cloud Run frontend (only if UI changed)

---

### Testing After Deploy
```bash
# Quick API test
curl -s -X POST "https://loan-agent-backend-632353252476.us-central1.run.app/api/chat" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer citi-poc-demo-token" \
  -d '{"question": "What loans do you offer?"}'

# SSE streaming test (what the frontend uses)
curl -s -X POST "https://loan-agent-backend-632353252476.us-central1.run.app/run_sse" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer citi-poc-demo-token" \
  -d '{"userId":"test","sessionId":"","newMessage":{"parts":[{"text":"Hello"}]}}'
```

---

## Service URLs
- **Frontend:** https://loan-agent-frontend-632353252476.us-central1.run.app
- **Backend:** https://loan-agent-backend-632353252476.us-central1.run.app
- **Agent Engine Console:** https://console.cloud.google.com/vertex-ai/agents/agent-engines/locations/us-central1/agent-engines/5798796837099929600?project=cs-host-d29276312550417ca85da7

## LLM Configuration
- **Gateway:** Trustwise (`https://aigw.tw-forge.trustwise.ai`)
- **Model:** `vertex_ai/gemini-2.0-flash` (set in `.env.gcp` as `LLM_MODEL`)
- **Routing:** LiteLlm with `openai/` prefix → Trustwise gateway → actual model provider
- **Config file:** `loan_application_agent/model_config.py`

## Gemini Compatibility
Gemini requires ALL function declarations to have OBJECT-type parameter schemas. Parameterless tools MUST have at least one parameter with a default value (e.g., `category: str = "all"`). This was already fixed in `loan_products.py`, `customer_lookup.py`, and `prequalification.py`.

## Local Development
```bash
# Start local server (uses .env for local DB)
DATABASE_URL=postgresql://riteshkumar@localhost:5433/loan_agent uvicorn server.main:app --port 8000

# Run agent directly with ADK
adk run loan_application_agent
```
