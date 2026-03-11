"""FastAPI server that proxies agent requests through Vertex AI Agent Engine.

All agent interactions (/run, /run_sse, sessions) are forwarded to Agent Engine,
so traces, monitoring, and sessions are unified in one place. Admin and chat
API routes continue to work directly.

Endpoints:
  POST /run          — Proxied to Agent Engine (synchronous)
  POST /run_sse      — Proxied to Agent Engine (SSE streaming)
  POST /apps/{app}/users/{user}/sessions  — Create session via Agent Engine
  GET  /apps/{app}/users/{user}/sessions  — List sessions via Agent Engine
  GET  /health       — Health check
  /api/admin/*       — Direct admin routes (DB access)
  /api/chat          — Simplified chat API (proxied via Agent Engine)
"""

import json
import os
import sys

import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from google.cloud.aiplatform_v1beta1 import ReasoningEngineExecutionServiceClient
from google.cloud.aiplatform_v1beta1.types import (
    QueryReasoningEngineRequest,
    StreamQueryReasoningEngineRequest,
)
from google.protobuf import struct_pb2
from starlette.responses import JSONResponse, StreamingResponse

# Load environment from loan_application_agent/.env
env_path = os.path.join(os.path.dirname(__file__), "..", "loan_application_agent", ".env")
load_dotenv(env_path)

