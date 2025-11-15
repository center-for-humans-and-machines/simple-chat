from typing import Optional

from pydantic import BaseSettings, Field


class Settings(BaseSettings):
    mongo_url: str = Field(..., env="MONGO_URL")
    database_name: str = Field(..., env="DATABASE_NAME")
    experiment_id: list = []
    participant_id: list = []
    s3_endpoint: str = Field(..., env="S3_ENDPOINT")
    s3_access_key: str = Field(..., env="S3_ACCESS_KEY")
    s3_secret_key: str = Field(..., env="S3_SECRET_KEY")
    s3_bucket_name: str = Field(..., env="S3_BUCKET_NAME")
    s3_region_name: str = Field(..., env="S3_REGION_NAME")
    openai_default_model: str = Field(..., env="OPENAI_DEFAULT_MODEL")
    azure_openai_api_key: str = Field(..., env="AZURE_OPENAI_API_KEY")
    azure_openai_base_url: str = Field(..., env="AZURE_OPENAI_BASE_URL")
    openai_api_key: str = Field(..., env="OPENAI_API_KEY")
    openai_base_url: str = Field(..., env="OPENAI_BASE_URL")
    together_ai_key: str = Field(..., env="TOGETHER_AI_KEY")
    together_ai_url: str = Field(..., env="TOGETHER_AI_URL")
    sentry_enabled: bool = Field(
        default=False, env="SENTRY_ENABLED", description="Enable Sentry monitoring"
    )
    sentry_dsn: Optional[str] = Field(
        env="SENTRY_DSN", description="Sentry Data Source Name"
    )
    langfuse_enabled: bool = Field(
        default=False, env="LANGFUSE_ENABLED", description="Enable Langfuse observability"
    )
    langfuse_public_key: Optional[str] = Field(
        env="LANGFUSE_PUBLIC_KEY", description="Langfuse public key"
    )
    langfuse_secret_key: Optional[str] = Field(
        env="LANGFUSE_SECRET_KEY", description="Langfuse secret key"
    )
    langfuse_host: Optional[str] = Field(
        default="https://cloud.langfuse.com", env="LANGFUSE_HOST", description="Langfuse host URL"
    )


def get_settings():
    return Settings()
