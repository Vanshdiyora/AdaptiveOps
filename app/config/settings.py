from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):

    app_name: str = "AdaptiveOps"

    # ============================================================
    # Repository
    # ============================================================

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
        ".turbo",
        ".nuxt",
        "out",
    ]

    repository_max_files: int = 200

    repository_max_search_results: int = 50

    repository_max_file_size_kb: int = 256

    repository_call_graph_depth: int = 2

    repository_max_context_files: int = 10

    repository_max_context_symbols: int = 20

    repository_max_lines_per_symbol: int = 150

    # ============================================================
    # Semantic Search
    # ============================================================

    repository_enable_semantic_search: bool = True

    repository_embedding_model: str = (
        "sentence-transformers/all-mpnet-base-v2"
    )

    repository_embedding_dimension: int = 768

    repository_chunk_lines: int = 250

    repository_chunk_overlap: int = 40

    repository_semantic_top_k: int = 20

    repository_embedding_batch_size: int = 16

    repository_embedding_max_seq_length: int = 2048

    # ============================================================
    # Local Qdrant
    # ============================================================

    qdrant_mode: str = "local"

    qdrant_path: str = "./qdrant_data"

    qdrant_collection: str = "adaptiveops_code"

    qdrant_timeout: int = 200

    # ============================================================
    # Observability
    # ============================================================

    observability_mode: str = "mock"

    observation_window_minutes: int = 10

    # ============================================================
    # Azure
    # ============================================================

    azure_application_insights_resource_id: str | None = None

    azure_tenant_id: str | None = None

    azure_client_id: str | None = None

    azure_client_secret: str | None = None

    # ============================================================
    # MAQ
    # ============================================================

    maq_api_key: str | None = Field(
        default=None,
        validation_alias="MAQ_API_KEY",
    )

    maq_base_url: str = (
        "https://llm.maqsoftware.net/v1"
    )

    maq_model: str = "muse-glimmer-30b"

    maq_temperature: float = 0.0

    # ============================================================
    # Settings
    # ============================================================

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
