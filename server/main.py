"""FastAPI server wrapping ADK's built-in API server with auth and CORS.

This provides all ADK endpoints (/run, /run_sse, session management)
plus bearer token authentication for external callers (Trustwise).

Endpoints provided by ADK:
  POST /run          — Synchronous agent execution
  POST /run_sse      — SSE streaming agent execution
  POST /apps/{app}/users/{user}/sessions/{session}  — Create/update session
  GET  /apps/{app}/users/{user}/sessions/{session}   — Get session
  DELETE /apps/{app}/users/{user}/sessions/{session}  — Delete session
  GET  /list-apps    — List available agents

Custom endpoints:
  GET  /health       — Health check
  GET  /docs         — Swagger UI (auto-generated)
"""

import os
import sys

from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware

# Load environment from loan_application_agent/.env
env_path = os.path.join(os.path.dirname(__file__), "..", "loan_application_agent", ".env")
load_dotenv(env_path)

# Ensure the project root is in the Python path
project_root = os.path.dirname(os.path.dirname(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from google.adk.cli.fast_api import get_fast_api_app

from .auth import BearerAuthMiddleware
from .admin_routes import router as admin_router
from .chat_api import router as chat_router

# Directory containing agent packages (project root)
AGENTS_DIR = os.path.join(os.path.dirname(__file__), "..")
ENABLE_TRACE = os.getenv("ENABLE_CLOUD_TRACE", "false").lower() == "true"

# Get ADK's built-in FastAPI app with all endpoints
app = get_fast_api_app(
    agents_dir=AGENTS_DIR,
    web=False,
    trace_to_cloud=ENABLE_TRACE,
)

# Add CORS middleware (allow all origins for POC; restrict in production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add bearer token authentication
app.add_middleware(BearerAuthMiddleware)

# Mount admin API routes
app.include_router(admin_router)

# Mount simplified chat API (for red teaming / evaluation systems)
app.include_router(chat_router)


@app.get("/health")
async def health():
    """Health check endpoint (no auth required)."""
    tools_status = {
        "google_drive": bool(os.getenv("GOOGLE_DRIVE_SERVICE_ACCOUNT_JSON")),
        "google_docs": bool(os.getenv("GOOGLE_DOCS_SERVICE_ACCOUNT_JSON")),
        "google_sheets": bool(os.getenv("GOOGLE_SHEETS_SERVICE_ACCOUNT_JSON")),
    }
    return {
        "status": "healthy",
        "agent": "loan_application_agent",
        "tools_enabled": tools_status,
        "tracing_enabled": ENABLE_TRACE,
    }
