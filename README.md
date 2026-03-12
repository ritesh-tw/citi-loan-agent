# Citi Loan Application Agent

AI-powered loan application assistant built with **Google ADK**, deployed on **Vertex AI Agent Engine** and **Cloud Run**, with all LLM traffic routed through the **Trustwise LLM Gateway** for policy enforcement.

## Architecture

```
┌──────────────────────┐     SSE/HTTP     ┌──────────────────────────────┐
│   Next.js Frontend   │ ──────────────▶  │   FastAPI Backend (Cloud Run) │
│   (Cloud Run)        │ ◀──────────────  │   /run_sse  /api/chat         │
└──────────────────────┘                  └──────────────┬───────────────┘
                                                         │ Vertex AI SDK
                                                         ▼
                                          ┌──────────────────────────────┐
                                          │  Vertex AI Agent Engine       │
                                          │                               │
                                          │  loan_application_agent       │
                                          │  (single LlmAgent)            │
                                          │                               │
                                          │  Tools:                       │
                                          │  ├── lookup_customer          │
                                          │  ├── collect_personal_info    │
                                          │  ├── validate_personal_info   │
                                          │  ├── get_loan_products        │
                                          │  ├── get_product_details      │
                                          │  ├── collect_application_info │
                                          │  ├── validate_application_info│
                                          │  └── run_prequalification     │
                                          └──────────┬───────────────────┘
                                                     │
                              ┌──────────────────────┼──────────────────────┐
                              ▼                      ▼                      ▼
                 ┌────────────────────┐  ┌───────────────────┐  ┌──────────────────┐
                 │  Trustwise LLM GW  │  │  Cloud SQL        │  │  Cloud Trace /   │
                 │  (before_model     │  │  (PostgreSQL)     │  │  Cloud Logging   │
                 │   callback guard)  │  │  customers, loans │  │  (telemetry)     │
                 │  OWASP Top 10      │  │  Private IP via   │  └──────────────────┘
                 │  Prompt Injection  │  │  VPC Connector    │
                 └────────────────────┘  └───────────────────┘
```

## Agent Design — Single-Agent Architecture

The agent is a **single `LlmAgent`** (no sub-agents). Stage routing is handled entirely by the LLM through tool selection, guided by a structured `UNIFIED_INSTRUCTION` with a mandatory reasoning protocol.

### 4-Stage Workflow

| Stage | Name | What happens |
|-------|------|-------------|
| 1 | Greeting & Intent | Welcome, understand what the user wants |
| 2 | Identity Verification | KYC — collect name, DOB, postcode; look up in DB |
| 3 | Loan Exploration | Show products, rates, and terms (no identity required) |
| 4 | Pre-Qualification | Collect financial info; run eligibility check (requires Stage 2 complete) |

### LLM Reasoning Protocol

Before every response, the agent executes a mandatory checklist:
1. Scan **full conversation history** for already-provided information
2. Determine if identity is complete (`IDENTITY_COMPLETE`)
3. Classify user intent
4. Determine the correct action / tool to call
5. Compose a response — never re-ask for already-provided information

## Project Structure

