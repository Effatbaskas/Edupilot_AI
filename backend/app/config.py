from functools import lru_cache
from typing import List
from urllib.parse import urlsplit

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Database
    DATABASE_URL: str = Field(min_length=1)

    # Security
    SECRET_KEY: str = Field(min_length=32)
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # AI
    GEMINI_API_KEY: str = ""
    # Mock is the safe default; real provider calls require explicit opt-in.
    AI_MODE: str = "mock"
    EMBEDDING_MODEL: str = "models/text-embedding-004"
    LLM_MODEL: str = "gemini-1.5-flash"

    # File Storage
    MAX_FILE_SIZE_MB: int = 10
    UPLOAD_DIR: str = "app/storage/uploads"

    # CORS
    # String avoids pydantic-settings JSON decoding before the comma-list parser.
    CORS_ORIGINS: str = ""

    # App
    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "INFO"

    @field_validator("CORS_ORIGINS")
    @classmethod
    def validate_cors_origins(cls, value: str) -> str:
        origins = [origin.strip() for origin in value.split(",") if origin.strip()]
        if "*" in origins:
            raise ValueError("CORS_ORIGINS must list explicit origins; wildcards are not allowed")

        for origin in origins:
            try:
                parsed = urlsplit(origin)
                parsed.port  # Access validates that any supplied port is numeric and in range.
            except ValueError as exc:
                raise ValueError("CORS_ORIGINS contains an invalid origin") from exc
            if (
                parsed.scheme not in {"http", "https"}
                or not parsed.netloc
                or not parsed.hostname
                or parsed.username is not None
                or parsed.password is not None
                or parsed.path not in {"", "/"}
                or parsed.query
                or parsed.fragment
            ):
                raise ValueError("CORS_ORIGINS entries must be HTTP(S) origins without paths or credentials")

        return ",".join(origins)

    @field_validator("AI_MODE")
    @classmethod
    def validate_ai_mode(cls, value: str) -> str:
        value = value.strip().lower()
        if value not in {"mock", "gemini"}:
            raise ValueError("AI_MODE must be mock or gemini")
        return value

    @field_validator("DATABASE_URL")
    @classmethod
    def validate_database_url(cls, value: str) -> str:
        # The application uses SQLAlchemy's async engine. Restricting the
        # schemes here catches common configuration mistakes without logging
        # the URL (which may contain credentials).
        # Managed PostgreSQL providers (including Render) expose a standard
        # postgresql:// URL. The application uses async SQLAlchemy, so adapt
        # that scheme to its installed asyncpg driver without logging secrets.
        if value.startswith("postgres://"):
            value = "postgresql+asyncpg://" + value[len("postgres://"):]
        elif value.startswith("postgresql://"):
            value = "postgresql+asyncpg://" + value[len("postgresql://"):]
        if not value.startswith(("postgresql+asyncpg://", "sqlite+aiosqlite://")):
            raise ValueError("DATABASE_URL must use postgresql+asyncpg or sqlite+aiosqlite")
        return value

    @field_validator("SECRET_KEY")
    @classmethod
    def validate_secret_key(cls, value: str) -> str:
        normalized = value.strip().lower()
        unsafe_markers = ("your-", "change-me", "example", "placeholder", "replace-me")
        if len(value) < 32 or any(marker in normalized for marker in unsafe_markers):
            raise ValueError("SECRET_KEY must be a configured random value of at least 32 characters")
        return value

    @model_validator(mode="after")
    def validate_production_settings(self):
        if self.is_production and not self.DATABASE_URL.startswith("postgresql+asyncpg://"):
            raise ValueError("Production must use PostgreSQL with asyncpg")
        if self.is_production and not self.CORS_ORIGINS:
            raise ValueError("CORS_ORIGINS must be configured in production")
        return self

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT.lower() == "production"

    @property
    def cors_origins(self) -> List[str]:
        origins = [origin.rstrip("/") for origin in self.CORS_ORIGINS.split(",") if origin]
        if not origins and self.is_development:
            return ["http://localhost:5173", "http://localhost:3000"]
        return origins

    @property
    def is_development(self) -> bool:
        return self.ENVIRONMENT.lower() == "development"

    @property
    def max_file_size_bytes(self) -> int:
        return self.MAX_FILE_SIZE_MB * 1024 * 1024


@lru_cache()
def get_settings() -> Settings:
    return Settings()
