from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    File,
    HTTPException,
    UploadFile,
    status,
)
from sqlmodel import Session, select

from ..core.config import settings
from ..core.deps import get_current_user
from ..core.ratelimit import RateLimiter
from ..database import get_session
from ..models import Document, User
from ..services import tasks, vectorstore

router = APIRouter(prefix="/documents", tags=["documents"])
upload_limiter = RateLimiter(settings.rate_limit_requests, settings.rate_limit_window_seconds)


@router.post("")
def upload_document(
    background: BackgroundTasks,
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    if not upload_limiter.allow(f"upload:{user.id}"):
        raise HTTPException(
            status.HTTP_429_TOO_MANY_REQUESTS, "Demasiadas subidas, inténtalo en un momento"
        )

    content = file.file.read()
    max_bytes = settings.max_upload_mb * 1024 * 1024
    if len(content) > max_bytes:
        raise HTTPException(
            status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            f"El archivo supera el límite de {settings.max_upload_mb} MB",
        )

    document = Document(
        tenant_id=user.tenant_id,
        name=file.filename,
        filename=file.filename,
        content_type=file.content_type,
        size=len(content),
    )
    session.add(document)
    session.commit()
    session.refresh(document)

    doc_dir = settings.documents_dir / str(user.tenant_id)
    doc_dir.mkdir(parents=True, exist_ok=True)
    file_path = doc_dir / f"{document.id}_{document.name}"
    file_path.write_bytes(content)

    tasks.enqueue_ingest(background, document.id)
    return document


@router.get("")
def list_documents(
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    docs = session.exec(select(Document).where(Document.tenant_id == user.tenant_id)).all()
    return docs


@router.delete("/{document_id}")
def delete_document(
    document_id: int,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    document = session.get(Document, document_id)
    if not document or document.tenant_id != user.tenant_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Documento no encontrado")

    vectorstore.delete_document(session, user.tenant_id, document_id)
    file_path = settings.documents_dir / str(user.tenant_id) / f"{document.id}_{document.name}"
    if file_path.exists():
        file_path.unlink()
    session.delete(document)
    session.commit()
    return {"status": "deleted"}
