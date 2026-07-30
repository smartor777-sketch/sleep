from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import SecretStr


class Settings(BaseSettings):
    """Настройки LLM Service"""

    # Gonka Proxy (OpenAI-compatible)
    gonka_base_url: str = "https://proxy.gonka.gg/v1"
    gonka_api_key: SecretStr
    gonka_model: str = "moonshotai/Kimi-K2.6"
    
    # CometAPI fallback (optional)
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
