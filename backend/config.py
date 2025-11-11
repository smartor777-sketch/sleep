"""Конфигурация Backend"""

import json
from typing import Annotated

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import SecretStr, PostgresDsn, BeforeValidator


def _parse_cors_origins(value):
    """Поддержка строковых значений для CORS_ORIGINS"""
    if isinstance(value, str):
        value = value.strip()
        if not value:
            return []
        if value.startswith("["):
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                pass
        return [origin.strip() for origin in value.split(",") if origin.strip()]
    return value


CorsOrigins = Annotated[list[str], BeforeValidator(_parse_cors_origins)]


class Settings(BaseSettings):
    """Настройки Backend приложения"""
    
    # Database
    database_url: PostgresDsn
    
    # Redis
    redis_url: str = "redis://redis:6379/0"
    
    # JWT
    jwt_secret_key: SecretStr
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 30
    jwt_refresh_token_expire_days: int = 7
    
    # OAuth2 - Google
    google_client_id: str | None = None
    google_client_secret: SecretStr | None = None
    google_redirect_uri: str | None = None
    
    # OAuth2 - Apple
    apple_client_id: str | None = None
    apple_team_id: str | None = None
    apple_key_id: str | None = None
    apple_private_key: str | None = None
    
    # Email (SMTP)
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_user: str | None = None
    smtp_password: SecretStr | None = None
    smtp_from: str | None = None
    
    # S3/MinIO
    s3_endpoint: str = "http://minio:9000"
    s3_access_key: str = "minioadmin"
    s3_secret_key: SecretStr = SecretStr("minioadmin")
    s3_bucket: str = "jungai-covers"
    s3_region: str = "us-east-1"
    s3_use_ssl: bool = False
    
    # LLM Service
    llm_service_url: str = "http://llm_service:8001"
    
    # Google Speech-to-Text
    google_application_credentials: str | None = None
    
    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    
    # Logging
    log_level: str = "INFO"
    
    # CORS
    cors_origins: CorsOrigins = ["*"]
    
    # Лимиты
    dreams_per_day_limit: int = 5
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False
    )


settings = Settings()

