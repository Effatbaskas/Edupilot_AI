"""CORS settings and middleware behavior."""

import pytest
from httpx import ASGITransport, AsyncClient
from pydantic import ValidationError

from app.config import Settings


def make_settings(**overrides) -> Settings:
    values = {
        "_env_file": None,
        "DATABASE_URL": "sqlite+aiosqlite:///:memory:",
        "SECRET_KEY": "unit-test-secret-value-long-enough-123456",
        "ENVIRONMENT": "test",
    }
    values.update(overrides)
    return Settings(**values)


def test_comma_separated_cors_origins_are_trimmed_and_normalized() -> None:
    settings = make_settings(
        ENVIRONMENT="production",
        DATABASE_URL="postgresql+asyncpg://localhost/edupilot",
        CORS_ORIGINS=" https://student.example.test/ , https://teacher.example.test ",
    )
    assert settings.cors_origins == [
        "https://student.example.test",
        "https://teacher.example.test",
    ]


def test_cors_origins_are_loaded_from_environment(monkeypatch) -> None:
    monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://localhost/edupilot")
    monkeypatch.setenv("SECRET_KEY", "unit-test-secret-value-long-enough-123456")
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.setenv("CORS_ORIGINS", "https://frontend.example.test, https://admin.example.test")

    settings = Settings(_env_file=None)
    assert settings.cors_origins == [
        "https://frontend.example.test",
        "https://admin.example.test",
    ]


def test_development_defaults_to_localhost_origins() -> None:
    settings = make_settings(ENVIRONMENT="development", CORS_ORIGINS="")
    assert settings.cors_origins == ["http://localhost:5173", "http://localhost:3000"]


def test_production_requires_explicit_cors_origins() -> None:
    with pytest.raises(ValidationError, match="CORS_ORIGINS must be configured in production"):
        make_settings(
            ENVIRONMENT="production",
            DATABASE_URL="postgresql+asyncpg://localhost/edupilot",
            CORS_ORIGINS="",
        )


def test_wildcard_cors_origin_is_rejected() -> None:
    with pytest.raises(ValidationError, match="wildcards are not allowed"):
        make_settings(CORS_ORIGINS="*")


def test_cors_origins_reject_paths_and_credentials() -> None:
    with pytest.raises(ValidationError, match="without paths or credentials"):
        make_settings(CORS_ORIGINS="https://user:pass@example.test/path")


def test_cors_origins_reject_invalid_ports() -> None:
    with pytest.raises(ValidationError, match="invalid origin"):
        make_settings(CORS_ORIGINS="https://frontend.example.test:not-a-port")


@pytest.mark.asyncio
async def test_cors_middleware_allows_configured_origins_only(monkeypatch) -> None:
    import app.main as main

    settings = make_settings(
        ENVIRONMENT="production",
        DATABASE_URL="postgresql+asyncpg://localhost/edupilot",
        CORS_ORIGINS="https://student.example.test,https://teacher.example.test",
    )
    monkeypatch.setattr(main, "settings", settings)
    app = main.create_app()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        allowed = await client.options(
            "/health",
            headers={
                "Origin": "https://student.example.test",
                "Access-Control-Request-Method": "GET",
            },
        )
        denied = await client.options(
            "/health",
            headers={
                "Origin": "https://unlisted.example.test",
                "Access-Control-Request-Method": "GET",
            },
        )

    assert allowed.status_code == 200
    assert allowed.headers["access-control-allow-origin"] == "https://student.example.test"
    assert allowed.headers["access-control-allow-credentials"] == "true"
    assert denied.status_code == 400
    assert "access-control-allow-origin" not in denied.headers
