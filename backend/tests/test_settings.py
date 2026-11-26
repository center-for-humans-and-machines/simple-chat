import pytest
from pydantic import ValidationError
from src.models.settings import Settings

REQUIRED_ENV = {
    "MONGO_URL": "mongodb://db:27017",
    "DATABASE_NAME": "chatbot",
    "S3_ENDPOINT": "http://localhost:9000",
    "S3_ACCESS_KEY": "access",
    "S3_SECRET_KEY": "secret",
    "S3_BUCKET_NAME": "bucket",
    "S3_REGION_NAME": "eu-central-1",
    "OPENAI_DEFAULT_MODEL": "gpt-4o",
    "AZURE_OPENAI_API_KEY": "azure-key",
    "AZURE_OPENAI_BASE_URL": "https://azure.example.com",
    "OPENAI_API_KEY": "openai-key",
    "OPENAI_BASE_URL": "https://openai.example.com",
    "TOGETHER_AI_KEY": "together-key",
    "TOGETHER_AI_URL": "https://together.example.com",
}

OPTIONAL_ENV = [
    "AZURE_OPENAI_API_VERSION",
    "AZURE_OPENAI_DEPLOYMENTS",
    "OPENAI_REASONING_EFFORT",
    "TOGETHER_AI_REASONING_EFFORT",
    "SENTRY_ENABLED",
    "SENTRY_DSN",
    "LANGFUSE_ENABLED",
    "LANGFUSE_PUBLIC_KEY",
    "LANGFUSE_SECRET_KEY",
    "LANGFUSE_HOST",
]


@pytest.fixture
def env(monkeypatch: pytest.MonkeyPatch) -> pytest.MonkeyPatch:
    """Set only the required variables, so no value leaks in from the test setup."""
    for name, value in REQUIRED_ENV.items():
        monkeypatch.setenv(name, value)
    for name in OPTIONAL_ENV:
        monkeypatch.delenv(name, raising=False)
    return monkeypatch


def test_reads_each_field_from_its_upper_case_variable(env: pytest.MonkeyPatch) -> None:
    settings = Settings()

    for name, value in REQUIRED_ENV.items():
        assert getattr(settings, name.lower()) == value


def test_optional_fields_default_when_unset(env: pytest.MonkeyPatch) -> None:
    settings = Settings()

    assert settings.azure_openai_api_version == "2024-02-01"
    assert settings.azure_openai_deployments == {}
    assert settings.openai_reasoning_effort is None
    assert settings.together_ai_reasoning_effort is None
    assert settings.sentry_enabled is False
    assert settings.sentry_dsn is None
    assert settings.langfuse_enabled is False
    assert settings.langfuse_public_key is None
    assert settings.langfuse_secret_key is None
    assert settings.langfuse_host == "https://cloud.langfuse.com"


def test_parses_optional_values(env: pytest.MonkeyPatch) -> None:
    env.setenv("AZURE_OPENAI_DEPLOYMENTS", '{"gpt-5.1": "my-deployment"}')
    env.setenv("SENTRY_ENABLED", "true")
    env.setenv("SENTRY_DSN", "https://key@example.ingest.sentry.io/1")

    settings = Settings()

    assert settings.azure_openai_deployments == {"gpt-5.1": "my-deployment"}
    assert settings.sentry_enabled is True
    assert settings.sentry_dsn == "https://key@example.ingest.sentry.io/1"


def test_missing_required_variable_fails(env: pytest.MonkeyPatch) -> None:
    env.delenv("MONGO_URL")

    with pytest.raises(ValidationError, match="mongo_url"):
        Settings()
