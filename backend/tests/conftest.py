import os

import pytest

TEST_DATABASE_URL = os.environ.get("TEST_DATABASE_URL")

os.environ.setdefault("AI_PROVIDER", "ollama")
os.environ.setdefault("JWT_SECRET", "test-secret-con-al-menos-32-caracteres-largo")
os.environ.setdefault("OLLAMA_EMBEDDING_DIM", "8")
os.environ.setdefault("CLOUD_EMBEDDING_DIM", "8")

if TEST_DATABASE_URL:
    os.environ["DATABASE_URL"] = TEST_DATABASE_URL

from app.core.config import settings  # noqa: E402


class FakeProvider:
    """Proveedor determinista para tests: sin red ni claves."""

    embedding_dim = settings.embedding_dim

    def embed(self, texts: list[str]) -> list[list[float]]:
        return [self._vec(text) for text in texts]

    def chat_stream(self, messages, model: str | None = None):
        yield "Hola"
        yield " mundo"

    @staticmethod
    def _vec(text: str) -> list[float]:
        seed = len(text)
        return [float((seed + i) % 7) for i in range(settings.embedding_dim)]


@pytest.fixture
def fake_provider(monkeypatch):
    fake = FakeProvider()
    monkeypatch.setattr("app.services.vectorstore.get_provider", lambda: fake)
    monkeypatch.setattr("app.services.rag.get_provider", lambda: fake)
    return fake


@pytest.fixture(scope="session")
def _db():
    if not TEST_DATABASE_URL:
        pytest.skip("TEST_DATABASE_URL no configurada (requiere Postgres + pgvector)")

    from sqlalchemy import text

    from app.database import engine
    from app.models import SQLModel

    SQLModel.metadata.drop_all(engine)
    with engine.begin() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        conn.execute(text("DROP TYPE IF EXISTS role"))
        conn.execute(text("DROP TYPE IF EXISTS documentstatus"))
    SQLModel.metadata.create_all(engine)
    yield engine
    SQLModel.metadata.drop_all(engine)


@pytest.fixture
def client(_db, fake_provider):
    from fastapi.testclient import TestClient

    from app.main import app

    with TestClient(app) as c:
        yield c
