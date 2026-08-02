from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import SecretStr


class Settings(BaseSettings):
    """Настройки LLM Service"""

    # Google Gemini (free tier). Fallback-цепочка моделей: при недоступности
    # первичной модели пробуем следующие по порядку.
    gemini_api_key: SecretStr | None = None
    gemini_base_url: str = "https://generativelanguage.googleapis.com"
    gemini_model: str = "gemini-3.5-flash-lite"
    gemini_fallback_models: list[str] = ["gemini-3.6-flash", "gemini-3.5-flash"]

    # Mistral AI fallback (optional, OpenAI-compatible)
    mistral_api_key: SecretStr | None = None
    mistral_base_url: str = "https://api.mistral.ai/v1"
    mistral_model: str = "mistral-large-latest"

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
