import io
from pathlib import Path

from pypdf import PdfReader
from docx import Document as DocxDocument

from ..core.config import settings
from . import vectorstore

CHUNK_SIZE = 1000
CHUNK_OVERLAP = 150


def extract_text(filename: str, content: bytes) -> str:
    suffix = Path(filename).suffix.lower()
    if suffix == ".pdf":
        reader = PdfReader(io.BytesIO(content))
        return "\n".join(page.extract_text() or "" for page in reader.pages)
    if suffix == ".docx":
        doc = DocxDocument(io.BytesIO(content))
        return "\n".join(p.text for p in doc.paragraphs)
    if suffix in (".txt", ".md"):
        return content.decode("utf-8", errors="ignore")
    raise ValueError(f"Formato no soportado: {suffix}")


def chunk_text(text: str) -> list[str]:
    text = " ".join(text.split())
    chunks = []
    start = 0
    while start < len(text):
        end = min(start + CHUNK_SIZE, len(text))
        chunks.append(text[start:end])
        if end == len(text):
            break
        start = end - CHUNK_OVERLAP
    return chunks


def ingest(
    filename: str,
    content: bytes,
    tenant_id: int,
    document_id: int,
):
    text = extract_text(filename, content)
    chunks = chunk_text(text)
    count = vectorstore.add_chunks(tenant_id, document_id, chunks)
    return count