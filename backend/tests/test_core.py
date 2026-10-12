from app.core.config import Settings
from app.core.ratelimit import RateLimiter


def test_db_url_se_normaliza_a_psycopg():
    assert (
        Settings(database_url="postgres://u:p@h/db", jwt_secret="x" * 40).database_url
        == "postgresql+psycopg://u:p@h/db"
    )
    assert (
        Settings(database_url="postgresql://u:p@h/db", jwt_secret="x" * 40).database_url
        == "postgresql+psycopg://u:p@h/db"
    )
    assert (
        Settings(database_url="postgresql+psycopg://u:p@h/db", jwt_secret="x" * 40).database_url
        == "postgresql+psycopg://u:p@h/db"
    )


def test_cors_origin_list():
    settings = Settings(
        jwt_secret="x" * 40,
        cors_origins="https://a.com, https://b.com ,",
    )
    assert settings.cors_origin_list == ["https://a.com", "https://b.com"]


def test_rate_limiter_permite_y_bloquea():
    limiter = RateLimiter(max_requests=2, window_seconds=1000)
    assert limiter.allow("user") is True
    assert limiter.allow("user") is True
    assert limiter.allow("user") is False
    assert limiter.allow("otro") is True
