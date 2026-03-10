"""Root Agent Definition - Loan Application Agent.

This is the main entry point for the ADK agent. It follows ADK convention
by exporting `root_agent`, making it compatible with:
  - adk run loan_application_agent
  - adk web loan_application_agent
  - adk api_server loan_application_agent
  - adk deploy agent_engine loan_application_agent
"""

from google.adk.agents import LlmAgent

from .instructions import ROOT_INSTRUCTION
from .model_config import get_model
from .sub_agents.greeting_agent import create_greeting_agent
from .sub_agents.identity_agent import create_identity_agent
from .sub_agents.loan_explorer_agent import create_loan_explorer_agent
from .sub_agents.prequalification_agent import create_prequalification_agent
from .tools.common import get_current_time

root_agent = LlmAgent(
    model=get_model(),
    name="loan_application_agent",
    description="Citibank UK Loan Application Agent — routes to specialized sub-agents for greeting, identity check, loan exploration, and pre-qualification",
    instruction=ROOT_INSTRUCTION,
    tools=[get_current_time],
    sub_agents=[
        create_greeting_agent(),
        create_identity_agent(),
        create_loan_explorer_agent(),
        create_prequalification_agent(),
    ],
)
