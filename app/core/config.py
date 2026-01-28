"""
Core module - Configuration and settings management
"""
import os
from typing import List

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings from environment variables"""

    # Application
    APP_NAME: str = "tagihan-wifi-api"
    APP_VERSION: str = "1.0.0"
    APP_ENV: str = os.getenv("APP_ENV", "development")
    APP_DEBUG: bool = os.getenv("APP_DEBUG", "False").lower() == "true"
    APP_HOST: str = os.getenv("APP_HOST", "127.0.0.1")
    APP_PORT: int = int(os.getenv("APP_PORT", "8000"))

    # API
    API_V1_STR: str = "/api/v1"

    # Database
    DATABASE_PATH: str = os.getenv("DATABASE_PATH", "./tagihan-wifi.db")
    DB_THREADS: int = int(os.getenv("DB_THREADS", "4"))
    DB_MEMORY_LIMIT: str = os.getenv("DB_MEMORY_LIMIT", "2GB")
    DB_MAX_MEMORY: str = os.getenv("DB_MAX_MEMORY", "4GB")

    # Authentication
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = int(os.getenv("JWT_REFRESH_TOKEN_EXPIRE_DAYS", "7"))

    # Sqids
    SQIDS_ALPHABET: str = os.getenv(
        "SQIDS_ALPHABET",
        "QnUpaur6msw2E9zF4lMvAhfbtBDS0R1NoVdxXT3qWyOkZjYPig8JK7GCIeLcH5"
    )

    # CORS
    CORS_ORIGINS: List[str] = ["*"]

    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"  # Ignore extra fields


settings = Settings()
