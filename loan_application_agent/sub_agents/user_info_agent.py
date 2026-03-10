"""User Information Collection Sub-Agent.

Handles the onboarding use case where the agent collects personal information
(name, age, email, phone) from the user. All PII flows through the Trustwise
LLM gateway where policies are automatically enforced.
"""

from google.adk.agents import LlmAgent

from ..instructions import USER_INFO_INSTRUCTION
from ..model_config import get_model
from ..tools.user_info import collect_user_info, validate_user_info


def create_user_info_agent() -> LlmAgent:
    """Create the user info collection sub-agent."""
    return LlmAgent(
        model=get_model(),
        name="user_info_agent",
        description=(
            "Handles user onboarding — collects personal information "
            "(name, age, email, phone) for loan application or profile updates. "
            "Route here when user wants to apply for a loan or provide personal details."
        ),
        instruction=USER_INFO_INSTRUCTION,
        tools=[collect_user_info, validate_user_info],
    )