# Ensure the project root is in the Python path
project_root = os.path.dirname(os.path.dirname(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from .auth import BearerAuthMiddleware
from .admin_routes import router as admin_router
from .chat_api import router as chat_router

# Agent Engine configuration
PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT", "cs-host-d29276312550417ca85da7")
LOCATION = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")
AGENT_ENGINE_ID = os.getenv("AGENT_ENGINE_ID", "5798796837099929600")
AGENT_ENGINE_RESOURCE = f"projects/{PROJECT_ID}/locations/{LOCATION}/reasoningEngines/{AGENT_ENGINE_ID}"

# Lazy-loaded execution client
_exec_client = None


def get_exec_client() -> ReasoningEngineExecutionServiceClient:
    """Lazy-load the Agent Engine execution client."""
    global _exec_client
    if _exec_client is None:
        _exec_client = ReasoningEngineExecutionServiceClient(
            client_options={"api_endpoint": f"{LOCATION}-aiplatform.googleapis.com"}
        )
    return _exec_client


def _snake_to_camel(s: str) -> str:
    """Convert snake_case to camelCase."""
    parts = s.split("_")
    return parts[0] + "".join(p.capitalize() for p in parts[1:])


def _normalize_event(obj):
    """Recursively convert snake_case keys to camelCase for ADK frontend compatibility.

    Agent Engine returns snake_case (function_call, function_response, state_delta, etc.)
    but the ADK frontend expects camelCase (functionCall, functionResponse, stateDelta, etc.).
    """
    if isinstance(obj, dict):
        return {_snake_to_camel(k): _normalize_event(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_normalize_event(item) for item in obj]
    return obj


def _make_input(**kwargs) -> struct_pb2.Struct:
    """Create a protobuf Struct from keyword arguments."""
    s = struct_pb2.Struct()
    s.update(kwargs)
    return s


def _call_agent_engine(class_method: str, **kwargs):
    """Call Agent Engine via query (non-streaming)."""
    from google.protobuf.json_format import MessageToDict

    client = get_exec_client()
    resp = client.query_reasoning_engine(
        QueryReasoningEngineRequest(
            name=AGENT_ENGINE_RESOURCE,
            input=_make_input(**kwargs),
            class_method=class_method,
        )
    )
    # Convert protobuf response to dict via the underlying _pb message
    result = MessageToDict(resp._pb)
    return _normalize_event(result.get("output", {}))


def _stream_agent_engine(class_method: str, **kwargs):
    """Call Agent Engine via stream_query (streaming). Yields parsed JSON dicts."""
    client = get_exec_client()
    responses = client.stream_query_reasoning_engine(
        StreamQueryReasoningEngineRequest(
            name=AGENT_ENGINE_RESOURCE,
            input=_make_input(**kwargs),
            class_method=class_method,
        )
    )
    for resp in responses:
        data = resp.data.decode("utf-8") if resp.data else ""
        if data.strip():
            for line in data.strip().split("\n"):
                line = line.strip()
                if line:
                    try:
                        yield _normalize_event(json.loads(line))
                    except json.JSONDecodeError:
                        pass


# Create FastAPI app
app = FastAPI(
    title="Loan Application Agent API",
    description="Proxies to Vertex AI Agent Engine for unified tracing and monitoring",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add bearer token authentication
app.add_middleware(BearerAuthMiddleware)

# Mount admin API routes (direct DB access)
app.include_router(admin_router)

# Mount simplified chat API
app.include_router(chat_router)


# ── Gateway Pre-screen ───────────────────────────────────────────────────────

async def _check_gateway(message: str) -> str | None:
    """Check message against Trustwise gateway. Returns error string if blocked, None if OK."""
    gateway_url = os.getenv("LLM_GATEWAY_BASE_URL", "")
    gateway_key = os.getenv("LLM_GATEWAY_API_KEY", "")
    model = os.getenv("LLM_MODEL", "gpt-4o-mini")
    if not gateway_url or not gateway_key:
        return None
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(
                f"{gateway_url}/chat/completions",
                headers={"Content-Type": "application/json", "Authorization": f"Bearer {gateway_key}"},
                json={"model": model, "messages": [{"role": "user", "content": message}], "max_tokens": 1},
            )
            if resp.status_code == 200:
                return None
            from .chat_api import _format_gateway_error
            return _format_gateway_error(resp.text)
    except Exception:
        return None


@app.middleware("http")
async def gateway_prescreen_middleware(request: Request, call_next):
    """Pre-screen messages against gateway before forwarding to Agent Engine."""
    if request.method == "POST" and request.url.path in ("/run_sse", "/run"):
        try:
            body_bytes = await request.body()
            body = json.loads(body_bytes)
            parts = body.get("newMessage", body.get("new_message", {})).get("parts", [])
            message = ""
            for p in parts:
                if p.get("text"):
                    message = p["text"]
                    break
            if message:
                gateway_error = await _check_gateway(message)
                if gateway_error:
                    origin = request.headers.get("origin", "*")
                    cors_headers = {
                        "Access-Control-Allow-Origin": origin,
                        "Access-Control-Allow-Credentials": "true",
                    }
                    if request.url.path == "/run_sse":
                        event_data = json.dumps({
                            "content": {"parts": [{"text": gateway_error}]},
                            "author": "gateway_policy",
                            "partial": False,
                        })

                        async def sse_stream():
                            yield f"data: {event_data}\n\n"

                        return StreamingResponse(
                            sse_stream(),
                            media_type="text/event-stream",
                            headers=cors_headers,
                        )
                    else:
                        event = {
                            "content": {"parts": [{"text": gateway_error}]},
                            "author": "gateway_policy",
                        }
                        return JSONResponse(content=[event], headers=cors_headers)
        except Exception:
            pass

    return await call_next(request)


# ── Agent Engine Proxy Endpoints ─────────────────────────────────────────────

@app.post("/apps/{app_name}/users/{user_id}/sessions")
async def create_session_no_id(app_name: str, user_id: str):
    """Create a new session via Agent Engine."""
    try:
        result = _call_agent_engine("create_session", user_id=user_id)
        return {
            "id": result.get("id", ""),
            "appName": app_name,
            "userId": user_id,
            "state": result.get("state", {}),
            "events": [],
        }
    except Exception as e:
        return JSONResponse(status_code=500, content={"detail": f"Failed to create session: {str(e)}"})


@app.get("/apps/{app_name}/users/{user_id}/sessions")
async def list_sessions(app_name: str, user_id: str):
    """List sessions for a user via Agent Engine."""
    try:
        result = _call_agent_engine("list_sessions", user_id=user_id)
        sessions = result.get("sessions", result) if isinstance(result, dict) else []
        if isinstance(sessions, list):
            return [{"id": s.get("id", ""), "appName": app_name, "userId": user_id} for s in sessions]
        return []
    except Exception as e:
        return JSONResponse(status_code=500, content={"detail": f"Failed to list sessions: {str(e)}"})


@app.post("/apps/{app_name}/users/{user_id}/sessions/{session_id}")
async def create_session_with_id(app_name: str, user_id: str, session_id: str):
    """Create a session via Agent Engine (ID assigned by engine)."""
    try:
        result = _call_agent_engine("create_session", user_id=user_id)
        return {
            "id": result.get("id", ""),
            "appName": app_name,
            "userId": user_id,
            "state": result.get("state", {}),
            "events": [],
        }
    except Exception as e:
        return JSONResponse(status_code=500, content={"detail": f"Failed to create session: {str(e)}"})


@app.get("/apps/{app_name}/users/{user_id}/sessions/{session_id}")
async def get_session(app_name: str, user_id: str, session_id: str):
    """Get a specific session from Agent Engine."""
    try:
        result = _call_agent_engine("get_session", user_id=user_id, session_id=session_id)
        return {
            "id": result.get("id", session_id),
            "appName": app_name,
            "userId": user_id,
            "state": result.get("state", {}),
            "events": [],
        }
    except Exception as e:
        return JSONResponse(status_code=500, content={"detail": f"Session not found: {str(e)}"})


@app.delete("/apps/{app_name}/users/{user_id}/sessions/{session_id}")
async def delete_session(app_name: str, user_id: str, session_id: str):
    """Delete a session from Agent Engine."""
    try:
        _call_agent_engine("delete_session", user_id=user_id, session_id=session_id)
        return {"status": "deleted"}
    except Exception as e:
        return JSONResponse(status_code=500, content={"detail": f"Failed to delete session: {str(e)}"})


@app.post("/run_sse")
async def run_sse(request: Request):
    """Stream agent response via SSE, proxied through Agent Engine."""
    import asyncio
    from concurrent.futures import ThreadPoolExecutor

    body = await request.json()

    user_id = body.get("user_id", body.get("userId", "default"))
    session_id = body.get("session_id", body.get("sessionId", ""))
    new_message = body.get("new_message", body.get("newMessage", {}))

    # Extract message text
    message = ""
    parts = new_message.get("parts", [])
    for p in parts:
        if isinstance(p, dict) and p.get("text"):
            message = p["text"]
            break

    if not message:
        return JSONResponse(status_code=400, content={"detail": "No message text provided"})

    async def generate_sse():
        loop = asyncio.get_event_loop()
        queue: asyncio.Queue = asyncio.Queue()

        def _stream_in_thread():
            try:
                for event in _stream_agent_engine(
                    "stream_query",
                    user_id=user_id,
                    session_id=session_id,
                    message=message,
                ):
                    loop.call_soon_threadsafe(queue.put_nowait, event)
            except Exception as e:
                loop.call_soon_threadsafe(
                    queue.put_nowait,
                    {"content": {"parts": [{"text": f"Error: {str(e)}"}]}, "author": "system", "partial": False},
                )
            finally:
                loop.call_soon_threadsafe(queue.put_nowait, None)  # sentinel

        executor = ThreadPoolExecutor(max_workers=1)
        executor.submit(_stream_in_thread)

        while True:
            event = await queue.get()
            if event is None:
                break
            yield f"data: {json.dumps(event, default=str)}\n\n"

        executor.shutdown(wait=False)

    return StreamingResponse(generate_sse(), media_type="text/event-stream")


@app.post("/run")
async def run(request: Request):
    """Synchronous agent query, proxied through Agent Engine."""
    body = await request.json()

    user_id = body.get("user_id", body.get("userId", "default"))
    session_id = body.get("session_id", body.get("sessionId", ""))
    new_message = body.get("new_message", body.get("newMessage", {}))

    message = ""
    parts = new_message.get("parts", [])
    for p in parts:
        if isinstance(p, dict) and p.get("text"):
            message = p["text"]
            break

    if not message:
        return JSONResponse(status_code=400, content={"detail": "No message text provided"})

    try:
        # Collect all streamed events into a list
        events = list(_stream_agent_engine(
            "stream_query",
            user_id=user_id,
            session_id=session_id,
            message=message,
        ))
        return JSONResponse(content=events)
    except Exception as e:
        return JSONResponse(status_code=500, content={"detail": f"Agent Engine error: {str(e)}"})


@app.get("/list-apps")
async def list_apps():
    """List available agent apps."""
    return [{"name": "loan_application_agent", "description": "Citibank UK Loan Application Agent"}]


@app.get("/health")
async def health():
    """Health check endpoint."""
    tools_status = {
        "google_drive": bool(os.getenv("GOOGLE_DRIVE_SERVICE_ACCOUNT_JSON")),
        "google_docs": bool(os.getenv("GOOGLE_DOCS_SERVICE_ACCOUNT_JSON")),
        "google_sheets": bool(os.getenv("GOOGLE_SHEETS_SERVICE_ACCOUNT_JSON")),
    }
    return {
        "status": "healthy",
        "agent": "loan_application_agent",
        "agent_engine": AGENT_ENGINE_RESOURCE,
        "tools_enabled": tools_status,
        "tracing_enabled": True,
    }
