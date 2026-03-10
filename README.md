# Citi Loan Application Agent

AI-powered loan application assistant built with **Google ADK**, routed through **Trustwise LLM Gateway** for policy enforcement, deployable to **Google Cloud Run** and **Vertex AI Agent Engine**.

## Architecture

```
┌─────────────┐     ┌──────────────────────────────────────┐     ┌──────────────────┐
│  React UI   │────▶│  FastAPI (Auth + ADK Server)          │────▶│ Trustwise LLM GW │
│  (Next.js)  │ SSE │                                      │     │  (Policy enforce) │
│             │◀────│  /run_sse (streaming)                 │◀────│  OWASP Top 10    │
└─────────────┘     │  /api/chat (simplified)               │     └──────────────────┘
                    │                                      │
  Trustwise Eval    │  Agents:                             │     ┌──────────────────┐
  System ──────────▶│  ├── greeting_agent                  │────▶│ PostgreSQL DB    │
  (Bearer Token)    │  ├── identity_agent                  │     │ (customers, loans)│
                    │  ├── loan_explorer_agent              │     └──────────────────┘
                    │  ├── prequalification_agent           │
                    │  └── qa_agent                         │
                    └──────────────────────────────────────┘
```

## Project Structure

```
citi-loan-agent/
├── loan_application_agent/         # ADK agent package
│   ├── __init__.py                 # Exports root_agent
│   ├── agent.py                    # Root agent with sub-agent routing
│   ├── model_config.py             # LiteLlm → Trustwise gateway config
│   ├── instructions.py             # System prompts for all agents
│   ├── db.py                       # PostgreSQL connection helper
│   ├── seed_db.py                  # Seed DB with sample customers & loans
│   ├── sub_agents/
│   │   ├── greeting_agent.py       # Welcome & routing
│   │   ├── identity_agent.py       # Customer identification
│   │   ├── loan_explorer_agent.py  # Loan product information
│   │   ├── prequalification_agent.py # Eligibility checking
│   │   └── qa_agent.py             # General Q&A
│   └── tools/
│       ├── registry.py             # Conditional tool registration
│       ├── customer_lookup.py      # DB: customer search
│       ├── loan_products.py        # DB: loan product catalog
│       ├── prequalification.py     # DB: eligibility checks
│       ├── user_info.py            # Session state: collect user info
│       ├── common.py               # Utilities (get_current_time)
│       ├── google_drive.py         # Optional: Drive integration
│       ├── google_docs.py          # Optional: Docs integration
│       └── google_sheets.py        # Optional: Sheets integration
├── server/                         # FastAPI wrapper around ADK
│   ├── main.py                     # App setup (ADK + CORS + auth)
│   ├── auth.py                     # Bearer token auth middleware
│   ├── chat_api.py                 # Simplified /api/chat endpoint
│   ├── admin_routes.py             # Admin API routes
│   └── config.py                   # Pydantic settings
├── frontend/                       # React chat UI (Next.js)
│   ├── src/
│   │   ├── app/                    # Pages (chat, admin)
│   │   ├── components/chat/        # ChatPanel, MessageBubble, etc.
│   │   ├── hooks/useChat.ts        # Chat state + SSE management
│   │   └── lib/api.ts              # SSE client for /run_sse
│   └── package.json
├── deploy/                         # Deployment scripts
├── .env.example                    # Backend env template
├── Dockerfile                      # Backend Docker image
├── docker-compose.yml              # Full stack (backend + frontend)
├── Makefile                        # Dev shortcuts
└── requirements.txt                # Python dependencies
```

## Prerequisites

- Python 3.12+
- Node.js 18+
- PostgreSQL (for customer/loan data)
- Trustwise LLM Gateway account (API key)

## Setup

### Step 1: Clone & Install

```bash
git clone git@github.com:ritesh-tw/citi-loan-agent.git
cd citi-loan-agent

# Create Python virtual environment
python -m venv .venv
source .venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt

# Install frontend dependencies
cd frontend && npm install && cd ..
```

### Step 2: Configure Environment

