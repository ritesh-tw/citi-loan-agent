"""Deploy Loan Application Agent to Vertex AI Agent Engine.

This script registers the agent with Vertex AI for monitoring, tracing,
and management. The actual agent execution happens on Cloud Run (which has
VPC access to Cloud SQL).

Usage:
    python deploy/vertex_deploy_sdk.py

Environment:
    GOOGLE_CLOUD_PROJECT: GCP project ID
    GOOGLE_CLOUD_LOCATION: Region (default: us-central1)
    STAGING_BUCKET: GCS bucket for staging (default: gs://loan-agent-staging-cs)
"""

import os
import sys

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import vertexai
from vertexai.preview import reasoning_engines

PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT", "cs-host-d29276312550417ca85da7")
LOCATION = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")
STAGING_BUCKET = os.getenv("STAGING_BUCKET", "gs://loan-agent-staging-cs")

# Cloud SQL connection for the deployed agent
CLOUD_SQL_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://finagent:LoanAgent2024!@10.21.0.3:5432/loan_agent"
)


def deploy():
    """Deploy agent to Vertex AI Agent Engine."""
    print(f"Project:  {PROJECT_ID}")
    print(f"Location: {LOCATION}")
    print(f"Bucket:   {STAGING_BUCKET}")
    print()

    vertexai.init(
        project=PROJECT_ID,
        location=LOCATION,
        staging_bucket=STAGING_BUCKET,
    )

    # Import agent here so env vars are set first
    os.environ["DATABASE_URL"] = CLOUD_SQL_URL
    os.environ.setdefault("LLM_GATEWAY_BASE_URL", "https://aigw.tw-forge.trustwise.ai")
    os.environ.setdefault("LLM_GATEWAY_API_KEY", "sk-NebaTwT-LDV8MGphvjlD9w")
    os.environ.setdefault("LLM_MODEL", "gpt-4o-mini")

    from loan_application_agent.agent import root_agent

    print("Creating ADK App for Vertex AI...")
    app = reasoning_engines.AdkApp(
        agent=root_agent,
        enable_tracing=True,
    )

    # Test locally first
    print("Testing agent locally...")
    test_session = app.create_session(user_id="test-deploy")
    response = app.stream_query(
        user_id="test-deploy",
        session_id=test_session["id"],
        message="Hello",
    )
    for event in response:
        if hasattr(event, "content") and event.content:
            print(f"  Agent responded: {str(event.content)[:100]}...")
            break
    print("Local test passed!")
    print()

    # Deploy to Vertex AI
    print("Deploying to Vertex AI Agent Engine...")
    print("(This may take 5-10 minutes)")
    remote_agent = reasoning_engines.ReasoningEngine.create(
        reasoning_engine=app,
        display_name="Citi Loan Application Agent",
        description="Citibank UK Loan Application Agent - 4-stage workflow with identity verification, loan exploration, and pre-qualification",
        requirements=[
            "google-adk>=1.0.0",
            "litellm>=1.40.0",
            "psycopg2-binary>=2.9.0",
            "python-dotenv>=1.0.0",
            "google-cloud-aiplatform[adk]>=1.76.0",
        ],
        env_vars={
            "DATABASE_URL": CLOUD_SQL_URL,
            "LLM_GATEWAY_BASE_URL": "https://aigw.tw-forge.trustwise.ai",
            "LLM_GATEWAY_API_KEY": "sk-NebaTwT-LDV8MGphvjlD9w",
            "LLM_MODEL": "gpt-4o-mini",
            "ENABLE_CLOUD_TRACE": "true",
        },
    )

    print()
    print("=== Deployment Successful! ===")
    print(f"Resource Name: {remote_agent.resource_name}")
    print()
    print("View in GCP Console:")
    print(f"  https://console.cloud.google.com/vertex-ai/reasoning-engines?project={PROJECT_ID}")
    print()
    print("Monitoring Dashboard:")
    print(f"  https://console.cloud.google.com/traces?project={PROJECT_ID}")

    return remote_agent


if __name__ == "__main__":
    deploy()
