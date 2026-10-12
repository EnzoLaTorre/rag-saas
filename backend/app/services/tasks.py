"""Tareas de ingesta de documentos.

Por defecto corren en segundo plano con ``BackgroundTasks``. Si se define
``REDIS_URL`` se encolan en un worker RQ (``rq worker ingest``), lo que permite
escalar el procesamiento por separado del servidor web.
"""

from fastapi import BackgroundTasks
from sqlmodel import Session

from ..core.config import settings
from ..database import engine
from ..models import Document, DocumentStatus
from . import ingestion


def ingest_document(document_id: int) -> None:
    with Session(engine) as session:
        document = session.get(Document, document_id)
        if not document:
            return
        file_path = (
            settings.documents_dir / str(document.tenant_id) / f"{document.id}_{document.name}"
        )
        try:
            content = file_path.read_bytes()
            count = ingestion.ingest(
                session, document.name, content, document.tenant_id, document.id
            )
            document.status = DocumentStatus.ready
            document.chunk_count = count
        except Exception as exc:
            document.status = DocumentStatus.failed
            document.error = str(exc)
        session.add(document)
        session.commit()


def enqueue_ingest(background: BackgroundTasks, document_id: int) -> None:
    if settings.redis_url:
        from redis import Redis
        from rq import Queue

        queue = Queue("ingest", connection=Redis.from_url(settings.redis_url))
        queue.enqueue("app.services.tasks.ingest_document", document_id)
    else:
        background.add_task(ingest_document, document_id)
