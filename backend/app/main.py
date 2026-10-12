from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from .api import auth, chat, documents
from .core.config import settings
from .database import engine
from .models import SQLModel


@asynccontextmanager
async def lifespan(app: FastAPI):
    # La extensión `vector` debe existir antes de crear la tabla `chunk`.
    with engine.begin() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
    SQLModel.metadata.create_all(engine)
    yield


app = FastAPI(title="RAG SaaS", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api")
app.include_router(documents.router, prefix="/api")
app.include_router(chat.router, prefix="/api")


@app.get("/")
def root():
    return {"message": "RAG SaaS API"}


@app.get("/health")
def health():
    return {"status": "ok"}
