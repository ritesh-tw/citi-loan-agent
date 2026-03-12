"""Deploy Loan Application Agent to Vertex AI Agent Engine.

This script UPDATES the existing Agent Engine instance (rather than creating
a new one each time).  The target engine is read from AGENT_ENGINE_ID in
loan_application_agent/.env.gcp.

Usage:
    python deploy/vertex_deploy_sdk.py          # update existing engine
    python deploy/vertex_deploy_sdk.py --create  # create a brand-new engine

Environment:
    Loads from loan_application_agent/.env.gcp by default.
    Can be overridden via environment variables.
"""

import os
import sys

# Resolve project root (no '..' in paths — required for Agent Engine tar packaging)
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, PROJECT_ROOT)

# Load GCP environment from .env.gcp
from dotenv import load_dotenv

env_gcp_path = os.path.join(PROJECT_ROOT, "loan_application_agent", ".env.gcp")
load_dotenv(env_gcp_path)

import vertexai
from vertexai.preview import reasoning_engines

PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT", "cs-host-d29276312550417ca85da7")
LOCATION = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")
STAGING_BUCKET = os.getenv("STAGING_BUCKET", "gs://loan-agent-staging-cs")
AGENT_ENGINE_ID = os.getenv("AGENT_ENGINE_ID", "5798796837099929600")
CLOUD_SQL_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://finagent:LoanAgent2024!@10.21.0.3:5432/loan_agent",
)

REQUIREMENTS = [
    "google-adk>=1.0.0",
    "litellm>=1.40.0",
    "psycopg2-binary>=2.9.0",
    "python-dotenv>=1.0.0",
    "google-cloud-aiplatform[adk]>=1.76.0",
    "httpx>=0.27.0",
]


def _build_app():
    """Build the ADK App for Vertex AI."""
    # Ensure env vars are set before importing the agent
    os.environ["DATABASE_URL"] = CLOUD_SQL_URL

    from loan_application_agent.agent import root_agent

    print("Creating ADK App for Vertex AI...")
    return reasoning_engines.AdkApp(
        agent=root_agent,
        enable_tracing=True,
    )


def _test_locally(app):
    """Quick local smoke test."""
    print("Testing agent locally...")
    test_session = app.create_session(user_id="test-deploy")
    session_id = test_session.id if hasattr(test_session, "id") else test_session["id"]
    response = app.stream_query(
        user_id="test-deploy",
        session_id=session_id,
        message="Hello",
    )
    for event in response:
        if hasattr(event, "content") and event.content:
            print(f"  Agent responded: {str(event.content)[:100]}...")
            break
    print("Local test passed!\n")


def update():
    """Update the existing Agent Engine instance with new code."""
    print(f"Project:      {PROJECT_ID}")
    print(f"Location:     {LOCATION}")
    print(f"Bucket:       {STAGING_BUCKET}")
    print(f"Engine ID:    {AGENT_ENGINE_ID}")
    print(f"Model:        {os.getenv('LLM_MODEL', 'NOT SET')}")
    print()

    vertexai.init(
        project=PROJECT_ID,
        location=LOCATION,
        staging_bucket=STAGING_BUCKET,
    )

    app = _build_app()
    _test_locally(app)

    # Get reference to the existing engine
    resource_name = f"projects/{PROJECT_ID}/locations/{LOCATION}/reasoningEngines/{AGENT_ENGINE_ID}"
    print(f"Fetching existing engine: {resource_name}")
    remote_agent = reasoning_engines.ReasoningEngine(resource_name)

    # Use absolute path (no '..') so tar doesn't reject the archive
    loan_agent_pkg = os.path.join(PROJECT_ROOT, "loan_application_agent")

    print("Updating Agent Engine...")
    print("(This may take 5-10 minutes)")
    remote_agent.update(
        reasoning_engine=app,
        requirements=REQUIREMENTS,
        extra_packages=[loan_agent_pkg],
    )

    print()
    print("=== Update Successful! ===")
    print(f"Resource Name: {remote_agent.resource_name}")
    print()
    print("View in GCP Console:")
    print(f"  https://console.cloud.google.com/vertex-ai/agents/agent-engines/locations/{LOCATION}/agent-engines/{AGENT_ENGINE_ID}?project={PROJECT_ID}")

    return remote_agent


def create():
    """Create a brand-new Agent Engine instance."""
    print(f"Project:  {PROJECT_ID}")
    print(f"Location: {LOCATION}")
    print(f"Bucket:   {STAGING_BUCKET}")
    print(f"Model:    {os.getenv('LLM_MODEL', 'NOT SET')}")
    print()

    vertexai.init(
        project=PROJECT_ID,
        location=LOCATION,
        staging_bucket=STAGING_BUCKET,
    )

    app = _build_app()
    _test_locally(app)

    loan_agent_pkg = os.path.join(PROJECT_ROOT, "loan_application_agent")

    print("Creating NEW Agent Engine...")
    print("(This may take 5-10 minutes)")
    remote_agent = reasoning_engines.ReasoningEngine.create(
        reasoning_engine=app,
        display_name="Citi Loan Application Agent",
        description="Citibank UK Loan Application Agent - 4-stage workflow with identity verification, loan exploration, and pre-qualification",
        requirements=REQUIREMENTS,
        extra_packages=[loan_agent_pkg],
    )

    print()
    print("=== Creation Successful! ===")
    print(f"Resource Name: {remote_agent.resource_name}")
    print(f"Engine ID: {remote_agent.resource_name.split('/')[-1]}")
    print()
    print("IMPORTANT: Update AGENT_ENGINE_ID in .env.gcp and redeploy Cloud Run backend!")

    return remote_agent


if __name__ == "__main__":
    if "--create" in sys.argv:
        create()
    else:
        update()
