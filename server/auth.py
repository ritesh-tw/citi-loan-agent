"""Bearer token authentication middleware.

Validates Authorization header for external API callers (e.g., Trustwise evaluation system).
If API_BEARER_TOKEN is not set, auth is disabled (open access for development).
"""

import json
import os

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

# Paths that skip authentication
PUBLIC_PATHS = {"/health", "/docs", "/openapi.json", "/redoc", "/list-apps"}
PUBLIC_PREFIXES = ("/api/admin", "/api/chat")


class BearerAuthMiddleware(BaseHTTPMiddleware):
    """Middleware that validates Bearer token on all API requests."""

    async def dispatch(self, request: Request, call_next):
        # Skip auth for public endpoints
        if request.url.path in PUBLIC_PATHS:
            return await call_next(request)

        # Skip auth for admin API (POC — add auth in production)
        if any(request.url.path.startswith(p) for p in PUBLIC_PREFIXES):
            return await call_next(request)

        # Skip auth for OPTIONS (CORS preflight)
        if request.method == "OPTIONS":
            return await call_next(request)

        expected_token = os.getenv("API_BEARER_TOKEN", "")

        # If no token configured, auth is disabled (dev mode)
        if not expected_token:
            return await call_next(request)

        # Validate bearer token
        auth_header = request.headers.get("authorization", "")
        if not auth_header.startswith("Bearer "):
            return JSONResponse(
                status_code=401,
                content={"detail": "Missing or invalid Authorization header. Expected: Bearer <token>"},
            )

        token = auth_header[7:]

        # Check main token
        if token == expected_token:
            return await call_next(request)

        # Check additional CHAT_API_TOKENS (format: "token1:user1,token2:user2")
        extra_tokens = os.getenv("CHAT_API_TOKENS", "")
        if extra_tokens:
            for entry in extra_tokens.split(","):
                entry = entry.strip()
                if ":" in entry and entry.split(":")[0].strip() == token:
                    return await call_next(request)

        return JSONResponse(
            status_code=401,
            content={"detail": "Invalid bearer token"},
        )
