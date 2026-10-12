from sqlalchemy import delete
from sqlmodel import Session, select

from ..models import Chunk
from .providers import get_provider


def add_chunks(session: Session, tenant_id: int, document_id: int, chunks: list[str]) -> int:
    embeddings = get_provider().embed(chunks)
    session.add_all(
        [
            Chunk(
                tenant_id=tenant_id,
                document_id=document_id,
                chunk_index=i,
                text=text,
                embedding=embedding,
            )
            for i, (text, embedding) in enumerate(zip(chunks, embeddings, strict=True))
        ]
    )
    session.commit()
    return len(chunks)


def search(
    session: Session,
    tenant_id: int,
    query: str,
    document_id: int | None = None,
    top_k: int = 4,
) -> list[Chunk]:
    query_embedding = get_provider().embed([query])[0]
    stmt = select(Chunk).where(Chunk.tenant_id == tenant_id)
    if document_id is not None:
        stmt = stmt.where(Chunk.document_id == document_id)
    stmt = stmt.order_by(Chunk.embedding.cosine_distance(query_embedding)).limit(top_k)
    return list(session.exec(stmt).all())


def delete_document(session: Session, tenant_id: int, document_id: int) -> None:
    session.exec(
        delete(Chunk).where(
            Chunk.tenant_id == tenant_id,
            Chunk.document_id == document_id,
        )
    )
    session.commit()
