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
    allow_sqlite_fallback: bool = Field(default=False, alias="ALLOW_SQLITE_FALLBACK")
    knowledge_vault_path: str = Field(default="Data/knowledge_vault", alias="KNOWLEDGE_VAULT_PATH")
    assistant_timezone: str | None = Field(default=None, alias="ASSISTANT_TIMEZONE")

    # Google Workspace OAuth
    google_credentials_file: str | None = Field(default=None, alias="GOOGLE_CREDENTIALS_FILE")
    google_token_file: str | None = Field(default=None, alias="GOOGLE_TOKEN_FILE")
    google_allow_interactive_oauth: bool = Field(default=False, alias="GOOGLE_ALLOW_INTERACTIVE_OAUTH")

    # Gmail MCP (Google Workspace developer preview)
    gmail_credentials_file: str | None = Field(default=None, alias="GMAIL_CREDENTIALS_FILE")
    gmail_token_file: str | None = Field(default=None, alias="GMAIL_TOKEN_FILE")
    gmail_mcp_endpoint: str = Field(
        default="https://gmailmcp.googleapis.com/mcp/v1",
        alias="GMAIL_MCP_ENDPOINT",
    )
    gmail_mcp_timeout_seconds: float = Field(default=30, alias="GMAIL_MCP_TIMEOUT_SECONDS")

    # Legacy Google Calendar setting
    gcal_token_file: str | None = Field(default=None, alias="GCAL_TOKEN_FILE")

    # API
    api_host: str = Field(default="0.0.0.0", alias="API_HOST")
    api_port: int = Field(default=8000, alias="API_PORT")
    cors_origins: list[str] = Field(default=["*"], alias="CORS_ORIGINS")

    # Auth
    auth_allowed_emails: str = Field(default="majg2708@gmail.com", alias="AUTH_ALLOWED_EMAILS")
    backend_internal_auth_token: str | None = Field(default=None, alias="BACKEND_INTERNAL_AUTH_TOKEN")
    backend_auth_token_secret: str | None = Field(default=None, alias="BACKEND_AUTH_TOKEN_SECRET")


settings = Settings()
