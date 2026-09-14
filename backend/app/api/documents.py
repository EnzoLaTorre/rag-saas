from pathlib import Path

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

from ..core.deps import get_current_user
from ..database import get_session, engine
from ..models import Document, DocumentStatus, User
from ..services import ingestion, vectorstore

router = APIRouter(prefix="/documents", tags=["documents"])
DATA_DIR = Path("data/documents")


@router.post("")
def upload_document(
    background: BackgroundTasks,
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    content = file.file.read()

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

    doc_dir = DATA_DIR / str(user.tenant_id)
    doc_dir.mkdir(parents=True, exist_ok=True)
    file_path = doc_dir / f"{document.id}_{document.name}"
    file_path.write_bytes(content)

    background.add_task(process_in_background, document.id)
    return document


def process_in_background(document_id: int):
    with Session(engine) as session:
        document = session.get(Document, document_id)
        file_path = DATA_DIR / str(document.tenant_id) / f"{document.id}_{document.name}"
        try:
            content = file_path.read_bytes()
            count = ingestion.ingest(document.name, content, document.tenant_id, document.id)
            document.status = DocumentStatus.ready
            document.chunk_count = count
        except Exception as exc:
            document.status = DocumentStatus.failed
            document.error = str(exc)
        session.add(document)
        session.commit()


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

    vectorstore.delete_document(user.tenant_id, document_id)
    file_path = DATA_DIR / str(user.tenant_id) / f"{document.id}_{document.name}"
    if file_path.exists():
        file_path.unlink()
    session.delete(document)
    session.commit()
    return {"status": "deleted"}