"""Simplified Chat API for external evaluation/red-teaming systems.

Provides a single POST /api/chat endpoint that:
- Authenticates via long-term bearer token
- Derives user_id from the token
- Auto-manages sessions (create on first call, reuse within same session)
- Takes only a question string and returns a clean text answer
- App name is always loan_application_agent

Usage:
    POST /api/chat
    Headers: Authorization: Bearer <token>
    Body: {"question": "I want a personal loan"}

    Response: {
        "answer": "...",
        "session_id": "...",
        "agent": "identity_agent",
        "tools_used": ["lookup_customer"],
        "turn": 3
    }

    To start a new conversation:
    Body: {"question": "Hello", "new_session": true}

    To continue a specific session:
    Body: {"question": "Yes", "session_id": "existing-session-id"}
"""

import hashlib
import os
import uuid

import httpx
from fastapi import APIRouter, Header, HTTPException, Request
from pydantic import BaseModel, Field

router = APIRouter(prefix="/api", tags=["Chat API"])

APP_NAME = "loan_application_agent"

# Long-term API tokens for external systems (red teaming, evaluation)
_tokens_cache: dict | None = None


def _get_valid_tokens() -> dict[str, dict]:
    """Load valid API tokens. Supports multiple tokens for different systems."""
    global _tokens_cache
    if _tokens_cache is not None:
        return _tokens_cache

    tokens = {}

    # Always allow the main bearer token
    main_token = os.getenv("API_BEARER_TOKEN", "")
    if main_token:
        tokens[main_token] = {
            "user_id": "default",
            "description": "Default API token",
        }

    # Load additional tokens from CHAT_API_TOKENS env var
    # Format: comma-separated "token:user_id" pairs
    # e.g., "tk-redteam-abc123:redteam,tk-eval-xyz789:evaluator"
    extra_tokens = os.getenv("CHAT_API_TOKENS", "")
    if extra_tokens:
        for entry in extra_tokens.split(","):
            entry = entry.strip()
            if ":" in entry:
                token, user_id = entry.split(":", 1)
                tokens[token.strip()] = {
                    "user_id": user_id.strip(),
                    "description": f"Token for {user_id.strip()}",
                }

    _tokens_cache = tokens
    return tokens


