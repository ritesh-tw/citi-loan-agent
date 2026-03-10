"""Server configuration using Pydantic BaseSettings."""

from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Server settings loaded from environment variables."""

    # Auth
    api_bearer_token: str = ""

    # Server
    host: str = "0.0.0.0"
    port: int = 8000

    # Tracing
    enable_cloud_trace: bool = False

    # GCP
    google_cloud_project: str = ""
    google_cloud_location: str = "us-central1"

    model_config = {"env_file": "loan_application_agent/.env", "extra": "ignore"}


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
