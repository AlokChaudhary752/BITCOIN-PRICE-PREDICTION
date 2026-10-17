"""
Application Configuration Settings.
Loads environment variables and sets production defaults.
"""
from pathlib import Path
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    APP_NAME: str = "BTC Oracle API"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = False

    # Database: clean forward-slash path for SQLite on Windows
    DATABASE_URL: str = "sqlite+aiosqlite:///./btc_oracle.db"

    # Security & JWT
    JWT_SECRET: str = "oracle-super-secret-key-change-in-production-institutional-grade"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]

    # Rate limiting
    RATE_LIMIT_PER_MINUTE: int = 60

    model_config = SettingsConfigDict(env_file=".env", extra="allow")


settings = Settings()
