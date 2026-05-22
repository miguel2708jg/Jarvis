from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import AliasChoices, Field


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
    object_storage_provider: str = Field(default="local", alias="OBJECT_STORAGE_PROVIDER")
    s3_bucket: str | None = Field(default=None, validation_alias=AliasChoices("S3_BUCKET", "BUCKET"))
    s3_endpoint: str | None = Field(default=None, validation_alias=AliasChoices("S3_ENDPOINT", "ENDPOINT"))
    s3_region: str = Field(default="auto", validation_alias=AliasChoices("S3_REGION", "REGION"))
    s3_access_key_id: str | None = Field(default=None, validation_alias=AliasChoices("S3_ACCESS_KEY_ID", "ACCESS_KEY_ID"))
    s3_secret_access_key: str | None = Field(
        default=None,
        validation_alias=AliasChoices("S3_SECRET_ACCESS_KEY", "SECRET_ACCESS_KEY"),
    )
    assistant_timezone: str | None = Field(default=None, alias="ASSISTANT_TIMEZONE")

    # Voice I/O
    stt_provider: str = Field(default="groq", alias="STT_PROVIDER")
    tts_provider: str = Field(default="piper", alias="TTS_PROVIDER")
    groq_api_key: str | None = Field(default=None, alias="GROQ_API_KEY")
    groq_stt_model: str = Field(default="whisper-large-v3", alias="GROQ_STT_MODEL")
    groq_stt_language: str | None = Field(default=None, alias="GROQ_STT_LANGUAGE")
    ffmpeg_path: str = Field(default="ffmpeg", alias="FFMPEG_PATH")
    tts_voice: str = Field(default="en_US-lessac-medium", alias="TTS_VOICE")
    piper_model_path: str | None = Field(default=None, alias="PIPER_MODEL_PATH")
    piper_config_path: str | None = Field(default=None, alias="PIPER_CONFIG_PATH")

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
