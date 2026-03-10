"""Identity & Customer Status Check Sub-Agent — Stage 2.

Determines if the user is an existing Citibank UK customer,
verifies their identity, and retrieves their account details.
For new customers, collects personal information (PII).
"""

from google.adk.agents import LlmAgent

from ..instructions import IDENTITY_INSTRUCTION
from ..model_config import get_model
from ..tools.customer_lookup import (
    collect_personal_info,
    lookup_customer,
    validate_personal_info,
)


def create_identity_agent() -> LlmAgent:
    """Create the identity verification sub-agent."""
    return LlmAgent(
        model=get_model(),
        name="identity_agent",
        description=(
            "ABSOLUTE FIRST STEP — route here BEFORE any other agent (except greeting_agent for bare hellos). "
            "This agent MUST run before prequalification_agent can be used. "
            "Verifies existing customers (lookup) or collects personal info from new customers. "
            "Route here for ANY message about loans, applying, eligibility, quotes, OR when user provides "
            "personal details (name, DOB, postcode, email, phone, loan amount). "
            "Identity is COMPLETE only when 'welcome back' or 'details are saved' appears in history. "
            "If neither appears yet, ALWAYS route here first, regardless of what the user says."
        ),
        instruction=IDENTITY_INSTRUCTION,
        tools=[lookup_customer, collect_personal_info, validate_personal_info],
    )
