"""Greeting & Intent Detection Sub-Agent — Stage 1.

Handles initial user interaction, welcomes them, and determines their intent
to route them to the appropriate next stage.
"""

from google.adk.agents import LlmAgent

from ..instructions import GREETING_INSTRUCTION
from ..model_config import get_model
from ..tools.common import get_current_time


def create_greeting_agent() -> LlmAgent:
    """Create the greeting and intent detection sub-agent."""
    return LlmAgent(
        model=get_model(),
        name="greeting_agent",
        description=(
            "ONLY handles simple greetings like 'hello', 'hi', 'good morning'. "
            "Do NOT route here if the user mentions loans, applying, eligibility, borrowing, or any specific request."
        ),
        instruction=GREETING_INSTRUCTION,
        tools=[get_current_time],
    )