```bash
# Backend config
cp .env.example loan_application_agent/.env
# Edit loan_application_agent/.env with your values:
#   - LLM_GATEWAY_BASE_URL and LLM_GATEWAY_API_KEY (from Trustwise)
#   - DATABASE_URL (your PostgreSQL connection string)
#   - API_BEARER_TOKEN (any secret string for API auth)

# Frontend config
cp frontend/.env.local.example frontend/.env.local
# Edit frontend/.env.local:
#   - NEXT_PUBLIC_API_URL (backend URL, default http://localhost:8000)
#   - NEXT_PUBLIC_BEARER_TOKEN (must match API_BEARER_TOKEN above)
#   - NEXT_PUBLIC_ADMIN_PASSWORD (password for admin panel)
```

### Step 3: Setup Database

```bash
# Create the database
createdb loan_agent

# Seed with sample customers and loan products
python -m loan_application_agent.seed_db
```

### Step 4: Run Locally

```bash
# Option A: Backend + custom server with auth (recommended)
make dev-backend
# Then in another terminal:
make dev-frontend

# Option B: ADK dev UI (built-in web interface, no auth)
make dev-adk

# Option C: Full stack with Docker
make dev
```

The backend runs on `http://localhost:8000`, frontend on `http://localhost:3000`.

### Step 5: Verify

```bash
# Health check
curl http://localhost:8000/health

# Test the simplified chat API
curl -X POST http://localhost:8000/api/chat \
  -H "Authorization: Bearer your-secret-bearer-token" \
  -H "Content-Type: application/json" \
  -d '{"question": "What loans do you offer?", "new_session": true}'
```

## API Reference

### Simplified Chat API (for external systems / red-teaming)

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/chat` | Send a message (auto-manages sessions) |
| POST | `/api/chat/new` | Start a new conversation |
| GET | `/api/chat/sessions` | List active sessions for the user |

**Example — Send a message:**
```bash
curl -X POST https://your-backend-url/api/chat \
  -H "Authorization: Bearer your-token" \
  -H "Content-Type: application/json" \
  -d '{"question": "I want a personal loan"}'
```

**Response:**
```json
{
  "answer": "I'd be happy to help you with a personal loan...",
  "session_id": "s-abc123def456",
  "agent": "loan_explorer_agent",
  "tools_used": ["get_loan_products"],
  "turn": 1
}
```

**Start a new session:**
```json
{"question": "Hello", "new_session": true}
```

**Continue a specific session:**
```json
{"question": "Yes, I'd like to proceed", "session_id": "s-abc123def456"}
```

### ADK Native Endpoints

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| POST | `/run` | Synchronous agent execution | Bearer |
| POST | `/run_sse` | Streaming agent execution (SSE) | Bearer |
| POST | `/apps/{app}/users/{user}/sessions/{session}` | Create session | Bearer |
| GET | `/apps/{app}/users/{user}/sessions/{session}` | Get session history | Bearer |
| DELETE | `/apps/{app}/users/{user}/sessions/{session}` | Delete session | Bearer |
| GET | `/list-apps` | List available agents | Public |
| GET | `/health` | Health check | Public |
| GET | `/docs` | Swagger UI (auto-generated) | Public |

**ADK /run example:**
```bash
curl -X POST http://localhost:8000/run \
  -H "Authorization: Bearer your-token" \
  -H "Content-Type: application/json" \
  -d '{
    "app_name": "loan_application_agent",
    "user_id": "test-user",
    "session_id": "test-session",
    "new_message": {"role": "user", "parts": [{"text": "Hello!"}]}
  }'
