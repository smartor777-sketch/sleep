from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import SecretStr


class Settings(BaseSettings):
    """Настройки LLM Service"""
    
    # Yandex Cloud
    yandex_folder_id: str
    yandex_api_key: SecretStr
    
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