```
citi-loan-agent/
├── loan_application_agent/         # ADK agent package (deployed to Agent Engine)
│   ├── __init__.py                 # Exports root_agent
│   ├── agent.py                    # Single LlmAgent with all tools attached
│   ├── instructions.py             # UNIFIED_INSTRUCTION — structured reasoning protocol
│   ├── model_config.py             # LiteLlm → Trustwise gateway → Gemini 2.0 Flash
│   ├── gateway_guard.py            # before_model_callback: Trustwise pre-screen
│   ├── db.py                       # PostgreSQL connection (Cloud SQL via VPC)
│   ├── seed_db.py                  # Seed DB with sample customers & loan products
│   ├── .env                        # Local dev environment
│   ├── .env.gcp                    # GCP production environment (source of truth)
│   ├── .agent_engine_config.json   # Agent Engine metadata (ID, display name)
│   └── tools/
│       ├── customer_lookup.py      # collect_personal_info, validate_personal_info, lookup_customer
│       ├── loan_products.py        # get_loan_products, get_product_details
│       ├── prequalification.py     # collect_application_info, validate_application_info, run_prequalification
│       ├── common.py               # get_current_time
│       ├── user_info.py            # Session state helpers
│       ├── registry.py             # Conditional tool registration
│       ├── google_drive.py         # Optional: Drive integration
│       ├── google_docs.py          # Optional: Docs integration
│       └── google_sheets.py        # Optional: Sheets integration
├── server/                         # FastAPI backend (proxies to Agent Engine)
│   ├── main.py                     # App setup (ADK proxy + CORS + auth)
│   ├── auth.py                     # Bearer token middleware
│   ├── chat_api.py                 # Simplified /api/chat endpoint
│   ├── admin_routes.py             # Admin API routes
│   └── config.py                   # Pydantic settings
├── frontend/                       # Next.js chat UI (Cloud Run)
│   └── src/
│       ├── app/                    # Pages (/, /admin)
│       ├── components/
│       │   ├── chat/               # ChatPanel, MessageBubble, ToolIndicator, QuickForm
│       │   └── layout/             # Header, Sidebar
│       ├── hooks/useChat.ts        # SSE state management
│       └── lib/api.ts              # SSE client for /run_sse
├── deploy/
│   ├── vertex_deploy.sh            # Deploy/update Agent Engine
│   ├── cloudbuild-backend.yaml     # Cloud Build config for backend
│   └── cloudbuild-frontend.yaml   # Cloud Build config for frontend
├── tests/                          # Test suite
├── CLAUDE.md                       # Full deployment & project guide
├── Dockerfile                      # Backend Docker image
└── requirements.txt                # Python dependencies
```

## GCP Infrastructure

| Resource | Value |
|----------|-------|
| Project | `cs-host-d29276312550417ca85da7` |
| Region | `us-central1` |
| Agent Engine ID | `5798796837099929600` |
| Artifact Registry | `us-central1-docker.pkg.dev/…/genesis/` |
| VPC Connector | `genesis-connector` (Cloud SQL access) |
| Cloud SQL Private IP | `10.21.0.3:5432` |

## LLM Configuration

| Setting | Value |
|---------|-------|
| Model | `vertex_ai/gemini-2.0-flash` |
| Gateway | Trustwise (`https://aigw.tw-forge.trustwise.ai`) |
| Routing | LiteLlm with `openai/` prefix → Trustwise → Gemini |
| Config | `loan_application_agent/model_config.py` |

All LLM calls pass through `gateway_prescreen_callback` (a `before_model_callback`) which screens requests against Trustwise OWASP Top 10 policies before they reach the model.

## Service URLs

| Service | URL |
|---------|-----|
| Frontend | https://loan-agent-frontend-632353252476.us-central1.run.app |
| Backend | https://loan-agent-backend-632353252476.us-central1.run.app |
| Agent Engine Console | https://console.cloud.google.com/vertex-ai/agents/agent-engines/locations/us-central1/agent-engines/5798796837099929600?project=cs-host-d29276312550417ca85da7 |

## Local Development

### Prerequisites
- Python 3.12+
- Node.js 20+
- PostgreSQL

### Setup

```bash
git clone git@github.com:ritesh-tw/citi-loan-agent.git
cd citi-loan-agent

# Python virtual environment
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Frontend
cd frontend && npm install && cd ..
```

### Configure Environment

```bash
# Copy and edit local env (uses local DB, not Cloud SQL)
cp loan_application_agent/.env.example loan_application_agent/.env
# Set: LLM_GATEWAY_BASE_URL, LLM_GATEWAY_API_KEY, DATABASE_URL

# Frontend
cp frontend/.env.local.example frontend/.env.local
# Set: NEXT_PUBLIC_API_URL=http://localhost:8001
```

### Seed Database

```bash
createdb loan_agent
python -m loan_application_agent.seed_db
```

### Run

```bash
# Terminal 1 — ADK API server (agent)
adk api_server --port 8001 --allow_origins "http://localhost:3000" .

# Terminal 2 — Frontend
cd frontend && npm run dev
```