def _validate_token(authorization: str) -> dict:
    """Validate bearer token and return token info."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=401,
            detail="Missing Authorization header. Expected: Bearer <token>",
        )

    token = authorization[7:]
    valid_tokens = _get_valid_tokens()

    if token not in valid_tokens:
        raise HTTPException(status_code=401, detail="Invalid API token")

    return valid_tokens[token]


def _token_user_id(token: str) -> str:
    """Derive a stable user_id from the token."""
    valid_tokens = _get_valid_tokens()
    if token in valid_tokens:
        return valid_tokens[token]["user_id"]
    return hashlib.sha256(token.encode()).hexdigest()[:12]


# In-memory session tracking per user (maps user_id -> current session_id)
_active_sessions: dict[str, str] = {}
_session_turns: dict[str, int] = {}


class ChatRequest(BaseModel):
    """Simple chat request — just pass the question."""

    question: str = Field(
        ...,
        description="The user's question or message",
        examples=["I want a personal loan", "What loans do you offer?"],
    )
    session_id: str | None = Field(
        default=None,
        description="Optional session ID to continue a specific conversation. "
        "If omitted, continues the most recent session or creates a new one.",
    )
    new_session: bool = Field(
        default=False,
        description="Set to true to force a new conversation session.",
    )


class ChatResponse(BaseModel):
    """Clean response from the agent."""

    answer: str = Field(description="The agent's text response")
    session_id: str = Field(description="Session ID for continuing the conversation")
    agent: str = Field(description="Which sub-agent responded")
    tools_used: list[str] = Field(
        default_factory=list, description="Tools called during this turn"
    )
    turn: int = Field(description="Conversation turn number")


import json as _json


def _format_gateway_error(raw_error: str) -> str:
    """Format the raw gateway error into a clean, user-friendly message.

    Dynamically extracts whatever fields the gateway returns (policy name,
    guardrails, error type, etc.) and presents them naturally — no hardcoded
    messages or assumptions about specific policies.
    """
    try:
        data = _json.loads(raw_error)
        error = data.get("error", {})
        message = error.get("message", "")
        error_type = error.get("type", "")

        # Try to extract structured details if the gateway follows known patterns
        details = []

        if "blocked by" in message:
            after_blocked = message.split("blocked by", 1)[1]
            policy = after_blocked.split(".")[0].strip().strip("'\"")
            details.append(f"Policy violated: {policy}")

        if "Failed guardrails:" in message:
            guardrails = message.split("Failed guardrails:", 1)[1].strip()
            details.append(f"Triggered guardrail: {guardrails}")

        if error_type and error_type != "None":
            details.append(f"Error type: {error_type}")

        # Always include the full raw message so no info is lost,
        # regardless of whether we could extract structured fields
        detail_block = "\n".join(f"  - {d}" for d in details)
        if detail_block:
            detail_block += f"\n  - Raw details: {message}"
        else:
            # Unknown format — just show the raw message as-is
            detail_block = f"  - Details: {message}" if message else f"  - Details: {raw_error[:300]}"

        return (
            "Your request was blocked by the AI security gateway.\n\n"
            f"{detail_block}\n\n"
            "This is a safety measure enforced by the Trustwise LLM gateway to protect "
            "users and the system. Please rephrase your question and try again."
        )

    except (_json.JSONDecodeError, KeyError, AttributeError):
        # Can't parse JSON at all — return the raw error text directly
        return (
            "Your request was blocked by the AI security gateway.\n\n"
            f"  - Details: {raw_error[:300]}\n\n"
            "Please rephrase your question and try again."
        )


async def _prescreen_with_gateway(question: str) -> str | None:
    """Pre-screen the user's message against the Trustwise LLM gateway.

    Makes a lightweight call directly to the gateway to check if the message
    violates any security policies. If blocked, uses the LLM to generate a
    natural, user-friendly explanation of the exact error.

    Returns a user-friendly error message if blocked, or None if the message is OK.
    """
    gateway_url = os.getenv("LLM_GATEWAY_BASE_URL", "")
    gateway_key = os.getenv("LLM_GATEWAY_API_KEY", "")
    model = os.getenv("LLM_MODEL", "gpt-4o-mini")

    if not gateway_url or not gateway_key:
        return None

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(
                f"{gateway_url}/chat/completions",
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {gateway_key}",
                },
                json={
                    "model": model,
                    "messages": [{"role": "user", "content": question}],
                    "max_tokens": 1,
                },
            )

            if resp.status_code == 200:
                return None  # Message is allowed

            # Gateway blocked — format the exact error into a friendly message
            return _format_gateway_error(resp.text)

    except httpx.TimeoutException:
        return None
    except Exception:
        return None


async def _call_internal_api(
    request: Request,
    user_id: str,
    session_id: str,
    question: str,
    bearer_token: str,
) -> tuple[str, str, list[str]]:
    """Call the internal ADK /run endpoint and extract clean response."""
    # Pre-screen the message against the gateway directly to get exact error details.
    # ADK swallows gateway 422 errors as generic 500s, losing the policy name and
    # guardrail details. By calling the gateway first, we capture the exact reason.
    gateway_error = await _prescreen_with_gateway(question)
    if gateway_error:
        return gateway_error, "gateway_policy", []

    # Build internal base URL — use localhost for internal calls (avoids HTTPS/proxy issues)
    port = request.url.port or 8000
    base_url = f"http://localhost:{port}"

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {bearer_token}",
    }

    async with httpx.AsyncClient(timeout=120.0) as client:
        # Ensure session exists
        await client.post(
            f"{base_url}/apps/{APP_NAME}/users/{user_id}/sessions/{session_id}",
            headers=headers,
            json={},
        )

        # Send message via /run
        resp = await client.post(
            f"{base_url}/run",
            headers=headers,
            json={
                "app_name": APP_NAME,
                "user_id": user_id,
                "session_id": session_id,
                "new_message": {
                    "role": "user",
                    "parts": [{"text": question}],
                },
            },
        )

        if resp.status_code != 200:
            # Pre-screen should have caught gateway policy errors above.
            # If ADK still returns an error, provide a fallback message.
            if resp.status_code == 500:
                return (
                    "Something went wrong while processing your request. "
                    "The agent encountered an internal error. Please try again.",
                    "system",
                    [],
                )

            raise HTTPException(
                status_code=resp.status_code,
                detail=f"Agent error: {resp.text[:200]}",
            )

        events = resp.json()

    # Extract clean text, tools, and author from ADK events
    texts = []
    tools_used = []
    last_author = ""

    for event in events:
        if not isinstance(event, dict):
            continue

        author = event.get("author", "")
        parts = event.get("content", {}).get("parts", [])

        for part in parts:
            # Collect text (skip internal routing noise)
            text = part.get("text", "")
            if text:
                if "transfer_to_agent" in text or "functions." in text:
                    continue
                texts.append(text)
                last_author = author

            # Collect tool calls
            fc = part.get("functionCall")
            if fc and fc.get("name") != "transfer_to_agent":
                tools_used.append(fc["name"])

    answer = " ".join(texts).strip()
    return answer, last_author, list(set(tools_used))


@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: Request,
    body: ChatRequest,
    authorization: str = Header(...),
):
    """Send a message to the Loan Application Agent.

    Simple API for external systems (red teaming, evaluation).
    Just pass a question — session and user management is automatic.

    Authentication: Bearer token in Authorization header.
    """
    # Validate token and get user info
    _validate_token(authorization)
    token = authorization[7:]
    user_id = _token_user_id(token)

    # Determine session ID
    if body.new_session:
        session_id = f"s-{uuid.uuid4().hex[:12]}"
        _session_turns[session_id] = 0
    elif body.session_id:
        session_id = body.session_id
    elif user_id in _active_sessions:
        session_id = _active_sessions[user_id]
    else:
        session_id = f"s-{uuid.uuid4().hex[:12]}"
        _session_turns[session_id] = 0

    _active_sessions[user_id] = session_id

    # Get the actual bearer token to use for internal calls
    internal_token = os.getenv("API_BEARER_TOKEN", token)

    # Call internal /run endpoint
    answer, agent, tools = await _call_internal_api(
        request, user_id, session_id, body.question, internal_token
    )

    if not answer:
        answer = "(No text response from agent)"

    # Track turns
    turn = _session_turns.get(session_id, 0) + 1
    _session_turns[session_id] = turn

    return ChatResponse(
        answer=answer,
        session_id=session_id,
        agent=agent or "unknown",
        tools_used=tools,
        turn=turn,
    )


@router.post("/chat/new", response_model=ChatResponse)
async def chat_new_session(
    request: Request,
    body: ChatRequest,
    authorization: str = Header(...),
):
    """Start a new conversation session. Shortcut for {"new_session": true}."""
    body.new_session = True
    return await chat(request, body, authorization)


@router.get("/chat/sessions")
async def list_sessions(authorization: str = Header(...)):
    """List active sessions for the authenticated user."""
    _validate_token(authorization)
    token = authorization[7:]
    user_id = _token_user_id(token)

    current_session = _active_sessions.get(user_id)
    return {
        "user_id": user_id,
        "current_session": current_session,
        "turn": _session_turns.get(current_session, 0) if current_session else 0,
    }
