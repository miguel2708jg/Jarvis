from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # AWS / Bedrock
    aws_region: str = Field(default="us-east-1", alias="AWS_REGION")
    aws_access_key_id: str | None = Field(default=None, alias="AWS_ACCESS_KEY_ID")
    aws_secret_access_key: str | None = Field(default=None, alias="AWS_SECRET_ACCESS_KEY")
    bedrock_model_id: str = Field(
        default="us.anthropic.claude-sonnet-4-5",
        alias="BEDROCK_MODEL_ID",
    )

    # Storage
    data_dir: str = Field(default="data", alias="DATA_DIR")

    # Gmail (Phase 2)
    gmail_credentials_file: str | None = Field(default=None, alias="GMAIL_CREDENTIALS_FILE")
    gmail_token_file: str | None = Field(default=None, alias="GMAIL_TOKEN_FILE")

    # API
    api_host: str = Field(default="0.0.0.0", alias="API_HOST")
    api_port: int = Field(default=8000, alias="API_PORT")
    cors_origins: list[str] = Field(default=["*"], alias="CORS_ORIGINS")


settings = Settings()
