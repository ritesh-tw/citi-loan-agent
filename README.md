# Citi Bank AI Advisor Agent

AI-powered banking advisor built with **Google ADK**, routed through **Trustwise LLM Gateway**, deployable to **Vertex AI Agent Engine**.

## Architecture

```
React UI ──SSE──▶ FastAPI (Auth + ADK Server) ──▶ Trustwise LLM Gateway ──▶ Vertex AI
                         │                              (PII policies enforced)
                         ├── User Info Sub-Agent
                         ├── Q&A Sub-Agent
                         └── Configurable Tools (Drive, Docs, Sheets)
```

## Features

- **Multi-agent system**: Root agent routes to specialized sub-agents (user onboarding, Q&A)
- **Trustwise LLM Gateway**: All LLM calls go through the gateway where PII policies, compliance rules, and logging are enforced automatically
- **Configurable tools**: Google Drive/Docs/Sheets tools activate only when credentials are present
- **Streaming chat API**: SSE-based streaming via ADK's built-in `/run_sse` endpoint
- **Bearer token auth**: External evaluation systems (Trustwise) can call the API with bearer tokens
- **Vertex AI deployment**: Deploy via `adk deploy agent_engine` with tracing, monitoring, and auto-scaling
- **Cloud Trace**: OpenTelemetry auto-instrumentation for agent_run, call_llm, execute_tool spans

## Quick Start

### 1. Install dependencies

```bash
pip install -r requirements.txt
cd frontend && npm install && cd ..
```

### 2. Configure environment

```bash
cp .env.example advisor_agent/.env
# Edit advisor_agent/.env with your settings
```

### 3. Run locally

```bash
# Option A: ADK dev UI (includes built-in web interface)
make dev-adk

# Option B: Custom server with auth (for API access)
make dev-backend

# Option C: Full stack with Docker
make dev
```

### 4. Test the API

```bash
# Health check
curl http://localhost:8000/health

# Chat (synchronous)
curl -X POST http://localhost:8000/run \
  -H "Authorization: Bearer citi-poc-demo-token" \
  -H "Content-Type: application/json" \
  -d '{
    "appName": "advisor_agent",
    "userId": "test-user",
    "sessionId": "test-session",
    "newMessage": {"role": "user", "parts": [{"text": "I want to open an account"}]}
  }'

# Chat (streaming SSE)
curl -N -X POST http://localhost:8000/run_sse \
  -H "Authorization: Bearer citi-poc-demo-token" \
  -H "Content-Type: application/json" \
  -d '{
    "appName": "advisor_agent",
    "userId": "test-user",
    "sessionId": "test-session",
    "newMessage": {"role": "user", "parts": [{"text": "Hello!"}]},
    "streaming": true
  }'
```

## Deploy to Vertex AI

```bash
# Set required env vars
export GOOGLE_CLOUD_PROJECT=your-project-id
export STAGING_BUCKET=gs://your-staging-bucket

# Deploy to Agent Engine
make deploy-vertex

# Or deploy to Cloud Run
make deploy-cloud-run
```

## API Endpoints

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| POST | `/run` | Synchronous chat | Bearer |
| POST | `/run_sse` | Streaming chat (SSE) | Bearer |
| POST | `/apps/{app}/users/{user}/sessions/{session}` | Create session | Bearer |
| GET | `/apps/{app}/users/{user}/sessions/{session}` | Get session | Bearer |
| DELETE | `/apps/{app}/users/{user}/sessions/{session}` | Delete session | Bearer |
| GET | `/list-apps` | List agents | Public |
| GET | `/health` | Health check | Public |
| GET | `/docs` | Swagger UI | Public |

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `LITELLM_PROXY_API_BASE` | Yes | Trustwise gateway URL |
| `LITELLM_PROXY_API_KEY` | Yes | Trustwise API key |
| `LLM_MODEL` | No | Model ID (default: `vertex_ai/gemini-2.0-flash`) |
| `API_BEARER_TOKEN` | No | Bearer token for API auth (empty = no auth) |
| `GOOGLE_DRIVE_SERVICE_ACCOUNT_JSON` | No | Service account JSON to enable Drive tools |
| `GOOGLE_DOCS_SERVICE_ACCOUNT_JSON` | No | Service account JSON to enable Docs tools |
| `GOOGLE_SHEETS_SERVICE_ACCOUNT_JSON` | No | Service account JSON to enable Sheets tools |
| `GOOGLE_CLOUD_PROJECT` | No | GCP project for tracing |
| `ENABLE_CLOUD_TRACE` | No | Enable Cloud Trace export (default: false) |

## Use Case: User Info Collection

The agent demonstrates PII collection with automatic policy enforcement:

1. User says "I want to open an account"
2. Agent routes to `user_info_agent`
3. Agent asks for name, age, email, phone one at a time
4. Each message containing PII passes through the Trustwise gateway
5. Gateway enforces PII policies (masking, logging, compliance)
6. Agent stores info in session state and confirms with user

## Vertex AI Features

| Feature | Status |
|---------|--------|
| Cloud Trace | Auto-instrumented (agent_run, call_llm, execute_tool spans) |
| Cloud Monitoring | Dashboard with token usage, latency, error rates |
| Cloud Logging | All agent interactions logged |
| Session Persistence | VertexAiSessionService (automatic on Agent Engine) |
| Auto-scaling | Managed by Agent Engine |
