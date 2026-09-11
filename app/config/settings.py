from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):

    app_name: str = "AdaptiveOps"

    repository_path: str | None = None
    repository_ignored_dirs: list[str] = [
        ".git",
        "node_modules",
        "__pycache__",
        ".pytest_cache",
        ".venv",
        "venv",
        "dist",
        "build",
        ".next",
        "coverage",
        "target",
        "vendor",
        ".idea",
        ".vscode",
    ]
    repository_max_files: int = 200
    repository_max_search_results: int = 50
    repository_max_file_size_kb: int = 256

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

    maq_api_key: str | None = Field(
        default=None,
        validation_alias="MAQ_API_KEY",
    )
    maq_base_url: str = "https://llm.maqsoftware.net/v1"
    maq_model: str = "muse-glimmer-30b"
    # maq_model: str = "gemma-4-31b"

    maq_temperature: float = 0.0

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()