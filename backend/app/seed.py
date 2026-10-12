"""Crea un tenant demo con un usuario admin e ingiere documentos de ejemplo.

Uso:
    python -m app.seed

Requiere el proveedor de IA configurado (Ollama o nube) para generar embeddings
y las tablas creadas (Alembic o `create_all`).
"""

from pathlib import Path

from sqlalchemy import text
from sqlmodel import Session, SQLModel, select

from .core.config import settings
from .core.security import hash_password
from .database import engine
from .models import Document, DocumentStatus, Role, Tenant, User
from .services import ingestion

SAMPLE_DIR = Path(__file__).resolve().parent.parent / "sample_docs"

DEMO_TENANT = "Demo Corp"
DEMO_EMAIL = "demo@example.com"
DEMO_PASSWORD = "demo1234"


def _ensure_schema() -> None:
    with engine.begin() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
    SQLModel.metadata.create_all(engine)


def seed() -> None:
    _ensure_schema()

    with Session(engine) as session:
        tenant = session.exec(select(Tenant).where(Tenant.name == DEMO_TENANT)).first()
        if not tenant:
            tenant = Tenant(name=DEMO_TENANT)
            session.add(tenant)
            session.commit()
            session.refresh(tenant)
            print(f"Tenant creado: {tenant.name} (#{tenant.id})")

        user = session.exec(select(User).where(User.email == DEMO_EMAIL)).first()
        if not user:
            user = User(
                tenant_id=tenant.id,
                email=DEMO_EMAIL,
                hashed_password=hash_password(DEMO_PASSWORD),
                full_name="Usuario Demo",
                role=Role.admin,
            )
            session.add(user)
            session.commit()
            print(f"Usuario creado: {DEMO_EMAIL} / {DEMO_PASSWORD}")

        doc_dir = settings.documents_dir / str(tenant.id)
        doc_dir.mkdir(parents=True, exist_ok=True)

        for path in sorted(SAMPLE_DIR.glob("*")):
            if not path.is_file():
                continue
            existing = session.exec(
                select(Document).where(
                    Document.tenant_id == tenant.id,
                    Document.name == path.name,
                )
            ).first()
            if existing:
                print(f"Ya existe: {path.name}")
                continue

            content = path.read_bytes()
            document = Document(
                tenant_id=tenant.id,
                name=path.name,
                filename=path.name,
                content_type="text/plain",
                size=len(content),
                status=DocumentStatus.processing,
            )
            session.add(document)
            session.commit()
            session.refresh(document)

            (doc_dir / f"{document.id}_{document.name}").write_bytes(content)

            count = ingestion.ingest(session, document.name, content, tenant.id, document.id)
            document.status = DocumentStatus.ready
            document.chunk_count = count
            session.add(document)
            session.commit()
            print(f"Ingerido: {path.name} ({count} chunks)")

    print("\nSeed completado.")


if __name__ == "__main__":
    print(f"Proveedor de IA: {settings.ai_provider} (dim {settings.embedding_dim})")
    seed()
