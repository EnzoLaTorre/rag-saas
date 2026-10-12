from starlette.background import BackgroundTasks

from app.core.config import settings
from app.services import tasks


def test_enqueue_ingest_usa_background_sin_redis(monkeypatch):
    monkeypatch.setattr(settings, "redis_url", "")
    background = BackgroundTasks()

    tasks.enqueue_ingest(background, 42)

    assert len(background.tasks) == 1
    assert background.tasks[0].func is tasks.ingest_document
    assert background.tasks[0].args == (42,)


def test_enqueue_ingest_encola_en_rq_con_redis(monkeypatch):
    monkeypatch.setattr(settings, "redis_url", "redis://localhost:6379/0")
    captured = {}

    class FakeQueue:
        def __init__(self, name, connection):
            captured["name"] = name

        def enqueue(self, func, *args):
            captured["func"] = func
            captured["args"] = args

    monkeypatch.setattr("rq.Queue", FakeQueue)
    background = BackgroundTasks()

    tasks.enqueue_ingest(background, 7)

    assert captured["name"] == "ingest"
    assert captured["func"] == "app.services.tasks.ingest_document"
    assert captured["args"] == (7,)
    assert len(background.tasks) == 0
