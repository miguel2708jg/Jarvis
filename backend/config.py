from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Ollama
    llm_provider: str = Field(default="ollama", alias="LLM_PROVIDER")
    ollama_base_url: str = Field(default="http://localhost:11434", alias="OLLAMA_BASE_URL")
    ollama_model_id: str = Field(default="qwen3", alias="OLLAMA_MODEL_ID")
    ollama_api_key: str | None = Field(default=None, alias="OLLAMA_API_KEY")
    ollama_temperature: float = Field(default=0, alias="OLLAMA_TEMPERATURE")

    # Storage
    data_dir: str = Field(default="Data", alias="DATA_DIR")
    database_path: str | None = Field(default=None, alias="DATABASE_PATH")
    database_url: str | None = Field(default=None, alias="DATABASE_URL")
    knowledge_vault_path: str = Field(default="Data/knowledge_vault", alias="KNOWLEDGE_VAULT_PATH")
    assistant_timezone: str | None = Field(default=None, alias="ASSISTANT_TIMEZONE")

    # Gmail (Phase 2)
    gmail_credentials_file: str | None = Field(default=None, alias="GMAIL_CREDENTIALS_FILE")
    gmail_token_file: str | None = Field(default=None, alias="GMAIL_TOKEN_FILE")

    # Legacy Google Calendar setting (unused; calendar events are local SQLite)
    gcal_token_file: str | None = Field(default=None, alias="GCAL_TOKEN_FILE")

    # API
    api_host: str = Field(default="0.0.0.0", alias="API_HOST")
    api_port: int = Field(default=8000, alias="API_PORT")
    cors_origins: list[str] = Field(default=["*"], alias="CORS_ORIGINS")


settings = Settings()
