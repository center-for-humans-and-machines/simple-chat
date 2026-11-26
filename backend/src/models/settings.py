from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Backend settings, read from environment variables.

    Each field reads the environment variable of the same name in upper case,
    e.g. ``mongo_url`` reads ``MONGO_URL``.
    """

    mongo_url: str
    database_name: str
    experiment_id: list = []
    participant_id: list = []
    s3_endpoint: str
    s3_access_key: str
    s3_secret_key: str
    s3_bucket_name: str
    s3_region_name: str
    openai_default_model: str
    azure_openai_api_key: str
    azure_openai_base_url: str
    openai_api_key: str
    openai_base_url: str
    azure_openai_api_version: str = Field(
        default="2024-02-01",
        description=(
            'Azure API version, or "v1" for the /openai/v1/ endpoint '
            "(needed for GPT-5 models)"
        ),
    )
    azure_openai_deployments: dict = Field(
        default_factory=dict,
        description=(
            "JSON map from model name to Azure deployment name, "
            'e.g. {"gpt-5.1-2025-11-13": "my-deployment"}'
        ),
    )
    openai_reasoning_effort: Optional[str] = Field(
        default=None,
        description=(
            "reasoning_effort for reasoning models (e.g. none, low, medium, high); "
            "unset uses the model default"
        ),
    )
    together_ai_reasoning_effort: Optional[str] = Field(
        default=None,
        description=(
            "reasoning_effort for Together AI models; "
            '"none" turns thinking off for hybrid models'
        ),
    )
    together_ai_key: str
    together_ai_url: str
    sentry_enabled: bool = Field(default=False, description="Enable Sentry monitoring")
    sentry_dsn: Optional[str] = Field(default=None, description="Sentry Data Source Name")
    langfuse_enabled: bool = Field(
        default=False, description="Enable Langfuse observability"
    )
    langfuse_public_key: Optional[str] = Field(
        default=None, description="Langfuse public key"
    )
    langfuse_secret_key: Optional[str] = Field(
        default=None, description="Langfuse secret key"
    )
    langfuse_host: Optional[str] = Field(
        default="https://cloud.langfuse.com", description="Langfuse host URL"
    )


def get_settings():
    return Settings()
