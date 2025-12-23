import json
from pathlib import Path

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Google OAuth Configuration
    google_client_id: str
    google_client_secret: str
    google_redirect_uri: str = "http://localhost:8000/auth/callback"

    # Database Configuration
    database_url: str

    # Security
    secret_key: str
    encryption_key: str

    # Redis/Celery Configuration
    redis_url: str = "redis://localhost:6379/0"

    # Frontend URL (for OAuth redirects)
    frontend_url: str = "http://localhost:3000"

    # CORS Configuration
    cors_origins: list[str] = ["http://localhost:3000", "http://localhost:5173"]

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        """Parse CORS origins from string (JSON array or comma-separated) or list."""
        if isinstance(v, list):
            return v
        if isinstance(v, str):
            v = v.strip()
            if v.startswith("["):
                return json.loads(v)
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v

    # Rate Limiting Configuration
    rate_limit_requests: int = 100
    rate_limit_period: int = 60  # seconds

    # Application Settings
    environment: str = "development"
    log_level: str = "INFO"

    # Rate limiting (per user)
    email_scan_rate_limit: int = 5
    email_scan_rate_window_seconds: int = 60 * 60  # 1 hour
    response_scan_rate_limit: int = 5
    response_scan_rate_window_seconds: int = 60 * 60
    task_trigger_rate_limit: int = 8
    task_trigger_rate_window_seconds: int = 60 * 60

    # Gemini AI configuration
    gemini_timeout_seconds: int = 20

    model_config = SettingsConfigDict(
        env_file=[
            Path(__file__).resolve().parents[2] / ".env",
            ".env",
        ],
        case_sensitive=False,
        extra="ignore",
    )

    @property
    def is_production(self) -> bool:
        return self.environment == "production"


settings = Settings()
