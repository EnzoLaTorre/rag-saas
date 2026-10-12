import json

from conftest import FakeProvider

from app.core.config import settings
from app.models import Chunk
from app.services import rag


def _chunk(**overrides) -> Chunk:
    data = {
        "id": 1,
        "tenant_id": 1,
        "document_id": 10,
        "chunk_index": 0,
        "text": "El gato duerme en el sofá.",
        "embedding": [0.0] * settings.embedding_dim,
    }
    data.update(overrides)
    return Chunk(**data)


def test_answer_stream_emite_sources_tokens_y_done(monkeypatch):
    monkeypatch.setattr(rag, "get_provider", lambda: FakeProvider())
    monkeypatch.setattr(rag.vectorstore, "search", lambda *a, **k: [_chunk()])

    events = [json.loads(e) for e in rag.answer_stream(None, 1, "¿Dónde duerme?")]

    assert [e["type"] for e in events] == ["sources", "token", "token", "done"]
    assert events[0]["sources"][0]["document_id"] == 10
    assert events[0]["sources"][0]["text"] == "El gato duerme en el sofá."
    assert events[-1]["answer"] == "Hola mundo"


def test_answer_stream_sin_fuentes(monkeypatch):
    monkeypatch.setattr(rag, "get_provider", lambda: FakeProvider())
    monkeypatch.setattr(rag.vectorstore, "search", lambda *a, **k: [])

    events = [json.loads(e) for e in rag.answer_stream(None, 1, "nada")]

    assert events[0]["sources"] == []
    assert events[-1]["type"] == "done"
