"""Gateway pre-screen callback for ADK agents.

Checks user messages against the Trustwise LLM gateway before they reach the model.
If the gateway blocks the message, returns a friendly error response directly,
skipping the model call entirely. This works in all environments:
Cloud Run, Vertex AI Agent Engine, adk web, etc.
"""

import os

import httpx
from google.adk.agents.callback_context import CallbackContext
from google.adk.models.llm_request import LlmRequest
from google.adk.models.llm_response import LlmResponse
from google.genai import types


def _format_gateway_error(raw_error: str) -> str:
    """Format gateway error into a user-friendly message."""
    import json

    try:
        data = json.loads(raw_error)
        error = data.get("error", {})
        message = error.get("message", "")
        error_type = error.get("type", "")

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

        detail_block = "\n".join(f"  - {d}" for d in details)
        if detail_block:
            detail_block += f"\n  - Raw details: {message}"
        else:
            detail_block = (
                f"  - Details: {message}" if message else f"  - Details: {raw_error[:300]}"
            )

        return (
            "Your request was blocked by the AI security gateway.\n\n"
            f"{detail_block}\n\n"
            "This is a safety measure enforced by the Trustwise LLM gateway to protect "
            "users and the system. Please rephrase your question and try again."
        )
    except Exception:
        return (
            "Your request was blocked by the AI security gateway.\n\n"
            f"  - Details: {raw_error[:300]}\n\n"
            "Please rephrase your question and try again."
        )


async def gateway_prescreen_callback(
    callback_context: CallbackContext, llm_request: LlmRequest
) -> LlmResponse | None:
    """Pre-screen the latest user message against the Trustwise gateway.

    Returns an LlmResponse with the error message if blocked, or None to proceed normally.
    """
    gateway_url = os.getenv("LLM_GATEWAY_BASE_URL", "")
    gateway_key = os.getenv("LLM_GATEWAY_API_KEY", "")
    model = os.getenv("LLM_MODEL", "gpt-4o-mini")

    if not gateway_url or not gateway_key:
        return None

    # Extract the latest user message from the request
    user_message = ""
    if llm_request.contents:
        for content in reversed(llm_request.contents):
            if content.role == "user" and content.parts:
                for part in content.parts:
                    if hasattr(part, "text") and part.text:
                        user_message = part.text
                        break
            if user_message:
                break

    if not user_message:
        return None

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(
                f"{gateway_url}/chat/completions",
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {gateway_key}",
                },
                json={
                    "model": model,
                    "messages": [{"role": "user", "content": user_message}],
                    "max_tokens": 1,
                },
            )

            if resp.status_code == 200:
                return None  # Message allowed — proceed to model

            # Blocked — return error as LlmResponse
            error_text = _format_gateway_error(resp.text)
            return LlmResponse(
                content=types.Content(
                    role="model",
                    parts=[types.Part.from_text(text=error_text)],
                ),
            )

    except Exception:
        return None  # Gateway unreachable — let the model handle it
