from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    app_name: str = "School SaaS Platform"
    debug: bool = True

    # SQLite for local dev (no server needed), PostgreSQL for production
    database_url: str = "sqlite+aiosqlite:///./school_saas.db"

    jwt_secret: str = "CHANGE-THIS-SECRET-IN-PRODUCTION"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    r2_account_id: str = ""
    r2_access_key_id: str = ""
    r2_secret_access_key: str = ""
    r2_bucket_name: str = "school-content"

    cors_origins: List[str] = ["http://localhost:3000", "http://localhost:5173", "http://localhost:8080"]


settings = Settings()
