"""Pre-Qualification Sub-Agent — Stage 4.

Collects financial information and runs the pre-qualification engine
to provide indicative loan offers to users.
"""

from google.adk.agents import LlmAgent

from ..instructions import PREQUALIFICATION_INSTRUCTION
from ..model_config import get_model
from ..tools.prequalification import (
    collect_application_info,
    run_prequalification,
    validate_application_info,
)


def create_prequalification_agent() -> LlmAgent:
    """Create the pre-qualification sub-agent."""
    return LlmAgent(
        model=get_model(),
        name="prequalification_agent",
        description=(
            "Handles loan application and pre-qualification ONLY AFTER identity is complete "
            "(customer found via lookup OR new customer details saved). "
            "Collects employment status, income, loan amount, purpose, repayment term, "
            "and residency status, then runs the pre-qualification engine. "
            "Route here ONLY when identity_agent has finished AND user wants to apply/check eligibility. "
            "Also route here for confirmations ('yes', 'looks good', 'correct') when this agent last responded. "
            "NEVER route here if identity is not yet complete — use identity_agent first."
        ),
        instruction=PREQUALIFICATION_INSTRUCTION,
        tools=[collect_application_info, validate_application_info, run_prequalification],
    )
