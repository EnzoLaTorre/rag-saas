from chromadb import PersistentClient
from openai import OpenAI

from ..core.config import settings

CHROMA_PATH = "data/chroma"
EMBEDDING_MODEL = "text-embedding-3-small"

chroma = PersistentClient(path=CHROMA_PATH)
llm = OpenAI(api_key=settings.openai_api_key)


def _collection_for(tenant_id: int):
    return chroma.get_or_create_collection(
        f"tenant_{tenant_id}",
        metadata={"hnsw:space": "cosine"},
    )

def embed_texts(texts: list[str]):
    res = llm.embeddings.create(model=EMBEDDING_MODEL, input=texts)
    return [item.embedding for item in res.data]

def add_chunks(tenant_id: int, document_id: int, chunks: list[str]) -> int:
    collection = _collection_for(tenant_id)
    embeddings = embed_texts(chunks)
    collection.add(
        ids=[f"{document_id}_{i}" for i in range(len(chunks))],
        embeddings=embeddings,
        documents=chunks,
        metadatas=[
            {"document_id": document_id, "chunk_index": i}
            for i in range(len(chunks))
        ],
    )
    return len(chunks)

def search(tenant_id: int, query: str, document_id: int | None = None, top_k: int = 4):
    collection = _collection_for(tenant_id)
    where = {"document_id": document_id} if document_id else None
    result = collection.query(
        query_embeddings=embed_texts([query]),
        n_results=top_k,
        where=where,
    )
    return result

def delete_document(tenant_id: int, document_id: int):
    collection = _collection_for(tenant_id)
    collection.delete(where={"document_id": document_id}
)