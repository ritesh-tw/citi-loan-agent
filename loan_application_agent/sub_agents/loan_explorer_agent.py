"""Loan Exploration Sub-Agent — Stage 3.

Helps users explore available loan products, compare options,
and understand rates, terms, and eligibility criteria.
"""

from google.adk.agents import LlmAgent

from ..instructions import LOAN_EXPLORER_INSTRUCTION
from ..model_config import get_model
from ..tools.loan_products import get_loan_products, get_product_details


def create_loan_explorer_agent() -> LlmAgent:
    """Create the loan exploration sub-agent."""
    return LlmAgent(
        model=get_model(),
        name="loan_explorer_agent",
        description=(
            "ONLY explains loan product information — rates, terms, features, and eligibility criteria. "
            "Do NOT route here for 'apply', 'check eligibility', or 'get a quote' — those go to prequalification_agent. "
            "Route here ONLY when user asks 'what loans do you offer', 'tell me about personal loan', or 'compare loans'."
        ),
        instruction=LOAN_EXPLORER_INSTRUCTION,
        tools=[get_loan_products, get_product_details],
    )
