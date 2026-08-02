from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import SecretStr


class Settings(BaseSettings):
    """Настройки LLM Service"""

    # Google Gemini (free tier). Fallback-цепочка моделей: при недоступности
    # первичной модели пробуем следующие по порядку.
    gemini_api_key: SecretStr | None = None
    gemini_base_url: str = "https://generativelanguage.googleapis.com"
    gemini_model: str = "gemini-3.6-flash"
    gemini_fallback_models: list[str] = ["gemini-3.5-flash", "gemini-3.5-flash-lite"]

    # CometAPI fallback (optional, OpenAI-compatible)
    comet_api_key: SecretStr | None = None
    comet_base_url: str = "https://api.cometapi.com/v1"
    comet_model: str = "gpt-5.1"

    # Server
    host: str = "0.0.0.0"
    port: int = 8001
    
    # Logging
    log_level: str = "INFO"
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False
    )


settings = Settings()
