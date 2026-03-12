"""Root Agent Definition - Loan Application Agent.

This is the main entry point for the ADK agent. It follows ADK convention
by exporting `root_agent`, making it compatible with:
  - adk run loan_application_agent
  - adk web loan_application_agent
  - adk api_server loan_application_agent
  - adk deploy agent_engine loan_application_agent

Single-agent architecture: all tools are attached directly to the root agent.
No sub-agents — the LLM handles stage routing via tool selection and the
unified instruction, which enforces the identity → pre-qualification gate.
"""

from google.adk.agents import LlmAgent

from .gateway_guard import gateway_prescreen_callback
from .instructions import UNIFIED_INSTRUCTION
from .model_config import get_model
from .tools.common import get_current_time
from .tools.customer_lookup import collect_personal_info, lookup_customer, validate_personal_info
from .tools.loan_products import get_loan_products, get_product_details
from .tools.prequalification import (
    collect_application_info,
    run_prequalification,
    validate_application_info,
)

root_agent = LlmAgent(
    model=get_model(),
    name="loan_application_agent",
    description=(
        "Citibank UK Loan Application Agent — helps users explore loan products, "
        "verify identity, and complete pre-qualification for personal loans, "
        "debt consolidation loans, and home improvement loans."
    ),
    instruction=UNIFIED_INSTRUCTION,
    tools=[
        get_current_time,
        # Stage 2 — Identity & customer verification
        lookup_customer,
        collect_personal_info,
        validate_personal_info,
        # Stage 3 — Loan exploration (available without identity)
        get_loan_products,
        get_product_details,
        # Stage 4 — Pre-qualification (requires identity complete)
        collect_application_info,
        validate_application_info,
        run_prequalification,
    ],
    before_model_callback=gateway_prescreen_callback,
)
