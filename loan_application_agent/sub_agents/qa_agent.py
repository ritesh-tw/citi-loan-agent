"""General Q&A Sub-Agent.

Handles general questions and document-based Q&A. If Google Drive/Docs/Sheets
credentials are configured, this agent can search and read documents to provide
informed, sourced answers.
"""

from google.adk.agents import LlmAgent

from ..instructions import QA_INSTRUCTION
from ..model_config import get_model
from ..tools.registry import get_qa_tools


def create_qa_agent() -> LlmAgent:
    """Create the Q&A sub-agent with conditionally registered tools."""
    return LlmAgent(
        model=get_model(),
        name="qa_agent",
        description=(
            "Answers general questions about banking, policies, and procedures. "
            "Can search and read Google Drive, Docs, and Sheets if configured. "
            "Route here for knowledge-based queries and document searches."
        ),
        instruction=QA_INSTRUCTION,
        tools=get_qa_tools(),
    )
