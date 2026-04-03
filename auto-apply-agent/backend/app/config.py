"""
Application configuration and settings.
Loads environment variables and provides typed configuration access.
"""

from pydantic_settings import BaseSettings
from pydantic import Field
from typing import List, Optional
import os


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Application
    APP_NAME: str = "AutoApply Agent"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"

    # Database
    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://autoapply:securepassword123@localhost:5432/autoapply_db",
        description="PostgreSQL connection URL"
    )

    # Redis
    REDIS_URL: str = Field(
        default="redis://localhost:6379/0",
        description="Redis connection URL for Celery"
    )

    # JWT Authentication
    JWT_SECRET_KEY: str = Field(
        default="super-secret-key-change-in-production",
        description="Secret key for JWT token encoding"
    )
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # AI Providers
    GROQ_API_KEY: Optional[str] = None
    OPENROUTER_API_KEY: Optional[str] = None
    HUGGINGFACE_TOKEN: Optional[str] = None

    # AI Model Configuration
    PRIMARY_MODEL: str = "llama-3.1-70b-versatile"
    FALLBACK_MODEL_1: str = "mistral-large"
    FALLBACK_MODEL_2: str = "meta-llama/Meta-Llama-3-8B-Instruct"
    MAX_RETRY_ATTEMPTS: int = 3

    # Job APIs
    ADZUNA_APP_ID: Optional[str] = None
    ADZUNA_API_KEY: Optional[str] = None
    JOBBLE_API_KEY: Optional[str] = None

    # Browser Automation
    BROWSERLESS_URL: str = Field(
        default="http://localhost:3000",
        description="Browserless.io or local browserless instance URL"
    )
    PLAYWRIGHT_TIMEOUT: int = 30000  # milliseconds

    # Email Configuration
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    EMAIL_FROM_NAME: str = "AutoApply Agent"

    # Application Limits
    MAX_DAILY_APPLICATIONS: int = 20
    MIN_MATCH_SCORE: float = 0.6
    AUTO_APPROVE_HIGH_MATCH: bool = True
    REQUEST_TIMEOUT: int = 60

    # CORS
    FRONTEND_URL: str = "http://localhost:3000"
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]

    # File Storage
    RESUMES_DIR: str = "/app/resumes"
    CONTEXT_DIR: str = "/app/context"
    SCREENSHOTS_DIR: str = "/app/screenshots"

    # Monitoring
    SENTRY_DSN: Optional[str] = None
    PROMETHEUS_ENABLED: bool = False

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """Get the global settings instance."""
    return settings
