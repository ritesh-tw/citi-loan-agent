"""LLM Gateway Configuration - Routes all LLM calls through Trustwise gateway.

The Trustwise LLM gateway (OpenAI-compatible) sits between ADK and Vertex AI.
All messages pass through the gateway where PII policies, compliance rules,
and logging are enforced automatically.

Environment Variables:
    LLM_GATEWAY_BASE_URL: Trustwise gateway URL (e.g., https://aigw.tw-forge.trustwise.ai)
    LLM_GATEWAY_API_KEY: API key for the gateway
    LLM_MODEL: Model identifier passed to gateway (e.g., gpt-4o-mini)
"""

import os

from google.adk.models.lite_llm import LiteLlm


def get_model() -> LiteLlm:
    """Create a LiteLlm model instance pointing to the Trustwise LLM gateway.

    Uses 'openai/' prefix to tell LiteLlm to use OpenAI-compatible API format.
    Passes api_base and api_key directly to avoid proxy mode model name issues.
    """
    model_name = os.getenv("LLM_MODEL", "gpt-4o-mini")
    api_base = os.getenv("LLM_GATEWAY_BASE_URL", "https://aigw.tw-forge.trustwise.ai")
    api_key = os.getenv("LLM_GATEWAY_API_KEY", "")

    # Always use 'openai/' prefix so LiteLlm routes through the gateway
    # (OpenAI-compatible API). The actual model name (e.g. 'vertex_ai/gemini-2.0-flash')
    # is passed to the gateway which handles provider routing.
    return LiteLlm(
        model=f"openai/{model_name}",
        api_base=api_base,
        api_key=api_key,
    )