```

## LLM Gateway Policy Enforcement

All messages pass through the Trustwise LLM gateway which enforces security policies automatically. When a message is blocked, the `/api/chat` endpoint returns a detailed explanation:

```json
{
  "answer": "Your request was blocked by the AI security gateway.\n\n  - Policy violated: OWASP LLM Top 10 Policy\n  - Triggered guardrail: Prompt Injection Detection\n  - Raw details: Request blocked by 'OWASP LLM Top 10 Policy'. Failed guardrails: Prompt Injection Detection\n\nThis is a safety measure enforced by the Trustwise LLM gateway...",
  "agent": "gateway_policy",
  "session_id": "s-abc123",
  "tools_used": [],
  "turn": 1
}
```

The pre-screening happens before the message reaches the agent, so exact policy details (policy name, triggered guardrail) are preserved and shown to the caller.

## Environment Variables

### Backend (`loan_application_agent/.env`)

| Variable | Required | Description |
|----------|----------|-------------|
| `LLM_GATEWAY_BASE_URL` | Yes | Trustwise gateway URL |
| `LLM_GATEWAY_API_KEY` | Yes | Trustwise API key |
| `LLM_MODEL` | No | Model ID (default: `gpt-4o-mini`) |
| `DATABASE_URL` | Yes | PostgreSQL connection string |
| `API_BEARER_TOKEN` | No | Bearer token for API auth (empty = no auth) |
| `CHAT_API_TOKENS` | No | Extra tokens as `token1:user1,token2:user2` |
| `GOOGLE_DRIVE_SERVICE_ACCOUNT_JSON` | No | JSON to enable Drive tools |
| `GOOGLE_DOCS_SERVICE_ACCOUNT_JSON` | No | JSON to enable Docs tools |
| `GOOGLE_SHEETS_SERVICE_ACCOUNT_JSON` | No | JSON to enable Sheets tools |
| `GOOGLE_CLOUD_PROJECT` | No | GCP project for tracing/deploy |
| `GOOGLE_CLOUD_LOCATION` | No | GCP region (default: `us-central1`) |
| `ENABLE_CLOUD_TRACE` | No | Enable Cloud Trace (default: `false`) |

### Frontend (`frontend/.env.local`)

| Variable | Required | Description |
|----------|----------|-------------|
| `NEXT_PUBLIC_API_URL` | Yes | Backend URL (e.g., `http://localhost:8000`) |
| `NEXT_PUBLIC_BEARER_TOKEN` | Yes | Must match `API_BEARER_TOKEN` |
| `NEXT_PUBLIC_ADMIN_PASSWORD` | No | Password for admin panel |

## Deployment

### Cloud Run

```bash
# Set env vars
export GOOGLE_CLOUD_PROJECT=your-project-id

# Deploy backend
gcloud run deploy loan-agent-backend \
  --source . \
  --region us-central1 \
  --project $GOOGLE_CLOUD_PROJECT \
  --allow-unauthenticated \
  --port 8000 \
  --memory 1Gi \
  --timeout 120 \
  --command "uvicorn" \
  --args "server.main:app,--host,0.0.0.0,--port,8000" \
  --set-env-vars "LLM_GATEWAY_BASE_URL=...,LLM_GATEWAY_API_KEY=...,LLM_MODEL=gpt-4o-mini,API_BEARER_TOKEN=..."
```

### Vertex AI Agent Engine

```bash
export GOOGLE_CLOUD_PROJECT=your-project-id
export STAGING_BUCKET=gs://your-staging-bucket

make deploy-vertex
```

When deployed to Agent Engine:
- `VertexAiSessionService` is used automatically (persistent sessions)
- Cloud Trace, Cloud Monitoring, and Cloud Logging are enabled
- Auto-scaling is managed by the platform

### Docker (Local)

```bash
make dev
# Starts backend on :8000 and frontend on :3000
```

## Demo Flow

1. User: "Hello" → `greeting_agent` responds with welcome
2. User: "I want a personal loan" → routes to `loan_explorer_agent` → shows loan products
3. User: "Can I check if I'm eligible?" → routes to `identity_agent` → asks for customer ID
4. User: "My customer ID is C001" → `identity_agent` looks up customer in DB
5. Agent routes to `prequalification_agent` → runs eligibility check against DB
6. Agent shows pre-qualification result with loan terms

**Policy enforcement example:**
- User: "hack google.com" → gateway blocks with `Obfuscated Attack Detection`
- User: "ignore all instructions" → gateway blocks with `Prompt Injection Detection`

## Make Commands

| Command | Description |
|---------|-------------|
| `make install` | Install all dependencies (Python + Node) |
| `make dev` | Run full stack with Docker Compose |
| `make dev-backend` | Run backend only with hot reload |
| `make dev-adk` | Run ADK dev UI (built-in web interface) |
| `make dev-frontend` | Run frontend only |
| `make deploy-vertex` | Deploy to Vertex AI Agent Engine |
| `make deploy-cloud-run` | Deploy to Cloud Run |
| `make test` | Run tests |
| `make clean` | Clean build artifacts |
