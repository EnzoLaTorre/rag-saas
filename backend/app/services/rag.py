import json

from ..core.config import settings
from . import vectorstore

MODEL = "gpt-4o-mini"
SYSTEM_PROMPT = (
    "Eres un asistente que responde usando únicamente el contexto que se te da. "
    "Si la respuesta no está en el contexto, di que no tienes esa información. "
    "Responde de forma clara y concisa en el mismo idioma de la pregunta."
)


def _unwrap(result):
    out = []
    for i, chunk_id in enumerate(result["ids"][0]):
        out.append({
            "chunk_id": chunk_id,
            "text": result["documents"][0][i],
            "document_id": result["metadatas"][0][i]["document_id"],
            "chunk_index": result["metadatas"][0][i]["chunk_index"],
        })
    return out


def answer_stream(tenant_id: int, question: str, document_id: int | None = None, top_k: int = 4):
    result = vectorstore.search(tenant_id, question, document_id=document_id, top_k=top_k)
    chunks = _unwrap(result)

    yield json.dumps({"type": "sources", "sources": chunks}, ensure_ascii=False) + "\n"

    context = "\n\n".join(f"[Fuente {i + 1}]\n{c['text']}" for i, c in enumerate(chunks))
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"Contexto:\n{context}\n\nPregunta:\n{question}"},
    ]

    stream = vectorstore.llm.chat.completions.create(
        model=MODEL,
        messages=messages,
        stream=True,
        temperature=0.2,
    )

    full = ""
    for part in stream:
        delta = part.choices[0].delta.content
        if delta:
            full += delta
            yield json.dumps({"type": "token", "content": delta}, ensure_ascii=False) + "\n"

    yield json.dumps({"type": "done", "answer": full, "sources": chunks}, ensure_ascii=False) + "\n"