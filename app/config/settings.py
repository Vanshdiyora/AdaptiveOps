from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):

    app_name: str = "AdaptiveOps"

    # mock / azure
    observability_mode: str = "mock"

    # Azure
    azure_application_insights_resource_id: str | None = None

    # Optional explicit credentials.
    # DefaultAzureCredential will be preferred.
    azure_tenant_id: str | None = None
    azure_client_id: str | None = None
    azure_client_secret: str | None = None

    observation_window_minutes: int = 10

    groq_api_key: str | None = None
    groq_model: str = "qwen/qwen3.6-27b"
    groq_temperature: float = 0.0

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()