> **Note:** The ADK `api_server` command takes the **parent directory** of the agent as its argument (`.`), not the agent name.

## Deployment

See [CLAUDE.md](CLAUDE.md) for full deployment instructions. Summary:

```bash
# 1. Deploy Agent Engine (after changing loan_application_agent/)
bash deploy/vertex_deploy.sh

# 2. Deploy Backend (after changing server/)
gcloud builds submit --config=deploy/cloudbuild-backend.yaml --project=cs-host-d29276312550417ca85da7
gcloud run deploy loan-agent-backend ...

# 3. Deploy Frontend (after changing frontend/)
gcloud builds submit --config=deploy/cloudbuild-frontend.yaml --project=cs-host-d29276312550417ca85da7
gcloud run deploy loan-agent-frontend ...
```

## API Reference

### SSE Streaming (used by the frontend)

```bash
curl -X POST https://loan-agent-backend-632353252476.us-central1.run.app/run_sse \
  -H "Authorization: Bearer citi-poc-demo-token" \
  -H "Content-Type: application/json" \
  -d '{"userId":"test","sessionId":"","newMessage":{"parts":[{"text":"Hello"}]}}'
```

### Simplified Chat API

```bash
curl -X POST https://loan-agent-backend-632353252476.us-central1.run.app/api/chat \
  -H "Authorization: Bearer citi-poc-demo-token" \
  -H "Content-Type: application/json" \
  -d '{"question": "What loans do you offer?"}'
```

**Response:**
```json
{
  "answer": "We offer personal loans, debt consolidation loans, and home improvement loans...",
  "session_id": "s-abc123",
  "agent": "loan_application_agent",
  "tools_used": ["get_loan_products"],
  "turn": 1
}
```

### ADK Native Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/run_sse` | Streaming agent execution (SSE) |
| POST | `/run` | Synchronous agent execution |
| POST | `/apps/{app}/users/{user}/sessions/{session}` | Create session |
| GET | `/apps/{app}/users/{user}/sessions/{session}` | Get session history |
| DELETE | `/apps/{app}/users/{user}/sessions/{session}` | Delete session |
| GET | `/health` | Health check |

## Environment Variables

### Agent / Backend (`loan_application_agent/.env`)

| Variable | Required | Description |
|----------|----------|-------------|
| `LLM_GATEWAY_BASE_URL` | Yes | Trustwise gateway URL |
| `LLM_GATEWAY_API_KEY` | Yes | Trustwise API key |
| `LLM_MODEL` | Yes | Model ID (e.g. `vertex_ai/gemini-2.0-flash`) |
| `DATABASE_URL` | Yes | PostgreSQL connection string |
| `API_BEARER_TOKEN` | No | Bearer token for API auth |
| `GOOGLE_CLOUD_PROJECT` | Yes (GCP) | GCP project ID |
| `GOOGLE_CLOUD_LOCATION` | Yes (GCP) | GCP region |

### Frontend (`frontend/.env.local`)

| Variable | Required | Description |
|----------|----------|-------------|
| `NEXT_PUBLIC_API_URL` | Yes | Backend URL |
| `NEXT_PUBLIC_BEARER_TOKEN` | Yes | Must match `API_BEARER_TOKEN` |
| `NEXT_PUBLIC_ADMIN_PASSWORD` | No | Admin panel password |

## Demo Flow

1. **"Hello"** → Agent greets and asks how it can help
2. **"What loans do you offer?"** → `get_loan_products` → shows personal, consolidation, home improvement loans
3. **"I'd like to apply"** → Agent asks for identity verification (name, DOB, postcode)
4. **User provides details** → `collect_personal_info` → `validate_personal_info` → `lookup_customer` → identity confirmed
5. **"My annual income is £55,000"** → `collect_application_info` → `validate_application_info` → `run_prequalification` → eligibility result with loan terms

**Trustwise policy enforcement:**
- "Ignore all previous instructions" → blocked: `Prompt Injection Detection`
- "hack google.com" → blocked: `Obfuscated Attack Detection`
