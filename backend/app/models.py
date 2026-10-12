from datetime import datetime
from enum import Enum

from pgvector.sqlalchemy import Vector
from sqlalchemy import Column
from sqlmodel import Field, SQLModel

from .core.config import settings


class Role(str, Enum):
    admin = "admin"
    user = "user"


class Tenant(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str
    created_at: datetime = Field(default_factory=datetime.utcnow)


class User(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    tenant_id: int = Field(foreign_key="tenant.id")
    email: str = Field(index=True, unique=True)
    hashed_password: str
    full_name: str = ""
    role: Role = Role.user
    created_at: datetime = Field(default_factory=datetime.utcnow)


class DocumentStatus(str, Enum):
    processing = "processing"
    ready = "ready"
    failed = "failed"
    deleted = "deleted"


class Document(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    tenant_id: int = Field(foreign_key="tenant.id")
    name: str
    filename: str
    content_type: str
    size: int
    status: DocumentStatus = DocumentStatus.processing
    chunk_count: int = 0
    error: str | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Chunk(SQLModel, table=True):
    """Fragmento de documento con su embedding, almacenado en pgvector.

    La dimensión del vector depende del proveedor de embeddings activo
    (`EMBEDDING_DIM`). Cambiar de proveedor requiere reindexar.
    """

    id: int | None = Field(default=None, primary_key=True)
    tenant_id: int = Field(foreign_key="tenant.id", index=True)
    document_id: int = Field(foreign_key="document.id", index=True)
    chunk_index: int
    text: str
    embedding: list[float] = Field(sa_column=Column(Vector(settings.embedding_dim)))


class ChatMessage(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    tenant_id: int = Field(foreign_key="tenant.id")
    user_id: int = Field(foreign_key="user.id")
    question: str
    answer: str
    sources_json: str = ""
    created_at: datetime = Field(default_factory=datetime.utcnow)
