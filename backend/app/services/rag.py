import json

from sqlmodel import Session

from ..models import Chunk
from . import vectorstore
from .providers import get_provider

SYSTEM_PROMPT = (
    "Eres un asistente que responde usando únicamente el contexto que se te da. "
    "Si la respuesta no está en el contexto, di que no tienes esa información. "
    "Responde de forma clara y concisa en el mismo idioma de la pregunta."
)


def _unwrap(chunks: list[Chunk]) -> list[dict]:
    return [
        {
            "chunk_id": str(chunk.id),
            "text": chunk.text,
            "document_id": chunk.document_id,
            "chunk_index": chunk.chunk_index,
        }
        for chunk in chunks
    ]


def answer_stream(
    session: Session,
    tenant_id: int,
    question: str,
    document_id: int | None = None,
    top_k: int = 4,
):
    chunks = vectorstore.search(session, tenant_id, question, document_id=document_id, top_k=top_k)
    sources = _unwrap(chunks)

    yield json.dumps({"type": "sources", "sources": sources}, ensure_ascii=False) + "\n"

    context = "\n\n".join(f"[Fuente {i + 1}]\n{c['text']}" for i, c in enumerate(sources))
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"Contexto:\n{context}\n\nPregunta:\n{question}"},
    ]

    full = ""
    for delta in get_provider().chat_stream(messages):
        full += delta
        yield json.dumps({"type": "token", "content": delta}, ensure_ascii=False) + "\n"

    yield (
        json.dumps({"type": "done", "answer": full, "sources": sources}, ensure_ascii=False) + "\n"
    )
